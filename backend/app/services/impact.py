from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any
from app.models.orm import Battery, Deployment, Assessment, Site
from app.core.logging import logger

def get_impact_summary(db: Session) -> Dict[str, Any]:
    """
    Computes live fleet sustainability impact aggregates.
    """
    # 1. Total processed vs total batteries
    total_count = db.query(func.count(Battery.id)).scalar() or 0
    processed_count = db.query(func.count(Battery.id)).filter(
        Battery.status != "ingested"
    ).scalar() or 0

    # 2. Deployed sums (Grade S-C)
    mwh_unlocked = db.query(func.sum(Deployment.energy_unlocked_mwh)).scalar() or 0.0
    carbon_saved_kg = db.query(func.sum(Deployment.carbon_saved_kg)).scalar() or 0.0
    carbon_saved_tonnes = float(carbon_saved_kg) / 1000.0

    # 3. Diverted count (Grades S-C successfully deployed)
    # Filter deployments where site is not recycler
    diverted_count = db.query(func.count(Deployment.id)).join(Site).filter(
        Site.site_type != "recycler"
    ).scalar() or 0

    # 4. Responsibly recycled count (Grade D routed to recyclers)
    recycled_count = db.query(func.count(Battery.id)).filter(
        Battery.status == "recycled"
    ).scalar() or 0

    # 5. Histogram by Grade (latest assessment wins)
    # Query latest assessment grade for each battery
    subq = db.query(
        Assessment.battery_id,
        Assessment.grade,
        func.row_number().over(
            partition_by=Assessment.battery_id,
            order_by=Assessment.created_at.desc()
        ).label("rn")
    ).subquery()
    
    grade_counts = db.query(
        subq.c.grade,
        func.count(subq.c.battery_id)
    ).filter(subq.c.rn == 1).group_by(subq.c.grade).all()
    
    by_grade = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for grade, count in grade_counts:
        if grade in by_grade:
            by_grade[grade] = count

    # 6. Histogram by Destination Site Type
    site_counts = db.query(
        Site.site_type,
        func.count(Deployment.id)
    ).join(Deployment).group_by(Site.site_type).all()
    
    by_site_type = {
        "solar_storage": 0,
        "rural_microgrid": 0,
        "school_backup": 0,
        "health_center_backup": 0,
        "industrial_backup": 0,
        "telecom_tower": 0,
        "ev_charging_buffer": 0,
        "street_lighting": 0,
        "recycler": 0
    }
    
    for stype, count in site_counts:
        if stype in by_site_type:
            by_site_type[stype] = count
            
    # Include recycled count explicitly under recycler category
    by_site_type["recycler"] = recycled_count

    return {
        "mwh_unlocked": round(float(mwh_unlocked), 1),
        "carbon_saved_tonnes": round(carbon_saved_tonnes, 1),
        "diverted_from_recycling": int(diverted_count),
        "recycled_responsibly": int(recycled_count),
        "processed": int(processed_count),
        "total": int(total_count),
        "by_grade": by_grade,
        "by_site_type": by_site_type
    }
