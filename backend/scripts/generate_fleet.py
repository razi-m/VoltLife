"""
Deterministic synthetic fleet generator (Excellence Pass T2).
Emits app/seed/sample_fleet.csv: 847 valid batteries hitting the target grade mix
(S ~5% / A ~15% / B ~35% / C ~30% / D ~15%) + 3 deliberately invalid rows for the
reject-report demo beat (doc 04 example: accepted 847, rejected 3).
Grades are controlled by construction against the stub/grading policy thresholds
in shared/constants.py. Run: python scripts/generate_fleet.py
"""
import csv, random, os
random.seed(847)

CITIES = [  # (city, state, lat, lng, weight)
    ("Pune", "Maharashtra", 18.5204, 73.8567, 16), ("Mumbai", "Maharashtra", 19.0760, 72.8777, 12),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946, 16), ("Hyderabad", "Telangana", 17.3850, 78.4867, 14),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707, 10), ("New Delhi", "Delhi", 28.6139, 77.2090, 10),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873, 5), ("Ahmedabad", "Gujarat", 23.0225, 72.5714, 6),
    ("Kochi", "Kerala", 9.9312, 76.2673, 3), ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462, 4),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882, 2), ("Indore", "Madhya Pradesh", 22.7196, 75.8577, 2),
]
CITY_W = [c[4] for c in CITIES]

def pick_pack():
    r = random.random()
    if r < 0.80:  # 2W
        return ("2W", round(random.uniform(3.0, 4.4), 1), random.choice([48.0, 52.0, 60.0]))
    if r < 0.95:  # 3W
        return ("3W", round(random.uniform(5.0, 8.0), 1), random.choice([48.0, 60.0]))
    return ("4W", round(random.uniform(25.0, 40.0), 1), 96.0)

def pick_chem():
    r = random.random()
    return "NMC" if r < 0.60 else ("LFP" if r < 0.90 else "LCO")

def base_row(i, soh, ir, max_t, thermal, cycles, avg_t):
    seg, rated, volt = pick_pack()
    city, state, lat, lng, _ = random.choices(CITIES, weights=CITY_W)[0]
    lat += random.uniform(-0.15, 0.15); lng += random.uniform(-0.15, 0.15)
    fade = 100.0 - soh
    fade_rate = round(max(0.05, fade / max(cycles, 1) * 100 * random.uniform(0.8, 1.2)), 3)
    knee = round(random.uniform(0.06, 0.12), 3) if (soh < 80 and random.random() < 0.18) else round(random.uniform(0.001, 0.045), 3)
    quality = max(0.0, min(1.0, (soh - 55) / 40))   # 0 bad .. 1 good
    return {
        "external_ref": f"BAT-{i:04d}",
        "oem": f"Fleet Operator {random.choice('AABBC')} ({seg})",
        "model": f"VoltPack-{int(rated*1000)}",
        "chemistry": pick_chem(),
        "rated_capacity_kwh": rated,
        "nominal_voltage": volt,
        "manufacture_date": f"{random.randint(2021,2024)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "source_city": city, "source_state": state,
        "lat": round(lat, 4), "lng": round(lng, 4),
        "cycle_count": cycles,
        "capacity_now_kwh": round(rated * soh / 100.0, 2),
        "avg_temp_c": round(avg_t, 1), "max_temp_c": round(max_t, 1),
        "thermal_stress_hours": round(thermal, 1),
        "internal_resistance_mohm": round(random.uniform(12, 45), 1),
        "ir_growth_pct": round(ir, 1),
        "coulombic_efficiency": round(0.985 + 0.013 * quality, 4),
        "fade_rate": fade_rate,
        "fade_acceleration": knee,
        "cv_phase_fraction": round(0.12 + 0.30 * (1 - quality), 3),
        "voltage_slope": round(0.08 + 0.20 * (1 - quality), 3),
        "voltage_variance": round(0.004 + 0.12 * (1 - quality) * random.uniform(0.5, 1.5), 4),
        "discharge_efficiency": round(0.90 + 0.085 * quality, 4),
    }

rows, i = [], 0
def add(n, mk):
    global i
    for _ in range(n):
        i += 1
        rows.append(mk(i))

# S (42): pristine — soh>=90, ir<20, thermal<20, max_temp low, cycles<=900 (conf high)
add(42,  lambda i: base_row(i, random.uniform(90.2, 95.0), random.uniform(5, 17), random.uniform(36, 44), random.uniform(2, 14), random.randint(150, 600), random.uniform(26, 31)))
# A (127): soh 80.5-89.5, no flags
add(127, lambda i: base_row(i, random.uniform(80.6, 89.4), random.uniform(8, 38), random.uniform(38, 50), random.uniform(5, 35), random.randint(300, 950), random.uniform(28, 34)))
# B (297): soh 70.5-79.5
add(297, lambda i: base_row(i, random.uniform(70.6, 79.4), random.uniform(10, 55), random.uniform(40, 53), random.uniform(10, 60), random.randint(400, 1600), random.uniform(29, 36)))
# C (254): soh 60.5-69.5
add(254, lambda i: base_row(i, random.uniform(60.6, 69.4), random.uniform(10, 57), random.uniform(40, 54), random.uniform(20, 90), random.randint(600, 1900), random.uniform(30, 38)))
# D (127): three safety-override causes
add(60, lambda i: base_row(i, random.uniform(45, 58.5), random.uniform(20, 58), random.uniform(42, 54), random.uniform(40, 120), random.randint(900, 1950), random.uniform(31, 39)))   # SoH floor
add(35, lambda i: base_row(i, random.uniform(62, 80), random.uniform(20, 50), random.uniform(56.5, 66), random.uniform(60, 160), random.randint(700, 1800), random.uniform(34, 41)))  # overheat
add(32, lambda i: base_row(i, random.uniform(62, 80), random.uniform(62, 85), random.uniform(44, 54), random.uniform(30, 90), random.randint(800, 1900), random.uniform(31, 38)))     # IR critical

random.shuffle(rows)
# Re-number after shuffle for tidy refs
for n, r in enumerate(rows, 1):
    r["external_ref"] = f"BAT-{n:04d}"

# 3 deliberately invalid rows (demo reject-report beat: 850 uploaded -> 847 accepted, 3 rejected)
bad1 = base_row(9001, 75, 20, 45, 20, 500, 30); bad1["external_ref"] = "BAT-0848"; bad1["capacity_now_kwh"] = bad1["rated_capacity_kwh"] + 0.5      # capacity > rated
bad2 = base_row(9002, 75, 20, 45, 20, 500, 30); bad2["external_ref"] = "BAT-0849"; bad2["lat"], bad2["lng"] = 40.7128, -74.0060                       # outside India
bad3 = base_row(9003, 75, 20, 45, 20, 500, 30); bad3["external_ref"] = "BAT-0850"; bad3["chemistry"] = "NCA"                                          # invalid chemistry
rows += [bad1, bad2, bad3]

out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app", "seed", "sample_fleet.csv")
cols = list(rows[0].keys())
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} rows ({len(rows)-3} valid + 3 invalid) -> {out}")
