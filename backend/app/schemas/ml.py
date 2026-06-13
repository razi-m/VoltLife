from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class AssessmentResult(BaseModel):
    soh_pct: float = Field(..., ge=0.0, le=100.0)
    rul_cycles: int = Field(..., ge=0, le=2400)  # Must-Fix #2 clamp rule
    rul_years: float = Field(..., ge=0.0, le=8.0)
    rul_low: float = Field(..., ge=0.0, le=8.0)
    rul_high: float = Field(..., ge=0.0, le=8.0)
    grade: str = Field(..., pattern="^[SABCD]$")
    confidence: str = Field(..., pattern="^(high|medium|low)$")
    explanation: List[Dict[str, Any]]
    reasons: List[str]

    @field_validator("rul_high")
    @classmethod
    def check_rul_bounds(cls, v: float, info):
        # Enforce rul_low <= rul_years <= rul_high
        values = info.data
        if "rul_low" in values and values["rul_low"] > v:
            raise ValueError("rul_low must be less than or equal to rul_high")
        return v

class RecommendationItem(BaseModel):
    destination: str
    site_id: int
    score: int = Field(..., ge=0, le=100)
    factors: List[str]

class RecommendationResult(BaseModel):
    recommendations: List[RecommendationItem]
    selected_destination: Optional[str] = None
    selected_site_id: Optional[int] = None
    energy_unlocked_mwh: float = Field(..., ge=0.0)
    carbon_saved_kg: float = Field(..., ge=0.0)
