# 10 — Backend Folder Structure & Build Order

Extends docs/08 (frozen tree) with the Alembic baseline, shared constants, and scripts — no structural redesign. `workers/` from the prompt's example maps to `services/pipeline.py` (one background worker, not a folder of them).

```
backend/
├─ app/
│  ├─ main.py                    # init, CORS, WS route, startup: alembic head → load bundle → seed
│  ├─ core/
│  │  ├─ config.py               # env: DATABASE_URL (sqlite fallback), DEMO_KEY, MODEL_PATH,
│  │  │                          #      PACE_S, PUBLIC_BASE_URL, AUTONOMY_MODE
│  │  ├─ db.py                   # engine/session
│  │  └─ events.py               # WS manager + broadcast + ring-buffer hook (07_*)
│  ├─ models/orm.py              # 6 tables (docs/03) + nullable event_hash
│  ├─ schemas/
│  │  ├─ api.py                  # Pydantic mirrors of docs/04 — copy shapes EXACTLY
│  │  └─ ml.py                   # mirror of ml-plan/01 assess()/recommend() returns (seam validation)
│  ├─ api/                       # ingest · jobs · batteries (incl. both aadhaar routes) · sites · impact · demo
│  ├─ services/
│  │  ├─ ingestion.py  ·  pipeline.py  ·  deployment.py  ·  aadhaar.py  ·  impact.py
│  ├─ ml/                        # VENDORED from ml repo (ml-plan/15): features, predictor, recommend,
│  │  │                          #   confidence, explain, grade, stub_predictor, models/model_v1.pkl
│  └─ seed/
│     ├─ sites.json              # ~25 sites incl. school_backup + health_center_backup (05_*)
│     ├─ sample_fleet.csv        # 847 (from ml generate_fleet.py)
│     ├─ replay_results.json     # recorded at H24 (08_*)
│     └─ seed.py                 # idempotent
├─ shared/constants.py           # THE constants file (integration_validation §7) — ML mirrors it
├─ db/migrations/                # Alembic: ONE baseline revision, frozen after H2
├─ scripts/make_qr_card.py       # offline hero-card QR (06_*)
├─ mocks/mock_server.py          # day-1 stub for Zaki (docs/04) — built FIRST
├─ tests/test_smoke.py           # ingest 5 → assessed+assigned+aadhaar'd+events; THE integration test
├─ requirements.txt              # pinned: fastapi, uvicorn, sqlalchemy, alembic, psycopg2, pydantic,
│                                #   scikit-learn/shap/joblib (== ml repo pins), python-multipart
└─ railway.toml
```

## Build order (Antigravity sequence; aligns with docs/08 + docs/10 milestones)

| Step | Deliverable | Done when |
|---|---|---|
| 1 | mocks/mock_server.py | Zaki unblocked: every endpoint serves docs/04 literal JSON; WS loops 30 events |
| 2 | core/ + models + alembic baseline + seed | tables exist on fresh DB with one command; sites seeded; generic JSON/DateTime types only + `create_all()` branch for sqlite URLs verified (S1) |
| 3 | schemas (api.py + ml.py) | Pydantic mirrors compile; sample payloads from docs/04 validate verbatim |
| 4 | ingestion + GET endpoints | sample_fleet.csv → 847 rows; list/detail/sites/impact return real DB data |
| 5 | events.py + pipeline w/ **stub_predictor** | full cascade end-to-end on stub; WS + ring buffer + polling identical |
| 6 | deployment + aadhaar + impact services | smoke test green: 5 batteries fully lifecycle'd |
| 7 | real model swap (one import) | H10–12 milestone M2; outputs validated by schemas/ml.py |
| 8 | demo/reset + demo/replay + healthz | reset <1 s; replay pixel-identical; preflight checkable |
| 9 | Railway deploy + PUBLIC_BASE_URL | public passport QR resolves from a phone |

## Definition of done (whole backend)

`test_smoke.py` green · 847 unpaced < 5 s (with `asyncio.to_thread`, 08_*) · `/healthz` reports model_version · `demo/reset` + relaunch produces an identical cascade twice in a row (the rehearsal invariant).
