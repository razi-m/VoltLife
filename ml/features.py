"""
features.py — canonical 14-feature extraction  (Phase 2)

Two responsibilities:
  A. Training: compute the 14 canonical features from a cell trajectory at a
     lifecycle cutoff K (deterministic).
  B. Inference: turn an arbitrary telemetry dict into a model-ready vector,
     handling missing features gracefully (never crash) and reporting which
     features were missing (for the confidence engine).

All extraction is deterministic. Normalization uses the training OOD envelope
(min/max per feature) stored in the model bundle.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C

HOURS_PER_CYCLE = 2.0   # assumed wall-clock per full cycle for thermal_stress_hours


def _slope(x, y):
    """Least-squares slope of y vs x; 0 if degenerate."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if len(x) < 2 or np.allclose(x, x[0]):
        return 0.0
    return float(np.polyfit(x, y, 1)[0])


def compute_features_from_trajectory(records, cutoff_k=None, window=60):
    """Compute the 14 canonical features from cycle records up to cutoff_k.

    records: list of per-cycle dicts (parse_nasa schema). Must be cycle-ordered.
    cutoff_k: include cycles with cycle <= cutoff_k (None -> full life).
    Returns a dict keyed by the 14 canonical FEATURE_KEYS.
    """
    recs = sorted(records, key=lambda r: r["cycle"])
    if cutoff_k is not None:
        recs = [r for r in recs if r["cycle"] <= cutoff_k]
    if len(recs) < 3:
        return None  # not enough history to extract a stable feature vector

    cycles = np.array([r["cycle"] for r in recs], float)
    caps = np.array([r["capacity_ah"] for r in recs], float)
    nominal = float(recs[0]["nominal_capacity_ah"]) or float(caps[0])
    fade_frac = np.clip(1.0 - caps / nominal, 0.0, 1.0)

    avg_t = np.array([r["avg_temp_c"] for r in recs], float)
    max_t = np.array([r["max_temp_c"] for r in recs], float)
    ir = np.array([r["internal_resistance_mohm"] for r in recs], float)
    v_mean = np.array([r["voltage_mean"] for r in recs], float)
    v_var = np.array([r["voltage_var"] for r in recs], float)
    cv = np.array([r["cv_phase_fraction"] for r in recs], float)
    eff_c = np.array([r["charge_efficiency"] for r in recs], float)
    eff_d = np.array([r["discharge_efficiency"] for r in recs], float)

    w = min(window, len(recs))
    cyc_w, fade_w = cycles[-w:], fade_frac[-w:]

    fade_rate = max(0.0, _slope(cyc_w, fade_w))                      # fraction/cycle
    # acceleration: difference of slope between recent half and earlier half of window
    half = max(2, w // 2)
    rate_recent = _slope(cycles[-half:], fade_frac[-half:])
    rate_early = _slope(cycles[-w:-half] if w > half else cycles[:half],
                        fade_frac[-w:-half] if w > half else fade_frac[:half])
    span = max(1.0, cycles[-1] - cycles[-w])
    fade_acceleration = float((rate_recent - rate_early) / span)

    ir_baseline = float(ir[0]) if ir[0] > 0 else float(np.median(ir))
    ir_growth_pct = float((ir[-1] - ir_baseline) / ir_baseline * 100.0) if ir_baseline else 0.0
    thermal_stress_hours = float(np.sum(max_t > 45.0) * HOURS_PER_CYCLE)

    feats = {
        "cycle_count": float(cycles[-1]),
        "capacity_fade_pct": float(fade_frac[-1] * 100.0),
        "fade_rate": float(fade_rate),
        "fade_acceleration": float(fade_acceleration),
        "avg_temp_c": float(np.mean(avg_t)),
        "max_temp_c": float(np.max(max_t)),
        "thermal_stress_hours": thermal_stress_hours,
        "internal_resistance_mohm": float(ir[-1]),
        "ir_growth_pct": ir_growth_pct,
        "cv_phase_fraction": float(np.mean(cv[-w:])),
        "voltage_slope": _slope(cyc_w, v_mean[-w:]),
        "voltage_variance": float(np.mean(v_var[-w:])),
        "charge_efficiency": float(np.mean(eff_c[-w:])),
        "discharge_efficiency": float(np.mean(eff_d[-w:])),
    }
    return feats


def soh_from_trajectory(records, cutoff_k):
    """Ground-truth SoH (%) at cutoff = 100 - capacity_fade_pct."""
    recs = sorted(records, key=lambda r: r["cycle"])
    recs = [r for r in recs if r["cycle"] <= cutoff_k]
    if not recs:
        return None
    nominal = float(recs[0]["nominal_capacity_ah"])
    cap = float(recs[-1]["capacity_ah"])
    return float(np.clip(100.0 * cap / nominal, 0.0, 100.0))


def features_dict_to_vector(feat):
    """Order a feature dict into the canonical 14-vector.

    Missing keys or None/NaN values become np.nan (HGB handles NaN natively).
    Returns (vector[14], missing_features list).
    """
    vec = np.full(C.N_FEATURES, np.nan, dtype=float)
    missing = []
    for i, key in enumerate(C.FEATURE_KEYS):
        val = feat.get(key, None) if isinstance(feat, dict) else None
        if val is None:
            missing.append(key)
            continue
        try:
            f = float(val)
        except (TypeError, ValueError):
            missing.append(key)
            continue
        if np.isnan(f) or np.isinf(f):
            missing.append(key)
            continue
        vec[i] = f
    return vec, missing


def normalize_vector(vec, envelope):
    """Min-max normalize a raw 14-vector to [0,1] using the training envelope.

    NaN entries stay NaN. Values outside the envelope are clipped to [0,1].
    envelope: {"min": [...14], "max": [...14]}.
    """
    vmin = np.asarray(envelope["min"], float)
    vmax = np.asarray(envelope["max"], float)
    rng = np.where((vmax - vmin) == 0, 1.0, (vmax - vmin))
    norm = (vec - vmin) / rng
    return np.clip(norm, 0.0, 1.0)


def build_model_input(feat, envelope):
    """Inference helper: dict -> (normalized_vector[1,14], missing_features)."""
    vec, missing = features_dict_to_vector(feat)
    norm = normalize_vector(vec, envelope)
    return norm.reshape(1, -1), missing
