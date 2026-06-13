import hashlib
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.models.orm import Battery, LifecycleEvent, Assessment, Deployment, Site
from app.core.config import settings
from app.core.logging import logger

def encode_bpan(country: str, mfr: str, chemistry: str, voltage: float, capacity: float, mfg_date: date, serial: int) -> str:
    """
    Encodes battery parameters into a 21-character BPAN-style Aadhaar ID.
    [2 country][3 mfr][1 chemistry][2 voltage][2 capacity][6 date DDMMYY][5 serial]
    """
    country_part = country[:2].upper().ljust(2, "X")
    mfr_part = mfr[:3].upper().ljust(3, "X")
    
    chem_map = {"NMC": "N", "LFP": "L", "LCO": "C"}
    chem_part = chem_map.get(chemistry.upper(), "X")
    
    volt_val = max(0, min(99, int(voltage)))
    volt_part = f"{volt_val:02d}"
    
    cap_val = max(0, min(99, int(capacity)))
    cap_part = f"{cap_val:02d}"
    
    date_part = mfg_date.strftime("%d%m%y")
    
    serial_val = max(0, min(99999, serial))
    serial_part = f"{serial_val:05d}"
    
    return f"{country_part}{mfr_part}{chem_part}{volt_part}{cap_part}{date_part}{serial_part}"


def decode_bpan(bpan: str) -> Dict[str, Any]:
    """
    Decodes a 21-character BPAN-style Aadhaar ID.
    """
    if len(bpan) != 21:
        raise ValueError("BPAN must be exactly 21 characters")
        
    country = bpan[0:2]
    mfr = bpan[2:5]
    chem_char = bpan[5]
    volt_str = bpan[6:8]
    cap_str = bpan[8:10]
    date_str = bpan[10:16]
    serial = bpan[16:21]
    
    chem_map = {"N": "NMC", "L": "LFP", "C": "LCO", "X": "UNKNOWN"}
    chemistry = chem_map.get(chem_char, "UNKNOWN")
    
    try:
        mfg_date = datetime.strptime(date_str, "%d%m%y").date()
    except ValueError:
        mfg_date = date(2026, 1, 1)
        
    return {
        "country": country,
        "manufacturer": mfr,
        "chemistry": chemistry,
        "voltage": f"{int(volt_str)}V",
        "capacity_kwh": float(int(cap_str)),
        "manufactured": mfg_date,
        "serial": serial
    }


def compute_event_hash(prev_hash: str, event_type: str, occurred_at: datetime, payload: dict) -> str:
    """
    Computes a cryptographic sha256 hash representing a tamper-evident blockchain step.
    """
    payload_str = json.dumps(payload, sort_keys=True)
    occurred_str = occurred_at.isoformat()
    data = f"{prev_hash}{event_type}{occurred_str}{payload_str}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def append_lifecycle_event(db: Session, battery_id: int, event_type: str, payload: dict = None, occurred_at: datetime = None) -> LifecycleEvent:
    """
    Appends a lifecycle event to the database and builds the tamper-evident hash chain.
    """
    if occurred_at is None:
        occurred_at = datetime.utcnow()
    if payload is None:
        payload = {}
        
    # Get previous event to read its hash
    prev_event = db.query(LifecycleEvent).filter(
        LifecycleEvent.battery_id == battery_id
    ).order_by(LifecycleEvent.occurred_at.desc(), LifecycleEvent.id.desc()).first()
    
    prev_hash = prev_event.event_hash if prev_event and prev_event.event_hash else "genesis_hash"
    event_hash = compute_event_hash(prev_hash, event_type, occurred_at, payload)
    
    event = LifecycleEvent(
        battery_id=battery_id,
        event_type=event_type,
        payload_json=payload,
        event_hash=event_hash,
        occurred_at=occurred_at
    )
    db.add(event)
    return event


def generate_life_story(battery: Battery, assessment: Assessment, deployment: Deployment) -> str:
    """
    Generates a deterministic 3-sentence narrative biography for the battery pack.
    """
    # 1. Origin sentence
    city = battery.source_city or "Pune"
    mfg_date = battery.manufacture_date or date(2024, 3, 15)
    month_str = mfg_date.strftime("%B")
    year_str = mfg_date.strftime("%Y")
    origin = f"Born in a {city} factory, {month_str} {year_str}."
    
    # 2. EV operations sentence
    cycle_count = battery.telemetry.cycle_count if battery.telemetry else 400
    est_km = cycle_count * 45  # Estimating ~45 km per cycle
    usage = f"Carried a commuter ~{est_km:,} km on {cycle_count} charges."
    
    # 3. Next life sentence
    soh = int(assessment.soh_pct)
    dest_name = deployment.site.name if deployment and deployment.site else "India's clean energy grid"
    dest_state = deployment.site.state if deployment and deployment.site else "local community"
    
    if assessment.grade == "D":
        next_chapter = f"Retired with {soh}% capacity — now safely recycled via certified recovery centers for material circularity."
    else:
        next_chapter = f"Retired with {soh}% of its heart intact — now it stores {dest_state}'s sunlight at {dest_name}."
        
    return f"{origin} {usage} {next_chapter}"


