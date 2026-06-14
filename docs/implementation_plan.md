# VoltLife — Implementation Readiness Plan

VoltLife is an autonomous battery lifecycle operating system designed to address India's projected 128 GWh battery retirement by 2030. It ingests battery telemetry, assesses State of Health (SoH) and Remaining Useful Life (RUL) using machine learning (HistGradientBoosting / Gradient Boosting), determines optimal second-life destinations or routing to certified recyclers, generates dynamic Battery Pack Aadhaar Numbers (BPAN) in compliance with the Ministry of Road Transport and Highways (MoRTH) draft guidelines, and tracks lifecycle events.

This implementation plan establishes a bulletproof, stage-ready roadmap designed to coordinate parallel tracks for the backend, machine learning, and frontend developers.

## User Review Required

> [!IMPORTANT]
> **Regulatory Compatibility:** The Battery Aadhaar implementation mirrors MoRTH's draft guidelines for a 21-character Battery Pack Aadhaar Number (BPAN). We explicitly state that VoltLife is the *intelligence layer* that computes and updates these dynamic fields, rather than claiming to have invented the passport itself.
>
> **Simulated vs. Real Data:** In order to remain highly credible under judge interrogation, the fleet data (847 packs) is simulated using trajectories perturbed from actual NASA and CALCE degradation curves. This is labeled "Simulated batch, real physics" on the pitch deck.
>
> **Safety Guardrails:** Grade D batteries must have a hard rule preventing deployment under any circumstances, routing them strictly to certified recyclers. This rule is absolute and overrides all ML predictions.

> [!WARNING]
> **Hacking Window & Cut-Lines:** HackPrix Season 3 may announce a compressed 24-hour hacking window at kickoff. If this occurs, cut-line 1 (drop SitesView page) and cut-line 2 (drop UART hardware) are triggered immediately at Hour 0.

## Open Questions

There are no unresolved questions that block starting the project design, but the following confirmation is required at kickoff:
* **Hacking Window:** Confirm if the window is exactly 36 hours or compressed (e.g., 24 hours).
* **UART Rehearsal:** Confirm if the UART hardware is ready and can pass two clean dry-runs before Hour 24 to be included in the live pitch.

---

## Proposed Changes

The codebase is structured as a modular monolith inside a single repository. To eliminate integration friction, contract details are frozen in `docs/04-api-contracts.md` and `docs/integration_validation.md`. A shared constants module (`shared/constants.py`) will be created at H1 to house all physical parameters and grading thresholds.

### [NEW] Shared Constants

#### [NEW] [constants.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/shared/constants.py)
* Define global parameters:
  * Cycles per year: 300
  * Avoided manufacturing footprint: 60 kg CO₂e/kWh
  * Depth of Discharge (DoD): 0.80
  * Round-trip efficiency: 0.90
  * Grade thresholds (S/A/B/C/D)
  * Safety thresholds (max temp > 55°C, IR growth > 60%, SoH < 60%)
  * Pacing constant: `PACE_S = 0.15` (can be overridden via env)

---

### [NEW] ML Subsystem

#### [NEW] [predictor.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/predictor.py)
* Thin wrapper exposing `assess(features: dict) -> dict` returning State of Health (SoH), Remaining Useful Life (RUL) cycles/years, quantile bounds, grade, confidence rating, and structured SHAP reasons.

#### [NEW] [recommend.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/recommend.py)
* Scoring logic matching graded packs to the demand registry based on capacity match, grade headroom, proximity, carbon benefit, and site priority.

#### [NEW] [features.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/features.py)
* Canonical feature mapping to derive the 14 features from raw BMS telemetry. Used in both training and inference.

---

### [NEW] Backend Subsystem

#### [NEW] [main.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/main.py)
* FastAPI application startup. Loads `model_v1.pkl` into memory, initializes the database connection, handles CORS, and registers the WebSocket endpoints.

#### [NEW] [orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py)
* SQLAlchemy definitions for the 6 core tables: `batteries`, `telemetry_summaries`, `assessments`, `sites`, `deployments`, and `lifecycle_events`.

#### [NEW] [pipeline.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/services/pipeline.py)
* Asynchronous lifecycle processing logic (runs in `FastAPI.BackgroundTask`). Featurizes, assesses health, assigns destinations, generates Battery Aadhaar numbers, accounts for sustainability impact, and broadcasts events to WebSockets.

#### [NEW] [mock_server.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/mocks/mock_server.py)
* Hour 1 stub that serves mock JSON for the 12 routes and streams a pre-recorded WebSocket event sequence on loop, completely unblocking the frontend.

---

### [NEW] Frontend Subsystem

#### [NEW] [App.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/App.tsx)
* Main shell containing sidebar navigation (Command Center, Fleet, Sites, Impact) and the persistent top bar impact ticker.

#### [NEW] [useLiveFeed.ts](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/lib/useLiveFeed.ts)
* Custom hook supporting WebSocket streaming with an automatic HTTP polling fallback mode when `VITE_USE_POLLING=true`. Buffers events to ensure a smooth, jank-free 60fps cascade.

#### [NEW] [CommandCenter.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/CommandCenter.tsx)
* Main page: Leaflet map of India (CartoDB dark matter), scrolling Live Decision Feed cards, FleetPulse grade distribution, upload progress, and the Safety Saves counter.

#### [NEW] [BatteryDetail.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/BatteryDetail.tsx)
* Detailed view rendering the 21-character Aadhaar Passport (decoded offline), the narrative Life Story, interactive lifecycle timeline, SoH/RUL gauge panel, and SHAP explainability charts.

#### [NEW] [PublicPassport.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/PublicPassport.tsx)
* Public, read-only, mobile-optimized version of the Aadhaar Passport page resolved via QR scan.

---

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/test_smoke.py`
  - Ingests 5 sample batteries, asserts they run through the pipeline, write records to SQLite/Postgres, issue BPAN IDs, make assignments, and emit correct schemas.
- Run typechecking: `npm run typecheck` (loose tsconfig).

### Manual Verification
1. **Mock Cascade Verification:** Boot frontend pointing to the mock server, trigger ingestion, and ensure the scrolling cards, populating map markers, and counting tickers render smoothly.
2. **End-to-End Pipeline Verification:** Swap base URL to the real backend, drop the 20-row `sample_small.csv`, and assert that the battery gets written to the DB, graded by `model_v1.pkl`, matched to a seeded site, and displays a dynamic "Life Story".
3. **Aadhaar QR Validation:** Scan the QR code rendered on the passport page using a phone; verify it resolves to the public read-only page hosted on Railway.
4. **Replay Validation:** Wreak havoc on the database, trigger `POST /demo/reset`, and run `POST /demo/replay` to verify the backup playback runs identically.
