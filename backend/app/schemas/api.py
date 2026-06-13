from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# Row-level ingestion schema (for validation in service)
class BatteryIngestRow(BaseModel):
    external_ref: str
    oem: str
    model: Optional[str] = None
    chemistry: str
    rated_capacity_kwh: float
    nominal_voltage: Optional[float] = None
    manufacture_date: Optional[date] = None
    source_city: Optional[str] = None
    source_state: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    cycle_count: int
    capacity_now_kwh: float
    avg_temp_c: Optional[float] = None
    max_temp_c: Optional[float] = None
    thermal_stress_hours: Optional[float] = None
    internal_resistance_mohm: Optional[float] = None
    ir_growth_pct: Optional[float] = None
    coulombic_efficiency: Optional[float] = None
    
    # Optional Must-Fix #1 columns
    fade_rate: Optional[float] = None
    fade_acceleration: Optional[float] = None
    cv_phase_fraction: Optional[float] = None
    voltage_slope: Optional[float] = None
    voltage_variance: Optional[float] = None
    discharge_efficiency: Optional[float] = None


# Ingestion request (JSON payload format)
class IngestRequest(BaseModel):
    batteries: List[Dict[str, Any]]


# Reject details
class IngestReject(BaseModel):
    row: int
    reason: str


# Ingest response
class IngestResponse(BaseModel):
    job_id: str
    accepted: int
    rejected: int
    rejects: List[IngestReject]


# Job Status response
class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued | running | done | failed
    processed: int
    total: int
    recent_events: List[Dict[str, Any]]


# Battery Summary (for list view)
class BatterySummaryItem(BaseModel):
    id: int
    aadhaar_id: Optional[str] = None
    external_ref: str
    oem: str
    chemistry: str
    rated_capacity_kwh: float
    status: str
    soh_pct: Optional[float] = None
    rul_years: Optional[float] = None
    grade: Optional[str] = None
    confidence: Optional[str] = None
    site_name: Optional[str] = None


# Paginated Battery list response
class BatteryListResponse(BaseModel):
    items: List[BatterySummaryItem]
    total: int
    page: int


# Battery Detail response
class BatteryDetailResponse(BaseModel):
    id: int
    aadhaar_id: Optional[str] = None
    external_ref: str
    oem: str
    model: Optional[str] = None
    chemistry: str
    form_factor: str
    rated_capacity_kwh: float
    nominal_voltage: Optional[float] = None
    manufacture_date: Optional[date] = None
    source_city: Optional[str] = None
    source_state: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    status: str
    created_at: datetime
    
    telemetry: Optional[Dict[str, Any]] = None
    assessment: Optional[Dict[str, Any]] = None
    deployment: Optional[Dict[str, Any]] = None


# Aadhaar Passport Decoded segment
class AadhaarDecoded(BaseModel):
    country: str
    manufacturer: str
    chemistry: str
    voltage: str
    capacity_kwh: float
    manufactured: date
    serial: str


# Aadhaar Passport response (composed, matches docs/04 format)
class AadhaarPassportResponse(BaseModel):
    aadhaar_id: str
    decoded: AadhaarDecoded
    qr_payload: str
    static: Dict[str, Any]
    dynamic: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    life_story: str
    impact: Dict[str, Any]


# Sites response items
class SiteItem(BaseModel):
    id: int
    name: str
    site_type: str
    state: Optional[str] = None
    lat: float
    lng: float
    demand_kwh: float
    remaining_kwh: float
    min_grade: str
    assigned_count: int


class SiteListResponse(BaseModel):
    items: List[SiteItem]


# Impact summary response
class ImpactSummaryResponse(BaseModel):
    mwh_unlocked: float
    carbon_saved_tonnes: float
    diverted_from_recycling: int
    recycled_responsibly: int
    processed: int
    total: int
    by_grade: Dict[str, int]
    by_site_type: Dict[str, int]
