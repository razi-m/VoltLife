"""
parse_nasa.py — NASA PCoE battery dataset parser  (Phase 1)

Three modes, auto-selected:
  1. CSV   : if a measurement-level discharge.csv is given (--csv / found at the
             known dataset path), aggregate per-(Battery, id_cycle) measurement
             rows into per-cell cycle trajectories. This is the REAL NASA PCoE
             aging data exported to CSV (B0005/B0006/B0007/B0018).
  2. MAT   : if .mat files exist in --input, parse the NASA PCoE struct
             (B0005.mat style) into per-cell cycle trajectories.
  3. SYNTH : if no raw files are present, generate a physics-motivated
             synthetic dataset matching the parsed schema EXACTLY, so train.py
             runs immediately (master plan §Synthetic Fallback).

Parsed schema (data/parsed/cells.json):
  { cell_id: [ {cycle, capacity_ah, nominal_capacity_ah, avg_temp_c, max_temp_c,
               internal_resistance_mohm, voltage_mean, voltage_var,
               cv_phase_fraction, charge_efficiency, discharge_efficiency}, ... ] }

The 14 canonical features in shared_constants.FEATURE_KEYS are *derived* from
these per-cycle trajectories by features.compute_features_from_trajectory; this
module produces the clean per-cycle table they are derived from.

Usage:
  python parse_nasa.py --csv "<path>/discharge.csv" --output data/parsed/
  python parse_nasa.py --input data/raw/nasa --output data/parsed/   # .mat
  python parse_nasa.py --synthetic --n-cells 34 --output data/parsed/
"""
import os
import sys
import json
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C

NOMINAL_CAPACITY_AH = 2.0   # NASA 18650 cells are ~2 Ah rated (datasheet nominal)

# Known location of the measurement-level NASA discharge export on this machine.
DEFAULT_CSV = r"C:\Users\Razi\Documents\Batt Dataset\battery_aging-master\battery_aging-master\discharge.csv"


