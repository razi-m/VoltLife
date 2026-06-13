# 03 — Feature Specification (canonical, BINDING)

`features.py` is **one shared module** — used by training, the fleet generator, and the backend (vendored, per docs/08). The 14 keys below are the canonical feature vector stored in `telemetry_summaries.features_json` and accepted by `assess()`. Order-independent (dict), names exact.

At training time, features are computed *at cutoff cycle k* (sliding window → many rows per cell). At serving time, "history" = the telemetry summary the operator uploads.

| # | Key | Why it matters | Computation |
|---|---|---|---|
| 1 | `cycle_count` | Age proxy; anchors every other trend | k (cycles completed) |
| 2 | `capacity_fade_pct` | Primary degradation magnitude | `(1 − cap_k / cap_initial) × 100`, smoothed capacity |
| 3 | `fade_rate` | Speed of decline — separates graceful agers from crashers | Linear-fit slope of capacity over last 50 cycles, % per 100 cycles |
| 4 | `fade_acceleration` | **Knee detector** — capacity-cliff onset collapses RUL | `slope(last 25 cycles) − slope(prior 25 cycles)` |
| 5 | `avg_temp_c` | Cumulative thermal aging | Mean of per-cycle mean temperature over history |
| 6 | `max_temp_c` | Worst-case abuse; safety-gate input | Max temperature ever recorded |
| 7 | `thermal_stress_hours` | Dose, not just peak — Arrhenius logic | Σ hours with temp > 40°C |
| 8 | `internal_resistance_mohm` | Power fade; second axis of aging independent of capacity | Latest `Re + Rct` (NASA impedance) or V-drop/I at discharge onset |
| 9 | `ir_growth_pct` | Aging marker robust to cell size | `(R_now − R_initial)/R_initial × 100` |
| 10 | `cv_phase_fraction` | Aged cells spend longer in constant-voltage charge — subtle, impressive to explain | CV-phase time / total charge time, recent-cycle mean |
| 11 | `voltage_slope` | Discharge-curve sag steepness rises with degradation | Mean dV/dt over the mid-section (20–80% DoD) of recent discharge curves |
| 12 | `voltage_variance` | Curve instability ↔ internal inconsistency / imbalance proxy | Variance of discharge-curve residuals vs the cell's own smoothed reference curve |
| 13 | `charge_efficiency` | Coulombic efficiency; side-reaction indicator | `discharge_Ah / charge_Ah`, recent-cycle mean (≡ doc 03's `coulombic_efficiency`) |
| 14 | `discharge_efficiency` | Energy efficiency; rises in losses = aging | `discharge_Wh / charge_Wh`, recent-cycle mean |

## CSV supply (audit fix M1)

All 14 features are suppliable through the ingestion CSV: 8 arrive via the base columns (cycle_count, capacity-fade from rated vs now, temps, thermal stress, IR + growth, charge_efficiency ≡ coulombic_efficiency) and the remaining 6 (`fade_rate, fade_acceleration, cv_phase_fraction, voltage_slope, voltage_variance, discharge_efficiency`) via the optional feature columns in the template (docs/04 §1). `features.from_telemetry` passes them through; missing → NaN with the confidence consequences in 08_*. The fleet generator always emits all 6.

## Mappings to existing schema (no DB change)

- `degradation_rate` (mandated name) ≡ `fade_rate` — alias documented here; canonical key is `fade_rate`.
- `telemetry_summaries.voltage_stability` (display column) = `1 − normalize(voltage_variance)`; `coulombic_efficiency` column = `charge_efficiency`. `features_json` always holds the full canonical 14-key vector; display columns are derived for the UI.

## Rules for Antigravity

1. Every feature function takes the tidy per-cycle DataFrame (parser output) + cutoff k; returns float or NaN. No feature may raise on missing inputs — return NaN.
2. NaN is a legal value end-to-end (HistGradientBoosting native); the OOD/confidence engine counts NaNs (08_confidence_strategy.md).
3. Initial-reference values (`cap_initial`, `R_initial`) = median of cycles 2–10, never cycle 1 (break-in noise).
4. Unit discipline: temperatures °C, resistance mΩ, capacity Ah internally / kWh at pack level. Pack scaling: synthetic generator scales capacity; rates and fractions are size-invariant by construction — state this in the model card.
5. Constants (40°C stress threshold, 50/25-cycle windows) live in `shared/constants.py` — no magic numbers in feature code.
