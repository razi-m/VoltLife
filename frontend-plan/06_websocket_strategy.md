# 06 — WebSocket Strategy (frontend side)

Server side is backend-plan/07 (one broadcast channel, 4 event types, shapes frozen in docs/04 §3). The frontend's job: make 847 events feel alive without ever stuttering or lying.

## LiveFeedProvider — the single stream owner

```
mode = VITE_USE_POLLING ? polling : websocket        // both paths MANDATORY, built day one
websocket: ws(s)://<base>/ws/feed, JSON events
polling:   GET /jobs/{id} every 1000 ms → recent_events (identical shapes — backend ring buffer)
```

Internals: incoming events → bounded queue → **rAF drain at ~6 events/s** (server paces the story at ~0.15 s/event; the drain smooths bursts after reconnects) → dispatch to subscribers. Feed list capped at 100 DOM nodes (older cards drop off — the feed is a window, not a log; P6 is the log).

## Event handling per type

| Event | UI reactions |
|---|---|
| `assessment` | BatteryMarker pops (grade color) · feed card prepends (ASSESSED chip) · FleetPulse/GradeDonut increment · grade-D: SafetySaves count + reason aggregation (derived #2) |
| `deployment` | DeploymentArc animates from→to · feed card gains ASSIGNED chip + site + score · site gauge nudges |
| `impact` | ImpactTicker + hero counters animate to new values (count-up from previous, 400 ms) |
| `job_done` | progress bar completes · "847 decided" hero state · invalidate `['batteries']`, `['impact']`, `['sites']` — REST truth reconciles everything the stream painted |

Ordering: the backend guarantees assessment-before-deployment per battery (backend-plan/07); the frontend may therefore key arcs/chips off prior assessment state without defensive buffering — but unknown event types are ignored silently (forward compatibility, not a crash).

## Simulation progress

`processed/total` arrives via `impact` events (every 5th) and `useJob` polling — JobProgress renders whichever is fresher; ETA = simple linear extrapolation, labeled "~".

## Reconnect & failure ladder (client side of the docs/02 chain)

WS `onclose` → exponential retry (1s, 2s, 4s, max 3) while showing a quiet "reconnecting" dot on SystemStatus — never a modal. On reconnect: one `useJob` refetch backfills the gap from the ring buffer (≤20 events lost visual motion, zero lost truth — REST holds state). Three failures → automatic flip to polling mode for the session (same provider interface; subscribers never know). Replay mode (`/demo/replay`) is invisible to the frontend by design — same events, same pipe.

## The "feels alive" checklist (acceptance criteria, not vibes)

Counters never jump backwards · no event renders twice (event keying: `type+battery_id+processed`) · cascade runs 60 fps on the demo laptop at 1920×1080 with the projector mirroring (test THIS, not just the laptop panel) · feed motion continues smoothly across a WS drop (queue drains while reconnecting) · zero motion when idle except the status dot — stillness when nothing happens is what makes motion mean something.
