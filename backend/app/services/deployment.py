from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from typing import List, Dict, Any, Tuple
from app.models.orm import Battery, Site, Deployment, Assessment, LifecycleEvent
from app.ml.recommend import recommend
from app.services.aadhaar import append_lifecycle_event
from app.core.config import settings
from app.core.logging import logger

def get_derived_sites(db: Session) -> List[Any]:
    """
    Retrieves all sites, computing remaining_kwh and assigned_count derived fields.
    remaining_kwh = demand_kwh - SUM(battery.rated_capacity_kwh * (assessment.soh_pct/100))
    """
    sites = db.query(Site).all()
    
    # Subquery to get latest assessment per battery
    latest_assessment_subq = db.query(
        Assessment.battery_id,
        func.max(Assessment.created_at).label("max_created_at")
    ).group_by(Assessment.battery_id).subquery()

    # Join back to Assessment to get SOH%
    latest_assessment = db.query(
        Assessment.battery_id,
        Assessment.soh_pct
    ).join(
        latest_assessment_subq,
        (Assessment.battery_id == latest_assessment_subq.c.battery_id) &
        (Assessment.created_at == latest_assessment_subq.c.max_created_at)
    ).subquery()

    # Query all deployments, joining Battery and the latest_assessment
    deployments_data = db.query(
        Deployment.site_id,
        Battery.rated_capacity_kwh,
        latest_assessment.c.soh_pct
    ).join(
        Battery, Deployment.battery_id == Battery.id
    ).outerjoin(
        latest_assessment, Battery.id == latest_assessment.c.battery_id
    ).all()

    site_aggregates = {}
    for site_id, rated_capacity, soh in deployments_data:
        if site_id not in site_aggregates:
            site_aggregates[site_id] = {"count": 0, "kwh": 0.0}
        
        soh_val = float(soh) if soh is not None else 80.0
        cap_val = float(rated_capacity)
        
        site_aggregates[site_id]["count"] += 1
        site_aggregates[site_id]["kwh"] += cap_val * (soh_val / 100.0)

    for site in sites:
        agg = site_aggregates.get(site.id, {"count": 0, "kwh": 0.0})
        site.assigned_count = agg["count"]
        site.remaining_kwh = max(0.0, float(site.demand_kwh) - agg["kwh"])
        
    return sites


