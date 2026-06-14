# VoltLife (BatteryOS) — HackPrix 2026 Master Plan

> 📖 New here? Start with [project_master_guide.md](project_master_guide.md) — the whole project in plain English, 10 minutes, no technical background needed.

> India will retire **128 GWh** of batteries by 2030 (NITI Aayog). Most still hold 70–80% capacity. VoltLife is the autonomous system that decides what happens to every single one: **assess → explain → decide → identify → track → count the impact.**

**Event:** HackPrix Season 3 · Jun 13–14, 2026 · Kismatpur · 2-day in-person (last season 36h — confirm window at kickoff) · Team 2–4 · MLH partnered.

## The pack

| Doc | What | Read first |
|---|---|---|
| [01 Strategy](docs/01-strategy.md) | Positioning, hard truths, BPAN finding, real-vs-simulated, sources | **Everyone, tonight** |
| [02 Architecture](docs/02-architecture.md) | System diagram, pipeline, demo machinery, anti-scope | Everyone |
| [03 Database](docs/03-database.md) | 6-table DDL, Aadhaar ID format | Farhan, Zaid |
| [04 API Contracts](docs/04-api-contracts.md) | Frozen endpoint + WS shapes, mock plan | Farhan, Zaki |
| [05 ML Engine](docs/05-ml-engine.md) | Datasets, features, models, explainability, fleet generator, tonight's list | **Razi, tonight** |
| [06 Deployment Engine](docs/06-deployment-engine.md) | Demand registry, scoring, impact math + citations | Farhan, Zaid |
| [07 Frontend](docs/07-frontend.md) | Component tree, tokens, wow moments, useLiveFeed | Zaki |
| [08 Backend](docs/08-backend.md) | Folder structure, pipeline code, build order | Farhan |
| [09 Demo Script](docs/09-demo-script.md) | Word-for-word script, build plan, fallback per beat | Zaid, Zaki |
| [10 Execution Plan](docs/10-36-hour-plan.md) | Tonight's prep + hour-by-hour + milestones + cut-lines | **Everyone, tonight** |
| [11 Pitch & Q&A](docs/11-pitch-and-qa.md) | Pitch skeleton + 20 drilled judge answers | Everyone (H24 drill) |
| [12 Risks](docs/12-risks.md) | Risk register, fallback chain, submission checklist | Zaid |
| [Innovation Features](docs/innovation_features.md) | Top 20 ranked; **build #1–3** (Life Story, India 2030, Safety Saves) | Zaid, Zaki |
| [Product Experience Blueprint](docs/product_experience_blueprint.md) | UX source of truth: 7 pages, flows, demo journey, tiers | **Zaki, tonight** |
| [Judge Attacks](docs/judge_attacks.md) | 102 attacks with answers + drill protocol (H24/H32) | Everyone |
| [Integration Validation](docs/integration_validation.md) | Endpoint/ML/DB dependency matrix, audit findings, consistency sign-off | Zaid, Farhan |
| [Hardware Note](docs/hardware_note.md) | ESP32 rig: optional bonus, standard ingestion path, framing decision, gate rule | Razi |
| [ML Plan (15 docs)](ml-plan/) | Complete ML subsystem spec for implementation: contract, datasets, features, models, confidence, SHAP, 5-tier grading, recommendation engine, QA harness, folder structure | **Razi, tonight** |
| [Backend Plan (13 docs)](backend-plan/) | Complete backend spec for implementation: architecture, DB, endpoints, ML seam, WS, batch pipeline, Aadhaar service, sustainability engine, Antigravity guide | Farhan, Zaid |
| [Frontend Plan (13 docs)](frontend-plan/) | Complete frontend spec for implementation: pages, components, state, live feed, judge experience, demo UI, Stitch design handoff, Antigravity guide | Zaki |

**Audit-created obligation:** Farhan creates `shared/constants.py` at H1 (grade thresholds, 300 cycles/yr, 60 kg CO₂e/kWh, weights, PACE_S) — backend and ML import it; no duplicated magic numbers.

## The ten commandments

1. The government mandated the identity layer (BPAN, 2027). **We are the intelligence layer.** Say it everywhere.
2. No fabricated stats about real companies. Cited numbers + "simulated batch, real physics."
3. scikit-learn, not PyTorch. Leave-one-cell-out, not random splits. Intervals, not point estimates.
4. Contracts freeze at H1. Zaki develops on mocks; integration is a URL swap.
5. Grade D cannot deploy. That rule is the answer to every safety question.
6. Every demo beat has a tested understudy: WS → polling → replay → video.
7. Hardware is a gated bonus. It must earn stage time by passing two rehearsals.
8. Feature freeze at H30. Then theatre: dry runs, video, submission by H33.
9. One voice per Q&A answer, 20 seconds, domain owner speaks.
10. One unforgettable demo beats ten unfinished features.

## Team

| | Owns | Docs |
|---|---|---|
| **Zaid** | Architecture, contracts, integration, pitch, demo narration | 02, 04, 10, 11, 12 |
| **Farhan** | FastAPI, DB, pipeline, deployment engine, Aadhaar service | 03, 04, 06, 08 |
| **Zaki** | React dashboard, map, passport UI, demo experience | 04, 07, 09 |
| **Razi** | ML models, features, explainability, fleet generator | 05, 06 |
