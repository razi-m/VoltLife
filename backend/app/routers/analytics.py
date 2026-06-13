from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.models.orm import Battery, TelemetrySummary, Assessment

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get("/analytics/fleet")
def get_fleet_analytics(db: Session = Depends(get_db)):
    """
    Returns fleet-wide telemetry aggregates for the Deep Health Analytics page.
    """
    total_batteries = db.query(func.count(Battery.id)).scalar() or 0
    total_with_telemetry = db.query(func.count(TelemetrySummary.battery_id)).scalar() or 0

    # Telemetry aggregates
    avg_cycle_count = db.query(func.avg(TelemetrySummary.cycle_count)).scalar()
    avg_capacity_fade = db.query(func.avg(TelemetrySummary.capacity_fade_pct)).scalar()
    avg_temp = db.query(func.avg(TelemetrySummary.avg_temp_c)).scalar()
    avg_max_temp = db.query(func.avg(TelemetrySummary.max_temp_c)).scalar()
    avg_ir = db.query(func.avg(TelemetrySummary.internal_resistance_mohm)).scalar()
    avg_ir_growth = db.query(func.avg(TelemetrySummary.ir_growth_pct)).scalar()
    avg_coulombic = db.query(func.avg(TelemetrySummary.coulombic_efficiency)).scalar()
    avg_voltage_stability = db.query(func.avg(TelemetrySummary.voltage_stability)).scalar()
    total_thermal_stress = db.query(func.sum(TelemetrySummary.thermal_stress_hours)).scalar()

    # SoH distribution buckets
    latest_subq = db.query(
        Assessment.battery_id,
        Assessment.soh_pct,
        func.row_number().over(
            partition_by=Assessment.battery_id,
            order_by=Assessment.created_at.desc()
        ).label("rn")
    ).subquery()

    soh_values = db.query(latest_subq.c.soh_pct).filter(
        latest_subq.c.rn == 1
    ).all()

    soh_distribution = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "below-60": 0}
    for (soh,) in soh_values:
        v = float(soh)
        if v >= 90:
            soh_distribution["90-100"] += 1
        elif v >= 80:
            soh_distribution["80-89"] += 1
        elif v >= 70:
            soh_distribution["70-79"] += 1
        elif v >= 60:
            soh_distribution["60-69"] += 1
        else:
            soh_distribution["below-60"] += 1

    # Chemistry distribution
    chem_counts = db.query(
        Battery.chemistry, func.count(Battery.id)
    ).group_by(Battery.chemistry).all()
    by_chemistry = {c: n for c, n in chem_counts}

    # OEM distribution
    oem_counts = db.query(
        Battery.oem, func.count(Battery.id)
    ).group_by(Battery.oem).all()
    by_oem = {o: n for o, n in oem_counts}

    # Cycle count distribution
    cycle_values = db.query(TelemetrySummary.cycle_count).all()
    cycle_distribution = {"0-200": 0, "200-500": 0, "500-1000": 0, "1000-2000": 0, "2000+": 0}
    for (cyc,) in cycle_values:
        if cyc < 200:
            cycle_distribution["0-200"] += 1
        elif cyc < 500:
            cycle_distribution["200-500"] += 1
        elif cyc < 1000:
            cycle_distribution["500-1000"] += 1
        elif cyc < 2000:
            cycle_distribution["1000-2000"] += 1
        else:
            cycle_distribution["2000+"] += 1

    def safe_round(val, digits=2):
        return round(float(val), digits) if val is not None else 0.0

    return {
        "total_batteries": total_batteries,
        "total_with_telemetry": total_with_telemetry,
        "averages": {
            "cycle_count": safe_round(avg_cycle_count, 0),
            "capacity_fade_pct": safe_round(avg_capacity_fade),
            "avg_temp_c": safe_round(avg_temp),
            "max_temp_c": safe_round(avg_max_temp),
            "internal_resistance_mohm": safe_round(avg_ir),
            "ir_growth_pct": safe_round(avg_ir_growth),
            "coulombic_efficiency": safe_round(avg_coulombic, 4),
            "voltage_stability": safe_round(avg_voltage_stability, 3),
            "total_thermal_stress_hours": safe_round(total_thermal_stress, 0),
        },
        "soh_distribution": soh_distribution,
        "cycle_distribution": cycle_distribution,
        "by_chemistry": by_chemistry,
        "by_oem": by_oem,
    }
