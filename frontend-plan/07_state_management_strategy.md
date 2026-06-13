# 07 — State Management Strategy

Assumed stack: React + TypeScript + TanStack Query (mandated; synced to docs/07). **No Redux, no Zustand, no global store library** — the prompt's example `store/` folder maps to "TanStack cache + one context," and that's deliberate: at this app's size a store library is integration surface with no payoff.

## The four state domains and their single owners

| Domain | Owner | Contents | Rules |
|---|---|---|---|
| **API state** (server truth) | TanStack Query cache | fleet, detail, passports, sites, impact, job, health | the ONLY source of truth at rest; keys/staleness per 05_*; no copying query data into other state |
| **WebSocket state** (motion) | LiveFeedProvider (context) | bounded event queue, feed window (≤100), cascade accumulators (grade counts, safety saves, latest impact values), connection status | ephemeral by definition — wiped on `job_done` reconciliation + on demo reset; never persisted |
| **Global UI state** | one small AppContext | active job_id, feed filter, demo-mode flags, India-2030 overlay open | if it doesn't need to survive navigation, it doesn't belong here |
| **Local state** | component `useState` | dropzone hover, expanded panels, marker tooltips, count-up animation values | default home for everything; promotion to context requires a second consumer |

URL state: feed filter (`?feed=deployments`), P6 filters/sort (`?grade=A&status=assigned`) — judges' Q&A bookmarks are URLs, and refresh-safety comes free. `localStorage`: nothing (demo machines are reset between rehearsals; persistence is a liability here).

## The one hard problem: stream/REST reconciliation

During a cascade the screen is painted by events; at rest it must equal the database. Protocol (single implementation in LiveFeedProvider, not per-component):

1. Events mutate **accumulators**, never the Query cache (no `setQueryData` writes from the stream — too easy to corrupt).
2. Components render `accumulator ?? query.data` during `job.status === running`, query data otherwise.
3. `job_done` → invalidate `['batteries'] ['impact'] ['sites']` → queries refetch → accumulators cleared after refetch settles (one render-frame handoff; counters must not flicker to zero — pass previous values as count-up baselines).

The QA-checked determinism upstream (ml-plan/14) means accumulator and refetched truth agree to the digit — any visible jump at reconciliation is a bug with a known owner.

## Derived state (selectors, computed in render, never stored)

Grade distribution (from accumulator or `by_grade`) · Safety Saves count + chips (derived #2) · mining avoided + circularity (derived #3/#4, from impact values) · India 2030 scaling (derived #1) · ETA extrapolation. All four declared derivations cite their formula source in a code comment (`integration_validation §4`, `backend-plan/09`) — auditability down to the component.

## TypeScript discipline at the seams

`lib/types.ts`: `AssessmentEvent`, `DeploymentEvent`, `ImpactEvent`, `JobStatus`, `Battery`, `Assessment`, `Deployment`, `Site`, `Passport`, `ApiError` — hand-mirrored from docs/04 + ml-plan/01, with a comment linking each type to its contract section. Enums as union literals (`'S'|'A'|'B'|'C'|'D'`). These types are the frontend's copy of the frozen contracts: changing one = changing a contract = forbidden without the docs changing first.

Two ambiguities resolved explicitly (audit fixes S2/S3 — these comments MUST appear in types.ts):

```ts
// ID convention: REST resource objects carry `id` (DB primary key).
// WebSocket event payloads carry `battery_id` (referencing that same id).
// They never appear in the same payload. Example: GET /batteries/42 → { id: 42, … }
// vs WS → { type: "assessment", payload: { battery_id: 42, … } }

// Score units: `score` on the wire is a RAW 0–1 FLOAT (e.g. 0.87).
// UI displays it ×100 as an integer via format.score(): 0.87 → "87".
// Never send or store the ×100 form.
```
