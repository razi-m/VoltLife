# 12 — Integration Notes (frontend perspective)

Master matrix: integration_validation §2 (authoritative). This doc states the frontend's dependencies and **every assumption**, each one independently verifiable.

## On the backend (backend-plan/)

- All 12 routes per docs/04, error envelope on every non-2xx (03_*).
- `recent_events` (polling) shaped identically to WS events — one ring buffer (backend-plan/07). *Assumption verified by:* mock server uses the same fixture for both.
- Assessment-before-deployment ordering per battery (backend-plan/07) — arcs key off prior marker state.
- Server-side pacing (~0.15 s/event) — frontend drains at 6/s and assumes no sustained burst >20 events.
- `PUBLIC_BASE_URL` correct on deploy — P5 QR beat depends on it; printed-card fallback exists.
- Mock server available H1–2 (backend-plan/10 step 1) — Zaki's entire day one runs on it.
- Demo routes guarded by `VITE_DEMO_KEY` header; dev-panel only.

## On ML outputs (ml-plan/01 — consumed via backend, never directly)

- `grade ∈ S|A|B|C|D` (D rendered "Recycle" — GradeBadge owns the mapping, once).
- `confidence ∈ high|medium|low` (low rendered "Under review" + never has site recommendations).
- `reasons` exactly 3 non-empty strings; `explanation_json` 3–6 structured entries with `label/shap/impact` (ShapBar contract).
- `rul_range[0] ≤ rul_years ≤ rul_range[1]`, years ≤ 8.0 — RULRange renders without defensive clamping because ml-plan/14 QA guarantees it upstream. *The frontend trusts QA'd invariants rather than re-validating — by design.*
- Determinism: same battery always renders the same story (rehearsal safety).

## On contracts & docs

`lib/types.ts` mirrors docs/04 + ml-plan/01 by hand; any mismatch discovered = contract bug escalated to Zaid, never patched locally. Derived-data whitelist (4 items) per integration_validation §4 + backend-plan/09; constants mirrored from `shared/constants.py` into `lib/constants.ts` — drift between the two files is checked once at integration (print both, diff by eye — 8 numbers).

## On WebSockets

Single channel, broadcast-only, no client messages; unknown event types ignored; reconnect ladder ends in polling mode (06_*). Venue assumption: WS may die — therefore both paths are built day one and the flag flip is rehearsed, not theoretical.

## Assumption register (the complete list, for pre-flight)

1. Mock server up before frontend work starts (H1).
2. Real backend swap = env change only (no code).
3. `sample_fleet.csv` asset identical to backend's seeded copy.
4. Hero battery ids in `demo.ts` match the seeded fleet (set after H24 QA report).
5. Demo laptop renders 60 fps at projector resolution.
6. Stitch tokens by H18 or placeholder ships (08_* deadline).
7. CartoDB tiles reachable, or tile cache pre-warmed by panning during setup (docs/12).
8. Judge's phone can reach the Railway deploy for P5 (else printed card).

## Audit verdict vs the four mandated documents

ml_output_contract: all fields consumed as specified, none recomputed — **PASS**. backend_architecture (backend-plan/01): frontend touches only routes + WS, no internal coupling — **PASS**. api_contracts (docs/04): zero modifications, zero inventions — **PASS**. integration_validation: §2 consumer column fully implemented; derived-data list extended by zero items — **PASS**.
