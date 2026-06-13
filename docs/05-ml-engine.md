# 05 — ML Health Engine (Owner: Razi)

This is the module that makes or breaks the "AI is structurally necessary" claim. It must be real, validated, and explainable. It must NOT be deep learning.

## Decisions, locked

| Question | Answer | Why |
|---|---|---|
| Framework | scikit-learn only | 34 cells of training data. GBMs beat overnight LSTMs here, train in seconds, and SHAP TreeExplainer is instant. PyTorch = wasted night. |
| SoH model | `HistGradientBoostingRegressor` (fallback: RandomForest) | Strong on tabular, handles NaNs natively. |
| RUL model | `GradientBoostingRegressor` with `loss="quantile"`, α = 0.1 / 0.5 / 0.9 | Three models → median + honest interval. Never show a bare point estimate. |
| Grade | **Rules on top of ML outputs** (thresholds below) | "Model predicts, policy assigns" — defensible, tunable, and safety-arguable to judges. |
| Explainability | SHAP top-3 → templated English | Deterministic, instant, no LLM in the decision loop. |
| Validation | **Leave-one-cell-out** CV | The only honest scheme — random row splits leak cycles from the same cell into train and test. Saying "leave-one-cell-out" unprompted earns instant ML-judge respect. |

## Data

- **NASA PCoE battery dataset** — start with B0005, B0006, B0007, B0018 (18650 cells, 2.0 Ah rated, cycled to EOL ≈ 70% capacity = 1.4 Ah; charge/discharge curves, temperature, measured capacity per cycle). Add the 25–45°C ambient groups if time allows. Mirrors are easier to grab than the NASA site — the Kaggle mirror works.
- **CALCE CS2** prismatic cells (1.1 Ah) — second chemistry/form factor; even partial use strengthens the "not overfit to one dataset" answer.
- **Download both TONIGHT (June 12).** Put raw data + parsing notebook in `ml/` of the repo. Do not depend on venue Wi-Fi for datasets.

## Feature engineering (per battery, from cycle history)

From each cell's history compute, at any cutoff cycle k (this gives you thousands of training rows from few cells — state at cycle k → label at cycle k):

| Feature | Computation | Degradation signal |
|---|---|---|
| `cycle_count` | k | Age |
| `capacity_fade_pct` | (1 − cap_k / cap_initial) × 100 | Primary SoH proxy |
| `fade_rate` | Linear-fit slope of capacity over last 50 cycles | Speed of decline |
| `fade_acceleration` | Slope(last 25) − slope(prior 25) | **Knee detection** — the killer feature; capacity cliff = RUL collapse |
| `avg_temp_c`, `max_temp_c` | Means/max over history | Thermal aging |
| `thermal_stress_hours` | Hours above 40°C | Cumulative abuse |
| `internal_resistance_mohm` | From voltage drop at discharge onset (NASA provides R measurements on impedance cycles) | Power fade |
| `ir_growth_pct` | (R_now − R_initial)/R_initial | Aging marker |
| `cv_phase_fraction` | CV-charge time / total charge time | Rises with age — subtle, impressive to explain |
| `voltage_stability` | 1 − normalized std of discharge-curve residuals | Cell imbalance proxy |
| `coulombic_efficiency` | discharge_Ah / charge_Ah (recent mean) | Side-reaction indicator |

**Labels:** `SoH_k = cap_k / cap_rated × 100`. `RUL_k = cycles_to_EOL(70%) − k`, convert to years at an assumed **300 cycles/year (2W fleet duty ≈ ~25 cycles/month)** — state this assumption on the slide and in the UI tooltip; judges respect declared assumptions and punish hidden ones.

## Grading policy (rules over ML) — 5 tiers, full spec in ml-plan/10

```
Safety overrides first (raw data, non-negotiable): max_temp > 55°C OR ir_growth > 60% OR SoH < 60 → D
S: SoH ≥ 90 AND confidence high AND pristine thermal/IR AND RUL ≥ 4y  → premium grid-scale (~5% of fleet)
A: SoH ≥ 80, no flags                                                  → solar storage / industrial backup
B: SoH ≥ 70, no flags                                                  → microgrid / telecom / EV buffer
C: SoH ≥ 60, no flags                                                  → low-duty (street lighting, backup)
D: everything else — renders as "Recycle"                              → certified recycler (HARD STOP)
Low confidence caps the grade at C and blocks deployment (inspection queue).
```

Grade D is a non-overridable safety rule — this one line is your answer to every "what if the AI is wrong about a dangerous battery" question.

## Confidence

