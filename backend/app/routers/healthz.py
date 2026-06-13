from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.db.database import get_db

router = APIRouter(tags=["healthz"])

@router.get("/healthz")
def healthz(db: Session = Depends(get_db)):
    """
    Simple pre-flight endpoint validating system health.
    Checks DB availability and returns current loaded model version.
    """
    db_status = "down"
    try:
        # Check connection is active
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        pass
        
    return {
        "ok": db_status == "up",
        "model_version": "v1.2-stub",
        "db": db_status
    }
