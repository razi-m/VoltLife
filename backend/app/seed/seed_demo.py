"""
VoltLife — Enterprise Demo Data Seeder
Generates 847 realistic battery records with full telemetry, assessments,
deployments, lifecycle events, and Aadhaar profiles.

Usage:
    cd backend
    python -m app.seed.seed_demo
"""
import os
import sys
import random
import hashlib
import json
import math
from datetime import datetime, date, timedelta
from decimal import Decimal

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.orm import Battery, TelemetrySummary, Assessment, Deployment, Site, LifecycleEvent

random.seed(42)  # Reproducible data

# ─── Constants ────────────────────────────────────────────────────────
TOTAL_BATTERIES = 847

# Manufacturer distribution (maps to ~count)
MANUFACTURERS = [
    {"oem": "Tata Motors",       "share": 0.22, "models": ["Nexon EV", "Tigor EV", "Tiago EV", "Punch EV"],
     "voltages": [320, 400], "capacities": (30, 45), "chemistry": "NMC"},
    {"oem": "Ola Electric",      "share": 0.18, "models": ["S1 Pro", "S1 Air", "S1 X", "Roadster"],
     "voltages": [48, 72],   "capacities": (3, 4),   "chemistry": "NMC"},
    {"oem": "Ather Energy",      "share": 0.15, "models": ["450X", "450S", "Rizta", "Rizta Z"],
     "voltages": [48, 72],   "capacities": (2.9, 3.7), "chemistry": "NMC"},
    {"oem": "Mahindra Electric", "share": 0.12, "models": ["XUV400", "e2o Plus", "Treo", "Treo Zor"],
     "voltages": [72, 320, 400], "capacities": (10, 40), "chemistry": "LFP"},
    {"oem": "Hero Electric",     "share": 0.10, "models": ["Optima HX", "NYX HX", "Photon HX", "Eddy"],
     "voltages": [48, 72],   "capacities": (1.5, 3.5), "chemistry": "LFP"},
    {"oem": "MG Motor",          "share": 0.09, "models": ["ZS EV", "Comet EV", "Windsor EV"],
     "voltages": [320, 400], "capacities": (38, 51),  "chemistry": "NMC"},
    {"oem": "BYD",               "share": 0.08, "models": ["Atto 3", "Seal", "e6", "Dolphin"],
     "voltages": [320, 400], "capacities": (45, 75),  "chemistry": "LFP"},
    {"oem": "Hyundai",           "share": 0.06, "models": ["Ioniq 5", "Kona Electric", "Creta EV"],
     "voltages": [400],      "capacities": (42, 73),  "chemistry": "NMC"},
]

# Grade distribution (S=top 5%, A=15%, B=40%, C=25%, D=15%)
GRADE_DIST = [
    {"grade": "S", "share": 0.05, "soh_range": (90, 98)},
    {"grade": "A", "share": 0.15, "soh_range": (80, 89.9)},
    {"grade": "B", "share": 0.40, "soh_range": (70, 79.9)},
    {"grade": "C", "share": 0.25, "soh_range": (60, 69.9)},
    {"grade": "D", "share": 0.15, "soh_range": (45, 59.9)},
]

# Source programs
SOURCE_PROGRAMS = [
    "EV Fleets",
    "Battery Collection Centers",
    "OEM Recovery Programs",
    "Energy Storage Programs",
]

# 18 Indian cities with coordinates
CITIES = [
    {"city": "Hyderabad",       "state": "Telangana",         "lat": 17.3850, "lng": 78.4867},
    {"city": "Bangalore",       "state": "Karnataka",         "lat": 12.9716, "lng": 77.5946},
    {"city": "Pune",            "state": "Maharashtra",       "lat": 18.5204, "lng": 73.8567},
    {"city": "Mumbai",          "state": "Maharashtra",       "lat": 19.0760, "lng": 72.8777},
    {"city": "Chennai",         "state": "Tamil Nadu",        "lat": 13.0827, "lng": 80.2707},
    {"city": "Delhi",           "state": "Delhi",             "lat": 28.7041, "lng": 77.1025},
    {"city": "Ahmedabad",       "state": "Gujarat",           "lat": 23.0225, "lng": 72.5714},
    {"city": "Jaipur",          "state": "Rajasthan",         "lat": 26.9124, "lng": 75.7873},
    {"city": "Kolkata",         "state": "West Bengal",       "lat": 22.5726, "lng": 88.3639},
    {"city": "Lucknow",         "state": "Uttar Pradesh",     "lat": 26.8467, "lng": 80.9462},
    {"city": "Nagpur",          "state": "Maharashtra",       "lat": 21.1458, "lng": 79.0882},
    {"city": "Surat",           "state": "Gujarat",           "lat": 21.1702, "lng": 72.8311},
    {"city": "Kochi",           "state": "Kerala",            "lat":  9.9312, "lng": 76.2673},
    {"city": "Chandigarh",      "state": "Punjab",            "lat": 30.7333, "lng": 76.7794},
    {"city": "Bhopal",          "state": "Madhya Pradesh",    "lat": 23.2599, "lng": 77.4126},
    {"city": "Coimbatore",      "state": "Tamil Nadu",        "lat": 11.0168, "lng": 76.9558},
    {"city": "Visakhapatnam",   "state": "Andhra Pradesh",    "lat": 17.6868, "lng": 83.2185},
    {"city": "Indore",          "state": "Madhya Pradesh",    "lat": 22.7196, "lng": 75.8577},
]

