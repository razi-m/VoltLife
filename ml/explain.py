"""
explain.py — Explainability Engine (SHAP)  (Phase 9)

SHAP is the source of truth (NOT Volt AI, NO LLMs). Deterministic.

Produces, for a single prediction:
  - explanation : list[dict] {feature, value, impact ('+'/'-'), shap, label}
                  (backend contract app/schemas/ml.py; `value` keeps the numeric
                   feature value for the backend, but `label`/reasons are word-only)
  - reasons     : [label for top-3 by |shap|]   (exactly 3, NO numeric values — FIX 2)
  - top_factors / positive_signals / negative_signals (master plan contract)

Background dataset is stored in model_v1.pkl (small, 50-100 rows per risk register).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shap
import shared_constants as C

# Human-readable, NUMBER-FREE label templates keyed by feature. (good_label, bad_label)
_LABELS = {
    "capacity_fade_pct": ("Low capacity fade detected — aging within normal range",
                          "High capacity fade detected — significant ageing"),
    "fade_rate": ("Slow capacity fade rate — gentle degradation",
                  "Rapid capacity fade rate — accelerating degradation"),
    "fade_acceleration": ("Fade not accelerating — stable trajectory",
                          "Capacity fade is accelerating — knee detected"),
    "avg_temp_c": ("Low thermal stress — cool operating temperature",
                   "High operating temperature — elevated thermal load"),
    "max_temp_c": ("Peak temperature within safe limits",
                   "Elevated peak temperature recorded"),
    "thermal_stress_hours": ("Minimal time above heat threshold — low heat stress",
                             "Extended time above heat threshold — thermal stress recorded"),
    "internal_resistance_mohm": ("Healthy internal resistance",
                                 "Elevated internal resistance"),
    "ir_growth_pct": ("Low internal-resistance growth — stable impedance",
                      "Internal resistance rising from baseline"),
    "cv_phase_fraction": ("Short constant-voltage charge phase — good charge acceptance",
                          "Long constant-voltage charge phase — reduced charge acceptance"),
    "voltage_slope": ("Stable voltage trend under load",
                      "Drifting voltage trend over cycles"),
    "voltage_variance": ("Low voltage variance — consistent behaviour",
                         "High voltage variance — unstable behaviour"),
    "charge_efficiency": ("High charge efficiency — strong energy retention",
                          "Reduced charge efficiency"),
    "discharge_efficiency": ("High discharge efficiency — strong charge retention",
                             "Reduced discharge efficiency"),
    "cycle_count": ("Moderate cycle count — life headroom remaining",
                    "High cycle count — approaching end of life"),
}


def _label(feature, positive):
    good, bad = _LABELS.get(feature,
                            ("Favourable signal within expected range",
                             "Unfavourable signal outside expected range"))
    return good if positive else bad


_EXPLAINER_CACHE = {}


def _get_explainer(soh_model, background):
    key = id(soh_model)
    if key in _EXPLAINER_CACHE:
        return _EXPLAINER_CACHE[key]
    try:
        expl = shap.TreeExplainer(soh_model, background)
        _ = expl.shap_values(background[:1])  # probe support for HGB
        mode = "tree"
    except Exception:
        expl = shap.Explainer(soh_model.predict, background, seed=C.RANDOM_SEED)
        mode = "fn"
    _EXPLAINER_CACHE[key] = (expl, mode)
    return expl, mode


def explain(bundle, norm_vec, raw_feat, missing_features=None):
    """Return dict with explanation/reasons/top_factors/positive/negative signals."""
    missing_features = set(missing_features or [])
    soh_model = bundle["soh_model"]
    background = np.asarray(bundle["shap_background"], float)
    norm_vec = np.asarray(norm_vec, float).reshape(1, -1)

    expl, mode = _get_explainer(soh_model, background)
    try:
        if mode == "tree":
            sv = np.asarray(expl.shap_values(norm_vec)).reshape(-1)
        else:
            sv = np.asarray(expl(norm_vec, max_evals=2 * C.N_FEATURES + 1).values).reshape(-1)
    except Exception:
        sv = np.zeros(C.N_FEATURES)

    entries = []
    for i, key in enumerate(C.FEATURE_KEYS):
        if key in missing_features:
            continue
        shap_v = float(sv[i]) if i < len(sv) else 0.0
        raw_val = raw_feat.get(key) if isinstance(raw_feat, dict) else None
        positive = shap_v >= 0
        entries.append({
            "feature": key,
            "value": float(raw_val) if raw_val is not None else None,
            "impact": "+" if positive else "-",
            "shap": round(shap_v, 4),
            "label": _label(key, positive),  # NUMBER-FREE
        })

    entries.sort(key=lambda e: abs(e["shap"]), reverse=True)
    explanation = entries[:6] if len(entries) >= 6 else entries
    if not explanation:  # all missing — never return empty
        explanation = [{"feature": "insufficient_data", "value": None, "impact": "-",
                        "shap": 0.0, "label": "Insufficient telemetry for explanation"}]

    top = explanation[:3]
    reasons = [e["label"] for e in top]
    while len(reasons) < 3:
        reasons.append("Stable behaviour within expected range")
    positive_signals = [e["label"] for e in explanation if e["impact"] == "+"][:3]
    negative_signals = [e["label"] for e in explanation if e["impact"] == "-"][:3]

    return {
        "explanation": explanation,
        "reasons": reasons[:3],
        "top_factors": [e["feature"] for e in top],
        "positive_signals": positive_signals,
        "negative_signals": negative_signals,
    }
