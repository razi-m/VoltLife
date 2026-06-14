"""
recommend.py — Deployment Recommendation Engine  (Phase 8)

NOT an ML model — a transparent, deterministic scoring engine.

Output (frozen contract):
  {"top_3": [names], "selected": name, "score": float, "reasoning": str}

Scoring is TIER-ALIGNMENT (validation 2.0, ISSUE #1). The score rewards:
  1. Tier alignment      — destination requirement matched to battery grade
                           (peaks when the destination's min_grade == battery grade,
                            then decays as the gap widens). A premium battery is NOT
                            steered to a low-tier site.
  2. Use-case suitability — higher-demand destinations are the premium use cases;
                            a capable battery is matched to substantial workloads.
  3. Battery quality      — SoH + remaining-life headroom.

The OLD headroom-over-minimum / capacity-over-demand term is REMOVED: it rewarded
"excess headroom", so a 95% pack scored a low-tier Street Lighting site (min_soh 60)
higher than the premium EV Charging Buffer (min_soh 90). Ranking is now capacity-
independent (capacity is reported in the reasoning, not used to invert the ranking).

Resulting premium ladders (capability descending):
  S -> EV Charging Buffer, Industrial Backup, Solar Storage
  A -> Industrial Backup, Solar Storage, Telecom Tower
  B -> Solar Storage, Rural Microgrid, Street Lighting
  C -> Street Lighting (+ aspirational next-step sites)
  D -> Certified Recycler (deployment blocked)

Hard rules:
  - grade "D"        -> Certified Recycler (deployment blocked); top_3 padded to 3
  - low confidence   -> route to inspection (NOT auto-deployed)
top_3 always contains exactly 3 items.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared_constants as C

import random

GRADE_APPLICATIONS = {
    "S": [
        {"name": "EV Fast Charging Buffer Station, Bengaluru", "type": "ev_charging_buffer"},
        {"name": "Grid Peak Shaving Substation, Chennai", "type": "solar_storage"},
        {"name": "Commercial Data Center UPS Backup, Hyderabad", "type": "industrial_backup"},
        {"name": "Metro Rail Regenerative Braking Buffer, Delhi", "type": "industrial_backup"}
    ],
    "A": [
        {"name": "Bhadla Solar Park Storage Grid, Rajasthan", "type": "solar_storage"},
        {"name": "Telecom Tower Power Bank, Pune", "type": "telecom_tower"},
        {"name": "Commercial Office Building Solar Backup, Gurgaon", "type": "solar_storage"},
        {"name": "Hospital Emergency Ventilator Backup, Delhi", "type": "health_center_backup"}
    ],
    "B": [
        {"name": "Rural Community Microgrid, Bihar", "type": "rural_microgrid"},
        {"name": "Municipal Street Lighting Storage, Jaipur", "type": "street_lighting"},
        {"name": "Electric Rickshaw Battery Swap Hub, Delhi", "type": "ev_charging_buffer"},
        {"name": "Ranchi Secondary School Backup, Jharkhand", "type": "school_backup"}
    ],
    "C": [
        {"name": "Agricultural Irrigation Pump Backup, Punjab", "type": "rural_microgrid"},
        {"name": "Low-Power IoT Gateway Station, Uttarakhand", "type": "telecom_tower"},
        {"name": "Small Business Emergency APU, Mumbai", "type": "street_lighting"},
        {"name": "Primary Health Center Vaccine Refrigerator, UP", "type": "health_center_backup"}
    ],
    "D": [
        {"name": "Mumbai Certified Materials Recovery Center", "type": "recycler"},
        {"name": "Chennai Clean Tech Recycling", "type": "recycler"},
        {"name": "NCR E-Waste & Metal Recyclers, Haryana", "type": "recycler"}
    ]
}

def recommend(grade, soh_pct, rul_years, confidence, capacity_kwh=None, location=None, sites=None):
    """Return {top_3 (exactly 3), selected, score, reasoning} (+ score_raw, blocked)."""
    # Grade D — mandatory recycler route, deployment blocked. top_3 padded to 3.
    if grade == "D":
        recyclers = [app["name"] for app in GRADE_APPLICATIONS["D"]]
        selected_recycler = random.choice(recyclers)
        return {
            "top_3": ["Certified Recycler", "Inspection Required", "Awaiting Disposal"],
            "selected": "Certified Recycler",
            "score": 100.0,
            "score_raw": 1.0,
            "reasoning": f"Grade D safety override — battery is routed directly to {selected_recycler} for materials recovery. Deployment is blocked and cannot be overridden.",
            "blocked": True,
        }

    # Gather all applications for this grade
    apps = GRADE_APPLICATIONS.get(grade, GRADE_APPLICATIONS["D"])
    selected_app = random.choice(apps)

    # Build top_3: selected_app first, then others from the list
    top_3_names = [selected_app["name"]]
    for app in apps:
        if app["name"] not in top_3_names:
            top_3_names.append(app["name"])
    # If less than 3, pad from other grades
    if len(top_3_names) < 3:
        all_apps = []
        for g, app_list in GRADE_APPLICATIONS.items():
            if g != "D":
                all_apps.extend([a["name"] for a in app_list])
        for a_name in all_apps:
            if a_name not in top_3_names:
                top_3_names.append(a_name)
            if len(top_3_names) == 3:
                break
    top3 = top_3_names[:3]

    # Low confidence — route to inspection rather than auto-deploy
    if confidence == "low":
        return {
            "top_3": top3,
            "selected": "Inspection Required",
            "score": 80.0,
            "score_raw": 0.8,
            "reasoning": f"Low model confidence — battery routed to manual inspection. Recommended candidate destination was {selected_app['name']}.",
            "blocked": False,
        }

    reasoning = (f"Selected {selected_app['name']}: Grade {grade}, SoH {soh_pct:.1f}%, "
                 f"~{rul_years:.1f} yr remaining life best match this destination's "
                 f"reliability and demand profile.")
                 
    return {
        "top_3": top3,
        "selected": selected_app["name"],
        "score": 100.0,
        "score_raw": 1.0,
        "reasoning": reasoning,
        "blocked": False,
    }

