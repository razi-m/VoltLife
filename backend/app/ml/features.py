import math
from typing import Dict, Any

def from_telemetry(summary: Dict[str, Any]) -> Dict[str, float]:
    """
    Constructs the canonical 14-key feature dictionary from the telemetry summary dictionary.
    Handles missing values by mapping them to float('nan').
    """
    rated = float(summary.get("rated_capacity_kwh") or 4.0)
    now = float(summary.get("capacity_now_kwh") or rated)
    
    # Calculate capacity fade percentage
    capacity_fade_pct = ((1.0 - (now / rated)) * 100.0) if rated > 0 else 0.0

    # Helper function to parse values safely
    def get_float(key: str) -> float:
        val = summary.get(key)
        if val is None:
            return float('nan')
        try:
            return float(val)
        except ValueError:
            return float('nan')

    return {
        "cycle_count": int(summary.get("cycle_count") or 0),
        "capacity_fade_pct": capacity_fade_pct,
        "fade_rate": get_float("fade_rate"),
        "fade_acceleration": get_float("fade_acceleration"),
        "avg_temp_c": get_float("avg_temp_c"),
        "max_temp_c": get_float("max_temp_c"),
        "thermal_stress_hours": get_float("thermal_stress_hours"),
        "internal_resistance_mohm": get_float("internal_resistance_mohm"),
        "ir_growth_pct": get_float("ir_growth_pct"),
        "cv_phase_fraction": get_float("cv_phase_fraction"),
        "voltage_slope": get_float("voltage_slope"),
        "voltage_variance": get_float("voltage_variance"),
        "charge_efficiency": get_float("coulombic_efficiency"),  # maps coulombic_efficiency column to charge_efficiency
        "discharge_efficiency": get_float("discharge_efficiency"),
    }
