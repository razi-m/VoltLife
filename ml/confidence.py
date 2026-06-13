"""
confidence.py — Confidence Engine  (Phase 6)

Outputs one of: "high" | "medium" | "low".

Signals (master plan §CONFIDENCE ENGINE):
  - missing feature count
  - quantile spread (Q90 - Q10) of RUL
  - OOD detection via per-feature z-score against the training envelope
  - feature-envelope checks (folded into the z-score / clip)

Enforcement (applied by grade/recommend, not here):
  - low confidence batteries cannot auto-deploy and must route to inspection
  - low confidence output is NEVER suppressed
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C


def max_ood_z(raw_vec, envelope):
    """Largest absolute per-feature z-score vs the training mean/std (NaN ignored)."""
    mean = np.asarray(envelope.get("mean"), float)
    std = np.asarray(envelope.get("std"), float)
    if mean is None or std is None:
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        z = np.abs((raw_vec - mean) / std)
    z = z[~np.isnan(z)]
    return float(np.max(z)) if z.size else 0.0


def assess_confidence(raw_vec, missing_features, rul_low_cycles, rul_high_cycles, envelope):
    """Return 'high' | 'medium' | 'low' plus a signal dict (for transparency)."""
    n_missing = len(missing_features)
    spread = float(max(0.0, rul_high_cycles - rul_low_cycles))
    z = max_ood_z(np.asarray(raw_vec, float), envelope)

    level = "high"

    # Missing-feature rule
    if n_missing >= C.CONF_MISSING_LOW:
        level = "low"
    elif n_missing >= C.CONF_MISSING_MEDIUM:
        level = "medium"

    # OOD z-score rule
    if z > C.CONF_OOD_Z_LOW:
        level = "low"
    elif z >= C.CONF_OOD_Z_MEDIUM and level != "low":
        level = "medium"

    # Quantile-spread rule
    if spread > C.CONF_SPREAD_LOW_CYCLES:
        level = "low"
    elif spread > C.CONF_SPREAD_MEDIUM_CYCLES and level != "low":
        level = "medium"

    signals = {
        "missing_features": n_missing,
        "max_ood_z": round(z, 3),
        "rul_spread_cycles": round(spread, 1),
    }
    return level, signals
