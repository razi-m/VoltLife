# 08 — Background Processing Strategy

## Model: one FastAPI BackgroundTask per ingestion job

No Celery, no queues — the approved stack says BackgroundTasks and the scale (≤847 sequential, paced) fits with two orders of magnitude to spare. **One job at a time**: a module-level "active job" guard rejects a second concurrent ingest with `409 job_already_running` (demo reality: there is never a second batch; the guard prevents interleaved WS streams, which would wreck the cascade).

## Job registry (in-memory, deliberately not DB)

```python
JOBS[job_id] = {status: queued|running|done|failed, processed, total,
                failed_ids: [], ring_buffer: deque(maxlen=20), started_at}
```

Ephemeral by design (integration_validation §2): a process restart loses job *progress*, not data — batteries already processed are committed per-battery (02_* one-transaction rule). Restart mid-demo → `/demo/reset` → relaunch; that's the rehearsed recovery, not a journal-replay system.

## The loop (docs/08 pseudocode is binding; key properties)

Sequential per battery: featurize → assess → decide → aadhaar → impact → broadcast(assessment, deployment) → every 5th: broadcast(impact) → `await asyncio.sleep(PACE_S)`. Per-battery try/except: log, `failed_ids.append`, battery `status='error'`, continue. The cascade is unkillable by any single row.

**Async correctness (the one real trap for Antigravity):** DB + model calls are synchronous; inside an async task they must not starve the event loop or the WS broadcasts stutter. Pattern: run the sync per-battery work via `await asyncio.to_thread(process_one, bid)`, then broadcast + sleep on the loop. This is the difference between a smooth cascade and a janky one — it is not optional polish.

## Batch sizes & timing (QA-gated, ml-plan/14)

| Fleet | Compute (unpaced) | Paced @0.15s | Use |
|---|---|---|---|
| 100 | < 1 s | ~15 s | upload-wizard rehearsals, smoke test |
| 500 | < 3 s | ~75 s | dress rehearsal variant |
| 847 | < 5 s | ~2 min | THE demo |

Dashboard updates throughout: progress via WS events + `GET /jobs/{id}`; REST list endpoints reflect committed rows mid-run (per-battery commits make partial state queryable — FleetTable fills while the cascade runs).

## Demo machinery (same subsystem)

- `POST /demo/reset`: cancel active job flag → truncate fleet tables → re-seed sites → clear JOBS → broadcast zeroed `impact`. Idempotent; < 1 s.
- `POST /demo/replay`: streams `seed/replay_results.json` (written by a `--record` flag on a real run at H24) through the same broadcast+pacing path. Source swap, not code path swap (07_*).
- Seed on startup if tables empty (docs/08) so the dashboard never demos against a void.
