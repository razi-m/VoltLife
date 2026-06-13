"""
predict.py — Backend Integration Seam  (Phase 12)

Phase-3 integration is a one-line swap in the backend:
    from ml.predict import predict

predict(telemetry) returns the FROZEN output contract (master plan + backend
app/schemas/ml.py). It NEVER raises in pipeline context: any failure returns a
safe, low-confidence, contract-valid result.

Contract returned by predict():
  {
    "soh_pct": float, "rul_years": float, "rul_cycles": int,
    "rul_low": float, "rul_high": float,
    "confidence": "high|medium|low", "grade": "S|A|B|C|D",
    "recommendation": {"top_3": [...], "selected": str, "score": float, "reasoning": str},
    "reasons": [str, str, str],
    "explanation": [ {feature,value,impact,shap,label}, ... ],   # additive (backend)
    "volt_ai": { ...narratives... }                              # additive
  }
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import joblib

import shared_constants as C
from features import build_model_input, features_dict_to_vector
from confidence import assess_confidence
from grade import assign_grade
from recommend import recommend as recommend_engine
from explain import explain as explain_engine
from volt_ai import generate_narratives

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(_HERE, "models", "model_v1.pkl")
_BUNDLE = None


def load_bundle(path=None):
    global _BUNDLE
    if _BUNDLE is None or path is not None:
        _BUNDLE = joblib.load(path or DEFAULT_MODEL_PATH)
    return _BUNDLE


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def assess(features, bundle=None):
    """Core assessment -> AssessmentResult-compatible dict (no recommendation/volt_ai)."""
    bundle = bundle or load_bundle()
    env = bundle["ood_envelope"]
    norm, missing = build_model_input(features, env)
    raw_vec, _ = features_dict_to_vector(features)

    # SoH
    soh = round(float(_clamp(bundle["soh_model"].predict(norm)[0], 0.0, 100.0)), 1)

    # RUL (Q50 primary; conformalized Q10/Q90 band)
    margin = float(bundle.get("rul_conformal_margin", 0.0))
    q50 = float(bundle["rul_q50"].predict(norm)[0])
    q10 = float(bundle["rul_q10"].predict(norm)[0])
    q90 = float(bundle["rul_q90"].predict(norm)[0])
    lo_c, hi_c = q10 - margin, q90 + margin
    lo_c, hi_c = min(lo_c, hi_c), max(lo_c, hi_c)

    rul_cycles = int(_clamp(round(q50), C.RUL_CYCLES_MIN, C.RUL_CYCLES_MAX))
    lo_c = _clamp(lo_c, 0.0, C.RUL_CYCLES_MAX)
    hi_c = _clamp(hi_c, 0.0, C.RUL_CYCLES_MAX)
    rul_years = round(_clamp(rul_cycles / C.CYCLES_PER_YEAR, 0.0, C.RUL_YEARS_MAX), 1)
    rul_low = round(_clamp(lo_c / C.CYCLES_PER_YEAR, 0.0, C.RUL_YEARS_MAX), 1)
    rul_high = round(_clamp(hi_c / C.CYCLES_PER_YEAR, 0.0, C.RUL_YEARS_MAX), 1)
    # enforce rul_low <= rul_years <= rul_high
    rul_low = min(rul_low, rul_years)
    rul_high = max(rul_high, rul_years)

    confidence, signals = assess_confidence(raw_vec, missing, lo_c, hi_c, env)
    grade, blocked, route, note = assign_grade(
        soh, confidence, features.get("thermal_stress_hours"), rul_years,
        features.get("max_temp_c"), features.get("ir_growth_pct"))

    ex = explain_engine(bundle, norm, features, missing)
    return {
        "soh_pct": soh,
        "rul_cycles": rul_cycles,
        "rul_years": rul_years,
        "rul_low": rul_low,
        "rul_high": rul_high,
        "confidence": confidence,
        "grade": grade,
        "explanation": ex["explanation"],
        "reasons": ex["reasons"],
        "_blocked": blocked,
        "_route": route,
        "_grade_note": note,
        "_signals": signals,
        "_explain": ex,
    }


def _safe_default(reason):
    """Contract-valid fallback used only if inference fails (never raise)."""
    return {
        "soh_pct": 0.0, "rul_years": 0.0, "rul_cycles": 0, "rul_low": 0.0, "rul_high": 0.0,
        "confidence": "low", "grade": "D",
        "recommendation": {"top_3": ["Inspection Required"], "selected": "Inspection Required",
                           "score": 0.0, "reasoning": f"Assessment unavailable: {reason}"},
        "reasons": ["Assessment unavailable", "Routed to inspection", "Manual review required"],
        "explanation": [{"feature": "error", "value": None, "impact": "-", "shap": 0.0,
                         "label": f"Assessment unavailable: {reason}"}],
        "volt_ai": {},
    }


def predict(telemetry, battery_meta=None, sites=None, bundle=None):
    """Full ML response (frozen contract). Never raises in pipeline context."""
    try:
        bundle = bundle or load_bundle()
        core = assess(telemetry, bundle)
        meta = battery_meta or {}
        capacity = (meta.get("rated_capacity_kwh")
                    or telemetry.get("rated_capacity_kwh"))
        location = meta.get("location") or {
            "lat": telemetry.get("lat"), "lng": telemetry.get("lng")}

        rec = recommend_engine(core["grade"], core["soh_pct"], core["rul_years"],
                               core["confidence"], capacity_kwh=capacity,
                               location=location, sites=sites)
        result = {
            "soh_pct": core["soh_pct"],
            "rul_years": core["rul_years"],
            "rul_cycles": core["rul_cycles"],
            "rul_low": core["rul_low"],
            "rul_high": core["rul_high"],
            "confidence": core["confidence"],
            "grade": core["grade"],
            "recommendation": {
                "top_3": rec["top_3"],
                "selected": rec["selected"],
                "score": rec["score"],
                "reasoning": rec["reasoning"],
            },
            "reasons": core["reasons"],
            "explanation": core["explanation"],
        }
        result["volt_ai"] = generate_narratives(result, battery_meta)
        return result
    except Exception as e:  # never raise into the backend pipeline
        return _safe_default(type(e).__name__ + ": " + str(e)[:80])


if __name__ == "__main__":
    import json
    demo = {"cycle_count": 412, "capacity_fade_pct": 14.0, "fade_rate": 1.2e-4,
            "fade_acceleration": 1e-8, "avg_temp_c": 31.0, "max_temp_c": 43.0,
            "thermal_stress_hours": 6.0, "internal_resistance_mohm": 33.0,
            "ir_growth_pct": 18.0, "cv_phase_fraction": 0.22, "voltage_slope": -0.0009,
            "voltage_variance": 0.0015, "charge_efficiency": 0.985,
            "discharge_efficiency": 0.978, "rated_capacity_kwh": 40.0}
    print(json.dumps(predict(demo), indent=2, default=float))
