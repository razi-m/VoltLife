from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.orm import Battery, Assessment, Deployment, Site, TelemetrySummary

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregate KPI stats for the Mission Control dashboard.
    """
    total_batteries = db.query(func.count(Battery.id)).scalar() or 0
    processed = db.query(func.count(Battery.id)).filter(
        Battery.status != "ingested"
    ).scalar() or 0
    active_deployments = db.query(func.count(Deployment.id)).filter(
        Deployment.status.in_(["recommended", "approved", "dispatched"])
    ).scalar() or 0
    recycled = db.query(func.count(Battery.id)).filter(
        Battery.status == "recycled"
    ).scalar() or 0

    # Average SoH from latest assessments
    latest_subq = db.query(
        Assessment.battery_id,
        Assessment.soh_pct,
        Assessment.grade,
        func.row_number().over(
            partition_by=Assessment.battery_id,
            order_by=Assessment.created_at.desc()
        ).label("rn")
    ).subquery()

    avg_soh = db.query(func.avg(latest_subq.c.soh_pct)).filter(
        latest_subq.c.rn == 1
    ).scalar()

    # Grade distribution
    grade_counts = db.query(
        latest_subq.c.grade,
        func.count(latest_subq.c.battery_id)
    ).filter(latest_subq.c.rn == 1).group_by(latest_subq.c.grade).all()

    by_grade = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for grade, count in grade_counts:
        if grade in by_grade:
            by_grade[grade] = count

    # Energy and carbon totals
    mwh_unlocked = db.query(func.sum(Deployment.energy_unlocked_mwh)).scalar() or 0.0
    carbon_saved_kg = db.query(func.sum(Deployment.carbon_saved_kg)).scalar() or 0.0

    # Status distribution
    status_counts = db.query(
        Battery.status,
        func.count(Battery.id)
    ).group_by(Battery.status).all()
    by_status = {}
    for s, c in status_counts:
        by_status[s] = c

    # Recent batteries (last 5)
    recent = db.query(Battery).order_by(Battery.created_at.desc()).limit(5).all()
    recent_items = []
    for b in recent:
        ass = db.query(Assessment).filter(
            Assessment.battery_id == b.id
        ).order_by(Assessment.created_at.desc()).first()
        recent_items.append({
            "id": b.id,
            "aadhaar_id": b.aadhaar_id,
            "external_ref": b.external_ref,
            "oem": b.oem,
            "status": b.status,
            "grade": ass.grade if ass else None,
            "soh_pct": float(ass.soh_pct) if ass else None,
        })

    return {
        "total_batteries": total_batteries,
        "processed": processed,
        "active_deployments": active_deployments,
        "recycled": recycled,
        "avg_soh_pct": round(float(avg_soh), 1) if avg_soh else 0.0,
        "mwh_unlocked": round(float(mwh_unlocked), 2),
        "carbon_saved_tonnes": round(float(carbon_saved_kg) / 1000.0, 2),
        "by_grade": by_grade,
        "by_status": by_status,
        "recent_batteries": recent_items,
    }