# Deployment partner names
PARTNERS = [
    "Tata Power Solar", "Adani Green Energy", "ReNew Power", "Azure Power",
    "Hero Future Energies", "Vikram Solar", "Waaree Energies", "Sterling & Wilson",
    "Suzlon Energy", "Amplus Solar", "Fourth Partner Energy", "CleanMax Solar",
    "Acme Solar", "Greenko Group", "Avaada Energy", "Sembcorp India",
    "NLC India", "SJVN Green", "Torrent Power", "JSW Energy",
    "Reliance New Energy", "Mahindra Susten", "NTPC Green", "ITC Renewable",
    "Loom Solar", "Luminous Power", "Exide Green", "Amara Raja Energy",
    "Okaya Power", "Microtek Green", "TVS Motor Energy", "Bajaj Energy",
    "L&T Green", "Bharat Solar",
]

# Battery status mapping for deployment status
STATUS_MAP = {
    "S": "deployed",
    "A": "deployed",
    "B": "assigned",
    "C": "assigned",
    "D": "recycled",
}

# Assessment reasoning pools
POSITIVE_REASONS = [
    "Stable thermal profile across {cycles}+ charge cycles",
    "Low internal resistance growth ({ir_growth}% from baseline)",
    "Moderate capacity fade within acceptable second-life threshold",
    "Consistent voltage stability index ({vs:.3f}) across deep discharge cycles",
    "High coulombic efficiency ({ce:.4f}) indicates minimal parasitic losses",
    "Thermal stress hours ({tsh} hrs) well below safety threshold",
    "Capacity fade rate of {fade_rate:.2f}%/100 cycles is within expected range",
    "No anomalous temperature spikes detected in operational history",
    "Battery management system data shows healthy cell balancing",
    "Cycle count ({cycles}) appropriate for rated chemistry lifetime",
    "Average operating temperature ({temp}°C) within optimal range for {chemistry}",
    "Internal resistance at {ir} mΩ — within manufacturer specifications",
    "Consistent charge-discharge patterns indicate reliable performance",
    "No deep discharge events below critical voltage threshold detected",
    "Cell-to-cell variance within acceptable tolerance (< 3%)",
]

NEGATIVE_REASONS = [
    "Elevated thermal stress ({tsh} hrs above 40°C) indicates accelerated aging",
    "Internal resistance growth of {ir_growth}% exceeds typical degradation curve",
    "Significant capacity fade ({fade_pct}%) — limited second-life viability",
    "Irregular voltage stability ({vs:.3f}) suggests cell imbalance",
    "Low coulombic efficiency ({ce:.4f}) indicates internal losses",
    "High cycle count ({cycles}) approaching end-of-life for {chemistry} chemistry",
    "Maximum temperature spike of {max_temp}°C recorded — potential thermal abuse",
    "Capacity fade rate of {fade_rate:.2f}%/100 cycles exceeds manufacturer spec",
    "Deep discharge events detected — may have caused irreversible damage",
    "Significant cell-to-cell variance (> 5%) detected",
]