def issue_aadhaar(db: Session, battery: Battery, serial_num: int) -> str:
    """
    Generates and issues a unique Battery Aadhaar ID (BPAN) and inserts timeline events.
    """
    # Calculate BPAN
    mfg_date = battery.manufacture_date or date(2024, 3, 15)
    voltage = battery.nominal_voltage or 48.0
    capacity = battery.rated_capacity_kwh
    
    # Generate unique ID, conflict resolution by incrementing serial
    attempts = 0
    aadhaar_id = ""
    while attempts < 100:
        candidate_id = encode_bpan(
            country="IN",
            mfr=battery.oem,
            chemistry=battery.chemistry,
            voltage=voltage,
            capacity=capacity,
            mfg_date=mfg_date,
            serial=serial_num
        )
        # Check uniqueness
        exists = db.query(Battery).filter(Battery.aadhaar_id == candidate_id).first()
        if not exists:
            aadhaar_id = candidate_id
            break
        serial_num += 1
        attempts += 1
        
    if not aadhaar_id:
        # Fallback in case of massive collision
        aadhaar_id = f"IN{battery.oem[:3].upper()}N4804150324{serial_num:05d}"

    battery.aadhaar_id = aadhaar_id
    db.flush()

    # Backfill lifecycle history
    base_time = datetime(mfg_date.year, mfg_date.month, mfg_date.day)
    
    # Event 1: Manufactured
    append_lifecycle_event(db, battery.id, "manufactured", occurred_at=base_time)
    
    # Event 2: First Life Started (+30 days)
    first_life_time = base_time + timedelta(days=30)
    append_lifecycle_event(
        db, battery.id, "first_life_started",
        payload={"vehicle": f"e-scooter, {battery.source_city or 'Pune'}"},
        occurred_at=first_life_time
    )
    
    # Event 3: Retired from EV (recent, e.g. 7 days ago)
    retired_time = datetime.utcnow() - timedelta(days=7)
    append_lifecycle_event(db, battery.id, "retired_from_ev", occurred_at=retired_time)
    
    # Event 4: Ingested (at battery creation time)
    append_lifecycle_event(db, battery.id, "ingested", occurred_at=battery.created_at)

    return aadhaar_id


def compose_passport(db: Session, battery: Battery) -> Dict[str, Any]:
    """
    Composes a complete dynamic Aadhaar Passport response for a battery pack.
    """
    if not battery.aadhaar_id:
        raise ValueError("Aadhaar ID has not been issued yet")

    # Get latest assessment
    assessment = db.query(Assessment).filter(
        Assessment.battery_id == battery.id
    ).order_by(Assessment.created_at.desc()).first()
    
    # Get deployment
    deployment = db.query(Deployment).filter(
        Deployment.battery_id == battery.id
    ).order_by(Deployment.created_at.desc()).first()
    
    # Get timeline events
    events = db.query(LifecycleEvent).filter(
        LifecycleEvent.battery_id == battery.id
    ).order_by(LifecycleEvent.occurred_at.asc(), LifecycleEvent.id.asc()).all()

    # Decode ID segments
    decoded = decode_bpan(battery.aadhaar_id)
    
    # Static attributes
    static_data = {
        "chemistry": battery.chemistry,
        "rated_capacity_kwh": float(battery.rated_capacity_kwh),
        "mass_estimate_kg": int(float(battery.rated_capacity_kwh) * 6.0) # Estimate ~6kg per kWh
    }
    
    # Dynamic attributes
    dynamic_data = {}
    if assessment:
        dynamic_data = {
            "soh_pct": float(assessment.soh_pct),
            "status": "recycled" if assessment.grade == "D" else "repurposed",
            "grade": assessment.grade,
            "rul_years": float(assessment.rul_years)
        }
    else:
        dynamic_data = {
            "soh_pct": 0.0,
            "status": battery.status,
            "grade": "D",
            "rul_years": 0.0
        }

    # Life Story narrative
    life_story = ""
    if assessment:
        life_story = generate_life_story(battery, assessment, deployment)
        
    # Impact fields
    impact_data = {}
    if deployment:
        impact_data = {
            "energy_unlocked_mwh": float(deployment.energy_unlocked_mwh),
            "carbon_saved_kg": float(deployment.carbon_saved_kg)
        }
    else:
        impact_data = {
            "energy_unlocked_mwh": 0.0,
            "carbon_saved_kg": 0.0
        }

    # Timeline event mapping
    timeline = []
    for event in events:
        timeline.append({
            "event_type": event.event_type,
            "occurred_at": event.occurred_at.isoformat() + "Z",
            "payload": event.payload_json or {}
        })

    return {
        "aadhaar_id": battery.aadhaar_id,
        "decoded": decoded,
        "qr_payload": f"{settings.PUBLIC_FRONTEND_URL}/b/{battery.aadhaar_id}",
        "static": static_data,
        "dynamic": dynamic_data,
        "timeline": timeline,
        "life_story": life_story,
        "impact": impact_data
    }
