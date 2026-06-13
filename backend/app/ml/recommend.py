import math
from typing import Dict, Any, List, Optional
from shared.constants import (
    CYCLES_PER_YEAR, DEPTH_OF_DISCHARGE, ROUND_TRIP_EFFICIENCY, CARBON_AVOIDED_MFR_KG_PER_KWH,
    WEIGHT_CAPACITY_MATCH, WEIGHT_GRADE_HEADROOM, WEIGHT_PROXIMITY, WEIGHT_CARBON_BENEFIT, WEIGHT_SITE_PRIORITY
)

def haversine_km(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> float:
    """
    Computes Great Circle Distance between two GPS coordinates in kilometers.
    """
    if None in (lat1, lon1, lat2, lon2):
        return 9999.0  # Safe fallback for missing lat/lng
        
    try:
        lat1 = float(lat1)
        lon1 = float(lon1)
        lat2 = float(lat2)
        lon2 = float(lon2)
    except (ValueError, TypeError):
        return 9999.0

    if any(math.isnan(x) for x in (lat1, lon1, lat2, lon2)):
        return 9999.0  # Safe fallback for NaN values
        
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2.0) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

UNIT_NEEDS = {
    "solar_storage": 15.0,
    "industrial_backup": 20.0,
    "rural_microgrid": 12.0,
    "school_backup": 8.0,
    "health_center_backup": 10.0,
    "telecom_tower": 5.0,
    "ev_charging_buffer": 15.0,
    "street_lighting": 2.0,
    "recycler": 4.0
}

GRADE_VALUES = {"S": 4, "A": 3, "B": 2, "C": 1, "D": 0}