def decide_deployment(db: Session, battery: Battery, assessment: Assessment) -> Dict[str, Any]:
    """
    Orchestrates the deployment decision for a single assessed battery.
    Loads site state, invokes recommend(), persists the deployment, updates status,
    and returns the WS-shaped payload.
    """
    # 1. Load eligible sites
    sites = get_derived_sites(db)
    
    # 2. Extract battery metadata
    battery_meta = {
        "rated_capacity_kwh": float(battery.rated_capacity_kwh),
        "lat": float(battery.lat) if battery.lat is not None else None,
        "lng": float(battery.lng) if battery.lng is not None else None,
        "chemistry": battery.chemistry,
        "oem": battery.oem
    }
    
    # 3. Assess ML recommendation
    ass_dict = {
        "soh_pct": float(assessment.soh_pct),
        "rul_cycles": int(assessment.rul_cycles),
        "rul_years": float(assessment.rul_years),
        "grade": assessment.grade,
        "confidence": assessment.confidence
    }
    
    rec_result = recommend(ass_dict, battery_meta, sites)
    
    # 4. Handle Recycle case (Grade D)
    if assessment.grade == "D":
        battery.status = "recycled"
        
        # Load Recycler site details
        selected_sid = rec_result["selected_site_id"]
        recycler = db.query(Site).filter(Site.id == selected_sid).first() if selected_sid else None
        
        # Log recycled event
        append_lifecycle_event(
            db, battery.id, "recycled",
            payload={
                "site": recycler.name if recycler else "Certified Recycler",
                "materials_recovered": {
                    "lithium_kg": float(float(battery.rated_capacity_kwh) * (float(assessment.soh_pct)/100.0) * 0.10),
                    "cobalt_kg": float(float(battery.rated_capacity_kwh) * (float(assessment.soh_pct)/100.0) * 0.13),
                    "nickel_kg": float(float(battery.rated_capacity_kwh) * (float(assessment.soh_pct)/100.0) * 0.40)
                }
            }
        )
        
        # Insert Deployment record (recommending recycler)
        if selected_sid:
            deployment = Deployment(
                battery_id=battery.id,
                site_id=selected_sid,
                score=1.0,
                reasoning_json=rec_result["recommendations"],
                distance_km=rec_result.get("distance_km"),
                energy_unlocked_mwh=0.0,
                carbon_saved_kg=0.0,
                status="dispatched"  # Recyclers are immediately dispatched
            )
            db.add(deployment)
            
        # Return WS deployment shape
        return {
            "battery_id": battery.id,
            "site_id": selected_sid,
            "site_name": recycler.name if recycler else "Certified Recycler",
            "site_type": "recycler",
            "score": 1.00,
            "distance_km": rec_result.get("distance_km", 0.0),
            "reasons": rec_result["recommendations"][0]["factors"] if rec_result["recommendations"] else ["Safety override"],
            "energy_unlocked_mwh": 0.0,
            "carbon_saved_kg": 0.0,
            "from": [battery_meta["lat"], battery_meta["lng"]],
            "to": [float(recycler.lat), float(recycler.lng)] if recycler else [battery_meta["lat"], battery_meta["lng"]]
        }

    # 5. Handle inspection case (low confidence)
    if assessment.confidence == "low":
        battery.status = "inspection"
        append_lifecycle_event(
            db, battery.id, "inspection_queued",
            payload={"reason": "Low ML prediction confidence"}
        )
        return {}

    # 6. Deployed case (Grade S/A/B/C)
    selected_sid = rec_result["selected_site_id"]
    if selected_sid is None:
        # Sites are full, battery remains assessed
        battery.status = "assessed"
        append_lifecycle_event(
            db, battery.id, "awaiting_demand",
            payload={"reason": "No matching sites available with remaining demand"}
        )
        return {}

    # Update battery status
    battery.status = "assigned"
    
    # Load site info
    site = db.query(Site).filter(Site.id == selected_sid).first()
    
    # Insert Deployment record
    initial_status = "approved" if settings.AUTONOMY_MODE else "recommended"
    
    deployment = Deployment(
        battery_id=battery.id,
        site_id=selected_sid,
        score=float(rec_result["recommendations"][0]["score"]) / 100.0,
        reasoning_json=rec_result["recommendations"],
        distance_km=rec_result["distance_km"],
        energy_unlocked_mwh=rec_result["energy_unlocked_mwh"],
        carbon_saved_kg=rec_result["carbon_saved_kg"],
        status=initial_status
    )
    db.add(deployment)
    db.flush()
    
    # Log lifecycle event
    append_lifecycle_event(
        db, battery.id, "deployment_assigned",
        payload={
            "site": site.name,
            "score": int(rec_result["recommendations"][0]["score"]),
            "distance_km": float(rec_result["distance_km"])
        }
    )
    
    # Construct WS payload matching docs/04
    return {
        "battery_id": battery.id,
        "site_id": site.id,
        "site_name": site.name,
        "site_type": site.site_type,
        "score": float(rec_result["recommendations"][0]["score"]) / 100.0,
        "distance_km": float(rec_result["distance_km"]),
        "reasons": rec_result["recommendations"][0]["factors"],
        "energy_unlocked_mwh": float(rec_result["energy_unlocked_mwh"]),
        "carbon_saved_kg": float(rec_result["carbon_saved_kg"]),
        "from": [battery_meta["lat"], battery_meta["lng"]],
        "to": [float(site.lat), float(site.lng)]
    }
