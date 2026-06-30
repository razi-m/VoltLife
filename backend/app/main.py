import os
import sys

# Vercel fix: Add the 'backend' directory to sys.path so 'from app.X import Y' works!
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.events import manager as ws_manager
from app.db.database import init_db, SessionLocal
from app.routers import batteries, jobs, sites, impact, demo, healthz, dashboard, deployments, analytics, ai, marketplace, suppliers, buyers, requirements, quotes, payments, logistics, subscriptions, razorpay_payments

# Initialize Logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.2",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handlers conforming to frozen error envelope
# Envelope: {"error": {"code": "<machine_string>", "message": "<human>"}}
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request validation failed: {exc}")
    errors = exc.errors()
    msg = errors[0]["msg"] if errors else "Invalid request payload"
    # Format field path
    if errors and "loc" in errors[0]:
        field = ".".join(str(x) for x in errors[0]["loc"])
        msg = f"Field validation failed at '{field}': {msg}"
        
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "validation_error", "message": msg}}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "bad_request", "message": str(exc.detail)}}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": {"code": "internal_error", "message": "An unexpected error occurred on the server."}}
    )


# WebSocket feed endpoint (outside API version prefix)
@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; server ignores client payloads
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket endpoint exception: {e}")
        ws_manager.disconnect(websocket)


# Register APIRouters
app.include_router(healthz.router)  # /healthz (outside version prefix)
app.include_router(batteries.router)  # /api/v1/batteries
app.include_router(jobs.router)  # /api/v1/jobs
app.include_router(sites.router)  # /api/v1/sites
app.include_router(impact.router)  # /api/v1/impact
app.include_router(demo.router)  # /api/v1/demo
app.include_router(dashboard.router)  # /api/v1/dashboard
app.include_router(deployments.router)  # /api/v1/deployments
app.include_router(analytics.router)  # /api/v1/analytics
app.include_router(ai.router)  # /api/v1/ai
app.include_router(marketplace.router)  # /api/v1/marketplace
app.include_router(suppliers.router)
app.include_router(buyers.router)
app.include_router(requirements.router)
app.include_router(quotes.router)
app.include_router(payments.router)
app.include_router(logistics.router)
app.include_router(subscriptions.router)
app.include_router(razorpay_payments.router)  # /api/v1/payments/razorpay (additive; Stripe untouched)





# Database check and seeding on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing VoltLife backend startup tasks...")
    # Setup database/SQLite
    init_db()
    
    # Check if sites exist, if empty seed them
    db = SessionLocal()
    try:
        from app.models.orm import Site
        site_count = db.query(Site).count()
        if site_count == 0:
            logger.info("Sites table is empty. Seeding demand sites...")
            from app.seed.seed import seed_sites
            seed_sites(db)
        else:
            logger.info(f"Database already seeded. Found {site_count} demand sites.")
            
        # Write a dummy replay results file if it doesn't exist to prevent replay failures
        current_dir = os.path.dirname(os.path.abspath(__file__))
        replay_file = os.path.join(current_dir, "seed", "replay_results.json")
        if not os.path.exists(replay_file) or os.path.getsize(replay_file) == 0:
            logger.info("Replay results file missing or empty. Seeding basic mock replay...")
            mock_replay_events = [
                {
                    "type": "assessment",
                    "payload": {
                        "battery_id": 1,
                        "aadhaar_id": "INFOAN480415032400231",
                        "oem": "FOA",
                        "soh_pct": 82.4,
                        "rul_years": 4.3,
                        "rul_range": [3.1, 5.2],
                        "grade": "A",
                        "confidence": "high",
                        "reasons": ["Low thermal stress", "Stable voltage profile"],
                        "lat": 18.52,
                        "lng": 73.85
                    }
                },
                {
                    "type": "deployment",
                    "payload": {
                        "battery_id": 1,
                        "site_id": 1,
                        "site_name": "Bhadla Solar Park Storage, RJ",
                        "site_type": "solar_storage",
                        "score": 0.87,
                        "distance_km": 1142.0,
                        "reasons": ["Best capacity match", "Grade A meets solar bar"],
                        "energy_unlocked_mwh": 3.06,
                        "carbon_saved_kg": 197.8,
                        "from": [18.52, 73.85],
                        "to": [27.54, 71.91]
                    }
                }
            ]
            try:
                with open(replay_file, "w") as f:
                    json.dump(mock_replay_events, f, indent=2)
            except OSError as e:
                logger.warning(f"Could not write mock replay file (read-only filesystem?): {e}")
                
    except Exception as e:
        logger.error(f"VoltLife startup seeding failed: {e}")
    finally:
        db.close()
