# Integration Validation (Owner: Zaid — the integration contract)

**Rule zero: doc 04 (api-contracts) is the source of truth.** Frontend never invents endpoints; backend never invents schemas; ML never invents output fields. Any change goes through doc 04 first, then ripples. This document proves the pack integrates — and records what the audit caught.

## 1. Audit findings (caught and fixed — the audit has teeth)

| # | Inconsistency found | Fix applied |
|---|---|---|
| F1 | WS deployment example showed `energy_unlocked_mwh: 4.61`; doc 06 worked math gives 3.06 for the same battery | doc 04 corrected to 3.06 (both WS and aadhaar examples) |
| F2 | Aadhaar ID example used real-brand code `OLA`, violating doc 01 hard truth #1 | `FOA` ("Fleet Operator A") in docs 03 + 04 |
| F3 | Doc 04's example confidence ("high") contradicted doc 05's threshold (spread 0.49 vs <0.4) | doc 05 thresholds set to <0.5 high / <0.9 medium; example verified |
| F4 | Carbon credit ambiguity: grade-D recycler routings would have claimed avoided-manufacturing CO₂ | doc 06: carbon/energy credited only for deployed A–C; D counts as `recycled_responsibly` |
| F5 | `qr_payload` pointed at a public passport URL no doc defined | `GET /api/v1/aadhaar/{aadhaar_id}` added to doc 04; PublicPassport page added to doc 07 + blueprint P5 |
| F6 | `assess()` returned only rendered `reasons[]`, but DB stores structured `explanation_json` | doc 05 signature now returns both `explanation` (structured) and `reasons` (top-3 labels) |
| F7 | Adopted innovation features lacked data contracts | `life_story` added to aadhaar response (doc 04); Safety Saves + India 2030 declared frontend-derived (§4 below) |
| F8 | ML plan mandated 5 grade tiers (S/A/B/C/Recycle) vs A–D wire values | Value-set extension, not shape change: grade stays CHAR(1), 'S' added, 'D' renders as "Recycle". Synced: docs 03 (CHECK), 05 (thresholds + fleet mix), 06 (industrial_backup site type), 07 (S color). Wire examples (grade "A") remain valid. |
| F9 | ML plan additions vs frozen contracts | `rul_cycles` = internal/additive (not on wire); RUL redefined to 60% second-life EOL (prevents negative RUL on retired packs — judge_attacks #13 already consistent); `recommend.py` = pure engine wrapped by services/deployment.py (doc 08 synced); bundle path = ml/models/model_v1.pkl. Full audit: ml-plan/13. |
| F10 | Backend plan deltas vs frozen contracts | All additive, zero wire changes: site types school_backup + health_center_backup (docs/06, ml-plan/10 synced); Alembic baseline-only replaces "skip Alembic" (docs/08 synced); nullable `lifecycle_events.event_hash`; UART via existing ingest (no endpoint); mining-avoided + circularity score = frontend-derived (backend-plan/09); QR pixels stay client-side, payload backend-owned. Full audit: backend-plan/11, /13. |
| F12 | Final readiness audit findings (integration_readiness_report.md) | All applied in the pre-implementation sync: CSV template +6 optional feature columns (docs/04, ml-plan/03, generator specs); rul_cycles clamped [0, 2400] = 8.0 yr × 300 (ml-plan/01, /07); generic SQLAlchemy JSON/DateTime + sqlite→create_all branch (backend-plan/02, /10); types.ts id/battery_id + score-units annotations (frontend-plan/07); hardware formalized as optional bonus via standard ingest, framing option 1 adopted (docs/hardware_note.md). |
| F11 | Frontend plan deltas vs frozen pack | Page inventory unchanged (7 routes): mandated "Deployment Command Center" = P1 FeedFilter view state (blueprint synced); "Battery Intake & Assessment" = P4 + Run Demo button (posts bundled sample CSV through existing ingest — no endpoint); stack additions TypeScript + TanStack Query (docs/07 synced); docs/07 tokens declared placeholder pending Stitch (deadline H18, frontend-plan/08); derived-data whitelist unchanged at 4 items. Full audit: frontend-plan/12, /13. |

## 2. Endpoint matrix (every endpoint, all dependencies)

| Endpoint | Request | Response (doc 04 §) | DB tables | Backend module | Frontend consumers | ML |
|---|---|---|---|---|---|---|
| `POST /api/v1/batteries/ingest` | multipart CSV or `{batteries:[...]}` (§1 columns) | `{job_id, accepted, rejected, rejects[]}` | batteries, telemetry_summaries (writes) | api/ingest + services/ingestion | P4 Upload | — (triggers pipeline) |
| `GET /api/v1/jobs/{id}` | path param | `{status, processed, total, recent_events[]}` | — (in-process job state + event ring buffer — ephemeral by design) | api/jobs | P1 (polling fallback) | — |
| `WS /ws/feed` | — | `assessment` / `deployment` / `impact` / `job_done` events (§3) | emitted from pipeline | core/events + services/pipeline | P1 via useLiveFeed | assessment payload = `assess()` output |
| `GET /api/v1/batteries` | `?grade&status&page&page_size` | `{items[], total, page}` | batteries ⋈ assessments ⋈ deployments ⋈ sites | api/batteries | P6 Fleet | reads stored outputs |
| `GET /api/v1/batteries/{id}` | path | battery + telemetry + assessment (incl. explanation_json) + deployment (incl. reasoning_json) | all six tables | api/batteries | P2 Detail | reads stored outputs |
| `GET /api/v1/batteries/{id}/aadhaar` | path | passport payload (§5: decoded, static, dynamic, timeline, life_story, impact) | batteries, assessments, deployments, lifecycle_events | api/batteries + services/aadhaar | P2 passport panel | dynamic block = model outputs |
| `GET /api/v1/aadhaar/{aadhaar_id}` | path (public, read-only) | same payload as above | same | services/aadhaar | P5 Public Passport (QR target) | same |
| `GET /api/v1/sites` | — | `{items[]}` incl. derived `remaining_kwh`, `assigned_count` | sites ⋈ deployments | api/sites | P1 markers, P7 | — |
| `GET /api/v1/impact/summary` | — | impact payload + `by_grade` + `by_site_type` | SUM over deployments, assessments | api/impact + services/impact | P3, P1 initial state | aggregates of model outputs |
| `POST /api/v1/demo/reset` | header `X-Demo-Key` | `{ok}` | truncates fleet tables, re-seeds sites | api/demo | rehearsal ops | — |
| `POST /api/v1/demo/replay` | header `X-Demo-Key` | streams via WS | reads pre-computed results file | api/demo | fallback demo | replays stored outputs |
| `GET /healthz` | — | `{ok, model_version, db}` | ping | main | pre-flight check | reports model bundle version |

## 3. ML interface — binding name map (Razi → Farhan → Zaki)

Input: `assess(features: dict)` — keys exactly = doc 05 feature table = `telemetry_summaries.features_json` keys, produced by the **shared `ml/features.py`** (one module, vendored into backend, used by training and serving — the single most important anti-drift measure).

| predictor.py returns | DB column (assessments) | API field |
|---|---|---|
| `soh_pct` | `soh_pct` | `soh_pct` |
| `rul_years` | `rul_years` | `rul_years` |
| `rul_low` / `rul_high` | `rul_low_years` / `rul_high_years` | `rul_range[0]` / `rul_range[1]` |
| `grade` | `grade` | `grade` |
| `confidence` ("high"/"medium"/"low") | `confidence` | `confidence` |
| `explanation` (structured list) | `explanation_json` | `explanation_json` (detail endpoint) |
| `reasons` (3 label strings) | — (derived from explanation) | `reasons` (WS + cards) |

Deployment engine mirror: `decide()` → `deployments.reasoning_json` (factor contributions) → API `reasons` (3 strings) + full JSON in detail. Confidence ✔ included; explainability ✔ included — both validation requirements met by construction.

## 4. Derived-data declarations (no phantom endpoints)

| UI element | Source | New endpoint needed? |
|---|---|---|
| Safety Saves count | `impact.summary.by_grade.D` / `recycled_responsibly` | No |
| Safety Saves reason chips | client-side aggregation of streamed grade-D `assessment.reasons` | No |
| India 2030 overlay | frontend math: `impact.summary × (128 GWh ÷ batch GWh)` | No |
| `life_story` | server template over existing battery+assessment+deployment fields | No (field added to aadhaar payload, F7) |
| Site demand gauges | `sites.remaining_kwh` (derived in §2) | No |
| `mass_estimate_kg` (passport static) | constant kg/kWh × rated capacity, by form factor | No |

## 5. Module validation verdicts

**Frontend (doc 07 + blueprint):** consumes only §2 endpoints — verified page-by-page (P1: WS/jobs+sites+impact · P2: batteries/{id}+aadhaar · P3: impact · P4: ingest · P5: public aadhaar · P6: batteries list · P7: sites). Payload field names match doc 04 examples verbatim. **PASS** (post-F5/F7).

**Backend (doc 08):** every doc 04 endpoint has a named module in the folder tree; request/response schemas are Pydantic mirrors of doc 04 ("copy shapes EXACTLY" is written into the tree); error envelope defined (doc 04 header). Public aadhaar route lands in api/batteries + services/aadhaar. **PASS.**

**ML (doc 05):** input = shared features.py output; return signature = §3 map (post-F6); confidence + explanation included; pack-vs-cell honesty handled in Q&A docs, not hidden in code. **PASS.**

**Database (doc 03):** every API field traces to a column or a declared derivation (§2, §4); FKs defined with `ON DELETE CASCADE`; grade lives on assessments (re-assessment-safe); jobs are deliberately ephemeral (documented §2). **PASS.**

**Architecture (doc 02):** diagram modules = doc 08 folders; data flow = pipeline order = WS event order; pages in diagram are representative — the binding page inventory is the blueprint (stated there). Demo machinery (reset/replay) present in both 02 and 08. **PASS.**

## 6. Team independence test

Zaki receives doc 07 + blueprint + doc 04 → builds against the mock server (doc 04 §mock plan), never blocked. Farhan receives docs 03/04/06/08 → implements with stub-assess, never blocked on ML. Razi receives doc 05 → delivers one pickle + one function matching §3. The only physical handoffs: `features.py` (shared module), `model_v1.pkl` (H10–12 swap), `sample_fleet.csv` (shared fixture). **Verdict: PASS** — the docs are buildable in isolation because doc 04 + §3 fully specify every seam.

## 7. AI generation test

Could three separately AI-generated codebases integrate? Yes, **provided** the generators are fed doc 04 + this file verbatim (shapes are concrete JSON, not prose) and one extra artifact exists: **`shared/constants.py`** — grade thresholds, EOL=70%, 300 cycles/yr, 60 kg CO₂e/kWh, DoD 0.8, efficiency 0.9, scoring weights, PACE_S. Action: Farhan creates it at H1; backend and ML import it; frontend reads the same values from `/healthz`-adjacent config or hardcodes display copy only. With that, no cross-module redesign is required. **Verdict: PASS with the constants-file requirement (now mandatory, H1).**

## 8. Integration risks (residual, post-mitigation)

| Risk | Mitigation already in pack | Residual |
|---|---|---|
| Contract drift after H1 | Freeze rule + Zaid sign-off (doc 04) | Low |
| Razi's features.py diverges from backend copy | Single shared module, vendored not rewritten (§3) | Low |
| Model swap-in breaks pipeline at H10–12 | Stub-assess integration first (doc 08 build order) | Low |
| WS shape drift between mock and real | Mock replays literal doc 04 §3 JSON | Low |
| Constants drift (two values of "70%") | shared/constants.py (§7) | Low after H1 |
| Public passport needs live deploy | Railway by H12 + printed QR fallback (doc 12) | Medium — accepted |

## 9. FINAL CONSISTENCY AUDIT (mandated 10 questions)

1. Blueprint ↔ doc 07 match? **YES** — same 7 pages/routes; doc 07 defers UX authority to blueprint explicitly.
2. Doc 07 implements every blueprint page? **YES** — P1–P7 all present in the component tree (P3/P5 added in F5/F7 sync).
3. Every page has backend APIs? **YES** — §2 matrix column "frontend consumers" covers P1–P7 with zero gaps.
4. Every page has DB fields? **YES** — §2 + §4; no UI element lacks a table column or declared derivation.
5. Every page has ML outputs where required? **YES** — P1/P2/P3/P5/P6 render assess()/decide() outputs; P4/P7 need none by design.
6. Every widget has a real or simulated data source? **YES** — §4 table; simulated sources are flagged `is_simulated` in schema and labeled in pitch.
7. Frontend generatable from blueprint + doc 07? **YES** — pages, components, tokens, API shapes, and both live-feed paths are specified.
8. Backend generatable from doc 08 + doc 04? **YES** — folder-level modules, pipeline pseudocode, exact schemas, build order.
9. ML generatable from doc 05? **YES** — datasets, features, models, validation scheme, signature, and tonight's step list.
10. Independent development + integration without redesign? **YES** — §6 + §7 (with the H1 constants file).

## 10. FINAL VALIDATION (mandated 10 questions)

1. Startup, not class project? **YES** — regulatory wedge with dates, named buyers, cited TAM, competitor positioning, unit-economics answer (judge_attacks E).
2. AI solving the hardest problem? **YES** — health/RUL under uncertainty + allocation under constraints; everything else is rails.
3. Removing AI collapses the system? **YES** — grading and deployment halt; passports have nothing to record (judge_attacks #98 demonstrates it as a flex).
4. Memorable wow moment? **YES** — the cascade, the Life Story, the QR-in-judge's-pocket, the India 2030 multiplication. Four, sequenced.
5. Remembered six hours later? **YES** — "the team whose scooter battery had a biography and lit up the map of India" is a sentence judges repeat.
6. Buildable in 36h? **YES** — prep tonight is allowed and scoped (doc 10); Tier-1 surface ≈ 3.5 real pages; cut-lines pre-agreed; every beat has a fallback.
7. Teams work independently? **YES** — §6.
8. Modules integrate without redesign? **YES** — §5 all PASS; seams are one function, one pickle, one CSV, one constants file.
9. Demo stronger than architecture? **YES** — by design: architecture choices (pacing, replay, monolith) all serve the demo; doc 09 is the most rehearsed artifact in the pack.
10. Finalist/winning potential? **YES** — real ML + national policy hook + visible safety guardrails + cited impact + honest simulation framing is a combination no dashboard-only or wrapper project matches.

**Status: the pack passes. No regeneration required. Binding obligations created by this audit: `shared/constants.py` at H1 (§7); doc 04 remains frozen post-H1.**
