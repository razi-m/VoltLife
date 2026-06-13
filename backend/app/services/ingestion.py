import csv
import io
import json
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.orm import Battery, TelemetrySummary
from shared.constants import INDIA_BOUNDS, MAX_INGESTION_ROWS
from app.core.logging import logger

def validate_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates a single ingestion row.
    Returns (is_valid, reason_str).
    """
    # 1. Required fields check
    for req in ["external_ref", "oem", "chemistry", "rated_capacity_kwh", "cycle_count", "capacity_now_kwh"]:
        if not row.get(req):
            return False, f"Missing required field: {req}"

    # 2. Chemistry check
    chem = str(row["chemistry"]).upper().strip()
    if chem not in ("NMC", "LFP", "LCO"):
        return False, f"Invalid chemistry: {chem}. Must be NMC, LFP, or LCO"

    # 3. Numeric bounds checks
    try:
        rated = float(row["rated_capacity_kwh"])
        now = float(row["capacity_now_kwh"])
        cycle_count = int(row["cycle_count"])
    except (ValueError, TypeError):
        return False, "Non-numeric values in capacity or cycle count"

    if rated <= 0:
        return False, "rated_capacity_kwh must be greater than 0"
    if now <= 0:
        return False, "capacity_now_kwh must be greater than 0"
    if now > rated:
        return False, "capacity_now_kwh cannot be greater than rated_capacity_kwh"
    if cycle_count < 0:
        return False, "cycle_count cannot be negative"

    # 4. Lat/Lng Bounding Box check (India: 6-37 N, 68-98 E)
    lat_val = row.get("lat")
    lng_val = row.get("lng")
    if lat_val is None or lng_val is None:
        return False, "Missing lat or lng coordinates"
        
    try:
        lat = float(lat_val)
        lng = float(lng_val)
    except (ValueError, TypeError):
        return False, "Invalid non-numeric coordinates"

    if not (INDIA_BOUNDS["min_lat"] <= lat <= INDIA_BOUNDS["max_lat"]):
        return False, f"Latitude {lat} is outside India boundary ({INDIA_BOUNDS['min_lat']}-{INDIA_BOUNDS['max_lat']} N)"
    if not (INDIA_BOUNDS["min_lng"] <= lng <= INDIA_BOUNDS["max_lng"]):
        return False, f"Longitude {lng} is outside India boundary ({INDIA_BOUNDS['min_lng']}-{INDIA_BOUNDS['max_lng']} E)"

    return True, ""


def parse_csv_file(file_content: str) -> List[Dict[str, Any]]:
    """
    Parses CSV content into a list of dictionaries.
    """
    f = io.StringIO(file_content)
    reader = csv.DictReader(f)
    return [row for row in reader]


def process_ingestion(db: Session, rows: List[Dict[str, Any]]) -> Tuple[List[int], List[Dict[str, Any]]]:
    """
    Processes a list of parsed rows, validates them, and inserts valid rows to the DB.
    Returns a tuple of (inserted_battery_ids, rejects_list).
    """
    inserted_ids = []
    rejects = []
    
    if len(rows) > MAX_INGESTION_ROWS:
        raise ValueError(f"Batch size exceeds maximum limit of {MAX_INGESTION_ROWS} rows")

    # Normalize "" to None for all values in each row to prevent type conversion crashes on empty cells
    normalized_rows = []
    for row in rows:
        normalized_row = {}
        for k, v in row.items():
            if v == "" or (isinstance(v, str) and v.strip() == ""):
                normalized_row[k] = None
            else:
                normalized_row[k] = v
        normalized_rows.append(normalized_row)
    rows = normalized_rows

    for i, row in enumerate(rows, start=1):
        is_valid, reason = validate_row(row)
        if not is_valid:
            rejects.append({"row": i, "reason": reason})
            continue

        try:
            # Parse manufacture date
            mfg_date = None
            mfg_date_raw = row.get("manufacture_date")
            if mfg_date_raw:
                try:
                    # Support both YYYY-MM-DD and other formats if needed
                    mfg_date = datetime.strptime(str(mfg_date_raw).strip(), "%Y-%m-%d").date()
                except ValueError:
                    pass

            # Create Battery ORM Object
            battery = Battery(
                external_ref=str(row["external_ref"]).strip(),
                oem=str(row["oem"]).strip(),
                model=str(row["model"]).strip() if row.get("model") else None,
                chemistry=str(row["chemistry"]).upper().strip(),
                form_factor=str(row.get("form_factor") or "pack").strip(),
                rated_capacity_kwh=float(row["rated_capacity_kwh"]),
                nominal_voltage=float(row["nominal_voltage"]) if row.get("nominal_voltage") else None,
                manufacture_date=mfg_date,
                source_city=str(row["source_city"]).strip() if row.get("source_city") else None,
                source_state=str(row["source_state"]).strip() if row.get("source_state") else None,
                lat=float(row["lat"]),
                lng=float(row["lng"]),
                status="ingested"
            )
            db.add(battery)
            db.flush() # Populate battery.id

            # Save the canonical 14 feature dictionary
            from app.ml.features import from_telemetry
            features_dict = from_telemetry(row)

            # Create TelemetrySummary ORM Object
            telemetry = TelemetrySummary(
                battery_id=battery.id,
                cycle_count=int(row["cycle_count"]),
                capacity_now_kwh=float(row["capacity_now_kwh"]),
                capacity_fade_pct=float(features_dict["capacity_fade_pct"]),
                fade_rate_pct_per_100cyc=float(row["fade_rate"]) if row.get("fade_rate") is not None else None,
                avg_temp_c=float(row["avg_temp_c"]) if row.get("avg_temp_c") is not None else None,
                max_temp_c=float(row["max_temp_c"]) if row.get("max_temp_c") is not None else None,
                thermal_stress_hours=float(row["thermal_stress_hours"]) if row.get("thermal_stress_hours") is not None else None,
                internal_resistance_mohm=float(row["internal_resistance_mohm"]) if row.get("internal_resistance_mohm") is not None else None,
                ir_growth_pct=float(row["ir_growth_pct"]) if row.get("ir_growth_pct") is not None else None,
                voltage_stability=round(max(0.0, 1.0 - min(1.0, float(row["voltage_variance"]))), 3) if row.get("voltage_variance") is not None else None,  # stability = 1 - clamped variance (T7)
                coulombic_efficiency=float(row["coulombic_efficiency"]) if row.get("coulombic_efficiency") is not None else None,
                features_json=features_dict
            )
            db.add(telemetry)
            db.commit()
            
            inserted_ids.append(battery.id)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database insertion failed for row {i}: {e}")
            rejects.append({"row": i, "reason": f"Database error: {str(e)}"})

    return inserted_ids, rejects
