# 12 — Model Storage, Versioning, Loading

## Layout: one versioned bundle file (not loose pickles)

```
ml/models/model_v1.pkl        ← joblib dict, the ONLY artifact the backend needs
```

Bundle contents (keys binding for `train.py` writer and `predict.py` loader):

```python
{
  "version": "v1",                  # → assessments.model_version, /healthz
  "trained_at": iso8601,
  "sklearn_version": "x.y.z",       # pickle-compat guard — load-time assert vs installed
  "feature_keys": [...14 keys...],  # order + presence check at load
  "soh_model": HistGBR,
  "rul_models": {"q10": ..., "q50": ..., "q90": ...},
  "ood_envelope": {feature: [min, max]},      # confidence engine (08_*)
  "shap_background": ndarray(~100, 14),       # deterministic explainer init (09_*)
  "metrics": {...LOCO results...}             # model card + /healthz reads from here
}
```

The mandated `soh_model.pkl` / `rul_model.pkl` exist as **keys inside the bundle**, not separate files — one file means one path, one version, one load, zero "which pickle is stale" failure mode at 3 a.m. `evaluate.py` additionally writes `models/metrics_v1.json` (human-readable copy).

## Versioning

Bump = new file (`model_v2.pkl`), never overwrite. `MODEL_PATH` env var selects (docs/08 config). Every assessment row records `model_version` (docs/03) — re-grading after a retrain is auditable by design. Git: bundle committed if <50 MB (it will be ~1–5 MB for HistGBR), else Git LFS — committed is non-negotiable: clean-clone-must-run is a demo-day property.

## Loading (`predict.py`, consumed by backend at startup per docs/08)

1. `joblib.load(MODEL_PATH)` once at FastAPI startup — never per-request.
2. Assert `sklearn_version` matches installed (warn-and-continue on patch mismatch, hard-fail on minor mismatch).
3. Assert `feature_keys` == features.py's canonical list — catches vendoring drift (integration_validation §8).
4. Initialize SHAP explainer from `shap_background` once.
5. Expose `model_version` → `/healthz`.

Failure at any step = startup failure with a loud message, not a runtime surprise mid-cascade. **requirements.txt pins scikit-learn, shap, joblib to the exact versions used tonight** — train machine and Railway must resolve identically (judge-invisible, demo-critical).
