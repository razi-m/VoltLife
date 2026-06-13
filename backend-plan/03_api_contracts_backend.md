# 03 — API Contracts (backend view)

**docs/04 is the frozen source of truth — request/response JSON examples live there and are not duplicated here. This doc adds the backend-side specifics: status codes, error semantics, and implementation notes per endpoint. No new endpoints. No changed shapes.**

Error envelope (all non-2xx): `{"error": {"code": "<machine_string>", "message": "<human>"}}`.

| Endpoint | Success | Error cases (code → status) | Backend notes |
|---|---|---|---|
| `POST /api/v1/batteries/ingest` | 202 + job summary | `empty_file` → 400 · `unknown_columns` → 422 · `too_large` (>5,000 rows) → 413 | Multipart CSV **or** JSON array — one handler, two parsers. Row-level failures go in `rejects[]`, never fail the batch. Spawns the pipeline BackgroundTask. UART bridge posts single-battery JSON here (01_*). |
| `GET /api/v1/jobs/{job_id}` | 200 | `job_not_found` → 404 | In-memory job registry (08_*). `recent_events` = last 20 WS-shaped events from the ring buffer — THE polling fallback; shapes identical to WS. |
| `WS /ws/feed` | 101 upgrade | close codes only | Broadcast-only; server ignores client messages. See 07_*. |
| `GET /api/v1/batteries` | 200 + paginated | `bad_filter` → 422 | Joins latest assessment + deployment site_name per row; `page_size` cap 200. |
| `GET /api/v1/batteries/{id}` | 200 | `battery_not_found` → 404 | Full object incl. `explanation_json`, `reasoning_json`. |
| `GET /api/v1/batteries/{id}/aadhaar` | 200 | 404 · `not_assessed_yet` → 409 | Passport composition (06_*); includes `life_story`, BPAN `decoded`, timeline. |
| `GET /api/v1/aadhaar/{aadhaar_id}` | 200 | 404 | Public, read-only, no auth — the QR target (blueprint P5). Same payload as above; lookup via unique index. |
| `GET /api/v1/sites` | 200 | — | Derived `remaining_kwh`, `assigned_count` computed in query. |
| `GET /api/v1/impact/summary` | 200 | — | Live aggregates (09_*). Mining-avoided & circularity score are **frontend-derived** from these fields + shared constants — payload unchanged. |
| `POST /api/v1/demo/reset` | 200 | `bad_demo_key` → 401 | Truncate fleet tables, re-seed sites, clear job registry, zero counters. Idempotent. |
| `POST /api/v1/demo/replay` | 202 | 401 · `no_replay_file` → 409 | Streams `seed/replay_results.json` through the same WS pacing — pixel-identical fallback. |
| `GET /healthz` | 200 | — (degraded fields, never 500) | `{ok, model_version, db}` — model_version from the loaded bundle (ml-plan/12). Stage pre-flight check. |

## Request validation rules (Pydantic, `schemas/api.py`)

CSV/JSON rows validate against the ingestion template (docs/04 §1): required columns present; `0 < capacity_now_kwh ≤ rated_capacity_kwh`; `cycle_count ≥ 0`; lat/lng within India bounding box (6–37 N, 68–98 E) else reject row; dates parseable; chemistry ∈ {NMC, LFP, LCO}. The 6 optional feature columns (M1: fade_rate … discharge_efficiency) are accepted when present, range-sanity-checked, and forwarded into `features_json`; absent → NaN, never a reject. Every reject carries `{row, reason}` — the reject report is a demo-credibility feature (judge_attacks #22), not plumbing.

## Compatibility statement

Audited against docs/04 + integration_validation §2: 12 routes, zero additions, zero shape changes, zero renames. The only contract-adjacent items — `life_story`, public aadhaar route — were already added to docs/04 in earlier rounds (F5/F7).
