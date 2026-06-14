# VoltLife — Backend Phase 1 Validation Report

**Method:** full code read (31 files, ~3,300 lines) + live execution in a clean Linux environment: dependency install, compile check, the repo's own smoke test, 6 targeted runtime probes, and a 300-battery performance run. Every finding below marked **[RUNTIME-CONFIRMED]** was reproduced, not inferred.

---

## SECTION 1 — Build Validation

| Check | Result |
|---|---|
| Compiles (`compileall` on app/shared/tests) | ✅ clean |
| Imports resolve / no circular imports | ✅ at import time — but see M-1: a missing import only detonates at request time |
| FastAPI app starts (startup event runs, sites seed) | ✅ |
| Repo smoke test (`tests/test_smoke.py`) | ✅ **2/2 passed** — ingest→pipeline→aadhaar→impact verified end-to-end on 5 batteries |
| Dependencies | ⚠️ `requirements.txt` missing **httpx** (tests fail on a clean machine) and **alembic** (the Postgres init path comments "relying on Alembic" — which doesn't exist anywhere in the repo) |
| Missing files vs plan | ⚠️ no `db/migrations/`, no `railway.toml`/Procfile, no `.env.example` |
| Latent crash | ⚠️ `main.py` startup uses `json.dump` without `import json` — currently dormant only because the replay file exists (empty; see M-7) |

The committed `.venv` is a Windows venv (Python 3.14) — should be in `.gitignore`, and note `psycopg2-binary` may not have 3.14 wheels; verify before any Railway deploy.

## SECTION 2 — Architecture Compliance

**Strong.** Folder structure matches backend-plan/10 (routers/ vs api/ naming — cosmetic). Clean separation: routers thin, services own logic, ML vendored as pure modules, single WS manager, constants centralized in `shared/constants.py` and actually imported. No overengineering. The non-recalculation rule is honored — no grade/RUL math exists in services. Pipeline uses `asyncio.to_thread` per spec. One-job guard, job-cancel-on-reset, per-battery try/except with `status='error'` — all present.

Drift items: predictor delegates to stub via `predictor.py` exactly as planned (one-import swap for ML phase ✅); statuses `inspection` and `error` extend the spec enum (fine — must be reflected in frontend types).

## SECTION 3 — Database Audit

**Faithful to docs/03.** All 6 tables; generic `JSON`/`DateTime(timezone=True)` types (S1 fix honored); S-grade CHECK constraint; `event_hash` column with a **working sha256 chain implementation** (a planned-optional feature, delivered); cascades correct; indexes on status/battery_id/aadhaar_id. Audit trail complete: backfilled manufactured/first-life/retired events + live assessed/aadhaar_issued/deployment events.

Minor: `voltage_stability` column is loaded with raw `voltage_variance` (no 1−normalize transform) — mislabeled display data (S-4). Mixed naive/aware datetimes in lifecycle events (cosmetic on SQLite, could mis-order on Postgres).

## SECTION 4 — API Contract Audit

Endpoint inventory: **all 12 routes exist**, paths and verbs correct, response models mirror docs/04. But two contract breaks, both runtime-confirmed:

| # | Finding | Evidence |
|---|---|---|
| **M-2** | **Error envelope broken on every HTTPException path.** Routes raise `HTTPException(detail={"error": …})`; FastAPI wraps it → clients receive `{"detail": {"error": …}}`. The frozen contract is top-level `{"error": …}`. Frontend error parsing (frontend-plan/05) will miss every 4xx. | [RUNTIME-CONFIRMED] `GET /batteries/99999` → `{'detail': {'error': {...}}}` |
| **M-4** | **JSON ingestion is broken.** `POST /batteries/ingest` with `Content-Type: application/json` and `{"batteries": [...]}` returns `400 empty_file` — the Optional[UploadFile] + Body-model mix doesn't bind JSON. This also breaks the planned UART bridge (which posts JSON). | [RUNTIME-CONFIRMED] probe P4 → 400 |
| **M-1** | `GET /batteries?grade=A` → **500**: `func.row_number()` used but `func` never imported in `routers/batteries.py`. The grade-filter chips on FleetTable die. | [RUNTIME-CONFIRMED] NameError |

Correct: 202 on ingest, 409 job-guard, 404/409 on passports, 401 demo key, 413 over-limit, pagination caps, reject reports with row+reason.

## SECTION 5 — WebSocket Audit

**Good.** Connection manager with per-connection try/except + dead-client cleanup; single broadcast channel; **one ring buffer feeds both WS and `GET /jobs/{id}`** exactly per backend-plan/07; all four event types (`assessment`, `deployment`, `impact` every 5th + final, `job_done`) emitted with payloads matching docs/04 §3 field-for-field; assessment-before-deployment ordering structural.

Notes: new WS clients get a 20-event ring-buffer catch-up on connect (not in spec; harmless given the frontend's event-key dedupe, but reconnects will momentarily replay). `impact` event omits `by_grade`/`by_site_type` (correct — those are summary-endpoint fields; matches contract).

## SECTION 6 — ML Readiness Audit

**The seam is clean and swap-ready.** `predictor.assess()` is a one-line delegation to the stub — the real model lands by changing one import. `features.from_telemetry` produces the canonical 14-key dict (M1 columns flow through; NaN-native). `schemas/ml.py` validates the contract including the rul_cycles ≤ 2400 clamp (Must-Fix #2 honored). The stub itself is excellent: safety overrides first, S-tier rules, confidence from NaN-count + OOD-ish signals, knee explanation, sorted SHAP-style output.

Two readiness flags: **(a)** `schemas/ml.AssessmentResult` is defined but **never invoked in the pipeline** — the stub's dict goes straight to the DB. Add one `AssessmentResult(**result)` call in `pipeline.process_single_battery` so the real model is validated at the seam (the whole point of the schema). **(b) S-2 gate order:** both `deployment.py` and `recommend.py` check low-confidence *before* grade-D. Today that's masked because the stub forces `confidence="high"` on unsafe batteries — an invariant the real predictor might not preserve, at which point a dangerous low-confidence battery dodges the recycler. Swap the order (grade-D first) so safety isn't resting on a stub's side effect.

## SECTION 7 — Frontend Readiness Audit

| Page | Status |
|---|---|
| Mission Control | ✅ WS + jobs + sites + impact + healthz all serve correct shapes |
| Battery Intake | ⚠️ CSV path works incl. reject report; JSON path broken (M-4); **empty optional cells reject rows** (M-6, below) |
| Deployment Center | ⚠️ feed works; `?grade=` filter 500s (M-1) |
| Battery Aadhaar | ⚠️ passport payload complete & lovely (decoded ID, life story, timeline, hash chain) — but **`qr_payload` points at the API JSON route** (`/api/v1/aadhaar/{id}`), not the frontend page `/b/{id}`. A judge scanning the QR gets raw JSON on their phone (S-1). |
| Impact Center | ✅ all aggregates incl. by_grade/by_site_type; grade-D correctly zero-credited (F4 honored) |

**M-6** [RUNTIME-CONFIRMED]: a CSV row with blank optional cells (`…,0.999,,,,,,`) is **rejected** with `"Database error: could not convert string to float: ''"` — csv.DictReader yields `""` not `None`, and ingestion's explicit `float(row[...])` conversions choke. Real-world CSVs always have blanks; normalize `"" → None` per row before conversion.

## SECTION 8 — Demo Readiness Audit

This is where the audit gets ugly — three runtime-confirmed demo-breakers:

| # | Finding | Evidence |
|---|---|---|
| **M-3** | **`POST /demo/reset` returns 500 every single time** — `asyncio.create_task()` called from a sync route (worker thread, no event loop). Worse: the wipe + reseed **have already committed** before the crash, so state changes while the operator sees an error. Every rehearsal starts with this endpoint. | [RUNTIME-CONFIRMED] probe P3 → 500 |
| **M-5** | **N+1 query explosion in `get_derived_sites()`** — called per battery, it loops every site → every deployment → a per-deployment latest-assessment query. Measured: **300 batteries = 33.3 s of pure compute (PACE_S=0)**; quadratic growth ⇒ 847 ≈ **4–5 minutes** against the 5-second gate — and during the paced demo, per-battery compute exceeds the 0.15 s pacing well before battery #300, so the cascade visibly decelerates on stage. | [RUNTIME-CONFIRMED] perf run |
| **M-7** | **Replay is hollow.** `replay_results.json` is 0 bytes; `/demo/replay` returns 202 "success" and streams nothing (background task fails silently). The startup self-heal only triggers if the file is *absent* (it exists, empty) — and that code path has the missing `json` import anyway. The #1 demo fallback currently does not exist. | [RUNTIME-CONFIRMED] probe P6 |
| **S-3** | `sample_fleet.csv` has **9 rows, not 847** (2 deliberately invalid — nice touch for the reject-report beat). The real fleet is the ML-phase generator's job, but the Run Demo beat is blocked until it lands. | file inspection |

Working: pacing, one-job guard, job cancellation, impact ticking, the full ingest→assess→deploy→aadhaar cascade (5- and 7-battery runs, and 300 with patience).

## SECTION 9 — Security & Reliability

Appropriate for a hackathon: demo-key on destructive routes ✅; ORM throughout (no raw SQL, no injection surface) ✅; India-bbox + numeric validation with per-row rejects ✅; global exception handlers ✅; per-battery failure isolation in the pipeline ✅. Notes: default `DEMO_KEY="volt_secret_key"` hardcoded fallback (fine for demo; set the env on Railway); CORS `*` (fine); no auth on reads (by design).

## SECTION 10 — Performance Review

The single real problem is M-5 (quadratic site recomputation) — everything else is healthy: impact summary is proper aggregate SQL with a window function (0.01 s at 300 batteries); `/sites` 0.17 s; ingestion commits per row (847 commits — acceptable); list endpoint does small per-row queries (N+1 but page-capped at 200 — tolerable). **Exact M-5 fix, no schema change:** assigned kWh per site is recoverable from data already stored — `usable_kwh = carbon_saved_kg / 60` — so one `GROUP BY site_id` over deployments (SUM(carbon_saved_kg)/60, COUNT(*)) replaces the entire nested loop; or keep an in-memory `{site_id: remaining_kwh}` tracker for the job's duration.

## SECTION 11 — Required Fixes

**MUST FIX (7 — all runtime-confirmed, est. ~2 hours total):**

| # | Fix | Est. |
|---|---|---|
| M-1 | `from sqlalchemy import func` in `routers/batteries.py` | 1 min |
| M-2 | Add an `HTTPException` handler in `main.py`: if `detail` is a dict containing `"error"`, return it as the body unmodified | 10 min |
| M-3 | `async def reset_demo` + `await ws_manager.broadcast(...)` (drop `create_task`) | 5 min |
| M-4 | Ingest route: read raw `Request`; branch on content-type (multipart → file parse, application/json → `await request.json()` → `batteries` list) | 30 min |
| M-5 | Replace `get_derived_sites` internals with one GROUP-BY aggregate (`SUM(carbon_saved_kg)/60` per site) | 30 min |
| M-6 | Normalize `"" → None` for all row values at the top of `process_ingestion` | 10 min |
| M-7 | `import json` in main.py; treat empty replay file as missing; record a real replay file at the first clean E2E run | 15 min |

**SHOULD FIX:**
S-1 `qr_payload` → `{PUBLIC_FRONTEND_URL}/b/{aadhaar_id}` (new env var; the API route stays as the data source) · S-2 swap gate order so grade-D precedes low-confidence in `deployment.py` + `recommend.py` · S-3 generate the real 847-row fleet (ML phase, blocks Run Demo) · S-4 store `voltage_stability` as a stability value, not raw variance · S-5 add `httpx` to requirements; decide Postgres init (alembic baseline or extend `create_all`) · S-6 add `.env.example` + railway config · S-7 add `inspection`/`error` statuses to frontend types.

**NICE TO HAVE:** validate stub output through `schemas/ml.AssessmentResult` in the pipeline (turns the seam schema from decoration into a guard) · "Best capacity match" factor is templated onto every candidate even when capacity wasn't the top factor · `.venv` out of the repo · consistent naive/aware datetimes.

## SECTION 12 — Final Verdict

**Backend Readiness Score: 6.5/10**

(Architecture 9 · Database 9 · WS 8.5 · ML seam 8.5 · API contract 6 · Frontend readiness 6.5 · Demo readiness 5 · Build 7)

# **NOT READY FOR ML IMPLEMENTATION**

**Blockers:** M-1 through M-7. Three of them (reset 500, hollow replay, N+1 cascade drag) break the demo directly; two (error envelope, JSON ingest) break frozen contracts the frontend and UART bridge build against; the remaining two corrupt real-world ingestion.

**The honest framing:** this is a *good* Phase 1 — the architecture is faithful, the hard parts (pipeline, WS, aadhaar, hash chain, gates, impact math) are correct, and the ML seam is genuinely one-import-swap ready. The blockers are seven small, precisely-located defects totaling roughly two hours of fixes, and every one was caught by running the code rather than reading it. Apply M-1…M-7, re-run the smoke test plus the six probes in this report, and Phase 1 flips to approved. Until then, do not start ML generation — the first thing the real model meets must not be a broken seam.