`high / medium / low` from quantile spread: `(rul_high − rul_low) / rul_median` < 0.5 → high; < 0.9 → medium; else low (e.g. the doc 04 example battery: (5.2−3.1)/4.3 = 0.49 → high). Also force `low` when a feature is outside the training distribution (simple min/max envelope check) — "the model knows what it doesn't know" is a quotable line.

## Explainability → English

SHAP `TreeExplainer` on the SoH model → top 3 |contribution| features → template map:

```python
TEMPLATES = {
  ("avg_temp_c", "+"): "Low thermal stress (avg {v:.0f}°C)",
  ("avg_temp_c", "-"): "High operating temperature (avg {v:.0f}°C)",
  ("fade_acceleration", "-"): "Capacity fade is accelerating — knee detected",
  ("cycle_count", "+"): "Moderate cycle count ({v:.0f} cycles)",
  ("ir_growth_pct", "-"): "Internal resistance up {v:.0f}% from baseline",
  ("voltage_stability", "+"): "Stable voltage profile under load",
  ...
}
```

Output exactly 3 bullet reasons per battery — that's what the UI and the WS contract expect.

## Synthetic fleet generator (Razi builds, Zaid parameterizes)

The 847-pack demo fleet must be *derived from real degradation physics*, not `random()`:

1. Fit per-cell degradation trajectories (capacity vs cycle) from NASA/CALCE → a library of ~30 real aging archetypes.
2. For each synthetic pack: sample an archetype, jitter (fade rate ±20%, temps ±4°C, IR ±15%), scale to pack capacity, truncate at a random retirement cycle (weighted so the fleet lands ≈ 5% S / 15% A / 35% B / 30% C / 15% D — a believable retired-fleet mix that also makes every part of the demo fire, including an S-grade moment).
3. Attach metadata: 80% 2W (3–4 kWh), 15% 3W (5–8 kWh), 5% 4W (25–40 kWh); chemistry mix NMC/LFP; cities weighted to Maharashtra, Karnataka, Telangana, Tamil Nadu, Delhi NCR; manufacture dates 2021–2024. Label OEM as "Fleet Operator A/B/C" — **never fabricate real-brand telemetry** (see doc 01, hard truth #1).
4. Emit `sample_fleet.csv` in the ingestion schema — **including all 6 optional feature columns** (fade_rate, fade_acceleration, cv_phase_fraction, voltage_slope, voltage_variance, discharge_efficiency; audit fix M1) — + a 20-row `sample_small.csv` for upload-wizard demos.

Because features were sampled from real trajectories, model outputs on the synthetic fleet are smooth and plausible — no absurd "SoH 12%, RUL 9 years" rows on stage. Spot-check the extremes before demo (doc 12 checklist).

## Tonight (June 12) — Razi's prep list

1. Download NASA + CALCE; write the parser (`.mat` → tidy per-cycle DataFrame).
2. Build feature pipeline + training-row generator (sliding cutoffs).
3. Train SoH + 3 quantile RUL models; run leave-one-cell-out; **record MAE numbers** (expect roughly 2–4% SoH MAE; whatever you get, write it down — it goes in the pitch and the Q&A).
4. SHAP + templates working end-to-end on one battery.
5. Export `model_v1.pkl` bundle (dict: models + feature list + version + metrics) + `predictor.py` with a single entry point:

   ```
   assess(features: dict) -> {
     soh_pct, rul_cycles, rul_years, rul_low, rul_high, grade, confidence,   # rul_cycles: internal/additive, not on wire
     explanation: [{feature, value, impact, label}, ...],   # stored as assessments.explanation_json
     reasons: [label, label, label]                         # top-3 labels — what the WS/API emit
   }
   ```

   Field-name mapping to DB/API is binding (see integration_validation.md §3): `rul_low/rul_high` → DB `rul_low_years/rul_high_years` → API `rul_range[0]/[1]`.
6. Build the fleet generator; emit `sample_fleet.csv` (847 rows).

At the event, Razi's deliverable to Farhan is **one function and one pickle**. Everything else (retraining with more cells, calibration, CALCE expansion) is event-time polish.

## Traps (do not)

- Don't claim "95% accurate" — say "X% SoH MAE under leave-one-cell-out CV on NASA data."
- Don't show RUL without the interval. The interval IS the credibility.
- Don't let anyone talk you into an LSTM "because judges like deep learning." Judges like *working, explained* systems.
- Don't train on random row splits. Cell-level leakage is the first question an ML judge asks.
- Don't hide the cell-vs-pack gap; pre-empt it (doc 11, Q4 has the script).