DEPLOYMENT_REASONS = [
    "Best capacity match for site demand requirements",
    "Grade {grade} meets minimum threshold for {site_type} deployment",
    "Proximity advantage — {dist_km:.0f} km from collection center",
    "Chemistry ({chemistry}) well-suited for {site_type} operating conditions",
    "Remaining useful life ({rul} years) exceeds minimum deployment horizon",
    "Carbon savings potential of {carbon_kg:.0f} kg CO₂ over deployment lifetime",
    "Energy recovery of {energy_mwh:.2f} MWh expected over deployment period",
    "Temperature profile compatible with {state} climate conditions",
    "High site priority score for underserved {site_type} in {state}",
    "Battery voltage ({voltage}V) compatible with site inverter specification",
]


def compute_event_hash(prev_hash: str, event_type: str, occurred_at: datetime, payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    data = f"{prev_hash}{event_type}{occurred_at.isoformat()}{payload_str}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def build_grade_list() -> list:
    """Build a shuffled list of 847 grades matching the distribution."""
    grades = []
    for g in GRADE_DIST:
        count = round(TOTAL_BATTERIES * g["share"])
        grades.extend([g["grade"]] * count)
    # Pad or trim to exact count
    while len(grades) < TOTAL_BATTERIES:
        grades.append("B")  # pad with most common
    grades = grades[:TOTAL_BATTERIES]
    random.shuffle(grades)
    return grades


def build_manufacturer_list() -> list:
    """Build a shuffled list of 847 manufacturer configs."""
    mfrs = []
    for m in MANUFACTURERS:
        count = round(TOTAL_BATTERIES * m["share"])
        mfrs.extend([m] * count)
    while len(mfrs) < TOTAL_BATTERIES:
        mfrs.append(random.choice(MANUFACTURERS))
    mfrs = mfrs[:TOTAL_BATTERIES]
    random.shuffle(mfrs)
    return mfrs


def soh_for_grade(grade: str) -> float:
    for g in GRADE_DIST:
        if g["grade"] == grade:
            return round(random.uniform(g["soh_range"][0], g["soh_range"][1]), 1)
    return 75.0


def rul_for_soh(soh: float) -> float:
    """Estimate remaining useful life in years from SoH."""
    if soh >= 90:
        return round(random.uniform(5.0, 8.0), 1)
    elif soh >= 80:
        return round(random.uniform(3.5, 6.0), 1)
    elif soh >= 70:
        return round(random.uniform(2.0, 4.5), 1)
    elif soh >= 60:
        return round(random.uniform(1.0, 3.0), 1)
    else:
        return round(random.uniform(0.5, 1.5), 1)


def generate_telemetry(rated_kwh: float, soh: float, chemistry: str, grade: str, mfg_date: date) -> dict:
    """Generate realistic telemetry values consistent with the battery's grade/SoH."""
    age_years = max(0.5, (date(2026, 6, 1) - mfg_date).days / 365.25)
    cycles_per_year = random.randint(200, 400) if rated_kwh < 10 else random.randint(150, 350)
    cycle_count = int(age_years * cycles_per_year + random.randint(-50, 50))
    cycle_count = max(100, cycle_count)

    capacity_now = rated_kwh * (soh / 100.0)
    capacity_fade = 100.0 - soh
    fade_rate = (capacity_fade / max(1, cycle_count)) * 100  # per 100 cycles

    if grade in ("S", "A"):
        avg_temp = round(random.uniform(25, 35), 1)
        max_temp = round(avg_temp + random.uniform(3, 10), 1)
        thermal_stress = round(random.uniform(5, 40), 1)
        ir_mohm = round(random.uniform(15, 45), 1)
        ir_growth = round(random.uniform(2, 18), 1)
        voltage_stability = round(random.uniform(0.92, 0.99), 3)
        coulombic_eff = round(random.uniform(0.985, 0.998), 4)
    elif grade == "B":
        avg_temp = round(random.uniform(28, 38), 1)
        max_temp = round(avg_temp + random.uniform(5, 15), 1)
        thermal_stress = round(random.uniform(30, 100), 1)
        ir_mohm = round(random.uniform(30, 70), 1)
        ir_growth = round(random.uniform(10, 30), 1)
        voltage_stability = round(random.uniform(0.85, 0.94), 3)
        coulombic_eff = round(random.uniform(0.970, 0.990), 4)
    elif grade == "C":
        avg_temp = round(random.uniform(30, 42), 1)
        max_temp = round(avg_temp + random.uniform(8, 18), 1)
        thermal_stress = round(random.uniform(80, 200), 1)
        ir_mohm = round(random.uniform(50, 120), 1)
        ir_growth = round(random.uniform(20, 45), 1)
        voltage_stability = round(random.uniform(0.78, 0.88), 3)
        coulombic_eff = round(random.uniform(0.950, 0.975), 4)
    else:  # D
        avg_temp = round(random.uniform(33, 45), 1)
        max_temp = round(avg_temp + random.uniform(10, 20), 1)
        thermal_stress = round(random.uniform(150, 400), 1)
        ir_mohm = round(random.uniform(80, 200), 1)
        ir_growth = round(random.uniform(35, 60), 1)
        voltage_stability = round(random.uniform(0.65, 0.80), 3)
        coulombic_eff = round(random.uniform(0.920, 0.960), 4)

    return {
        "cycle_count": cycle_count,
        "capacity_now_kwh": round(capacity_now, 2),
        "capacity_fade_pct": round(capacity_fade, 2),
        "fade_rate_pct_per_100cyc": round(fade_rate, 3),
        "avg_temp_c": avg_temp,
        "max_temp_c": max_temp,
        "thermal_stress_hours": thermal_stress,
        "internal_resistance_mohm": ir_mohm,
        "ir_growth_pct": ir_growth,
        "voltage_stability": voltage_stability,
        "coulombic_efficiency": coulombic_eff,
    }


def pick_assessment_reasons(grade: str, telemetry: dict, chemistry: str) -> list:
    """Pick 3 unique assessment reasons appropriate for the grade."""
    vals = {
        "cycles": telemetry["cycle_count"],
        "ir_growth": telemetry["ir_growth_pct"],
        "vs": telemetry["voltage_stability"],
        "ce": telemetry["coulombic_efficiency"],
        "tsh": telemetry["thermal_stress_hours"],
        "fade_rate": telemetry["fade_rate_pct_per_100cyc"],
        "fade_pct": telemetry["capacity_fade_pct"],
        "temp": telemetry["avg_temp_c"],
        "max_temp": telemetry["max_temp_c"],
        "ir": telemetry["internal_resistance_mohm"],
        "chemistry": chemistry,
    }
    if grade in ("S", "A", "B"):
        pool = POSITIVE_REASONS[:]
        if grade == "B":
            pool.extend(NEGATIVE_REASONS[:3])
    else:
        pool = NEGATIVE_REASONS[:] + POSITIVE_REASONS[:3]

    selected = random.sample(pool, min(3, len(pool)))
    reasons = []
    for r in selected:
        try:
            reasons.append(r.format(**vals))
        except (KeyError, ValueError):
            reasons.append(r.split("{")[0].strip())
    return reasons


def pick_explanation_json(telemetry: dict, soh: float) -> list:
    """Generate feature importance explanation for the assessment."""
    features = [
        {"feature": "cycle_count",        "label": "Cycle Count",        "value": telemetry["cycle_count"],        "weight": round(random.uniform(0.10, 0.20), 3)},
        {"feature": "capacity_fade_pct",  "label": "Capacity Fade %",    "value": telemetry["capacity_fade_pct"],  "weight": round(random.uniform(0.15, 0.25), 3)},
        {"feature": "ir_growth_pct",      "label": "IR Growth %",        "value": telemetry["ir_growth_pct"],      "weight": round(random.uniform(0.08, 0.18), 3)},
        {"feature": "avg_temp_c",         "label": "Avg Temperature °C", "value": telemetry["avg_temp_c"],         "weight": round(random.uniform(0.05, 0.12), 3)},
        {"feature": "thermal_stress",     "label": "Thermal Stress Hrs", "value": telemetry["thermal_stress_hours"],"weight": round(random.uniform(0.05, 0.15), 3)},
        {"feature": "voltage_stability",  "label": "Voltage Stability",  "value": telemetry["voltage_stability"],  "weight": round(random.uniform(0.08, 0.15), 3)},
        {"feature": "coulombic_eff",      "label": "Coulombic Eff.",     "value": telemetry["coulombic_efficiency"],"weight": round(random.uniform(0.05, 0.10), 3)},
    ]
    # Normalize weights
    total_w = sum(f["weight"] for f in features)
    for f in features:
        f["weight"] = round(f["weight"] / total_w, 3)
    return features


def confidence_for_grade(grade: str) -> str:
    if grade in ("S", "A"):
        return random.choice(["high", "high", "high", "medium"])
    elif grade == "B":
        return random.choice(["high", "medium", "medium"])
    elif grade == "C":
        return random.choice(["medium", "medium", "low"])
    else:
        return random.choice(["high", "medium"])  # D is clear


def pick_deployment_reasons(grade: str, chemistry: str, site, dist_km: float, rul: float, energy_mwh: float, carbon_kg: float, voltage: float) -> list:
    vals = {
        "grade": grade, "site_type": site.site_type.replace("_", " "),
        "dist_km": dist_km, "chemistry": chemistry, "rul": rul,
        "carbon_kg": carbon_kg, "energy_mwh": energy_mwh,
        "state": site.state or "India", "voltage": voltage,
    }
    selected = random.sample(DEPLOYMENT_REASONS, 3)
    reasons = []
    for r in selected:
        try:
            reasons.append(r.format(**vals))
        except (KeyError, ValueError):
            reasons.append(r.split("{")[0].strip())
    return reasons


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def generate_lifecycle_events(battery_id: int, battery: dict, telemetry: dict, assessment: dict, deployment_info: dict) -> list:
    """Generate 5-9 lifecycle events for a battery."""
    events = []
    prev_hash = "genesis_hash"
    mfg_date = battery["manufacture_date"]

    # 1. Manufactured
    ts1 = datetime(mfg_date.year, mfg_date.month, mfg_date.day, 8, 0)
    payload1 = {"factory": f"{battery['oem']} plant, {battery['source_city']}"}
    h = compute_event_hash(prev_hash, "manufactured", ts1, payload1)
    events.append({"battery_id": battery_id, "event_type": "manufactured", "payload_json": payload1, "event_hash": h, "occurred_at": ts1})
    prev_hash = h

    # 2. Commissioned/first_life_started (+15-60 days)
    ts2 = ts1 + timedelta(days=random.randint(15, 60))
    model = battery.get("model", "EV")
    vehicle_desc = f"{battery['oem']} {model}"
    payload2 = {"vehicle": vehicle_desc, "city": battery["source_city"]}
    h = compute_event_hash(prev_hash, "first_life_started", ts2, payload2)
    events.append({"battery_id": battery_id, "event_type": "first_life_started", "payload_json": payload2, "event_hash": h, "occurred_at": ts2})
    prev_hash = h

    # 3. Optional: routine check (for older batteries) — 6-18 months after commissioning
    if telemetry["cycle_count"] > 400:
        ts3 = ts2 + timedelta(days=random.randint(180, 540))
        early_soh = min(98, assessment["soh_pct"] + random.randint(5, 15))
        payload3 = {"soh_pct": early_soh, "cycle_count": int(telemetry["cycle_count"] * 0.4)}
        h = compute_event_hash(prev_hash, "routine_check", ts3, payload3)
        events.append({"battery_id": battery_id, "event_type": "routine_check", "payload_json": payload3, "event_hash": h, "occurred_at": ts3})
        prev_hash = h

    # 4. Optional: second routine check for very old batteries
    if telemetry["cycle_count"] > 800:
        ts4 = ts2 + timedelta(days=random.randint(700, 1200))
        mid_soh = min(95, assessment["soh_pct"] + random.randint(3, 8))
        payload4 = {"soh_pct": mid_soh, "cycle_count": int(telemetry["cycle_count"] * 0.7)}
        h = compute_event_hash(prev_hash, "routine_check", ts4, payload4)
        events.append({"battery_id": battery_id, "event_type": "routine_check", "payload_json": payload4, "event_hash": h, "occurred_at": ts4})
        prev_hash = h

    # 5. Retired from EV — randomized date between Jan 2024 and Mar 2026
    retire_base = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 790))
    est_km = telemetry["cycle_count"] * random.randint(35, 55)
    payload5 = {"reason": "End of first life", "mileage_km": est_km, "soh_at_retirement": assessment["soh_pct"]}
    h = compute_event_hash(prev_hash, "retired_from_ev", retire_base, payload5)
    events.append({"battery_id": battery_id, "event_type": "retired_from_ev", "payload_json": payload5, "event_hash": h, "occurred_at": retire_base})
    prev_hash = h

    # 6. Received at VoltLife (+3-30 days after retirement)
    ts6 = retire_base + timedelta(days=random.randint(3, 30))
    source_prog = random.choice(SOURCE_PROGRAMS)
    payload6 = {"collection_center": f"{battery['source_city']} Collection Center", "source_program": source_prog}
    h = compute_event_hash(prev_hash, "ingested", ts6, payload6)
    events.append({"battery_id": battery_id, "event_type": "ingested", "payload_json": payload6, "event_hash": h, "occurred_at": ts6})
    prev_hash = h

    # 7. AI Assessment (+1-7 days after intake)
    ts7 = ts6 + timedelta(days=random.randint(1, 7))
    payload7 = {
        "grade": assessment["grade"],
        "soh_pct": assessment["soh_pct"],
        "confidence": assessment["confidence"],
        "recommendation": deployment_info.get("site_type", "recycler").replace("_", " ").title(),
    }
    h = compute_event_hash(prev_hash, "ai_assessment", ts7, payload7)
    events.append({"battery_id": battery_id, "event_type": "ai_assessment", "payload_json": payload7, "event_hash": h, "occurred_at": ts7})
    prev_hash = h

    # 8. Deployment or recycling (+2-14 days after assessment)
    ts8 = ts7 + timedelta(days=random.randint(2, 14))
    if assessment["grade"] == "D":
        payload8 = {"destination": "Certified Recycling Center", "city": deployment_info.get("city", battery["source_city"])}
        etype = "recycled"
    else:
        payload8 = {"site": deployment_info.get("site_name", "Solar Storage"), "city": deployment_info.get("city", battery["source_city"])}
        etype = "deployment_assigned"
    h = compute_event_hash(prev_hash, etype, ts8, payload8)
    events.append({"battery_id": battery_id, "event_type": etype, "payload_json": payload8, "event_hash": h, "occurred_at": ts8})
    prev_hash = h

    # 9. Optional: deployment confirmed for non-D grades
    if assessment["grade"] != "D" and random.random() < 0.7:
        ts9 = ts8 + timedelta(days=random.randint(1, 5))
        payload9 = {"status": "operational", "partner": random.choice(PARTNERS)}
        h = compute_event_hash(prev_hash, "deployment_confirmed", ts9, payload9)
        events.append({"battery_id": battery_id, "event_type": "deployment_confirmed", "payload_json": payload9, "event_hash": h, "occurred_at": ts9})

    return events


