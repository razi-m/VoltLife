# 15 — ML Folder Structure & Implementation Order (for Antigravity)

## Training/ML repo folder

```
ml/
├── data/
│   ├── raw/                     # NASA .mat + CALCE files (downloaded tonight, committed or scripted)
│   └── parsed/                  # tidy per-cycle parquet per cell (parser output, cached)
├── models/
│   ├── model_v1.pkl             # versioned bundle (12_*) — the ONLY backend-facing artifact
│   └── metrics_v1.json          # human-readable LOCO results
├── parse_nasa.py                # .mat → tidy DataFrame (handles 02_* quirks)
├── parse_calce.py               # Excel/CSV concat → tidy DataFrame (cuttable)
├── features.py                  # canonical 14-feature functions (03_*) — SHARED, vendored to backend
├── labels.py                    # SoH labels + 60%-crossing RUL labels w/ curve extrapolation (07_*)
├── train.py                     # rows → LOCO eval → final fit → bundle write (05_*, 12_*)
├── evaluate.py                  # LOCO metrics + coverage, writes metrics json (05_*)
├── predict.py                   # load bundle, assess(features) → contract dict (01_*, 06_*, 07_*)
├── confidence.py                # tier logic + OOD envelope (08_*)
├── explain.py                   # SHAP + templates → explanation/reasons (09_*)
├── grade.py                     # S/A/B/C/D rules + safety overrides (10_*)
├── recommend.py                 # gates + scoring + top-3 + factor templates (11_*)
├── generate_fleet.py            # archetype-based synthetic fleet → sample_fleet.csv (docs/05)
├── shared_constants.py          # mirrors/imports shared/constants.py values used by ML
├── requirements.txt             # PINNED: scikit-learn, shap, joblib, pandas, numpy, scipy
└── tests/
    ├── test_features.py         # each feature: known input → known value; NaN robustness
    ├── test_predict_contract.py # output schema, clips, ordering, enums (01_* rules)
    ├── test_grade.py            # threshold table + safety overrides, exhaustive
    ├── test_recommend.py        # gates (D→recycler only), score ordering, tie-breaks
    └── test_demo_validation.py  # the 14_* harness (100/500/847)
```

Vendoring into the backend (docs/08): `backend/app/ml/` receives `features.py`, `predict.py`, `recommend.py`, `confidence.py`, `explain.py`, `grade.py` + `models/model_v1.pkl` — copied verbatim, never rewritten. `predict.assess()` internally composes confidence/explain/grade so the backend imports **one function**.

## Implementation order (dependencies respected; acceptance criterion each)

| Step | File(s) | Done when |
|---|---|---|
| 1 | parse_nasa.py | B0005/06/07/18 → tidy frames; corrupt cycles skipped + counted |
| 2 | features.py + test_features | 14 features computed at arbitrary cutoff; NaN-in → NaN-out, no raise |
| 3 | labels.py | SoH series smoothed; 60%-crossing RUL labels per cell; fit plots saved for the model card |
| 4 | train.py + evaluate.py | LOCO report prints; bundle written; SoH MAE recorded |
| 5 | confidence.py, grade.py, explain.py | unit tests green; explainer fallback chain works (04_* risk note) |
| 6 | predict.py + test_predict_contract | one dict in → full contract dict out, all clips/enums enforced |
| 7 | recommend.py + test_recommend | worked example (11_*) reproduces; D-gate exhaustive |
| 8 | generate_fleet.py | 847-row sample_fleet.csv with **all 14 feature columns populated** (incl. the 6 optional columns, M1); grade mix within target ±7 pts |
| 9 | test_demo_validation.py | green at 100/500/847; <5 s; QA report written |
| 10 | parse_calce.py (optional, cut-line 5) | CALCE cells join training; LOCO re-run |

Steps 1–9 are tonight's critical path (docs/10, Razi's list — this folder IS that list, expanded). Step 10 only if hours remain.

## Antigravity ground rules

Generate against the numbered specs in this folder — they are complete; do not invent fields, thresholds, or endpoints. Constants come from shared_constants.py, never inline. Every module pure (no DB, no network, no global state besides the loaded bundle). Determinism everywhere: fixed seeds, fixed SHAP background. When a spec and convenience conflict, the spec wins; when two specs appear to conflict, 01_ml_output_contract.md and docs/04 win, in that order.
