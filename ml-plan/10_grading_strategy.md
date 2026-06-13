# 10 — Grading Strategy (5 tiers: S / A / B / C / Recycle)

## Wire encoding (contract-safe)

Five tiers ride the existing CHAR(1) field as `S, A, B, C, D` — **`D` renders as "Recycle"** everywhere user-facing. This is a value-set extension, not a shape change: docs/04 examples (grade "A") stay valid, `min_grade` ordering S>A>B>C>D works unchanged, and the demo script's "Grade D? Hard stop" line survives verbatim. Synced into docs/03 (CHECK constraint), 05, 06, 07 — see integration_validation F8.

## Thresholds (`grade.py` — rules over ML outputs, all constants in shared/constants.py)

```
Safety overrides (checked FIRST, on raw data not predictions — cannot be unlocked by any score):
  max_temp_c > 55  OR  ir_growth_pct > 60  OR  soh < 60       → D (Recycle)

S:  soh ≥ 90  AND confidence == high AND thermal_stress_hours < T_LOW
    AND ir_growth_pct < 20 AND rul_years ≥ 4                   → premium grid-scale
A:  soh ≥ 80  AND no flags                                     → solar storage / industrial backup
B:  soh ≥ 70  AND no flags                                     → microgrid / telecom / EV-charging buffer
C:  soh ≥ 60  AND no flags                                     → street lighting / low-duty backup
D:  everything else                                            → certified recycler ONLY
Confidence demotion: confidence == low  → cap at C (and block deployment per 08_*)
```

## Why five tiers (and why S earns its place)

S is scarce by design (~5% of a retired fleet) — scarcity is the story: *"an S-grade — top five percent of this fleet; it goes straight to grid-scale solar storage."* It also absorbs the "A is doing too much work" problem: premium buyers (grid storage) need a stricter bar (confidence + thermal history + RUL floor) than the SoH number alone provides. Recycle as a *named tier* (not just "D") reframes the bottom of the scale from failure to a routed, counted, material-recovery outcome — feeding the Safety Saves and Material Recovery Receipt features.

## Deployment suitability map (consumed by recommend.py gates)

| Tier | Eligible site types | Rationale |
|---|---|---|
| S | solar_storage, industrial_backup (+anything below) | longest horizon, tightest uncertainty → highest-value duty |
| A | solar_storage, industrial_backup, health_center_backup, ev_charging_buffer | high capacity retention, proven thermal history; PHC = critical load, also requires confidence high |
| B | rural_microgrid, school_backup, telecom_tower, ev_charging_buffer | dependable mid-duty; microgrid min-tier per docs/06 |
| C | street_lighting, low-duty backup | shallow cycles, non-critical loads |
| D / Recycle | recycler only — hard gate in recommend.py, not just here | safety is structural, not statistical |

## Expected fleet mix (synthetic generator target; QA-checked in 14_*)

S ~5% · A ~15% · B ~35% · C ~30% · D ~15%. Every tier fires visibly during the 847-battery cascade — the grade donut and FleetPulse read as a believable retired-fleet distribution, and the demo gets an S-moment, a microgrid-B story, and a Safety-Saves-D beat without staging.
