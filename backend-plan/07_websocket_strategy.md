# 07 — WebSocket Strategy

## Topology: one channel, broadcast-only

`WS /ws/feed` — every connected client gets every event. No rooms, no subscriptions, no client→server messages (server ignores them). The demo has one dashboard and a judge's phone; channel multiplexing is enterprise cosplay at this scale.

`core/events.py` = the connection manager: `connect/disconnect` bookkeeping + `async broadcast(event: dict)` that fans out with per-client try/except (one dead phone connection must not stall the cascade — send failures silently drop that client).

## Event vocabulary (frozen — docs/04 §3, shapes verbatim)

| type | When emitted | Drives |
|---|---|---|
| `assessment` | after assess() persists | marker pop, feed card, FleetPulse, Safety Saves (grade-D reasons) |
| `deployment` | after deployment persists | arc animation, feed card, site gauge |
| `impact` | every 5th battery + at job end | ImpactTicker, Impact Center counters |
| `job_done` | pipeline completes | progress bar completion, "847 decided" state |

**Ordering guarantee:** per battery, `assessment` is always broadcast before its `deployment` (the pipeline is sequential — the guarantee is free, but Antigravity must not parallelize it away). Events also append to the in-memory **ring buffer (last 20)** that `GET /jobs/{id}` serves — this single design point makes polling and WS pixel-identical.

## Live-feel mechanics

Pacing lives server-side (`PACE_S=0.15` env, docs/02): 847 × 0.15 ≈ 2 min of cascade. The frontend's useLiveFeed drains its queue at ~6 events/s with rAF (docs/07) — server paces the story, client smooths the frames. Tuning demo length = one env var, no redeploy of anything else.

## Failure & reconnect

- Client reconnect: on WS drop, useLiveFeed re-opens; missed state recovers via one `GET /jobs/{id}` (progress + recent events) — no server-side replay-from-offset machinery needed at this scale.
- Venue Wi-Fi kills WS entirely → `VITE_USE_POLLING=true` (frontend flag, built day one): 1s polls of the same ring buffer. Identical shapes, identical UI (docs/02 fallback chain).
- `POST /demo/replay` feeds pre-computed events through the **same** broadcast + pacing path — the fallback isn't a second implementation, it's the same pipe with a different source.

## Anti-scope

No socket.io, no Redis pub/sub, no per-event acks, no compression config, no heartbeat protocol beyond the framework's defaults. Native FastAPI WebSocket + one manager class. ~60 lines total.
