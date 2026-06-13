# 13 — Antigravity Implementation Guide (backend)

**You are an implementer, not an architect.** Every design decision is made. Where this folder, ml-plan/, and docs/ leave a gap, the precedence order is: **docs/04 api-contracts → integration_validation.md → ml-plan/01 → this folder → docs/08**. If two documents appear to conflict, the higher one wins and the conflict gets reported, not resolved creatively.

## FIXED — must not change

| Artifact | Status |
|---|---|
| All 12 routes + WS event shapes (docs/04) | frozen — copy JSON shapes into Pydantic verbatim |
| DB schema (docs/03) + the one nullable `event_hash` addition | frozen |
| `assess()` / `recommend()` signatures and return fields (ml-plan/01) | frozen — consumed, never reimplemented |
| Grade values S/A/B/C/D, confidence high/medium/low | frozen enums |
| Impact formulas + constants (docs/06, 09_*) via `shared/constants.py` | frozen — no inline numbers anywhere |
| Pipeline stage order: featurize → assess → decide → aadhaar → impact → broadcast | frozen |
| Error envelope, status codes (03_*) | frozen |

## GENERATE — in this exact order (10_* table has per-step acceptance criteria)

1. `mocks/mock_server.py` (unblocks frontend — FIRST, before anything real)
2. `core/` (config, db, events) + `models/orm.py` + Alembic baseline + `seed/`
3. `schemas/api.py` + `schemas/ml.py`
4. `services/ingestion.py` + read endpoints (batteries, sites, impact, jobs)
5. `services/pipeline.py` against `ml/stub_predictor.py` + WS broadcasting
6. `services/deployment.py`, `services/aadhaar.py`, `services/impact.py`
7. Real model swap (one import change) — validate via schemas/ml.py
8. `api/demo.py` (reset + replay) + `/healthz` + `scripts/make_qr_card.py`
9. `tests/test_smoke.py` green + Railway deploy

## RULES — non-negotiable implementation constraints

- **Never recalculate ML outputs** (04_*): no grade/RUL/confidence/reason derivation exists in `services/`. The single permitted consumer math: impact formulas.
- **One transaction per battery** (02_*): assessment + deployment + events + capacity decrement commit atomically.
- **`asyncio.to_thread` for sync work inside the pipeline** (08_*) — a stuttering cascade is a failed requirement, not a style issue.
- **One ring buffer feeds both WS and polling** (07_*) — do not implement them separately.
- **Per-battery try/except in the pipeline**: log, mark `status='error'`, continue. The cascade survives any row.
- **Determinism**: same seed data + same model ⇒ identical run, twice in a row (12_* rehearsal invariant).
- **No additions**: no extra endpoints, fields, tables, dependencies, or "improvements." A missing capability = report it against the spec; an invented one = a defect.
- requirements.txt pins must match the ML repo's pins exactly for scikit-learn/shap/joblib (ml-plan/12).

## Done means

`test_smoke.py` passes on a fresh clone with one setup command · 847-battery cascade runs paced (~2 min) and unpaced (<5 s) · reset→relaunch twice = identical output · `/healthz` truthful · public aadhaar route resolves from a phone against the Railway deploy · zero contract diffs against docs/04 (a literal diff of example payloads vs live responses is the final check).

## Final audit (mandated 7 questions)

1. Integrates with ML? **YES** — vendored seam, schema-validated, stub-first swap (04_*).
2. Integrates with frontend? **YES** — mock-first, all blueprint pages served, dual-path live feed (11_*).
3. Supports the demo? **YES** — every beat mapped to machinery with a fallback (12_*).
4. 847 simulations? **YES** — <5 s compute, paced to ~2 min, QA-gated (08_*, ml-plan/14).
5. WS supports live updates? **YES** — 4 event types, ordering guaranteed, polling-equivalent (07_*).
6. Buildable in 36 h? **YES** — 9 generate-steps mapping onto docs/10's existing milestones; nothing new was added to the timeline, only specified more precisely.
7. Improves winning chances? **YES** — the backend's contribution to winning is *reliability of the spectacle*: pacing, determinism, fallback ladder, and the PHC deployment beat.
