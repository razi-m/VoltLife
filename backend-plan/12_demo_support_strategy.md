# 12 — Demo Support Strategy (backend → each demo beat)

The demo script (docs/09) is the requirement spec; this maps every beat to the machinery that guarantees it.

| Demo beat | Backend machinery | Guarantee mechanism |
|---|---|---|
| **Upload → LAUNCH** (0:20) | `/ingest` + reject report + job spawn | exact rehearsed CSV; 409 guard blocks accidental double-launch |
| **Live grading cascade** (0:35) | pipeline pacing (PACE_S) + WS `assessment` events + `to_thread` smoothness | 847 × 0.15 s ≈ 2 min; QA harness pre-validates every number that will appear (ml-plan/14) |
| **Live routing / arcs** | WS `deployment` events with `from`/`to` coords; assessment-before-deployment ordering | sequential pipeline — ordering is structural |
| **Safety Saves beat** | grade-D assessments stream with flag reasons; D→recycler-only gate | gate lives in `recommend()` AND `deployment.py` (belt + suspenders) |
| **PHC/school deployment quotable** | seeded health-center + school sites with min grades | seed mix ensures ≥1 PHC assignment fires mid-cascade |
| **Impact counters** | WS `impact` every 5th battery + final | counters land in QA-checked plausible ranges (09_*) |
| **Aadhaar reveal** (1:45) | `GET /batteries/{id}/aadhaar`: decoded ID, timeline, life_story | hero battery pre-selected from QA report's clean-A list (docs/09) |
| **QR → judge's phone** | public `GET /aadhaar/{id}` on Railway + PUBLIC_BASE_URL | printed card fallback (offline script) if deploy is down |
| **Impact Center + India 2030 finale** (2:25) | `/impact/summary` correctness; finale math is frontend-side | backend's job = the multiplicand is right; ranges QA-gated |
| **"Want to see it raw?"** (Q&A) | PACE_S=0 relaunch after `/demo/reset` | proves 847 < 5 s compute (judge_attacks #35) |

## The fallback ladder, backend view (every rung built + rehearsed)

1. WS fails → polling fallback serves the **same ring buffer** (zero behavioral delta).
2. Live inference suspect → `/demo/replay` streams the H24 recording through the **same broadcast path** (pixel-identical).
3. Railway down → full stack on localhost (primary anyway, docs/02); QR beat degrades to printed card.
4. Everything down → backup video (recorded after a green QA report, docs/12).

## Pre-flight contract (15 min before stage, docs/09 — backend items)

`/healthz` shows `ok + model_version + db:up` → `POST /demo/reset` → confirm sites seeded (25 rows) → confirm hero battery ID resolves on the public route from a phone → PACE_S confirmed at 0.15 → replay file present (`409 no_replay_file` must NOT be possible on demo day).

## Rehearsal invariant

Reset → launch → identical cascade, twice in a row, same numbers. Determinism end-to-end (fixed seeds in ML, sequential pipeline, template explanations) is what makes the demo *rehearsable* — treat any run-to-run variance as a P0 bug.
