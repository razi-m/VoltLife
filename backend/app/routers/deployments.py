from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.orm import Deployment, Battery, Assessment, Site
from app.services.aadhaar import append_lifecycle_event
from app.core.logging import logger

router = APIRouter(prefix="/api/v1", tags=["deployments"])


@router.get("/deployments")
def list_deployments(
    site_type: Optional[str] = None,
    deployment_status: Optional[str] = None,
    grade: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of deployments with battery and site details joined.
    """
    page_size = min(200, max(1, page_size))
    page = max(1, page)
    offset = (page - 1) * page_size

    query = db.query(Deployment).join(Site).join(Battery)

    if site_type:
        query = query.filter(Site.site_type == site_type)
    if deployment_status:
        query = query.filter(Deployment.status == deployment_status)

    # Filter by grade requires joining latest assessment
    if grade:
        latest_subq = db.query(
            Assessment.battery_id,
            Assessment.grade,
            func.row_number().over(
                partition_by=Assessment.battery_id,
                order_by=Assessment.created_at.desc()
            ).label("rn")
        ).subquery()
        query = query.join(
            latest_subq, Battery.id == latest_subq.c.battery_id
        ).filter(latest_subq.c.rn == 1, latest_subq.c.grade == grade)

    total = query.count()
    deployments = query.order_by(Deployment.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    for dep in deployments:
        battery = dep.battery
        site = dep.site
        
        site_name = site.name
        site_type = site.site_type
        if dep.reasoning_json and len(dep.reasoning_json) > 0:
            first_rec = dep.reasoning_json[0]
            if isinstance(first_rec, dict):
                if "override_name" in first_rec:
                    site_name = first_rec["override_name"]
                if "override_type" in first_rec:
                    site_type = first_rec["override_type"]
                    
        ass = db.query(Assessment).filter(
            Assessment.battery_id == battery.id
        ).order_by(Assessment.created_at.desc()).first()

        items.append({
            "id": dep.id,
            "battery_id": battery.id,
            "aadhaar_id": battery.aadhaar_id,
            "external_ref": battery.external_ref,
            "oem": battery.oem,
            "chemistry": battery.chemistry,
            "rated_capacity_kwh": float(battery.rated_capacity_kwh),
            "grade": ass.grade if ass else None,
            "soh_pct": float(ass.soh_pct) if ass else None,
            "confidence": ass.confidence if ass else None,
            "site_id": site.id,
            "site_name": site_name,
            "site_type": site_type,
            "site_state": site.state,
            "score": float(dep.score),
            "distance_km": float(dep.distance_km) if dep.distance_km else None,
            "energy_unlocked_mwh": float(dep.energy_unlocked_mwh),
            "carbon_saved_kg": float(dep.carbon_saved_kg),
            "deployment_status": dep.status,
            "created_at": dep.created_at,
            "from_coords": [float(battery.lat), float(battery.lng)] if battery.lat else None,
            "to_coords": [float(site.lat), float(site.lng)] if site.lat else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
    }


@router.patch("/deployments/{deployment_id}/approve")
def approve_deployment(deployment_id: int, db: Session = Depends(get_db)):
    """
    Transitions a deployment from 'recommended' to 'approved'.
    """
    dep = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "deployment_not_found", "message": f"Deployment {deployment_id} not found"}}
        )
    if dep.status != "recommended":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "invalid_state", "message": f"Deployment is '{dep.status}', only 'recommended' can be approved"}}
        )

    dep.status = "approved"
    
    site_name = dep.site.name if dep.site else "Site"
    if dep.reasoning_json and len(dep.reasoning_json) > 0:
        first_rec = dep.reasoning_json[0]
        if isinstance(first_rec, dict) and "override_name" in first_rec:
            site_name = first_rec["override_name"]
            
    append_lifecycle_event(
        db, dep.battery_id, "deployment_approved",
        payload={"deployment_id": dep.id, "site_name": site_name}
    )
    db.commit()

    logger.info(f"Deployment {deployment_id} approved for battery {dep.battery_id} → {site_name}")

    return {
        "id": dep.id,
        "status": dep.status,
        "message": f"Deployment approved for {site_name}",
    }