# ---------------------------------------------------------------------------
# Real NASA discharge.csv parser (measurement rows -> per-cycle trajectory)
# ---------------------------------------------------------------------------
def parse_real_nasa_csv(csv_path):
    """Aggregate NASA discharge.csv (one row per in-cycle sample) into the
    per-cell parsed schema.

    Columns (NASA PCoE discharge export):
      Voltage_measured, Current_measured, Temperature_measured,
      Current_charge, Voltage_charge, Time, Capacity, id_cycle, type,
      ambient_temperature, time, Battery

    Aggregation key: (Battery, id_cycle). One discharge cycle -> one record.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    df = df[df["type"] == "discharge"].copy()
    cells = {}

    for bid, bdf in df.groupby("Battery"):
        # order cycles by their MATLAB start-time, then re-index 1..N so the
        # trajectory is monotonic regardless of the raw id_cycle numbering.
        cyc_order = (bdf.groupby("id_cycle")["time"].first()
                     .sort_values().index.tolist())
        records = []
        for k, cyc_id in enumerate(cyc_order, start=1):
            g = bdf[bdf["id_cycle"] == cyc_id]
            cap = float(g["Capacity"].iloc[0])           # constant within a cycle
            temp = g["Temperature_measured"].to_numpy(float)
            volt = g["Voltage_measured"].to_numpy(float)
            cur = np.abs(g["Current_measured"].to_numpy(float))
            vload = g["Voltage_charge"].to_numpy(float)

            # Internal-resistance proxy: overpotential between terminal and load
            # sense point divided by load current. Absolute level is an engineered
            # proxy (no impedance sweep in the discharge file); it grows monotonically
            # with aging, which is what ir_growth_pct needs.
            sel = cur > 0.5
            if sel.any():
                ir_mohm = float(np.median(np.abs(volt[sel] - vload[sel]) / cur[sel]) * 1000.0)
            else:
                ir_mohm = 30.0

            vmax = float(np.max(volt)) if volt.size else 0.0
            cv_frac = float(np.mean(volt > (vmax - 0.05))) if volt.size else 0.0

            records.append({
                "cycle": k,
                "capacity_ah": round(cap, 5),
                "nominal_capacity_ah": NOMINAL_CAPACITY_AH,
                "avg_temp_c": round(float(np.mean(temp)), 3),
                "max_temp_c": round(float(np.max(temp)), 3),
                "internal_resistance_mohm": round(ir_mohm, 3),
                "voltage_mean": round(float(np.mean(volt)), 5),
                "voltage_var": round(float(np.var(volt)), 6),
                "cv_phase_fraction": round(cv_frac, 4),
                # charge-side telemetry is not present in the discharge export;
                # use stable datasheet-typical defaults (near-constant features).
                "charge_efficiency": 0.98,
                "discharge_efficiency": 0.97,
            })
        if records:
            cells[str(bid)] = records
    return cells


# ---------------------------------------------------------------------------
# Synthetic generator (NASA-schema compatible)
# ---------------------------------------------------------------------------
def generate_synthetic_cells(n_cells=34, seed=C.RANDOM_SEED):
    """Generate n_cells degradation trajectories matching the parsed schema.

    Per-cycle feature SCALES are calibrated to the real NASA discharge.csv cells
    (IR ~440-490 mOhm with weak growth, voltage_mean ~3.5, voltage_var ~0.04-0.08,
    cv_phase_fraction ~0.008-0.025, avg_temp ~30-34, max_temp ~36-42) so a
    real + synthetic blend is coherent (no bimodal features / broken OOD envelope).

    Unlike the 4 accelerated-aged real cells (EOL in ~100 cycles), synthetic
    lifetimes span EOL in 250-2300 cycles. fade_rate then cleanly separates
    short-RUL (real) from long-RUL (synthetic) cells, which is what makes RUL
    learnable under LOCO and restores high-confidence / Grade-S coverage.
    """
    rng = np.random.default_rng(seed)
    cells = {}
    fade_eol = 1.0 - C.SOH_EOL_PCT / 100.0             # capacity loss at end-of-life
    for i in range(n_cells):
        cid = f"SYN{i+1:03d}"
        # Lifetime mix: a third long-life (healthy, supports Grade S/A), a third
        # mid, a third shorter — EOL anywhere in 250..2300 cycles.
        bucket = i % 3
        if bucket == 0:
            l_eol = int(rng.integers(1500, 2300))      # long-life / healthy
        elif bucket == 1:
            l_eol = int(rng.integers(700, 1500))       # mid-life
        else:
            l_eol = int(rng.integers(250, 700))        # shorter-life
        p = rng.uniform(1.3, 2.2)                       # convexity / knee sharpness
        life = min(2400, int(l_eol * rng.uniform(1.02, 1.4)))
        # per-cell regime — scales matched to the real NASA cells
        amb = rng.uniform(29.5, 34.0)                  # ambient avg temp (real: 30-34)
        temp_spread = rng.uniform(6.5, 9.5)            # max-avg gap (real: ~7.5)
        ir0 = rng.uniform(442.0, 478.0)                # baseline IR mOhm (real: 444-487)
        ir_gain = rng.uniform(0.05, 0.22)              # weak IR growth (real proxy: 1-6%)
        v_nom = rng.uniform(3.50, 3.58)               # nominal terminal voltage (real ~3.5)
        eff_c0 = rng.uniform(0.975, 0.99)
        eff_d0 = rng.uniform(0.965, 0.985)
        cv0 = rng.uniform(0.009, 0.020)               # real cv_phase_fraction range

        records = []
        for k in range(1, life + 1):
            fade_frac = fade_eol * (k / l_eol) ** p     # = fade_eol exactly at k=l_eol
            fade_frac = min(fade_frac, 0.55)            # cap at 55% loss
            cap = NOMINAL_CAPACITY_AH * (1.0 - fade_frac)
            cap += rng.normal(0, 0.004)                # measurement noise
            avg_t = amb + rng.normal(0, 0.9)
            max_t = avg_t + temp_spread + rng.normal(0, 1.0)
            ir = ir0 * (1.0 + ir_gain * fade_frac) + rng.normal(0, 1.5)
            v_mean = v_nom - 0.16 * fade_frac + rng.normal(0, 0.006)
            v_var = 0.045 + 0.05 * fade_frac + abs(rng.normal(0, 0.003))
            cv_frac = min(0.05, max(0.005, cv0 + 0.01 * fade_frac + rng.normal(0, 0.002)))
            eff_c = max(0.90, eff_c0 - 0.05 * fade_frac + rng.normal(0, 0.003))
            eff_d = max(0.88, eff_d0 - 0.06 * fade_frac + rng.normal(0, 0.003))
            records.append({
                "cycle": k,
                "capacity_ah": round(float(cap), 5),
                "nominal_capacity_ah": NOMINAL_CAPACITY_AH,
                "avg_temp_c": round(float(avg_t), 3),
                "max_temp_c": round(float(max_t), 3),
                "internal_resistance_mohm": round(float(ir), 3),
                "voltage_mean": round(float(v_mean), 5),
                "voltage_var": round(float(v_var), 6),
                "cv_phase_fraction": round(float(cv_frac), 4),
                "charge_efficiency": round(float(eff_c), 4),
                "discharge_efficiency": round(float(eff_d), 4),
            })
        cells[cid] = records
    return cells


# ---------------------------------------------------------------------------
# Real NASA PCoE .mat parser (best-effort; runs when .mat files are present)
# ---------------------------------------------------------------------------
def parse_real_nasa(input_dir):
    """Parse NASA PCoE .mat files (B0005.mat style) into the parsed schema."""
    from scipy.io import loadmat
    cells = {}
    mats = sorted(glob.glob(os.path.join(input_dir, "*.mat")))
    for path in mats:
        cid = os.path.splitext(os.path.basename(path))[0]
        mat = loadmat(path, simplify_cells=True)
        # NASA struct: mat[cid]['cycle'] -> list of cycle dicts with 'type','data'
        root = mat.get(cid) or next((v for k, v in mat.items() if not k.startswith("__")), None)
        if root is None or "cycle" not in root:
            continue
        cyc_list = root["cycle"]
        cyc_list = cyc_list if isinstance(cyc_list, list) else [cyc_list]
        records, k = [], 0
        baseline_cap = None
        for cyc in cyc_list:
            if cyc.get("type") != "discharge":
                continue
            data = cyc.get("data", {})
            cap = data.get("Capacity")
            cap = float(np.ravel(cap)[0]) if cap is not None and np.size(cap) else None
            if cap is None:
                continue
            k += 1
            if baseline_cap is None:
                baseline_cap = cap
            temp = np.ravel(data.get("Temperature_measured", [cyc.get("ambient_temperature", 24)]))
            volt = np.ravel(data.get("Voltage_measured", [3.7]))
            records.append({
                "cycle": k,
                "capacity_ah": round(cap, 5),
                "nominal_capacity_ah": round(baseline_cap, 5),
                "avg_temp_c": round(float(np.mean(temp)), 3),
                "max_temp_c": round(float(np.max(temp)), 3),
                # IR not directly in discharge curve; approximate from impedance cycles if absent
                "internal_resistance_mohm": round(float(cyc.get("Re", 0.0)) * 1000.0 or 30.0, 3),
                "voltage_mean": round(float(np.mean(volt)), 5),
                "voltage_var": round(float(np.var(volt)), 6),
                "cv_phase_fraction": round(float(np.mean(volt > (np.max(volt) - 0.05))), 4),
                "charge_efficiency": 0.98,
                "discharge_efficiency": 0.97,
            })
        if records:
            cells[cid] = records
    return cells


def build_feature_frame(cells):
    """Derive the canonical 14-feature table (one row per cell at full life).

    Returns a pandas DataFrame with exactly the C.FEATURE_KEYS columns (+ cell_id),
    demonstrating the column -> 14-feature mapping. The full per-cutoff training
    matrix is built by labels.build_training_rows.
    """
    import pandas as pd
    from features import compute_features_from_trajectory
    rows = []
    for cid, recs in cells.items():
        feats = compute_features_from_trajectory(recs, cutoff_k=None)
        if feats is None:
            continue
        rows.append({"cell_id": cid, **{k: feats[k] for k in C.FEATURE_KEYS}})
    return pd.DataFrame(rows, columns=["cell_id", *C.FEATURE_KEYS])


def main():
    ap = argparse.ArgumentParser(description="Parse NASA battery dataset (CSV / .mat / synthetic).")
    ap.add_argument("--csv", default=None, help="measurement-level discharge.csv path")
    ap.add_argument("--input", default="data/raw/nasa")
    ap.add_argument("--output", default="data/parsed/")
    ap.add_argument("--synthetic", action="store_true", help="force synthetic generation")
    ap.add_argument("--augment", type=int, default=0,
                    help="append N scale-matched synthetic cells to the real parsed cells "
                         "(real+synthetic blend; restores full lifetime/grade range)")
    ap.add_argument("--n-cells", type=int, default=34)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    in_dir = args.input if os.path.isabs(args.input) else os.path.join(here, args.input)
    out_dir = args.output if os.path.isabs(args.output) else os.path.join(here, args.output)
    os.makedirs(out_dir, exist_ok=True)

    csv_path = args.csv or (DEFAULT_CSV if os.path.exists(DEFAULT_CSV) else None)
    has_raw = os.path.isdir(in_dir) and glob.glob(os.path.join(in_dir, "*.mat"))

    if args.synthetic:
        print(f"[parse_nasa] SYNTHETIC mode (forced); generating {args.n_cells} cells.")
        cells = generate_synthetic_cells(args.n_cells)
        source = "NASA-synthetic"
    elif csv_path and os.path.exists(csv_path):
        print(f"[parse_nasa] CSV mode; parsing {csv_path}.")
        cells = parse_real_nasa_csv(csv_path)
        source = "NASA-PCoE-discharge.csv"
    elif has_raw:
        print(f"[parse_nasa] MAT mode; parsing .mat files in {in_dir}.")
        cells = parse_real_nasa(in_dir)
        source = "NASA"
    else:
        print(f"[parse_nasa] SYNTHETIC mode (no CSV/.mat found); generating {args.n_cells} cells.")
        cells = generate_synthetic_cells(args.n_cells)
        source = "NASA-synthetic"

    # Optional real+synthetic blend (user-approved augmentation). Synthetic cells
    # are scale-matched to the real cells but span full lifetimes, so the model
    # sees the fresh->dead range the 4 accelerated-aged real cells cannot cover.
    if args.augment > 0 and not args.synthetic:
        syn = generate_synthetic_cells(args.augment)
        cells = {**cells, **syn}
        source = f"{source}+synthetic({args.augment})"
        print(f"[parse_nasa] blended {args.augment} scale-matched synthetic cells "
              f"-> {len(cells)} cells total.")

    out_path = os.path.join(out_dir, "cells.json")
    with open(out_path, "w") as f:
        json.dump({"source": source, "cells": cells}, f)
    n_rows = sum(len(v) for v in cells.values())
    print(f"[parse_nasa] source={source}: wrote {len(cells)} cells / {n_rows} cycle-records -> {out_path}")

    # STEP 1 deliverable: clean parsed DataFrame with exactly the 14 canonical features.
    frame = build_feature_frame(cells)
    feat_only = frame[C.FEATURE_KEYS]
    print(f"[parse_nasa] 14-feature frame shape (per-cell, full-life): {feat_only.shape}")
    print(f"[parse_nasa] feature columns ({len(C.FEATURE_KEYS)}): {list(C.FEATURE_KEYS)}")
    try:
        import pandas as pd
        with pd.option_context("display.width", 200, "display.max_columns", 20):
            print(frame.head(3).to_string(index=False))
    except Exception:
        print(frame.head(3))
    return out_path


if __name__ == "__main__":
    main()
