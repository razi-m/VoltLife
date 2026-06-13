from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.api import ImpactSummaryResponse
from app.services.impact import get_impact_summary

router = APIRouter(prefix="/api/v1", tags=["impact"])

@router.get("/impact/summary", response_model=ImpactSummaryResponse)
def get_sustainability_summary(db: Session = Depends(get_db)):
    """
    Returns live fleet-wide sustainability aggregates (MWh unlocked, CO2 saved, grade mixes).
    """
    return get_impact_summary(db)
