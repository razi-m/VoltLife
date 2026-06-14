# VoltLife — Features Guide

*What the current application does and how it works. 5-minute read.*

---

## 1. What is VoltLife?

VoltLife is a battery lifecycle decision system. You upload the operating data of retired EV batteries; the system assesses each one, grades it, decides where it should go next (solar storage, microgrid, recycler, etc.), gives it a permanent digital identity (Battery Aadhaar), and tracks the environmental impact of every decision — all automatically and in real time.

The AI does the judging: it predicts each battery's health and remaining life from its data, with a confidence level and plain-language reasons. Rules sit on top for safety: a dangerous battery can only go to a certified recycler, no exceptions.

Everything happens live on a dashboard: batteries appear on a map of India, decisions stream past as cards, and impact counters climb as the batch is processed.

## 2. Current Application Workflow

```
Battery Upload          → operator uploads fleet data (CSV/JSON)
AI Assessment           → each battery's data is analyzed individually
Health Prediction       → State of Health (0–100%)
RUL Prediction          → Remaining Useful Life (years, with a low–high range)
Battery Grade           → S / A / B / C / Recycle
Deployment Recommendation → best destination chosen + ranked runner-ups, with reasons
Battery Aadhaar         → 21-character ID + QR code + lifecycle record issued
Impact Tracking         → energy unlocked, carbon saved, batteries diverted — counted live
```

One battery takes under a second. A batch streams to the dashboard at a watchable pace (~2 minutes for 847).

## 3. Current Features

### Battery Intake
* CSV upload (with column template)
* JSON upload (same endpoint)
* UART/BMS hardware support (bridge posts into the same intake — bonus feature)
* Batch upload up to 5,000 rows
* Validation with per-row reject report (bad rows skipped, never crash the batch)
* "Run Demo" button (one click loads the built-in 847-battery sample fleet)

### AI Assessment
* SoH prediction (0–100%)
* RUL prediction in cycles and years, always with a low–high range
* Confidence score (high / medium / low; low = routed to inspection, never deployed)
* Explainability: 3 plain-English reasons per battery + drill-down impact bars
* Safety overrides on raw data (overheating / high wear → Recycle, cannot be overridden)

### Grading
* 5 tiers: S (premium, top ~5%) · A · B · C · Recycle
* Grade determines which destinations a battery is eligible for
* Low confidence caps the grade and blocks deployment

### Deployment Engine
* Ranked recommendations (top 3 with scores out of 100)
* Capacity matching (battery size vs site need)
* Distance/transport optimization
* Carbon impact scoring
* Site priority weighting (rural microgrids favored)
* Hard gates: Recycle-grade → recycler only; site minimum grade and health floors
* Counterfactual view: why the runner-up site lost (optional build)
* Destination types: solar storage, rural microgrid, school backup, health center backup, industrial backup, telecom tower, EV charging buffer, street lighting, recycler

### Battery Aadhaar
* Unique 21-character ID in the government's draft BPAN format (encode + decode)
* QR code linking to a public passport page (works on any phone)
* Lifecycle timeline (manufactured → first life → retired → assessed → deployed)
* Health history and deployment history (every assessment/assignment recorded)
* Life Story: auto-generated 3-sentence battery biography
* Optional: tamper-evident event hash chain

### Sustainability Tracking
* Energy unlocked (projected lifetime MWh)
* Carbon saved (avoided new-battery manufacturing; conservative factor; deployed batteries only)
* Batteries diverted from premature recycling
* Batteries responsibly recycled (Safety Saves counter)
* Mining avoided (kg of lithium / cobalt / nickel)
* Circular Economy Score (0–100 per batch)
* India 2030 view: scales batch results to the national projection
* Methodology footnote with formulas and sources, one click away

### Real-Time Dashboard
* Live India map: battery markers (grade-colored), site markers, animated deployment arcs
* Live decision feed with filter (All / Assessments / Deployments)
* Live impact counters (always visible, top bar)
* Grade distribution chart, filling as the batch processes
* Job progress bar (n of 847 + ETA)
* WebSocket updates with automatic polling fallback

### Fleet Management
* Sortable/filterable fleet table (grade, status, destination)
* Battery detail view (full assessment + decision per battery)
* Sites registry view with demand gauges (optional build)
* Inspection queue for low-confidence batteries

### Demo & Operations
* Demo reset (wipe and reseed in one call)
* Replay mode (re-stream a recorded run, identical to live)
* Health check endpoint (system + model version status)
* Adjustable cascade pacing
* QA harness: validates all 847 outputs before any demo (no impossible numbers on screen)

