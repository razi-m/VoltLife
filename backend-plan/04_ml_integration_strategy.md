# 04 — ML Integration Strategy

## Topology: in-process import, not a service

The ML subsystem is vendored into the backend (`app/ml/`: `features.py`, `predictor.py`, `recommend.py`, `models/model_v1.pkl` — ml-plan/15 vendoring map) and imported as Python functions. There is **no HTTP hop, no serialization layer, no second deploy** (docs/02 decision, reaffirmed). Consequences for the mandated sections:

| Mandated concern | In-process equivalent |
|---|---|
| Request format | `assess(features: dict)` — canonical 14-key vector from shared `features.py` (ml-plan/03). The backend builds it from `telemetry_summaries.features_json`; it never hand-assembles feature math. |
| Response format | Exactly ml-plan/01 §1: `{soh_pct, rul_cycles, rul_years, rul_low, rul_high, grade, confidence, explanation, reasons}`. Pydantic-validated on receipt (`schemas/ml.py` mirrors the contract) — a malformed ML return is caught at the seam, not on the wire. |
| Timeouts | N/A (sub-ms in-process call). The pacing sleep dominates runtime by 100×. |
| Retry behavior | No retries — `assess()` is deterministic; retrying identical input is a no-op by design (fixed seeds, fixed SHAP background, ml-plan/09). Failure handling replaces retry logic: |
| Error handling | Per-battery `try/except` in the pipeline: log, append to job's `failed[]`, emit nothing, continue (docs/08). `ValueError` from invalid features = data bug → battery marked `status='error'`, visible in FleetTable, never silently dropped. |
| Availability | Load-time, not run-time: bundle loads at startup with version/feature-key asserts (ml-plan/12); failure = startup failure surfaced by `/healthz`. If the model can't load, the server doesn't lie about being healthy. |

## The non-recalculation rule (enforce structurally)

The backend stores and forwards ML outputs **verbatim**. Specifically forbidden in backend code: re-deriving grade from SoH, recomputing RUL years from cycles, editing reasons, remapping confidence, "fixing" out-of-range values (the predictor already clips — an out-of-range value reaching the backend is a bug to surface, not patch). The one legal computation on ML outputs: impact math (docs/06 formulas), which *consumes* `rul_cycles`/`soh_pct` as inputs — that's business logic, not prediction.

## Stub-first integration (the schedule-saving trick, docs/08)

H6–10: pipeline runs against `ml/stub_predictor.py` — schema-identical, returns plausible randomized values honoring all clips/enums. The entire backend + WS + frontend integrates against the stub; swapping `import stub_predictor as predictor` → `import predictor` at H10–12 is the whole "ML integration event." Antigravity generates the stub FIRST (it's ~30 lines and unblocks everything).

## Deployment engine seam

`services/deployment.py` calls `ml.recommend.recommend(assessment, battery_meta, sites)` (pure, ml-plan/11) and owns everything stateful: loading eligible sites with live `remaining_kwh`, persisting the deployment row, decrementing capacity in the same transaction, advancing battery status. Division of labor: **recommend() ranks; deployment.py commits.**
