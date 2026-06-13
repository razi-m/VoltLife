"""
generate_fleet.py — Demo Fleet Generation  (Phase 11)

Generate 847 batteries with a realistic grade distribution, run each through
the real ML predict() pipeline, and write complete assessment records so every
dashboard screen is populated (no empty charts/tables/placeholders).

Target distribution:  S~5% A~15% B~35% C~30% D~15%
Geo: distributed across India.  OEMs: Ola, Ather, Tata, TVS.

  python generate_fleet.py --count 847 --output data/fleet.json
"""
import os
import sys
import json
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import shared_constants as C
import predict as P

OEMS = [("Ola Electric", 0.30), ("Ather Energy", 0.25), ("Tata", 0.30), ("TVS", 0.15)]
MODELS = {"Ola Electric": ["S1 Pro Pack", "S1 Air Pack"], "Ather Energy": ["450X Pack", "Rizta Pack"],
          "Tata": ["Nexon EV Pack", "Tiago EV Pack"], "TVS": ["iQube Pack", "X Pack"]}
CITIES = [
    ("Pune", "Maharashtra", 18.52, 73.85), ("Chennai", "Tamil Nadu", 13.08, 80.27),
    ("Bengaluru", "Karnataka", 12.97, 77.59), ("Hyderabad", "Telangana", 17.39, 78.49),
    ("Delhi", "Delhi", 28.61, 77.21), ("Ahmedabad", "Gujarat", 23.02, 72.57),
    ("Jaipur", "Rajasthan", 26.91, 75.79), ("Kolkata", "West Bengal", 22.57, 88.36),
    ("Lucknow", "Uttar Pradesh", 26.85, 80.95), ("Bhopal", "Madhya Pradesh", 23.26, 77.41),
    ("Coimbatore", "Tamil Nadu", 11.02, 76.96), ("Nagpur", "Maharashtra", 21.15, 79.09),
    ("Surat", "Gujarat", 21.17, 72.83), ("Patna", "Bihar", 25.59, 85.14),
    ("Kochi", "Kerala", 9.93, 76.27),
]
TARGET = [("S", 0.05), ("A", 0.15), ("B", 0.35), ("C", 0.30), ("D", 0.15)]


def _base_features(rng, env):
    """Sample an in-distribution base vector near training means (keeps confidence high)."""
    mean = np.array(env["mean"]); std = np.array(env["std"])
    vmin = np.array(env["min"]); vmax = np.array(env["max"])
    vals = np.clip(mean + rng.normal(0, 0.25, size=len(mean)) * std, vmin, vmax)
    return {k: float(vals[i]) for i, k in enumerate(C.FEATURE_KEYS)}