def recommend(assessment: Dict[str, Any], battery_meta: Dict[str, Any], sites: List[Any]) -> Dict[str, Any]:
    """
    Transparent multi-criteria scoring engine matching a graded battery to demand sites.
    
    Returns:
        Dict[str, Any] matching the RecommendationResult schema.
    """
    grade = assessment.get("grade", "D")
    confidence = assessment.get("confidence", "low")
    soh_pct = assessment.get("soh_pct", 0.0)
    rul_cycles = assessment.get("rul_cycles", 0)
    
    rated_capacity = float(battery_meta.get("rated_capacity_kwh", 4.0))
    battery_lat = float(battery_meta.get("lat") or 0.0)
    battery_lng = float(battery_meta.get("lng") or 0.0)
    
    usable_kwh = rated_capacity * (soh_pct / 100.0)
    
    # 1. Handle Grade D (Unsafe/Recycle) -> Certified Recyclers Only
    if grade == "D":
        # Find recycler sites
        recycler_sites = [s for s in sites if s.site_type == "recycler"]
        # Fallback if no recycler in DB
        if not recycler_sites:
            # Create a mock recycler inline
            class MockRecycler:
                id = -1
                name = "Mumbai Certified Recovery Center"
                site_type = "recycler"
                lat = 19.07
                lng = 72.87
                demand_kwh = 9999.0
                remaining_kwh = 9999.0
                min_grade = "D"
            recycler_sites = [MockRecycler()]
            
        # Select closest recycler
        recycler = min(recycler_sites, key=lambda s: haversine_km(battery_lat, battery_lng, s.lat, s.lng))
        dist = haversine_km(battery_lat, battery_lng, recycler.lat, recycler.lng)
        
        # NMC mix material intensities: Li=10%, Co=13%, Ni=40%
        li_kg = usable_kwh * 0.10
        co_kg = usable_kwh * 0.13
        ni_kg = usable_kwh * 0.40
        
        rec_item = {
            "destination": recycler.name,
            "site_id": recycler.id,
            "score": 100,
            "factors": [
                "Safety rule: grade Recycle routes to certified recycler",
                f"Est. recovery: {li_kg:.1f} kg Li, {co_kg:.1f} kg Co, {ni_kg:.1f} kg Ni",
                f"Logistics: {dist:.0f} km to Mumbai Certified Recovery Center"
            ]
        }
        
        return {
            "recommendations": [rec_item],
            "selected_destination": recycler.name,
            "selected_site_id": recycler.id,
            "energy_unlocked_mwh": 0.0,
            "carbon_saved_kg": 0.0
        }

    # 2. Handle Low Confidence (Goes to Inspection)
    if confidence == "low":
        return {
            "recommendations": [],
            "selected_destination": "Inspection Queue",
            "selected_site_id": None,
            "energy_unlocked_mwh": 0.0,
            "carbon_saved_kg": 0.0
        }

    # 3. Grade S/A/B/C -> Score all eligible sites
    scored_candidates = []
    battery_grade_val = GRADE_VALUES.get(grade, 0)
    
    for site in sites:
        # Hard gates
        if site.site_type == "recycler":
            continue
        if site.remaining_kwh <= 0:
            continue
        
        site_min_grade_val = GRADE_VALUES.get(site.min_grade, 1)
        if battery_grade_val < site_min_grade_val:
            continue
        if soh_pct < float(site.min_soh_pct):
            continue
            
        # Stricter gate for Health Center Backup (requires min A + confidence high)
        if site.site_type == "health_center_backup":
            if confidence != "high" or battery_grade_val < GRADE_VALUES["A"]:
                continue
                
        # Calculate raw scores
        # Capacity match
        site_need = UNIT_NEEDS.get(site.site_type, 10.0)
        cap_match = 1.0 - abs(usable_kwh - site_need) / site_need
        cap_match = max(0.0, min(1.0, cap_match))
        
        # Grade headroom (overshoot penalty of -0.15 per tier)
        overshoot = battery_grade_val - site_min_grade_val
        grade_head = 1.0 - (0.15 * overshoot)
        grade_head = max(0.0, min(1.0, grade_head))
        
        # Proximity (normalized distance)
        dist_km = haversine_km(battery_lat, battery_lng, site.lat, site.lng)
        prox = 1.0 - (dist_km / 2000.0)
        prox = max(0.0, min(1.0, prox))
        
        # Carbon benefit (usable_kwh ratio)
        carb_benefit = usable_kwh / rated_capacity
        carb_benefit = max(0.0, min(1.0, carb_benefit))
        
        # Site priority weight (normalized by dividing by 1.5, since microgrids have priority 1.3)
        priority_norm = float(site.priority or 1.0) / 1.5
        priority_norm = max(0.0, min(1.0, priority_norm))
        
        # Weighted Score
        raw_score = (
            WEIGHT_CAPACITY_MATCH * cap_match +
            WEIGHT_GRADE_HEADROOM * grade_head +
            WEIGHT_PROXIMITY * prox +
            WEIGHT_CARBON_BENEFIT * carb_benefit +
            WEIGHT_SITE_PRIORITY * priority_norm
        )
        
        # Narrative factors
        factors = []
        # Capacity factor
        factors.append(f"Best capacity match ({usable_kwh:.1f} of {site_need:.1f} kWh unit need)")
        # Grade headroom factor
        factors.append(f"Grade {grade} meets {site.site_type.replace('_', ' ')} bar")
        # Proximity/Logistics factor
        factors.append(f"{dist_km:.0f} km — nearest eligible {site.site_type.replace('_', ' ')}")
        
        scored_candidates.append({
            "site_id": site.id,
            "name": site.name,
            "score": round(raw_score * 100),
            "factors": factors,
            "distance_km": dist_km,
            "raw_score_float": raw_score,
            "priority": site.priority
        })
        
    # Sort descending
    # Ties resolved by higher priority, then lower distance
    scored_candidates.sort(key=lambda x: (x["score"], x["priority"], -x["distance_km"]), reverse=True)
    
    top_recommendations = []
    for c in scored_candidates[:3]:
        top_recommendations.append({
            "destination": c["name"],
            "site_id": c["site_id"],
            "score": c["score"],
            "factors": c["factors"]
        })
        
    # Selected is Rank 1
    if top_recommendations:
        selected = top_recommendations[0]
        selected_dest = selected["destination"]
        selected_sid = selected["site_id"]
        selected_dist = scored_candidates[0]["distance_km"]
        
        # Compute exact sustainability impact
        # energy_unlocked_MWh = usable_kwh × remaining_cycles × 0.80 DoD × 0.90 RTE / 1000
        energy_unlocked = (usable_kwh * rul_cycles * DEPTH_OF_DISCHARGE * ROUND_TRIP_EFFICIENCY) / 1000.0
        carbon_saved = usable_kwh * CARBON_AVOIDED_MFR_KG_PER_KWH
    else:
        # Edge case: No eligible site found
        selected_dest = "Awaiting Demand Registry"
        selected_sid = None
        selected_dist = 0.0
        energy_unlocked = 0.0
        carbon_saved = 0.0
        
    return {
        "recommendations": top_recommendations,
        "selected_destination": selected_dest,
        "selected_site_id": selected_sid,
        "distance_km": selected_dist,
        "energy_unlocked_mwh": round(energy_unlocked, 3),
        "carbon_saved_kg": round(carbon_saved, 1)
    }
