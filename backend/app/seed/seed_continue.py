"""
Continuation seeder: adds remaining batteries (501-847) and lifecycle events.
"""
import os, sys, random, hashlib, json, math
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.orm import Battery, TelemetrySummary, Assessment, Deployment, Site, LifecycleEvent

# Reuse the same seed for deterministic output from index 500 onward
random.seed(42)
# Fast-forward random state to position 500
for _ in range(500 * 30):  # approx operations per battery
    random.random()

# Import all the helpers from the main seeder
from app.seed.seed_demo import (
    TOTAL_BATTERIES, MANUFACTURERS, GRADE_DIST, SOURCE_PROGRAMS, CITIES,
    PARTNERS, STATUS_MAP, build_grade_list, build_manufacturer_list,
    soh_for_grade, rul_for_soh, generate_telemetry, pick_assessment_reasons,
    pick_explanation_json, confidence_for_grade, pick_deployment_reasons,
    haversine_km, generate_lifecycle_events, generate_aadhaar_id,
    compute_event_hash
)


def seed_remaining(db: Session):
    existing = db.query(Battery).count()
    print(f"Existing batteries: {existing}")

    if existing >= TOTAL_BATTERIES:
        print(f"Already have {existing} batteries. Skipping battery creation.")
    else:
        # Rebuild the same distribution lists with same seed
        random.seed(42)
        grades = build_grade_list()
        mfrs = build_manufacturer_list()

        all_sites = db.query(Site).all()
        non_recycler_sites = [s for s in all_sites if s.site_type != "recycler"]
        recycler_sites = [s for s in all_sites if s.site_type == "recycler"]

        start_idx = existing
        remaining = TOTAL_BATTERIES - existing
        print(f"Adding {remaining} more batteries (index {start_idx} to {TOTAL_BATTERIES-1})...")

        # Fast-forward random state to match where we left off
        random.seed(42)
        # Consume random calls for already-created batteries to keep distribution consistent
        for i in range(start_idx):
            grade = grades[i]
            mfr = mfrs[i]
            city_info = random.choice(CITIES)
            mfg_start = date(2020, 1, 1)
            mfg_end = date(2023, 12, 31)
            mfg_days = (mfg_end - mfg_start).days
            random.randint(0, mfg_days)
            assess_start = datetime(2024, 1, 1)
            assess_end = datetime(2026, 6, 13)
            assess_days = (assess_end - assess_start).days
            random.randint(0, assess_days)
            random.randint(6, 22)
            random.randint(0, 59)
            random.choice(mfr["voltages"])
            cap_low, cap_high = mfr["capacities"]
            random.uniform(cap_low, cap_high)
            random.choice(mfr["models"])
            soh_for_grade(grade)
            # Skip remaining random calls per battery...
            for _ in range(20):
                random.random()

        # Now generate remaining batteries with fresh but sequential random state
        random.seed(4242 + start_idx)  # Use different seed for remaining to avoid conflicts

        for i in range(start_idx, TOTAL_BATTERIES):
            grade = grades[i]
            mfr = mfrs[i]
            city_info = random.choice(CITIES)

            mfg_date = date(2020, 1, 1) + timedelta(days=random.randint(0, 1460))
            assess_date = datetime(2024, 1, 1) + timedelta(
                days=random.randint(0, 893),
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59)
            )

            voltage = random.choice(mfr["voltages"])
            cap_low, cap_high = mfr["capacities"]
            rated_kwh = round(random.uniform(cap_low, cap_high), 2)
            chemistry = mfr["chemistry"]
            model = random.choice(mfr["models"])
            soh = soh_for_grade(grade)
            rul = rul_for_soh(soh)
            status = STATUS_MAP.get(grade, "assessed")

            lat = round(city_info["lat"] + random.uniform(-0.05, 0.05), 6)
            lng = round(city_info["lng"] + random.uniform(-0.05, 0.05), 6)

            aadhaar_id = generate_aadhaar_id(mfr["oem"], chemistry, voltage, rated_kwh, mfg_date, i + 1)

            # Check for aadhaar collision
            existing_bpan = db.query(Battery).filter(Battery.aadhaar_id == aadhaar_id).first()
            if existing_bpan:
                aadhaar_id = generate_aadhaar_id(mfr["oem"], chemistry, voltage, rated_kwh, mfg_date, i + 10000)

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
                lat=lat, lng=lng,
                status=status,
                created_at=assess_date - timedelta(days=random.randint(1, 14)),
            )
            db.add(battery)
            db.flush()

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

            reasons = pick_assessment_reasons(grade, telem, chemistry)
            explanation = pick_explanation_json(telem, soh)
            confidence = confidence_for_grade(grade)

            assessment = Assessment(
                battery_id=battery.id,
                soh_pct=soh, rul_years=rul,
                rul_low_years=round(rul * random.uniform(0.7, 0.9), 1),
                rul_high_years=round(rul * random.uniform(1.1, 1.4), 1),
                grade=grade, confidence=confidence,
                model_version="v1.2.0",
                explanation_json=explanation,
                created_at=assess_date,
            )
            db.add(assessment)
            db.flush()

            if grade == "D":
                site = random.choice(recycler_sites) if recycler_sites else all_sites[0]
                dist = haversine_km(lat, lng, float(site.lat), float(site.lng))
                energy, carbon, dep_status = 0.0, 0.0, "dispatched"
            else:
                site = random.choice(non_recycler_sites)
                dist = haversine_km(lat, lng, float(site.lat), float(site.lng))
                usable_kwh = rated_kwh * (soh / 100.0)
                energy = round(usable_kwh * 300 * rul * 0.80 * 0.90 / 1000.0, 3)
                carbon = round(energy * 650, 1)
                dep_status = "approved" if grade in ("S", "A") else "recommended"

            dep_reasons = pick_deployment_reasons(grade, chemistry, site, dist, rul, energy, carbon, voltage)
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

            if (i - start_idx + 1) % 50 == 0:
                db.commit()
                print(f"  Created {i - start_idx + 1}/{remaining} batteries")

        db.commit()
        print(f"  All {remaining} remaining batteries created!")

    # Now add lifecycle events for ALL batteries
    total_batteries = db.query(Battery).count()
    existing_events = db.query(LifecycleEvent).count()
    print(f"\nExisting lifecycle events: {existing_events}")

    if existing_events > 0:
        print("Clearing existing lifecycle events...")
        db.query(LifecycleEvent).delete()
        db.commit()

    print(f"Generating lifecycle events for {total_batteries} batteries...")
    batteries = db.query(Battery).order_by(Battery.id).all()

    random.seed(9999)  # Consistent seed for events
    event_count = 0

    for batch_start in range(0, len(batteries), 50):
        batch = batteries[batch_start:batch_start + 50]
        for b in batch:
            # Get assessment and deployment for this battery
            ass = db.query(Assessment).filter(Assessment.battery_id == b.id).order_by(Assessment.created_at.desc()).first()
            dep = db.query(Deployment).filter(Deployment.battery_id == b.id).first()

            if not ass:
                continue

            mfg_date = b.manufacture_date or date(2022, 1, 1)
            batt_dict = {
                "oem": b.oem, "model": b.model or "EV",
                "source_city": b.source_city or "Pune",
                "manufacture_date": mfg_date,
            }

            telem_dict = {
                "cycle_count": b.telemetry.cycle_count if b.telemetry else 500,
                "capacity_fade_pct": float(b.telemetry.capacity_fade_pct) if b.telemetry and b.telemetry.capacity_fade_pct else 15.0,
                "ir_growth_pct": float(b.telemetry.ir_growth_pct) if b.telemetry and b.telemetry.ir_growth_pct else 10.0,
                "thermal_stress_hours": float(b.telemetry.thermal_stress_hours) if b.telemetry and b.telemetry.thermal_stress_hours else 50.0,
                "voltage_stability": float(b.telemetry.voltage_stability) if b.telemetry and b.telemetry.voltage_stability else 0.9,
                "coulombic_efficiency": float(b.telemetry.coulombic_efficiency) if b.telemetry and b.telemetry.coulombic_efficiency else 0.98,
                "avg_temp_c": float(b.telemetry.avg_temp_c) if b.telemetry and b.telemetry.avg_temp_c else 32.0,
                "max_temp_c": float(b.telemetry.max_temp_c) if b.telemetry and b.telemetry.max_temp_c else 42.0,
                "internal_resistance_mohm": float(b.telemetry.internal_resistance_mohm) if b.telemetry and b.telemetry.internal_resistance_mohm else 40.0,
                "capacity_now_kwh": float(b.telemetry.capacity_now_kwh) if b.telemetry and b.telemetry.capacity_now_kwh else 20.0,
                "fade_rate_pct_per_100cyc": 0.5,
            }

            assess_dict = {
                "grade": ass.grade,
                "soh_pct": float(ass.soh_pct),
                "confidence": ass.confidence,
            }

            site = dep.site if dep else None
            deployment_info = {
                "site_name": site.name if site else "Unknown",
                "site_type": site.site_type if site else "recycler",
                "city": site.state if site else b.source_state,
            }

            events = generate_lifecycle_events(b.id, batt_dict, telem_dict, assess_dict, deployment_info)
            for evt in events:
                le = LifecycleEvent(
                    battery_id=evt["battery_id"],
                    event_type=evt["event_type"],
                    payload_json=evt["payload_json"],
                    event_hash=evt["event_hash"],
                    occurred_at=evt["occurred_at"],
                )
                db.add(le)
                event_count += 1

        db.commit()
        print(f"  Events batch {batch_start + len(batch)}/{len(batteries)} done ({event_count} events)")

    db.commit()
    print(f"\nDone! Total lifecycle events: {event_count}")

    # Final counts
    print("\n=== FINAL COUNTS ===")
    print(f"Batteries:    {db.query(Battery).count()}")
    print(f"Assessments:  {db.query(Assessment).count()}")
    print(f"Deployments:  {db.query(Deployment).count()}")
    print(f"Telemetry:    {db.query(TelemetrySummary).count()}")
    print(f"Events:       {db.query(LifecycleEvent).count()}")
    print(f"Sites:        {db.query(Site).count()}")


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        seed_remaining(db)
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
