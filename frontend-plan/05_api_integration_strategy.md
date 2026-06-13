# 05 — API Integration Strategy

**docs/04 is frozen; the consumer-side matrix in integration_validation §2 is authoritative. The frontend consumes exactly those 12 routes — zero invented endpoints, zero assumed fields.**

## Endpoint → TanStack Query map

| Hook | Endpoint | Key | Staleness / refetch |
|---|---|---|---|
| `useIngest()` (mutation) | `POST /batteries/ingest` | — | on success: store `job_id`, navigate to P1 |
| `useJob(jobId)` | `GET /jobs/{id}` | `['job', id]` | refetchInterval 1000 **only when** polling mode or job running |
| `useBatteries(filters)` | `GET /batteries?…` | `['batteries', filters]` | staleTime 5 s during cascade; invalidated on `job_done` |
| `useBatteryDetail(id)` | `GET /batteries/{id}` | `['battery', id]` | staleTime ∞ until events touch that id |
| `useAadhaar(id)` / `usePublicAadhaar(aid)` | both aadhaar routes | `['aadhaar', …]` | staleTime ∞ (passports don't change mid-demo) |
| `useSites()` | `GET /sites` | `['sites']` | invalidated every 25 deployment events (gauge freshness) |
| `useImpact()` | `GET /impact/summary` | `['impact']` | initial load + `job_done`; live values come from WS events, not refetching |
| `useDemoReset()` / `useDemoReplay()` (mutations) | demo routes | — | demo-key header from env; never rendered in normal UI (keyboard-shortcut dev panel) |
| `useHealth()` | `GET /healthz` | `['health']` | refetchInterval 30 s → SystemStatus chip |

Request flow per page = blueprint P-table (P1: job+sites+impact+stream · P2: detail+aadhaar · P3: impact · P4: ingest · P5: public aadhaar · P6: list · P7: sites).

## Error handling (the envelope is part of the contract)

`lib/api.ts` parses `{"error": {code, message}}` on non-2xx into a typed `ApiError`. Policy by class: **404** on P2/P5 → full-page "Passport not found" state (a judge may scan a stale QR — this state must look intentional) · **401 bad_demo_key** → dev-panel toast only · **422/400 on ingest** → inline on P4 (schema table highlights the offending columns; reject report rendered as its own table — it's a feature, not an error) · **409 job_already_running** → toast "A cascade is already running" + navigate to P1 · **network failure** → SystemStatus chip degrades + queries retry (TanStack default backoff, max 2); the UI never white-screens — every page has its EmptyState.

## Mock-first development (unchanged commitment)

Day one runs entirely against `mocks/mock_server.py` (backend-plan/10 step 1) — base URL env swap at integration (docs/04 mock plan). `lib/types.ts` is written against docs/04 examples on day one, so the mock and the real backend are interchangeable by construction.

## Demo-day data assumptions (each one verified at pre-flight)

`VITE_API_BASE` points at localhost stack · sample_fleet.csv bundled as a static asset for RunDemoButton (the file POSTs through the normal ingest path — same pipeline, guaranteed-clean rows) · hero battery id hardcoded in a `demo.ts` constants file (id + aadhaar_id) so the Aadhaar reveal is one keystroke, never a search.
