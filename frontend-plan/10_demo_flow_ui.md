# 10 — Demo Flow UI (screen-by-screen, action-by-action)

The 8 mandated steps, mapped to exact UI actions and expected visual responses. Spoken lines: docs/09. Total ≤ 3:00. Driver: Zaki (clicks), Zaid (voice). Every step lists its fallback.

| # | Step | Driver action | Expected visual response | Fallback |
|---|---|---|---|---|
| 1 | **Mission Control** (0:00) | none — page already open, reset state | dark India map, zero counters, "Awaiting fleet ingestion —", status dot green | static screenshot slide (last resort) |
| 2 | **Run Demo** (0:20) | click `+ Ingest Fleet` → P4; drag CSV (or click **Run Demo** which posts the bundled sample fleet) → preview renders → click LAUNCH | schema table all-green, 3 rejects visible in report, LAUNCH navigates to P1 | Run Demo button IS the fallback for a fumbled drag; pre-staged job_id if ingest itself fails |
| 3 | **847 enter the system** (0:35) | none — watch | JobProgress bar starts, "847" total appears, hero counter begins climbing | polling flag flip (one env toggle, rehearsed) |
| 4 | **AI assessments stream** (0:40–1:20) | hover one feed card mid-stream (pause-on-hover) | markers pop in grade colors across India; cards stream reasons-first; FleetPulse fills; Safety Saves ticks on each red card | `/demo/replay` — pixel-identical; then backup video |
| 5 | **Deployment decisions stream** (1:20–1:45) | click FeedFilter → "Deployments" for ~10 s, then back to All | arcs shoot battery→site; cards show site + score/100 + reasons; a health-center assignment appears (seeded to fire — backend-plan/12) | skip filter toggle; arcs alone carry the beat |
| 6 | **Battery Aadhaar reveal** (1:45) | press hero-battery hotkey (demo.ts constant) → P2 | passport renders: QR, ID decode animation, Life Story, timeline, SHAP bars; then judge scans QR → P5 on their phone | pre-opened P2 tab; printed QR card for the phone beat |
| 7 | **Impact Center** (2:25) | click Impact in sidebar | three hero counters count up to final values; donut + mining panel + circularity dial land | final-state screenshot slide |
| 8 | **India 2030 finale** (2:40) | click the "India 2030" hero button | overlay: batch numbers scale to 128 GWh national projection; counters roll to national scale; closing line over this screen | hard-cut static 2030 numbers (animation is optional polish) |

## Timing & rehearsal rules

Cascade pacing is server-side (PACE_S) — if dry run #1 overruns, shorten there, never by talking faster. Steps 4–5 are one continuous cascade (~70 s); the filter toggle in step 5 is the only interaction during it. The pause-on-hover in step 4 must be rehearsed — grabbing a streaming card and reading its three reasons aloud is the single highest-credibility moment available ("pick any battery — here's why").

## UI states that must exist for this flow (Antigravity checklist)

Reset/zero state for every P1 element · cascade-running states (progress, accumulating charts) · cascade-complete hero state ("847 decided") · P2 with full passport · P5 mobile layout · P3 resting + finale overlay states · all EmptyStates · the demo dev-panel (hotkeys: hero battery, reset, replay — hidden behind a keyboard chord, never visible to judges).
