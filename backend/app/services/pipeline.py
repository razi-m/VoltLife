import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.orm import Battery, Assessment, TelemetrySummary
from app.ml.predictor import assess
from app.schemas.ml import AssessmentResult
from app.services.aadhaar import issue_aadhaar, append_lifecycle_event
from app.services.deployment import decide_deployment
from app.services.impact import get_impact_summary
from app.core.events import manager as ws_manager
from app.core.config import settings
from app.core.logging import logger

# In-memory job registry
JOBS: Dict[str, Dict[str, Any]] = {}

def process_single_battery(db: Session, battery_id: int, serial_num: int) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Performs the database-bound assessment, Aadhaar issue, and deployment decision in a single transaction.
    This runs inside a background thread via asyncio.to_thread.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise ValueError(f"Battery {battery_id} not found")

    # 1. Construct canonical feature vector
    telemetry = battery.telemetry
    if not telemetry:
        raise ValueError(f"Telemetry summary missing for battery {battery_id}")
        
    features = telemetry.features_json

    # 2. Run ML Predictor assessment
    assessment_result = assess(features)

    # 2b. ML SEAM VALIDATION (Excellence Pass T1): enforce the frozen output contract
    # (ranges, enums, rul_cycles <= 2400 clamp, rul ordering) before anything is persisted.
    # A future model returning invalid output fails HERE, loudly, per battery - never on the wire.
    assessment_result = AssessmentResult(**assessment_result).model_dump()
    
    # 3. Save Assessment record
    assessment = Assessment(
        battery_id=battery.id,
        soh_pct=assessment_result["soh_pct"],
        rul_years=assessment_result["rul_years"],
        rul_low_years=assessment_result["rul_low"],
        rul_high_years=assessment_result["rul_high"],
        grade=assessment_result["grade"],
        confidence=assessment_result["confidence"],
        model_version="v1.2-stub",
        explanation_json=assessment_result["explanation"]
    )
    db.add(assessment)
    db.flush()
    
    # Attach transient rul_cycles for deployment logic (not stored in DB)
    assessment.rul_cycles = assessment_result["rul_cycles"]

    # 4. Issue Aadhaar (BPAN ID + Timeline events)
    issue_aadhaar(db, battery, serial_num)
    
    # 5. Make Deployment decision
    deployment_payload = decide_deployment(db, battery, assessment)
    
    # 6. Advance battery status and update timeline (aadhaar logs inside)
    # Status is handled inside decide_deployment
    append_lifecycle_event(
        db, battery.id, "assessed",
        payload={"soh_pct": assessment_result["soh_pct"], "grade": assessment_result["grade"]}
    )
    append_lifecycle_event(db, battery.id, "aadhaar_issued")

    db.commit()

    # Construct WS assessment payload
    assessment_payload = {
        "battery_id": battery.id,
        "aadhaar_id": battery.aadhaar_id,
        "oem": battery.oem,
        "soh_pct": float(assessment.soh_pct),
        "rul_years": float(assessment.rul_years),
        "rul_range": [float(assessment.rul_low_years), float(assessment.rul_high_years)],
        "grade": assessment.grade,
        "confidence": assessment.confidence,
        "reasons": assessment_result["reasons"],
        "lat": float(battery.lat),
        "lng": float(battery.lng)
    }

    return assessment_payload, deployment_payload


async def run_pipeline_task(job_id: str, battery_ids: List[int]):
    """
    Asynchronous background task coordinating the processing loop for a batch of batteries.
    """
    logger.info(f"Starting pipeline processing for job {job_id} containing {len(battery_ids)} batteries")
    
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",
        "processed": 0,
        "total": len(battery_ids),
        "failed_ids": [],
        "started_at": datetime.utcnow()
    }

    start_time = time.time()
    db = SessionLocal()
    
    try:
        for index, battery_id in enumerate(battery_ids, start=1):
            # Guard against job cancel (e.g. on demo reset)
            if JOBS.get(job_id, {}).get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled mid-run.")
                break
                
            try:
                # Run database transaction in separate thread to avoid event loop starvation
                serial_num = 10000 + battery_id  # Unique base serial number
                
                ass_payload, dep_payload = await asyncio.to_thread(
                    process_single_battery, db, battery_id, serial_num
                )
                
                # Broadcast assessment event
                await ws_manager.broadcast({
                    "type": "assessment",
                    "payload": ass_payload
                })
                
                # Broadcast deployment event (if routed successfully)
                if dep_payload:
                    await ws_manager.broadcast({
                        "type": "deployment",
                        "payload": dep_payload
                    })

                # Broadcast impact totals (every 5th battery, or at the end)
                if index % 5 == 0 or index == len(battery_ids):
                    impact_data = await asyncio.to_thread(get_impact_summary, db)
                    await ws_manager.broadcast({
                        "type": "impact",
                        "payload": {
                            "mwh_unlocked": impact_data["mwh_unlocked"],
                            "carbon_saved_tonnes": impact_data["carbon_saved_tonnes"],
                            "diverted_from_recycling": impact_data["diverted_from_recycling"],
                            "recycled_responsibly": impact_data["recycled_responsibly"],
                            "processed": impact_data["processed"],
                            "total": impact_data["total"]
                        }
                    })

            except Exception as e:
                logger.error(f"Error processing battery {battery_id} in pipeline: {e}", exc_info=True)
                JOBS[job_id]["failed_ids"].append(battery_id)
                # Mark battery status as error
                try:
                    bat = db.query(Battery).filter(Battery.id == battery_id).first()
                    if bat:
                        bat.status = "error"
                        db.commit()
                except Exception as inner_e:
                    db.rollback()
                    logger.error(f"Failed to mark battery {battery_id} as error: {inner_e}")

            # Increment progress
            JOBS[job_id]["processed"] += 1
            
            # Pacing sleep
            await asyncio.sleep(settings.PACE_S)

        # Mark job complete
        duration = time.time() - start_time
        if JOBS[job_id]["status"] != "cancelled":
            status = "failed" if len(JOBS[job_id]["failed_ids"]) == len(battery_ids) else "done"
            JOBS[job_id]["status"] = status
            
            logger.info(f"Pipeline job {job_id} complete. Status: {status}. Duration: {duration:.2f}s")
            
            # Broadcast job_done event
            await ws_manager.broadcast({
                "type": "job_done",
                "payload": {
                    "job_id": job_id,
                    "duration_s": round(duration, 1)
                }
            })
            
    finally:
        db.close()
