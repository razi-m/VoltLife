# 11 — Integration Notes (backend perspective)

The master dependency matrix lives in docs/integration_validation.md §2 and remains authoritative. This doc states the backend's obligations toward each neighbor + the deltas introduced by this planning round.

## Frontend dependencies (what the backend owes Zaki)

- Mock server on day one (build step 1 — before any real backend code).
- Every blueprint page's endpoints live by M2 (P1: WS/jobs+sites+impact · P2: detail+aadhaar · P3: impact · P4: ingest · P5: public aadhaar · P6: list · P7: sites).
- WS events and `recent_events` polling shapes **identical** (one ring buffer feeds both) — Zaki's dual-path useLiveFeed depends on this equivalence.
- `PUBLIC_BASE_URL` correct on the deployed instance, or the judge's-phone QR beat dies (06_*).

## ML dependencies (what the backend consumes, never reimplements)

Vendored files: `features.py`, `predictor.py`, `recommend.py` (+ confidence/explain/grade composed inside predictor), `models/model_v1.pkl`. Seam validated by `schemas/ml.py` at runtime and by identical version pins in both requirements files (ml-plan/12). Non-recalculation rule: 04_* — structurally enforced (no grade/RUL/confidence math exists anywhere in `services/`).

## Database dependencies

Schema = docs/03 verbatim + nullable `event_hash` (additive, F10). Alembic baseline only; schema frozen after H2. One-transaction-per-battery (02_*). Derived values (`remaining_kwh`, `assigned_count`) computed in queries, never stored.

## API & WS dependencies

docs/04 frozen: 12 routes, 4 WS event types, error envelope — zero additions this round (03_* compatibility statement). UART enters via existing ingest. Mining-avoided + circularity score = frontend-derived (09_*), payload untouched.

## Deltas introduced by backend-plan (all additive, synced into the pack)

| Delta | Where synced |
|---|---|
| site types `school_backup`, `health_center_backup` (+~5 seed sites) | docs/06 registry · ml-plan/10 suitability map |
| Alembic baseline replaces "skip Alembic" | docs/08 |
| `event_hash` nullable column (feature-flagged) | noted in 02_*; docs/03 unchanged DDL + comment acceptable at implementation |
| `AUTONOMY_MODE` config flag (recommended→approved auto-advance) | 05_*; no endpoint change |
| stub_predictor as a named, generated artifact | ml-plan/15 already lists vendoring; build step 5 |

## Audit verdict vs the four mandated documents

ml_output_contract (ml-plan/01): consumed verbatim, validated at seam — **PASS**. integration_validation: §2 matrix unchanged, deltas logged as F10 — **PASS**. product_experience_blueprint: all 7 pages served, demo journey fully backed — **PASS**. api_contracts (docs/04): zero modifications — **PASS**.