## 4. Application Pages

### Mission Control (home)
* **Purpose:** the live command center — watch the system decide.
* **Components:** India map, live decision feed + filter, national battery counter, grade distribution, Safety Saves card, job progress, impact ticker, system status.

### Battery Intake
* **Purpose:** get a fleet into the system.
* **Components:** drag-and-drop upload, Run Demo button, 5-row preview, schema check, reject report, Launch button (then auto-returns to Mission Control).

### Deployment Command Center
* **Purpose:** deployment-focused view of the live feed.
* **Components:** Mission Control with the feed filtered to deployment decisions — site, score, reasons, carbon per pack, deployment queue. (A view mode, not a separate page.)

### Battery Aadhaar (battery detail)
* **Purpose:** one battery's complete identity and assessment.
* **Components:** passport (QR + decoded ID + static/dynamic data), Life Story, lifecycle timeline, health panel (SoH gauge, RUL range, confidence), explainability bars, deployment card. Public phone-friendly version opens from the QR.

### Impact Center
* **Purpose:** the scoreboard.
* **Components:** hero counters (MWh / CO₂ / diverted), grade donut, destination breakdown, mining avoided panel, circularity dial, methodology footnote, India 2030 overlay.

*(Also: Fleet table page; Sites registry page — secondary.)*

## 5. What AI Does

* **Inputs:** each battery's operating record — cycle count, capacity trend, temperatures, internal resistance, voltage behaviour, charge efficiency (14 signals total).
* **Outputs:** SoH %, RUL (years + range), confidence level, grade, 3 reasons.
* **Predictions:** current health (without physical testing) and future remaining life (including spotting batteries about to decline sharply).
* **Grades:** computed by fixed rules applied to the AI's outputs — the model predicts, policy assigns. Trained on public battery-lifetime datasets (NASA, CALCE).

## 6. What Backend Does

* **Data storage:** batteries, telemetry summaries, assessments, sites, deployments, and a full event log per battery (PostgreSQL).
* **Deployment decisions:** runs the scoring engine against the site registry, enforces safety gates, reserves site capacity, records every decision with its reasoning.
* **Battery Aadhaar:** generates IDs, builds passports, maintains the lifecycle timeline, writes the Life Story.
* **WebSockets:** streams assessment / deployment / impact events live to the dashboard; identical polling fallback if the connection fails.
* **Impact calculations:** per-battery energy and carbon math at decision time; live batch totals on demand.
* **Demo operations:** reset, replay, health check, batch background processing with progress tracking.

## 7. Demo Flow

1. Mission Control open — map dark, counters at zero.
2. Upload the 847-battery file (or click Run Demo) → preview → Launch.
3. Cascade (~2 min): markers bloom across India, decision cards stream with grades + reasons, Safety Saves ticks on Recycle batteries, arcs connect batteries to destinations, counters climb.
4. Open one battery: ID decodes, Life Story, timeline, explainability bars.
5. Judge scans the QR → passport opens on their phone.
6. Impact Center: final counters, mining avoided, circularity score.
7. India 2030 button: batch numbers scale to the national projection. Done — under 3 minutes.

## 8. Current Feature Checklist

✓ CSV / JSON batch upload (+ reject report)
✓ Run Demo one-click ingestion
✓ UART/BMS intake path (bonus, gated)
✓ SoH prediction
✓ RUL prediction with range
✓ Confidence engine + inspection queue
✓ Explainability (reasons + impact bars)
✓ 5-tier grading (S/A/B/C/Recycle)
✓ Safety overrides (non-negotiable Recycle gate)
✓ Deployment recommendations (ranked, scored, reasoned)
✓ 9 destination types incl. schools + health centers
✓ Battery Aadhaar (BPAN-format ID, encode/decode)
✓ QR code + public passport page
✓ Lifecycle timeline + health/deployment history
✓ Life Story generator
✓ Impact tracking (energy, carbon, diverted, recycled)
✓ Mining avoided + Circularity Score
✓ Safety Saves counter
✓ India 2030 scaling view
✓ Live map with grade markers + deployment arcs
✓ Live decision feed with filter
✓ Live impact counters
✓ Grade distribution + progress tracking
✓ WebSockets + polling fallback
✓ Fleet table + battery detail
✓ Sites registry (optional)
✓ Counterfactual "why not" panel (optional)
✓ Tamper-evident event chain (optional)
✓ Demo reset / replay / health check
✓ Output QA harness (no impossible numbers)

> **Status note:** this describes the application as fully specified in the planning system; items marked *(optional)* are build-if-time. Implementation happens during the hackathon.
