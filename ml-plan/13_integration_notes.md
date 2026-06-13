# 13 — Integration Notes & Audit (vs docs/04, docs/08, integration_validation.md)

**Rule zero restated: docs/04 api-contracts is frozen. The ML subsystem adapts to it. Nothing in ml-plan/ changes a wire shape.**

## Backend → ML (inputs)

Pipeline (docs/08 `services/pipeline.py`) calls `features.from_telemetry(summary_row)` → canonical 14-key dict → `health_engine.assess(features)` (thin wrapper over `ml.predictor.assess`). For deployment: `services/deployment.py` loads eligible sites + live `remaining_kwh`, calls `ml.recommend.recommend(assessment, battery_meta, sites)`, persists, decrements. ML code never touches the DB or the WS — pure functions in, dicts out.

## ML → wire (output mapping — extends integration_validation §3)

| ML output | DB | Wire (docs/04) |
|---|---|---|
| soh_pct, rul_years, grade, confidence | assessments columns | WS `assessment` payload, same names ✔ |
| rul_low / rul_high | rul_low_years / rul_high_years | `rul_range[0]/[1]` ✔ |
| **rul_cycles** (new, additive) | not stored as column — recomputable (`rul_years × 300`); passed in-memory to impact math | not on wire — internal + composite only |
| explanation / reasons | explanation_json / derived | `explanation_json` (detail) / `reasons` (WS, cards) ✔ |
| recommendations top-3 | deployments.reasoning_json | `reasons` (3 strings) on WS `deployment`; ranks 2–3 → counterfactual panel ✔ |
| selected_destination / score | deployments.site_id / score (raw float) | `site_name` / display int = round(×100) ✔ |
| **grade value "S"** (new) | CHECK constraint extended (docs/03 synced) | CHAR(1) field unchanged; "D" displays as "Recycle" ✔ |

## Error handling contract

- `assess()`/`recommend()` never raise on plausible input: clip, order, enum-validate internally (01_*).
- Truly invalid input (unknown keys, empty dict) raises `ValueError` — the pipeline's per-battery try/except (docs/08) logs + skips; the cascade never dies on one battery.
- Load-time failures fail loudly at startup (12_*), surfaced by `/healthz` — checked at pre-flight (docs/09).
- Low confidence is not an error: it's a routed outcome (inspection queue, no deployment) — see 08_*.

## API compatibility checklist (audited)

| Check | Verdict |
|---|---|
| WS `assessment` / `deployment` / `impact` payload shapes unchanged | ✔ PASS |
| `GET /batteries/{id}`, `/aadhaar` payloads unchanged (life_story already contracted) | ✔ PASS |
| `confidence` keeps 3 wire values (demo policy is data-side, 08_*) | ✔ PASS |
| grade stays CHAR(1); "S" added to value set — additive, ordering preserved | ✔ PASS (sync edit, F8) |
| `rul_cycles` not added to any endpoint | ✔ PASS (internal) |
| recommend.py placement vs docs/08 `services/deployment.py` | ✔ PASS — service wraps pure engine (docs/08 synced) |
| Impact math round-trip: rul_cycles = rul_years × 300 = docs/06 `remaining_cycles` | ✔ PASS (one constant) |
| `shared/constants.py` obligation (integration_validation §7) — now also holds grade thresholds, confidence thresholds, EOL 60/70 split, feature windows | ✔ extended, same file |

## Handoff to Farhan (unchanged from docs/10)

Deliverables crossing the seam: `ml/features.py` (vendored), `ml/models/model_v1.pkl`, `ml/predictor.py`, `ml/recommend.py`, `sample_fleet.csv`. Stub-assess integration first, real model swap at H10–12 (docs/08 build order). Nothing else crosses.
