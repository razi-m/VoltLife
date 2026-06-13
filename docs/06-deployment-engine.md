# 06 — Autonomous Deployment Engine + Impact Math (Owner: Farhan · Logic sign-off: Zaid)

The second half of "AI is structurally necessary." The health engine predicts; this engine *decides*. Keep it a transparent multi-criteria optimizer — transparent beats clever, because every assignment must come with reasons.

## Demand registry (simulated, realistic)

~20 seeded sites. Realistic names/locations make the map demo land:

| Type | Examples (state) | min_grade | Typical demand | priority |
|---|---|---|---|---|
| solar_storage | Bhadla Solar Park Storage (RJ), Khavda BESS (GJ), Pavagada (KA) | A | 200–500 kWh | 1.0 |
| rural_microgrid | Gaya microgrid (BR), Dumka cluster (JH), Majuli island (AS) | B | 40–120 kWh | 1.3 ← mission weighting |
| telecom_tower | Indus-style tower clusters (UP, MP) | B | 15–40 kWh | 0.9 |
| industrial_backup | Chakan industrial park UPS (MH), Sriperumbudur (TN) | A | 60–200 kWh | 1.0 |
| school_backup | Govt school clusters (BR, JH, OD) | B | 8–20 kWh | 1.1 |
| health_center_backup | Primary health centres — vaccine cold chain (UP, AS) | A | 10–25 kWh | 1.2 |
| ev_charging_buffer | Hyderabad ORR hub (TS), Pune depot (MH), Bengaluru (KA) | B | 50–150 kWh | 1.0 |
| street_lighting | Nagpur smart lighting (MH) | C | 10–30 kWh | 0.8 |
| recycler | Greater Noida Li recycler (UP), Hyderabad recycler (TS) | D (accepts all) | ∞ | — |

`is_simulated = TRUE` on all — and say so when asked. Microgrid priority 1.3 gives you a story beat: *"the system slightly favors rural energy access when scores tie — policy is a parameter."*

## Decision logic

Hard constraints first (gates, not weights):
1. Grade D → recycler. Always. Non-negotiable safety rule.
2. `soh ≥ site.min_soh` and grade ≥ `site.min_grade`.
3. `site.remaining_kwh > 0` (decrement as batteries are assigned).

Then score every feasible (battery, site) pair:

```
score = 0.30 · capacity_match     # 1 − |usable_kwh − site_unit_need| / site_unit_need, clipped to [0,1]
      + 0.25 · grade_headroom     # battery grade vs site min_grade (A→C site wastes value: small penalty)
      + 0.20 · proximity          # 1 − distance_km / 2000, clipped  (haversine)
      + 0.15 · carbon_benefit     # normalized carbon_saved (below)
      + 0.10 · site_priority
```

Assignment: process batteries in ingestion order (it's a stream — fits the demo), greedy argmax per battery, decrement site capacity. Mention `scipy.optimize.linear_sum_assignment` as the batch-mode upgrade if a judge asks about global optimality — know the name, don't build it.

**Reasoning output** (contract: 3 strings): take top-3 scoring factor contributions → templates, e.g. "Best capacity match (3.2 of 4.0 kWh unit need)", "688 km — nearest eligible solar site", "Rural microgrid priority applied". Same pattern as the health engine: numbers → English, no LLM.

## Impact math (judges WILL check this)

Per battery, computed at assignment, summed for the counters:

```
usable_kwh        = rated_capacity_kwh × SoH
remaining_cycles  = rul_years × 300            # same cycles/yr assumption as doc 05 — keep consistent!
energy_unlocked_MWh = usable_kwh × remaining_cycles × 0.80 DoD × 0.90 round-trip eff / 1000
carbon_saved_kg   = usable_kwh × 60            # avoided NEW battery manufacturing
diverted_count    = grades A–C
recycled_responsibly = grade D routed to recycler
```

Carbon and energy are credited **only for deployed A–C packs** — a grade-D pack going to a recycler avoids no new manufacturing (its credit is material recovery, which we count separately as `recycled_responsibly`). Mixing the two would hand a sharp judge a free kill.

**The 60 kg CO₂e/kWh factor:** published cradle-to-gate estimates for Li-ion run ~48–120 kg CO₂e/kWh (median ~80; PMC meta-analysis, MIT Climate Portal). We use 60 — below median — and say the word **"conservative."** Logic: every kWh of second-life storage displaces a kWh of newly manufactured storage. Citations live in doc 01; have them on a phone tab during Q&A.

Worked example for the pitch (one A-grade 2W pack): 4.0 kWh × 0.82 SoH = 3.28 usable kWh → ×1,290 remaining cycles ×0.8 ×0.9 ≈ **3.0 MWh unlocked** and ≈ **197 kg CO₂e avoided**. "One scooter battery, three megawatt-hours" is a sticky line. Fleet of 847 ≈ 1.5–2.5 GWh unlocked, 100–150 t CO₂e — sanity-check final seeded numbers before the demo so the counters end on plausible values.

## What NOT to add

Route optimization / truck planning, dynamic pricing, multi-leg logistics, demand forecasting. Each is a rabbit hole; none changes the demo. The engine's job: every battery gets a destination + three reasons + two impact numbers, in milliseconds.
