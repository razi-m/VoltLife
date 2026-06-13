# 10 — Execution Plan: Tonight + 36 Hours (Owner: Zaid)

**Reality check:** HackPrix S3 runs Jun 13–14 as a "2-day" event; last season was 36h. The exact hacking window may be shorter. **At kickoff, confirm the window.** If it's ~24h, apply the cut-lines immediately (bottom of this doc). Prep is allowed — tonight is Hour −12.

## TONIGHT — June 12 (Hour −12 → −2)

| Who | Must finish tonight |
|---|---|
| Zaid | Repo + branch rules; commit docs/; freeze API contract v1 (doc 04); sites.json drafted; Railway + Vercel accounts ready; print/save BPAN + NITI Aayog source tabs |
| Razi | Datasets downloaded locally; parser + features + **model_v1.pkl trained & validated (record the MAE!)**; `predictor.py`; fleet generator + `sample_fleet.csv` (847) + `sample_small.csv` |
| Farhan | Python env + FastAPI hello-world deployed to Railway once (dependency dry run); mock server written (doc 04); skim docs 03/06/08 |
| Zaki | Vite + Tailwind + tokens scaffold; Leaflet dark map rendering India; Recharts + qrcode.react installed; skim docs 04/07/09 |
| All | Sleep ≥ 6 hours. Non-negotiable. Tired teams lose demos, not time. |

## Event — hour by hour

**H0–1 · Kickoff.** Confirm hacking window + judging format/time. Re-read cut-lines. Contracts re-frozen. Everyone states their H12 deliverable aloud.

**H1–6 · Parallel sprint 1** — *Farhan:* core/db/orm, ingestion + seed, mock server live for Zaki. *Zaki:* AppShell, CommandCenter layout, useLiveFeed (both paths) on mocks. *Razi:* predictor integration test w/ Farhan's `features.py`, edge-case sweep on synthetic fleet (no absurd outputs), starts CALCE expansion. *Zaid:* sites.json final, demo narrative v1, floats between blockers.

**✅ M1 (H6):** mock-driven frontend shows a fake cascade; real ingestion writes 847 rows to Postgres.

**H6–12 · Parallel sprint 2** — *Farhan:* pipeline with stub-assess → WS broadcasting real DB rows. *Zaki:* FleetTable + DecisionCard polish + map markers from real WS. *Razi:* hands over model bundle; pair-swap stub→real with Farhan (H10–12). *Zaid:* Railway deploy of real backend, starts pitch deck.

**✅ M2 (H12):** END-TO-END — real CSV → real model → DB → WS → map pin + feed card. *The project exists.* Celebrate for exactly 5 minutes.

**H12–18 · Sprint 3** — *Farhan:* deployment engine + impact service + aadhaar service. *Zaki:* BatteryDetail (passport, timeline, explainability bars). *Razi:* confidence calibration; templates English pass; starts UART **only if** M2 was on time. *Zaid:* deck v1 done; demo script rehearsal #0 (talk-over, no clicks).

**✅ M3 (H18):** full pipeline incl. deployments + aadhaar end-to-end on 50 batteries. **Decision point: behind? → cut SitesView now (doc 12 R1).**

**H18–24 · Sprint 4** — *Farhan:* `/demo/reset` + `/demo/replay` + smoke test green. *Zaki:* arcs, counters, FleetPulse, impact page. *Razi:* hero-battery selection, output QA on all 847, UART go/no-go at H24. *Zaid:* **dry run #1 at H22** (full clicks, timed). Sleep shifts H14–22 (2×2 staggered, 3–4h each).

**✅ M4 (H24):** 847-battery cascade runs clean in ≤ 2.5 min. Replay mode works. UART verdict rendered.

**H24–30 · Polish only.** Visual pass (spacing, empty states, number formatting), pacing tune (PACE_S), seed-number sanity (counters end plausible), deck v2, Q&A drill #1 (doc 11 — Zaid grills, everyone answers their domain). **H30: FEATURE FREEZE. Hard.** Record backup video immediately after freeze.

**H30–36 · Demo discipline.** Dry runs #2 and #3 (one on projector if accessible, one on hotspot). Devfolio submission (doc 12 checklist) by H33 — never at the deadline. Q&A drill #2. Reset → pre-flight → stage.

## Integration milestones (the contract between teammates)

| ⏱ | Milestone | Definition of done |
|---|---|---|
| H6 | M1 | Mock cascade renders; 847 real rows in DB |
| H12 | M2 | One real battery: CSV→model→WS→pixel |
| H18 | M3 | + deployment + aadhaar, 50 batteries clean |
| H24 | M4 | 847 full cascade + replay fallback + UART verdict |
| H30 | FREEZE | Code stops; theatre begins |
| H33 | SUBMITTED | Devfolio done, video uploaded |

Missing a milestone by >2h triggers the matching cut-line. Zaid enforces; no debate mid-event — the debate happened in this doc.

## Cut-lines (pre-agreed, in order)

1. **SitesView page** → site data shows only on map tooltips
2. **UART hardware** → never mention it
3. **Live WebSocket** → polling flag (Zaki built both day one)
4. **Live inference on stage** → `/demo/replay` (pixel-identical)
5. **CALCE second dataset** → NASA-only, adjust Q&A answer
6. **Upload wizard on stage** → pre-staged job + narration
7. Never cut: health engine, deployment reasons, Aadhaar passport page, impact counters, **backup video**

## If the window is ~24h, not 36

Apply cut-lines 1–2 at kickoff; compress sprints 3–4 into one (deployment engine simplifies to gates + distance only); freeze at H20; dry runs at H21/H23. The demo script is unchanged — that's the point of building demo-first.
