from fastapi import APIRouter, HTTPException, status
from app.services.pipeline import JOBS
from app.core.events import manager as ws_manager

router = APIRouter(prefix="/api/v1", tags=["jobs"])

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """
    Returns progress and status for an ingestion job.
    Serves as the dual-path HTTP polling fallback for WebSockets.
    """
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "job_not_found", "message": f"Job {job_id} not found"}}
        )

    # Return status payload, attaching the last 20 events from the connection manager's ring buffer
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "processed": job["processed"],
        "total": job["total"],
        "recent_events": list(ws_manager.ring_buffer)
    }