def generate_aadhaar_id(oem: str, chemistry: str, voltage: float, capacity: float, mfg_date: date, serial: int) -> str:
    """Generate a BPAN-style Aadhaar ID matching the existing schema."""
    country = "IN"
    mfr = oem[:3].upper().ljust(3, "X")
    chem_map = {"NMC": "N", "LFP": "L", "LCO": "C"}
    chem = chem_map.get(chemistry.upper(), "N")
    volt = f"{max(0, min(99, int(voltage))):02d}"
    cap = f"{max(0, min(99, int(capacity))):02d}"
    dt = mfg_date.strftime("%d%m%y")
    ser = f"{max(0, min(99999, serial)):05d}"
    return f"{country}{mfr}{chem}{volt}{cap}{dt}{ser}"


def clear_demo_data(db: Session):
    """Remove all existing demo data from all tables in correct FK order."""
    print("🗑️  Clearing existing data...")
    db.query(LifecycleEvent).delete()
    db.query(Deployment).delete()
    db.query(Assessment).delete()
    db.query(TelemetrySummary).delete()
    db.query(Battery).delete()
    db.commit()
    print("   ✓ All tables cleared")


def seed_all(db: Session):
    """Master seeder: populates all tables with 847 batteries and related data."""
    print("=" * 60)
    print("⚡ VoltLife Demo Data Seeder")
    print("=" * 60)

    # 0. Clear old data
    clear_demo_data(db)

    # 1. Ensure sites exist
    site_count = db.query(Site).count()
    if site_count == 0:
        print("⚠️  No sites found. Running site seeder first...")
        from app.seed.seed import seed_sites
        seed_sites(db)
        site_count = db.query(Site).count()
    print(f"   ✓ {site_count} deployment sites available")

    # Load all sites for deployment matching
    all_sites = db.query(Site).all()
    non_recycler_sites = [s for s in all_sites if s.site_type != "recycler"]
    recycler_sites = [s for s in all_sites if s.site_type == "recycler"]

    # 2. Build distribution lists
    grades = build_grade_list()
    mfrs = build_manufacturer_list()

    print(f"\n📦 Generating {TOTAL_BATTERIES} battery records...")
    grade_counts = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    mfr_counts = {}
    status_counts = {}
    total_energy_mwh = 0.0
    total_carbon_kg = 0.0
    all_lifecycle_events = []

    for i in range(TOTAL_BATTERIES):
        grade = grades[i]
        mfr = mfrs[i]
        grade_counts[grade] = grade_counts.get(grade, 0) + 1
        mfr_counts[mfr["oem"]] = mfr_counts.get(mfr["oem"], 0) + 1

        # Pick city
        city_info = random.choice(CITIES)

        # Generate battery dates
        # Manufacture: Jan 2020 - Dec 2023 (batteries retired by 2024-2026)
        mfg_start = date(2020, 1, 1)
        mfg_end = date(2023, 12, 31)
        mfg_days = (mfg_end - mfg_start).days
        mfg_date = mfg_start + timedelta(days=random.randint(0, mfg_days))

        # Assessment date: spread Jan 2024 – Jun 2026
        assess_start = datetime(2024, 1, 1)
        assess_end = datetime(2026, 6, 13)
        assess_days = (assess_end - assess_start).days
        assess_date = assess_start + timedelta(
            days=random.randint(0, assess_days),
            hours=random.randint(6, 22),
            minutes=random.randint(0, 59)
        )

        # Battery attributes
        voltage = random.choice(mfr["voltages"])
        cap_low, cap_high = mfr["capacities"]
        rated_kwh = round(random.uniform(cap_low, cap_high), 2)
        chemistry = mfr["chemistry"]
        model = random.choice(mfr["models"])
        soh = soh_for_grade(grade)
        rul = rul_for_soh(soh)
        status = STATUS_MAP.get(grade, "assessed")

        # Add slight coordinate jitter for visual spread on maps
        lat = round(city_info["lat"] + random.uniform(-0.05, 0.05), 6)
        lng = round(city_info["lng"] + random.uniform(-0.05, 0.05), 6)

        # Generate Aadhaar ID
        aadhaar_id = generate_aadhaar_id(mfr["oem"], chemistry, voltage, rated_kwh, mfg_date, i + 1)

        # Create Battery record
        battery = Battery(
            aadhaar_id=aadhaar_id,
            external_ref=f"VL-DEMO-{i+1:05d}",
            oem=mfr["oem"],
            model=model,
            chemistry=chemistry,
            form_factor="pack" if voltage >= 96 else "module",
            rated_capacity_kwh=rated_kwh,
            nominal_voltage=voltage,
            manufacture_date=mfg_date,
            source_city=city_info["city"],
            source_state=city_info["state"],
            lat=lat,
            lng=lng,
            status=status,
            created_at=assess_date - timedelta(days=random.randint(1, 14)),
        )
        db.add(battery)
        db.flush()

        status_counts[status] = status_counts.get(status, 0) + 1

        # Create Telemetry
        telem = generate_telemetry(rated_kwh, soh, chemistry, grade, mfg_date)
        telemetry = TelemetrySummary(
            battery_id=battery.id,
            cycle_count=telem["cycle_count"],
            capacity_now_kwh=telem["capacity_now_kwh"],
            capacity_fade_pct=telem["capacity_fade_pct"],
            fade_rate_pct_per_100cyc=telem["fade_rate_pct_per_100cyc"],
            avg_temp_c=telem["avg_temp_c"],
            max_temp_c=telem["max_temp_c"],
            thermal_stress_hours=telem["thermal_stress_hours"],
            internal_resistance_mohm=telem["internal_resistance_mohm"],
            ir_growth_pct=telem["ir_growth_pct"],
            voltage_stability=telem["voltage_stability"],
            coulombic_efficiency=telem["coulombic_efficiency"],
            features_json={
                "cycle_count": telem["cycle_count"],
                "capacity_fade_pct": telem["capacity_fade_pct"],
                "ir_growth_pct": telem["ir_growth_pct"],
                "avg_temp_c": telem["avg_temp_c"],
                "max_temp_c": telem["max_temp_c"],
                "thermal_stress_hours": telem["thermal_stress_hours"],
                "voltage_stability": telem["voltage_stability"],
                "coulombic_efficiency": telem["coulombic_efficiency"],
            },
        )
        db.add(telemetry)

        # Create Assessment
        reasons = pick_assessment_reasons(grade, telem, chemistry)
        explanation = pick_explanation_json(telem, soh)
        confidence = confidence_for_grade(grade)

        assessment = Assessment(
            battery_id=battery.id,
            soh_pct=soh,
            rul_years=rul,
            rul_low_years=round(rul * random.uniform(0.7, 0.9), 1),
            rul_high_years=round(rul * random.uniform(1.1, 1.4), 1),
            grade=grade,
            confidence=confidence,
            model_version="v1.2.0",
            explanation_json=explanation,
            created_at=assess_date,
        )
        db.add(assessment)
        db.flush()

        # Create Deployment
        deployment_info = {}
        if grade == "D":
            # Route to recycler
            site = random.choice(recycler_sites) if recycler_sites else all_sites[0]
            dist = haversine_km(lat, lng, float(site.lat), float(site.lng))
            energy = 0.0
            carbon = 0.0
            dep_status = "dispatched"
            deployment_info = {"site_name": site.name, "site_type": "recycler", "city": site.state}
        else:
            # Route to best matching non-recycler site
            site = random.choice(non_recycler_sites)
            dist = haversine_km(lat, lng, float(site.lat), float(site.lng))
            # Energy unlocked = usable capacity * cycles_per_year * RUL * DoD * efficiency / 1000 → MWh
            usable_kwh = rated_kwh * (soh / 100.0)
            energy = round(usable_kwh * 300 * rul * 0.80 * 0.90 / 1000.0, 3)
            carbon = round(energy * 650, 1)  # ~650 kg CO₂ per MWh displaced
            dep_status = "approved" if grade in ("S", "A") else "recommended"
            deployment_info = {"site_name": site.name, "site_type": site.site_type, "city": site.state}

        total_energy_mwh += energy
        total_carbon_kg += carbon

        dep_reasons = pick_deployment_reasons(
            grade, chemistry, site, dist, rul, energy, carbon, voltage
        )

        deployment = Deployment(
            battery_id=battery.id,
            site_id=site.id,
            score=round(random.uniform(0.65, 0.98), 3) if grade != "D" else 1.0,
            reasoning_json=[{"site_id": site.id, "score": random.randint(60, 98), "factors": dep_reasons}],
            distance_km=round(dist, 1),
            energy_unlocked_mwh=energy,
            carbon_saved_kg=carbon,
            status=dep_status,
            created_at=assess_date + timedelta(hours=random.randint(1, 48)),
        )
        db.add(deployment)

        # Generate lifecycle events
        batt_dict = {
            "oem": mfr["oem"], "model": model, "source_city": city_info["city"],
            "manufacture_date": mfg_date,
        }
        assess_dict = {"grade": grade, "soh_pct": soh, "confidence": confidence}
        lifecycle = generate_lifecycle_events(battery.id, batt_dict, telem, assess_dict, deployment_info)
        all_lifecycle_events.extend(lifecycle)

        # Periodic commit to avoid memory issues
        if (i + 1) % 100 == 0:
            db.commit()
            print(f"   ✓ {i + 1}/{TOTAL_BATTERIES} batteries created")

    # Final commit for remaining
    db.commit()
    print(f"   ✓ {TOTAL_BATTERIES}/{TOTAL_BATTERIES} batteries created")

    # 3. Insert all lifecycle events
    print(f"\n📜 Inserting {len(all_lifecycle_events)} lifecycle events...")
    for idx, evt in enumerate(all_lifecycle_events):
        le = LifecycleEvent(
            battery_id=evt["battery_id"],
            event_type=evt["event_type"],
            payload_json=evt["payload_json"],
            event_hash=evt["event_hash"],
            occurred_at=evt["occurred_at"],
        )
        db.add(le)
        if (idx + 1) % 500 == 0:
            db.commit()
    db.commit()
    print(f"   ✓ {len(all_lifecycle_events)} lifecycle events inserted")

    # 4. Print summary
    print("\n" + "=" * 60)
    print("✅ DEMO DATA SEEDED SUCCESSFULLY")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Total Batteries:    {TOTAL_BATTERIES}")
    print(f"   Total Assessments:  {TOTAL_BATTERIES}")
    print(f"   Total Deployments:  {TOTAL_BATTERIES}")
    print(f"   Lifecycle Events:   {len(all_lifecycle_events)}")
    print(f"   Energy Unlocked:    {total_energy_mwh:.1f} MWh")
    print(f"   Carbon Saved:       {total_carbon_kg/1000:.1f} tonnes CO₂")
    print(f"\n   Grade Distribution:")
    for g, c in sorted(grade_counts.items()):
        print(f"      {g}: {c}")
    print(f"\n   Manufacturer Distribution:")
    for m, c in sorted(mfr_counts.items(), key=lambda x: -x[1]):
        print(f"      {m}: {c}")
    print(f"\n   Status Distribution:")
    for s, c in sorted(status_counts.items()):
        print(f"      {s}: {c}")


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    db = SessionLocal()
    try:
        seed_all(db)
    except Exception as e:
        db.rollback()
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
