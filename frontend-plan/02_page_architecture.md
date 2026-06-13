# 02 — Page Architecture

**The blueprint (docs/product_experience_blueprint.md) is the frozen page inventory — 7 routes. The five mandated "experience pages" map onto it as follows; no new routes were invented where a view-state suffices.**

| Mandated experience page | Blueprint route | Resolution |
|---|---|---|
| 1. Mission Control | P1 `/` Command Center | same page; "Mission Control" is its display name |
| 2. Battery Intake & Assessment | P4 `/upload` + auto-navigate to P1 | upload + preview + **Run Demo button** live on P4; the assessment *feed* is P1 (you launch, you land in Mission Control watching it) |
| 3. Deployment Command Center | P1 with **FeedFilter = Deployments** | a view mode, not a page: filter chip switches the Live Decision Feed to deployment events + shows site demand gauges; URL state `/?feed=deployments` makes it linkable for Q&A |
| 4. Battery Aadhaar | P2 `/battery/:id` (+ P5 `/b/:aadhaarId` public) | unchanged |
| 5. Impact Center | P3 `/impact` | unchanged, India 2030 hero |

(P6 `/fleet` and P7 `/sites` remain Tier 2/3 per blueprint — Q&A depth, not demo path.)

## Per-page sections (mandated content → components, all data sources frozen)

**P1 Mission Control** — hero strip: **National Battery Counter** ("847 batteries processed today" = job `processed/total`; idle state shows lifetime count) + SystemStatus chip (from `/healthz`) · IndiaMap (mini in hero, dominant in body) · Live AI Decision Feed (FeedFilter: All / Assessments / Deployments) · FleetPulse grade distribution · Active deployments count + arcs · ImpactTicker (persistent top bar) · SafetySavesCard. *Answers "what is this?" in 20 seconds by showing a country, a stream of decisions, and a counter — no copy required.*

**P4 Intake & Assessment** — Dropzone (CSV) · **Run Demo button** (posts the bundled `sample_fleet.csv` asset to `/ingest` — zero new endpoints, one guaranteed-clean demo trigger) · telemetry preview table (5 rows) · schema check + reject report · LAUNCH → navigate to P1. Per-battery assessment details (ID, SoH, RUL, confidence, grade, explainability) render on P1 feed cards and in full on P2.

**P1 / Deployments view** — deployment event cards (site, score /100, 3 reasons, carbon per pack) · deployment queue = `recommended` status rows (autonomy story) · site demand gauges · per-event carbon impact. *Judges must see: the system is deciding — every card leads with the reason, not the destination.*

**P2 / P5 Battery Aadhaar** — AadhaarPassport (QR, 21-char decode animation, BPAN static/dynamic panels) · LifeStory · LifecycleTimeline · HealthPanel (SoH gauge, RUL ± band, confidence) · ExplainabilityPanel (SHAP bars) · DeploymentCard + counterfactual runner-up. Health history = all `assessed` events on the timeline; deployment history = all `deployment_assigned` events (append-only tables make history free).

**P3 Impact Center** — hero counters (MWh unlocked*, tCO₂e, batteries diverted) · grade donut · site-type breakdown · **Mining Avoided panel** (Li/Co/Ni kg — derived #3) · **Circularity Score dial** (derived #4) · methodology footnote · **India 2030 hero finale** (derived #1). *projected-lifetime label mandatory (judge_attacks #76).

## Navigation relationships

Sidebar: Mission Control · Fleet · Sites · Impact. Primary CTA: "+ Ingest Fleet" → P4. Flow edges: P4 →(launch)→ P1 →(card/marker click)→ P2 →(QR)→ P5 (judge's phone) · P1 →(finale nav)→ P3. P5 is unlisted (QR-only). Back-navigation always returns to P1 — Mission Control is home, structurally and narratively.
