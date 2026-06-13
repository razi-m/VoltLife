# 04 — Model Architecture Selection

## Pipeline position (fixed — per the architecture rule)

```
Telemetry → features.py → SoH model → RUL models (q10/q50/q90) → confidence.py
          → explain.py (SHAP) → grade.py (rules) → recommend.py (optimization, NOT ML) → composite
```

Deployment recommendation is a transparent scoring engine (11_*). Only SoH and RUL are learned.

## Candidate comparison (1 = best)

| Criterion | Random Forest | sklearn HistGradientBoosting | XGBoost |
|---|---|---|---|
| Accuracy (tabular, n~10³ rows) | 3 | 1 (tie) | 1 (tie) |
| Explainability (SHAP) | 1 — TreeExplainer rock-solid | 2 — supported; see risk note | 1 — first-class TreeExplainer |
| Training speed | 2 | 1 (seconds) | 2 |
| Deployment simplicity | 1 (sklearn only) | 1 (sklearn only) | 3 — extra dependency, version-pinning pain on Railway |
| Native NaN handling | 3 — needs imputation | 1 — native | 1 — native |
| Quantile loss (RUL intervals) | 3 — not native | 1 — `loss="quantile"` | 2 — possible, more config |
| Hackathon feasibility | 1 | 1 | 2 |

## Decision

**SoH:** `HistGradientBoostingRegressor`. **RUL:** 3 × `HistGradientBoostingRegressor` with `loss="quantile"`, alpha 0.1 / 0.5 / 0.9.

Why: top-tier tabular accuracy at this data scale, native NaN handling (kills the imputation module entirely), native quantile loss (the RUL interval is a model property, not a hack), zero dependencies beyond scikit-learn, trains in seconds → leave-one-cell-out CV is cheap, and supports `monotonic_cst` (SoH constrained non-increasing in `capacity_fade_pct` — a one-line guard against embarrassing demo outputs).

**Known risk + fallback chain (Antigravity must implement the chain, not just plan A):**
SHAP's TreeExplainer support for HistGradientBoosting has version sensitivity. Order of attempts: (1) `shap.TreeExplainer(model)`; (2) `shap.Explainer(model, masker=background_sample)` (generic, slower — fine at 847×ms); (3) swap SoH model to classic `GradientBoostingRegressor` (bulletproof SHAP support, needs median imputation — implement `SimpleImputer` in the pipeline only for this branch). Pin `shap` and `scikit-learn` versions in requirements tonight after verifying locally — this is a tonight task, not an event task.

XGBoost is the runner-up, rejected on dependency weight alone. Random Forest survives as the emergency SoH fallback (no quantiles — intervals would degrade to ensemble-std, acceptable in disaster mode only).

Out of scope, with reasons on record (judge_attacks #9, #2): LSTMs/transformers (data scale), Gaussian Processes (elegant intervals, poor NaN story, slower to tune in 36h), fine-tuned battery foundation models (dependency + opacity risk).
