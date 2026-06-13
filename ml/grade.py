"""
grade.py — Grade Engine  (Phase 7)

Grades: S / A / B / C / D.  D renders as "Recycle" in the frontend.

Grade D is a HARD SAFETY OVERRIDE — checked FIRST and never overridable:
    soh_pct < 60.0  OR  max_temp_c > 55.0  OR  ir_growth_pct > 60.0
Grade D blocks all deployment and routes directly to a Certified Recycler.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math
import shared_constants as C


def _is_nan(x):
    try:
        return x is None or math.isnan(float(x))
    except (TypeError, ValueError):
        return True


def safety_triggered(soh_pct, max_temp_c, ir_growth_pct):
    """Hard Grade-D safety triggers. Missing values do NOT trigger (fail-safe handled
    by confidence -> inspection); only present, out-of-bounds values trigger."""
    if soh_pct is not None and soh_pct < C.SAFETY_SOH_FLOOR:
        return True, f"SoH below safety floor ({soh_pct:.1f}% < {C.SAFETY_SOH_FLOOR:.0f}%)"
    if not _is_nan(max_temp_c) and float(max_temp_c) > C.SAFETY_MAX_TEMP_C:
        return True, f"Overheating ({float(max_temp_c):.1f}C > {C.SAFETY_MAX_TEMP_C:.0f}C)"
    if not _is_nan(ir_growth_pct) and float(ir_growth_pct) > C.SAFETY_IR_GROWTH_PCT:
        return True, f"Critical internal-resistance growth ({float(ir_growth_pct):.1f}% > {C.SAFETY_IR_GROWTH_PCT:.0f}%)"
    return False, ""


def assign_grade(soh_pct, confidence, thermal_stress_hours, rul_years,
                 max_temp_c=None, ir_growth_pct=None):
    """Return (grade, blocked, route, note).

    blocked == True only for Grade D (deployment planner receives status 'blocked').
    """
    # 1) HARD SAFETY OVERRIDE — Grade D (cannot be overridden by any later logic)
    triggered, why = safety_triggered(soh_pct, max_temp_c, ir_growth_pct)
    if triggered:
        return "D", True, "Certified Recycler", f"Grade D safety override: {why}"

    # 2) Standard SoH banding
    ts = 0.0 if _is_nan(thermal_stress_hours) else float(thermal_stress_hours)
    if (soh_pct >= C.GRADE_S_SOH and confidence == "high"
            and ts < C.GRADE_S_MAX_THERMAL_STRESS_H
            and rul_years >= C.GRADE_S_MIN_RUL_YEARS):
        return "S", False, "deployable", "Pristine: high SoH, high confidence, low thermal stress, long RUL"
    if soh_pct >= C.GRADE_A_SOH:
        return "A", False, "deployable", "Excellent state of health"
    if soh_pct >= C.GRADE_B_SOH:
        return "B", False, "deployable", "Good state of health"
    if soh_pct >= C.GRADE_C_SOH:
        return "C", False, "deployable", "Fair state of health — low-demand applications"
    # Below 60% with no explicit safety flag still falls to D by SoH rule
    return "D", True, "Certified Recycler", "Grade D: SoH below 60%"
