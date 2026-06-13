# 05 — Training Strategy

## Training-row generation

From each cell's full history, emit one row per cutoff k = 50, 55, 60, … (step 5) up to EOL: features-at-k (03_feature_spec) → labels-at-k. ~4–8 cells × ~150–300 cutoffs ≈ **1,000–2,500 rows**. Labels: `soh_k = smoothed_cap_k / cap_rated × 100`; `rul_k` = cycles from k to the 60%-SoH crossing of the fitted fade curve (07_rul_model_design.md).

## Split & validation: leave-one-cell-out (LOCO) — non-negotiable

Random row splits leak cycles from the same cell across train/test and inflate metrics by 2–5× — the first thing an ML judge checks (judge_attacks #4). Protocol: for each cell c, train on all others, evaluate on c; report **mean ± std across held-out cells**. Final shipped model trains on ALL cells (LOCO is for the reported number, not the artifact).

## Evaluation metrics (record tonight; they go in the pitch)

| Metric | Target | Notes |
|---|---|---|
| SoH MAE | ≤ 4 pts (expect 2–4) | headline number — "X% SoH MAE under leave-one-cell-out CV" |
| SoH RMSE | report | exposes outlier cutoffs (knee regions) |
| SoH R² | ≥ 0.85 | report honestly even if lower; LOCO R² is harsh |
| RUL q50 MAE | report in cycles | convert to years only with the 300/yr caveat attached |
| RUL interval coverage | 70–90% of true values inside [q10, q90] | THE credibility metric — quantile bands must mean something (judge_attacks #7) |

All metrics + per-cell breakdown saved to `models/.../metrics.json` by `evaluate.py` — the model card reads from it, no hand-typed numbers.

## Hyperparameter tuning (time-boxed: 30 minutes, tonight)

Small grid via LOCO: `learning_rate ∈ {0.05, 0.1}`, `max_iter ∈ {200, 400}`, `max_depth ∈ {3, 5}`, `min_samples_leaf ∈ {20, 50}`. Pick by SoH MAE. If the grid stalls, defaults + `max_iter=300` are fine — tuning is the lowest-ROI hour available tonight.

## Overfitting prevention

LOCO as the only reported metric (structural honesty) · `early_stopping=True` with validation fraction · `min_samples_leaf ≥ 20` (rows per cell are autocorrelated — small leaves memorize cells) · `monotonic_cst`: SoH non-increasing in `capacity_fade_pct` · 14 features max, no cell-identity leakage (no cell ID, no cutoff-index-as-feature beyond `cycle_count`) · fixed `random_state` everywhere (reproducible = debuggable at 3 a.m.).

## Reproducibility

`train.py` is deterministic end-to-end: seeded, versioned inputs (raw data SHA noted in manifest), outputs the versioned bundle (12_model_storage_strategy.md). One command retrains everything: that sentence is also a judge answer.
