"""
labels.py — training-row & label generation  (Phase 3)

For each cell, sample lifecycle cutoffs K. At each cutoff:
    X = features computed from cycles [0..K]   (features.compute_features_from_trajectory)
    y_soh  = SoH(%) at K
    y_rul  = remaining cycles from K until end-of-life (SoH <= SOH_EOL_PCT),
             clamped to [0, RUL_CYCLES_MAX]

This yields a (features at K -> labels at K) supervised dataset with NO leakage:
each row only sees history up to its own cutoff, and LOCO (in train.py) keeps
whole cells out of training. Cells that never reach EOL get a right-censored RUL
clamped at RUL_CYCLES_MAX (healthy-cell upper bound).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C
from features import compute_features_from_trajectory, soh_from_trajectory


def _eol_cycle(records):
    """First cycle where SoH drops to/below SOH_EOL_PCT; None if never reached."""
    recs = sorted(records, key=lambda r: r["cycle"])
    nominal = float(recs[0]["nominal_capacity_ah"])
    for r in recs:
        soh = 100.0 * float(r["capacity_ah"]) / nominal
        if soh <= C.SOH_EOL_PCT:
            return int(r["cycle"])
    return None


def build_training_rows(cells, n_cutoffs=20, min_cycle=30, seed=C.RANDOM_SEED):
    """Build LOCO-ready rows from a {cell_id: records} dict.

    Returns: X (n,14), y_soh (n,), y_rul (n,), groups (n,) cell ids, feature_keys.
    """
    rng = np.random.default_rng(seed)
    X, y_soh, y_rul, groups = [], [], [], []

    for cid, records in cells.items():
        recs = sorted(records, key=lambda r: r["cycle"])
        last_cycle = recs[-1]["cycle"]
        if last_cycle < min_cycle:
            continue
        eol = _eol_cycle(recs)

        # cutoffs spread across observed life (deterministic + jitter)
        cuts = np.unique(np.linspace(min_cycle, last_cycle, n_cutoffs).astype(int))
        for k in cuts:
            feats = compute_features_from_trajectory(recs, cutoff_k=int(k))
            if feats is None:
                continue
            soh = soh_from_trajectory(recs, int(k))
            if soh is None:
                continue
            if eol is None:
                # right-censored healthy cell: remaining life >= observed tail, cap high
                rul = C.RUL_CYCLES_MAX
            else:
                rul = max(0, eol - int(k))
            rul = int(min(C.RUL_CYCLES_MAX, max(C.RUL_CYCLES_MIN, rul)))

            X.append([feats[key] for key in C.FEATURE_KEYS])
            y_soh.append(float(soh))
            y_rul.append(float(rul))
            groups.append(cid)

    X = np.asarray(X, float)
    y_soh = np.asarray(y_soh, float)
    y_rul = np.asarray(y_rul, float)
    groups = np.asarray(groups)
    return X, y_soh, y_rul, groups, list(C.FEATURE_KEYS)
