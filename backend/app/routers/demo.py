import os
import json
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.orm import Battery, TelemetrySummary, Assessment, Deployment, LifecycleEvent, Site
from app.seed.seed import seed_sites, seed_marketplace_demo_users
from app.services.pipeline import JOBS
from app.core.events import manager as ws_manager
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["demo"])

# Dependency checking the Demo Key header
def verify_demo_key(x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key")):
    if x_demo_key != settings.DEMO_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "bad_demo_key", "message": "Invalid Demo Key provided in X-Demo-Key header"}}
        )
    return x_demo_key


@router.post("/demo/reset")
async def reset_demo(
    db: Session = Depends(get_db),
    _ = Depends(verify_demo_key)
):
    """
    Resets the application state. Wipes batteries, assessments, deployments, 
    and lifecycle events. Reseeds the sites table and clears event buffers.
    """
    logger.info("Demo reset requested. Wiping data tables...")
    
    # Set all active jobs as cancelled
    for job in JOBS.values():
        if job["status"] == "running":
            job["status"] = "cancelled"
            
    JOBS.clear()

    # Wipe tables in proper dependency order
    try:
        db.query(Deployment).delete()
        db.query(Assessment).delete()
        db.query(TelemetrySummary).delete()
        db.query(LifecycleEvent).delete()
        db.query(Battery).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to wipe data tables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "reset_failed", "message": f"Wipe database failed: {str(e)}"}}
        )
        
    # Reseed sites table
    seed_sites(db)
    
    # Reseed marketplace demo users (buyer + verified supplier)
    seed_marketplace_demo_users(db)
    
    # Clear WebSocket event ring buffer
    ws_manager.ring_buffer.clear()
    
    # Broadcast zeroed impact metrics to reset clients
    await ws_manager.broadcast({
        "type": "impact",
        "payload": {
            "mwh_unlocked": 0.0,
            "carbon_saved_tonnes": 0.0,
            "diverted_from_recycling": 0,
            "recycled_responsibly": 0,
            "processed": 0,
            "total": 0
        }
    })
    
    return {"status": "success", "message": "Demo reset completed successfully"}


async def run_replay_task(replay_file_path: str):
    """
    Background worker that streams a pre-recorded event file.
    """
    logger.info(f"Replay task started. Loading events from {replay_file_path}")
    try:
        with open(replay_file_path, "r") as f:
            events = json.load(f)
            
        logger.info(f"Loaded {len(events)} events. Commencing paced broadcast...")
        
        for event in events:
            # Broadcast identical payload structure
            await ws_manager.broadcast(event)
            # Pace it matching configuration
            await asyncio.sleep(settings.PACE_S)
            
        logger.info("Replay completed successfully.")
    except Exception as e:
        logger.error(f"Error during WebSocket replay task: {e}")


@router.post("/demo/replay", status_code=202)
def replay_demo(
    background_tasks: BackgroundTasks,
    _ = Depends(verify_demo_key)
):
    """
    Plays back a pre-recorded simulation run via WebSockets.
    Saves and loops pre-recorded JSON logs from seed/replay_results.json.
    """
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    replay_path = os.path.join(current_dir, "seed", "replay_results.json")
    
    if not os.path.exists(replay_path) or os.path.getsize(replay_path) == 0:
        logger.error(f"Replay results file not found or empty at {replay_path}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "no_replay_file", "message": "Pre-recorded replay file seed/replay_results.json is missing or empty"}}
        )
        
    # Queue replay background task
    background_tasks.add_task(run_replay_task, replay_path)
    
    return {"status": "success", "message": "Demo replay initiated"}