def _profile(rng, env, grade):
    """Synthesize a feature dict whose ML assessment targets `grade`.

    Only the grade-DRIVING features are moved (capacity_fade -> SoH; cycle_count
    & fade_rate -> RUL; max_temp & ir_growth -> hard-safety D). Every other feature
    is left at its in-distribution base (near the envelope mean) so non-D batteries
    keep a low OOD z-score and can reach high confidence — Grade S in particular
    requires confidence == "high". Tight-std features (avg_temp, cv_phase_fraction,
    voltage_*, efficiencies) are NEVER overridden, which previously forced S->low.
    """
    f = _base_features(rng, env)
    if grade == "S":
        # SoH >= 90, long RUL (rul_years >= 4 needs a healthy, low-fade-rate pack),
        # low thermal stress, in-distribution everything else -> high confidence.
        # fade_rate is the dominant RUL driver; keep it in the flat high-RUL region
        # (<=5e-5 -> Q50 ~4.2 yr) so rul_years clears the Grade-S >=4.0 gate reliably.
        f.update(capacity_fade_pct=rng.uniform(1.5, 4.0), cycle_count=rng.uniform(120, 260),
                 fade_rate=rng.uniform(1.0e-5, 5.0e-5), fade_acceleration=rng.uniform(-1e-6, 2e-6),
                 ir_growth_pct=rng.uniform(0.0, 3.0), thermal_stress_hours=rng.uniform(0, 6))
    elif grade == "A":
        f.update(capacity_fade_pct=rng.uniform(10.5, 19.5), cycle_count=rng.uniform(300, 700),
                 fade_rate=rng.uniform(1.0e-4, 5.0e-4), ir_growth_pct=rng.uniform(1.0, 6.0),
                 thermal_stress_hours=rng.uniform(2, 24))
    elif grade == "B":
        f.update(capacity_fade_pct=rng.uniform(20.5, 29.5), cycle_count=rng.uniform(600, 1100),
                 fade_rate=rng.uniform(3.0e-4, 1.0e-3), ir_growth_pct=rng.uniform(2.0, 8.0),
                 thermal_stress_hours=rng.uniform(5, 45))
    elif grade == "C":
        f.update(capacity_fade_pct=rng.uniform(30.5, 39.5), cycle_count=rng.uniform(900, 1500),
                 fade_rate=rng.uniform(6.0e-4, 1.5e-3), ir_growth_pct=rng.uniform(3.0, 9.0),
                 thermal_stress_hours=rng.uniform(10, 70))
    else:  # D — half by SoH<60, half by hard safety trigger (safety fires regardless of OOD)
        if rng.random() < 0.5:
            f.update(capacity_fade_pct=rng.uniform(42, 52), cycle_count=rng.uniform(1100, 1900),
                     fade_rate=rng.uniform(1.0e-3, 2.5e-3), ir_growth_pct=rng.uniform(4.0, 9.0))
        else:
            f.update(capacity_fade_pct=rng.uniform(16, 36), cycle_count=rng.uniform(600, 1200))
            if rng.random() < 0.5:
                f["max_temp_c"] = rng.uniform(56, 63)          # overheating trigger
            else:
                f["ir_growth_pct"] = rng.uniform(62, 95)        # IR-growth trigger
    return f


def _pick(rng, weighted):
    r, c = rng.random(), 0.0
    for name, w in weighted:
        c += w
        if r <= c:
            return name
    return weighted[-1][0]


def generate(count=847, seed=C.RANDOM_SEED):
    rng = np.random.default_rng(seed)
    bundle = P.load_bundle()
    env = bundle["ood_envelope"]

    # build target grade list
    grades = []
    for g, frac in TARGET:
        grades += [g] * round(frac * count)
    while len(grades) < count:
        grades.append("B")
    grades = grades[:count]
    rng.shuffle(grades)

    fleet = []
    actual = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0}
    for i, tgt in enumerate(grades):
        feats = _profile(rng, env, tgt)
        oem = _pick(rng, OEMS)
        city, state, lat, lng = CITIES[rng.integers(len(CITIES))]
        cap = float(round(rng.uniform(2.5, 6.0) if oem in ("Ola Electric", "Ather Energy", "TVS")
                          else rng.uniform(26.0, 50.0), 1))
        meta = {
            "external_ref": f"BAT-{i+1:04d}",
            "oem": oem,
            "model": MODELS[oem][rng.integers(len(MODELS[oem]))],
            "chemistry": "LFP" if rng.random() < 0.45 else "NMC",
            "rated_capacity_kwh": cap,
            "source_city": city, "source_state": state, "lat": lat + float(rng.normal(0, 0.05)),
            "lng": lng + float(rng.normal(0, 0.05)),
            "manufacture_date": (datetime.date(2021, 1, 1) +
                                 datetime.timedelta(days=int(rng.integers(0, 1400)))).isoformat(),
        }
        assessment = P.predict({**feats, "rated_capacity_kwh": cap}, battery_meta=meta)
        actual[assessment["grade"]] += 1
        fleet.append({**meta, "features": {k: round(feats[k], 5) for k in C.FEATURE_KEYS},
                      "assessment": assessment})

    return fleet, actual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=847)
    ap.add_argument("--output", default="data/fleet.json")
    args = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    out = args.output if os.path.isabs(args.output) else os.path.join(here, args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    fleet, actual = generate(args.count)
    with open(out, "w") as f:
        json.dump({"count": len(fleet), "generated_on": datetime.date.today().isoformat(),
                   "grade_distribution": actual, "batteries": fleet}, f)
    total = len(fleet)
    dist = {g: f"{actual[g]} ({actual[g]/total*100:.0f}%)" for g in ["S", "A", "B", "C", "D"]}
    print(f"[fleet] wrote {total} batteries -> {out}")
    print(f"[fleet] grade distribution: {dist}")
    return out


if __name__ == "__main__":
    main()
