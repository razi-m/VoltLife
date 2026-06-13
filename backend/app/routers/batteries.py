import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.orm import Battery, Assessment, Deployment, Site
from app.schemas.api import IngestRequest, IngestResponse, BatteryListResponse, BatteryDetailResponse, AadhaarPassportResponse
from app.services.ingestion import parse_csv_file, process_ingestion
from app.services.pipeline import run_pipeline_task, JOBS
from app.services.aadhaar import compose_passport
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["batteries"])

@router.post("/batteries/ingest", status_code=202)
async def ingest_batteries(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Ingests a fleet of batteries via Multipart CSV or JSON array.
    Spawns background lifecycle pipeline processing.
    """
    # Guard: One job at a time
    for job in JOBS.values():
        if job["status"] == "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "job_already_running", "message": "Another ingestion job is already running"}}
            )

    content_type = request.headers.get("content-type", "")
    rows = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file or not hasattr(file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "empty_file", "message": "No CSV file provided in multipart/form-data"}}
            )
        content = await file.read()
        try:
            rows = parse_csv_file(content.decode("utf-8"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_csv", "message": f"Failed to parse CSV: {str(e)}"}}
            )
    elif "application/json" in content_type:
        try:
            data = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_json", "message": f"Failed to parse JSON: {str(e)}"}}
            )
        if not isinstance(data, dict) or "batteries" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "empty_file", "message": "JSON payload must contain a 'batteries' list"}}
            )
        rows = data["batteries"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "unsupported_media_type", "message": "Unsupported Content-Type. Use multipart/form-data or application/json"}}
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "empty_file", "message": "No records found in upload"}}
        )

    try:
        inserted_ids, rejects = process_ingestion(db, rows)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": {"code": "too_large", "message": str(ve)}}
        )

    # Job ID generation
    job_id = f"j_{uuid.uuid4().hex[:6]}"

    if inserted_ids:
        # Spawn the BackgroundTask pacing processing
        background_tasks.add_task(run_pipeline_task, job_id, inserted_ids)
    else:
        # Empty job
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "processed": 0,
            "total": 0,
            "failed_ids": [],
            "started_at": datetime.utcnow()
        }

    return {
        "job_id": job_id,
        "accepted": len(inserted_ids),
        "rejected": len(rejects),
        "rejects": rejects
    }


@router.get("/batteries", response_model=BatteryListResponse)
def list_batteries(
    grade: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "desc",
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of batteries with their latest grade and deployment destination.
    Supports text search on aadhaar_id, external_ref, oem and sorting.
    """
    page_size = min(200, max(1, page_size))
    page = max(1, page)
    offset = (page - 1) * page_size

    query = db.query(Battery)

    if status:
        query = query.filter(Battery.status == status)

    # Text search across key fields
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Battery.aadhaar_id.ilike(search_term)) |
            (Battery.external_ref.ilike(search_term)) |
            (Battery.oem.ilike(search_term)) |
            (Battery.chemistry.ilike(search_term))
        )

    # Filter by grade requires joining assessment
    if grade:
        # Join with subquery of latest assessments
        subq = db.query(
            Assessment.battery_id,
            Assessment.grade,
            func.row_number().over(
                partition_by=Assessment.battery_id,
                order_by=Assessment.created_at.desc()
            ).label("rn")
        ).subquery()
        query = query.join(subq, Battery.id == subq.c.battery_id).filter(
            subq.c.rn == 1,
            subq.c.grade == grade
        )

    # Sorting
    sort_columns = {
        "id": Battery.id,
        "external_ref": Battery.external_ref,
        "oem": Battery.oem,
        "chemistry": Battery.chemistry,
        "rated_capacity_kwh": Battery.rated_capacity_kwh,
        "status": Battery.status,
        "created_at": Battery.created_at,
    }
    sort_col = sort_columns.get(sort_by, Battery.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    batteries = query.offset(offset).limit(page_size).all()

    items = []
    for b in batteries:
        # Load latest assessment
        ass = db.query(Assessment).filter(Assessment.battery_id == b.id).order_by(Assessment.created_at.desc()).first()
        # Load deployment site
        dep = db.query(Deployment).filter(Deployment.battery_id == b.id).order_by(Deployment.created_at.desc()).first()
        
        items.append({
            "id": b.id,
            "aadhaar_id": b.aadhaar_id,
            "external_ref": b.external_ref,
            "oem": b.oem,
            "chemistry": b.chemistry,
            "rated_capacity_kwh": float(b.rated_capacity_kwh),
            "status": b.status,
            "soh_pct": float(ass.soh_pct) if ass else None,
            "rul_years": float(ass.rul_years) if ass else None,
            "grade": ass.grade if ass else None,
            "confidence": ass.confidence if ass else None,
            "site_name": dep.site.name if dep and dep.site else None
        })

    return {
        "items": items,
        "total": total,
        "page": page
    }


@router.get("/batteries/{battery_id}", response_model=BatteryDetailResponse)
def get_battery(battery_id: int, db: Session = Depends(get_db)):
    """
    Returns full details for a single battery, including telemetry and latest assessment/deployment.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "battery_not_found", "message": f"Battery {battery_id} not found"}}
        )

    ass = db.query(Assessment).filter(Assessment.battery_id == battery.id).order_by(Assessment.created_at.desc()).first()
    dep = db.query(Deployment).filter(Deployment.battery_id == battery.id).order_by(Deployment.created_at.desc()).first()

    telemetry_dict = None
    if battery.telemetry:
        telemetry_dict = {
            "cycle_count": battery.telemetry.cycle_count,
            "capacity_now_kwh": float(battery.telemetry.capacity_now_kwh) if battery.telemetry.capacity_now_kwh else None,
            "capacity_fade_pct": float(battery.telemetry.capacity_fade_pct) if battery.telemetry.capacity_fade_pct else None,
            "avg_temp_c": float(battery.telemetry.avg_temp_c) if battery.telemetry.avg_temp_c else None,
            "max_temp_c": float(battery.telemetry.max_temp_c) if battery.telemetry.max_temp_c else None,
            "thermal_stress_hours": float(battery.telemetry.thermal_stress_hours) if battery.telemetry.thermal_stress_hours else None,
            "internal_resistance_mohm": float(battery.telemetry.internal_resistance_mohm) if battery.telemetry.internal_resistance_mohm else None,
            "ir_growth_pct": float(battery.telemetry.ir_growth_pct) if battery.telemetry.ir_growth_pct else None,
            "voltage_stability": float(battery.telemetry.voltage_stability) if battery.telemetry.voltage_stability else None,
            "coulombic_efficiency": float(battery.telemetry.coulombic_efficiency) if battery.telemetry.coulombic_efficiency else None
        }

    assessment_dict = None
    if ass:
        assessment_dict = {
            "soh_pct": float(ass.soh_pct),
            "rul_years": float(ass.rul_years),
            "rul_range": [float(ass.rul_low_years), float(ass.rul_high_years)],
            "grade": ass.grade,
            "confidence": ass.confidence,
            "reasons": [e["label"] for e in ass.explanation_json[:3]],
            "explanation_json": ass.explanation_json
        }

    deployment_dict = None
    if dep:
        site = dep.site
        deployment_dict = {
            "site_id": site.id,
            "site_name": site.name,
            "site_type": site.site_type,
            "score": float(dep.score),
            "distance_km": float(dep.distance_km) if dep.distance_km is not None else None,
            "reasons": dep.reasoning_json[0]["factors"] if dep.reasoning_json else [],
            "energy_unlocked_mwh": float(dep.energy_unlocked_mwh),
            "carbon_saved_kg": float(dep.carbon_saved_kg),
            "from": [float(battery.lat), float(battery.lng)] if battery.lat is not None else None,
            "to": [float(site.lat), float(site.lng)] if site.lat is not None else None,
            "reasoning_json": dep.reasoning_json
        }

    return {
        "id": battery.id,
        "aadhaar_id": battery.aadhaar_id,
        "external_ref": battery.external_ref,
        "oem": battery.oem,
        "model": battery.model,
        "chemistry": battery.chemistry,
        "form_factor": battery.form_factor,
        "rated_capacity_kwh": float(battery.rated_capacity_kwh),
        "nominal_voltage": float(battery.nominal_voltage) if battery.nominal_voltage else None,
        "manufacture_date": battery.manufacture_date,
        "source_city": battery.source_city,
        "source_state": battery.source_state,
        "lat": float(battery.lat) if battery.lat is not None else None,
        "lng": float(battery.lng) if battery.lng is not None else None,
        "status": battery.status,
        "created_at": battery.created_at,
        "telemetry": telemetry_dict,
        "assessment": assessment_dict,
        "deployment": deployment_dict
    }


@router.get("/batteries/{battery_id}/aadhaar", response_model=AadhaarPassportResponse)
def get_battery_passport(battery_id: int, db: Session = Depends(get_db)):
    """
    Returns the dynamic Battery Aadhaar passport.
    Returns 409 if the battery has not been assessed yet.
    """
    battery = db.query(Battery).filter(Battery.id == battery_id).first()
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "battery_not_found", "message": f"Battery {battery_id} not found"}}
        )

    if not battery.aadhaar_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "not_assessed_yet", "message": "Aadhaar Passport has not been generated yet. Please process the battery first."}}
        )

    return compose_passport(db, battery)


@router.get("/aadhaar/{aadhaar_id}", response_model=AadhaarPassportResponse)
def get_public_passport(aadhaar_id: str, db: Session = Depends(get_db)):
    """
    Public read-only Aadhaar route target for QR code resolution.
    Lookup via unique index, bypasses auth.
    """
    battery = db.query(Battery).filter(Battery.aadhaar_id == aadhaar_id).first()
    if not battery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "aadhaar_not_found", "message": f"Aadhaar passport {aadhaar_id} not found"}}
        )

    return compose_passport(db, battery)
