"""
parse_calce.py — CALCE battery dataset parser  (secondary / generalization)

CALCE is used for VALIDATION and generalization testing only. Same parsed
schema as parse_nasa.py. If no raw CALCE files are present, generate a
synthetic CALCE-style hold-out set (prismatic cells, slightly different
thermal + IR regime) so evaluate.py can run a cross-dataset check.

Usage:
  python parse_calce.py --input data/raw/calce --output data/parsed/
"""
import os
import sys
import json
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C

NOMINAL_CAPACITY_AH = 1.35   # CALCE CS2 prismatic cells ~1.35 Ah


def generate_synthetic_calce(n_cells=8, seed=C.RANDOM_SEED + 99):
    """Synthetic CALCE-style cells: different chemistry/thermal regime than NASA."""
    rng = np.random.default_rng(seed)
    cells = {}
    fade_eol = 1.0 - C.SOH_EOL_PCT / 100.0
    for i in range(n_cells):
        cid = f"CALCE_CS2_{i+1:02d}"
        l_eol = int(rng.integers(400, 1000))
        p = rng.uniform(1.4, 2.3)
        life = min(1300, int(l_eol * rng.uniform(1.02, 1.4)))
        amb = rng.uniform(22.0, 35.0)                  # cooler bench regime
        temp_spread = rng.uniform(4.0, 11.0)
        ir0 = rng.uniform(18.0, 38.0)
        ir_gain = rng.uniform(1.0, 2.4)
        v_nom = rng.uniform(3.5, 3.7)
        cv0 = rng.uniform(0.18, 0.32)
        records = []
        for k in range(1, life + 1):
            fade = min(0.55, fade_eol * (k / l_eol) ** p)
            cap = NOMINAL_CAPACITY_AH * (1.0 - fade) + rng.normal(0, 0.003)
            avg_t = amb + rng.normal(0, 1.0)
            max_t = avg_t + temp_spread + rng.normal(0, 1.2)
            ir = ir0 * (1.0 + ir_gain * fade) + rng.normal(0, 0.35)
            records.append({
                "cycle": k,
                "capacity_ah": round(float(cap), 5),
                "nominal_capacity_ah": NOMINAL_CAPACITY_AH,
                "avg_temp_c": round(float(avg_t), 3),
                "max_temp_c": round(float(max_t), 3),
                "internal_resistance_mohm": round(float(ir), 3),
                "voltage_mean": round(float(v_nom - 0.17 * fade + rng.normal(0, 0.004)), 5),
                "voltage_var": round(float(0.0007 + 0.018 * fade + abs(rng.normal(0, 0.0004))), 6),
                "cv_phase_fraction": round(float(min(0.6, cv0 + 0.33 * fade + rng.normal(0, 0.01))), 4),
                "charge_efficiency": round(float(max(0.80, 0.99 - 0.10 * fade + rng.normal(0, 0.003))), 4),
                "discharge_efficiency": round(float(max(0.78, 0.98 - 0.12 * fade + rng.normal(0, 0.003))), 4),
            })
        cells[cid] = records
    return cells


def parse_real_calce(input_dir):
    """Best-effort CALCE parser (CS2/CX2 Excel/CSV cycle summaries)."""
    import pandas as pd
    cells = {}
    files = sorted(glob.glob(os.path.join(input_dir, "*.csv")) +
                   glob.glob(os.path.join(input_dir, "*.xlsx")))
    for path in files:
        cid = os.path.splitext(os.path.basename(path))[0]
        df = pd.read_csv(path) if path.endswith(".csv") else pd.read_excel(path)
        cols = {c.lower(): c for c in df.columns}
        cap_col = next((cols[c] for c in cols if "capacity" in c), None)
        if cap_col is None:
            continue
        caps = df[cap_col].astype(float).to_numpy()
        base = caps[0]
        records = []
        for k, cap in enumerate(caps, start=1):
            fade = max(0.0, 1.0 - cap / base) if base else 0.0
            records.append({
                "cycle": k, "capacity_ah": round(float(cap), 5),
                "nominal_capacity_ah": round(float(base), 5),
                "avg_temp_c": 25.0, "max_temp_c": 30.0,
                "internal_resistance_mohm": round(25.0 * (1 + 1.5 * fade), 3),
                "voltage_mean": round(3.6 - 0.17 * fade, 5), "voltage_var": 0.001,
                "cv_phase_fraction": round(0.2 + 0.3 * fade, 4),
                "charge_efficiency": 0.98, "discharge_efficiency": 0.97,
            })
        cells[cid] = records
    return cells


def main():
    ap = argparse.ArgumentParser(description="Parse CALCE dataset (real or synthetic).")
    ap.add_argument("--input", default="data/raw/calce")
    ap.add_argument("--output", default="data/parsed/")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--n-cells", type=int, default=8)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    in_dir = args.input if os.path.isabs(args.input) else os.path.join(here, args.input)
    out_dir = args.output if os.path.isabs(args.output) else os.path.join(here, args.output)
    os.makedirs(out_dir, exist_ok=True)

    has_raw = os.path.isdir(in_dir) and (glob.glob(os.path.join(in_dir, "*.csv")) +
                                         glob.glob(os.path.join(in_dir, "*.xlsx")))
    if args.synthetic or not has_raw:
        print(f"[parse_calce] SYNTHETIC mode; generating {args.n_cells} CALCE cells.")
        cells = generate_synthetic_calce(args.n_cells)
        source = "CALCE-synthetic"
    else:
        print(f"[parse_calce] REAL mode; parsing {in_dir}.")
        cells = parse_real_calce(in_dir)
        source = "CALCE"

    out_path = os.path.join(out_dir, "calce_cells.json")
    with open(out_path, "w") as f:
        json.dump({"source": source, "cells": cells}, f)
    print(f"[parse_calce] wrote {len(cells)} cells -> {out_path}")
    return out_path


if __name__ == "__main__":
    main()
