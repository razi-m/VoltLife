"""
evaluate.py — model evaluation + threshold gate  (supports CALCE generalization)

  python evaluate.py --model models/model_v1.pkl
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import joblib
from sklearn.metrics import mean_absolute_error, r2_score

import shared_constants as C
from features import normalize_vector


def _cross_dataset_soh(bundle, calce_path):
    """Validate SoH generalization on the CALCE hold-out (if present)."""
    if not os.path.exists(calce_path):
        return None
    from labels import build_training_rows
    cells = json.load(open(calce_path))["cells"]
    X, y_soh, _, _, _ = build_training_rows(cells)
    env = bundle["ood_envelope"]
    Xn = np.vstack([normalize_vector(r, env) for r in X])
    pred = np.clip(bundle["soh_model"].predict(Xn), 0, 100)
    return {"n": int(len(X)),
            "soh_mae": round(float(mean_absolute_error(y_soh, pred)), 4),
            "soh_r2": round(float(r2_score(y_soh, pred)), 4)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="models/model_v1.pkl")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    mp = args.model if os.path.isabs(args.model) else os.path.join(here, args.model)
    bundle = joblib.load(mp)
    m = bundle["metrics"]

    print("=== VoltLife model_v1 evaluation ===")
    print("version:", bundle["version"], "| trained_on:", bundle["trained_on"],
          "| dataset:", m["dataset"], "| validation:", m["validation"])
    print("SoH : MAE={mae}  RMSE={rmse}  R2={r2}".format(**m["soh"]))
    print("RUL : MAE={mae}  coverage={coverage} (raw {coverage_raw}, margin {conformal_margin_cycles} cyc)".format(**m["rul"]))
    print("thresholds:", m["thresholds_passed"])

    calce = _cross_dataset_soh(bundle, os.path.join(here, "data", "parsed", "calce_cells.json"))
    if calce:
        print("CALCE generalization (SoH): MAE={soh_mae} R2={soh_r2} (n={n})".format(**calce))
    ok = all(m["thresholds_passed"].values())
    print("RESULT:", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
