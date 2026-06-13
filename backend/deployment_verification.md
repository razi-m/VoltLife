# Deployment Verification — Clean Clone Procedure

Run this on ANY machine before trusting it for deploy or demo (second laptop, Railway, post-pull).
Total time: ~3 minutes. Motivation: stale `__pycache__` bytecode and file-sync lag can make a broken
tree look healthy (and vice versa) — a clean clone kills both illusions.

## 1. Fresh clone & environment

```bash
git clone <repo-url> voltlife-verify && cd voltlife-verify/backend
python -m venv .venv && source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
find . -name "__pycache__" -type d -exec rm -rf {} +    # paranoia, costs nothing
```

## 2. Startup verification

```bash
uvicorn app.main:app --port 8000 &
sleep 3
curl -s localhost:8000/healthz
# EXPECT: {"ok": true, "model_version": "v1.2-stub", "db": "up"}
```

Startup log must show: tables created, **27 demand sites seeded**, no replay re-seed warning
(the committed `replay_results.json` is a real 1,865-event recording, ~733 KB — if startup says
"missing or empty", the clone is bad).

## 3. Database verification

```bash
python -c "
from app.db.database import SessionLocal
from app.models.orm import Site
db = SessionLocal(); print('sites:', db.query(Site).count())"   # EXPECT: sites: 27
```

Postgres path: set `DATABASE_URL=postgresql://...` before startup — `init_db()` runs idempotent
`create_all(checkfirst)` on both engines. SQLite (default) needs nothing.

## 4. Test execution

```bash
python -m pytest tests/ -q
# EXPECT: 11 passed  (conftest.py provides one shared test engine; both modules run together)
```

## 5. Smoke / demo verification

```bash
# Full 847-battery cascade against the committed fleet (PACE_S=0 for speed):
PACE_S=0 uvicorn app.main:app --port 8000 &
curl -s -X POST localhost:8000/api/v1/batteries/ingest -F "file=@app/seed/sample_fleet.csv"
# EXPECT: {"job_id": "...", "accepted": 847, "rejected": 3, ...}  (3 rejects are intentional demo rows)
sleep 25
curl -s localhost:8000/api/v1/impact/summary
# EXPECT (committed seed data): ~1314 MWh, ~176 t CO2, deployed 720, recycled 127, stranded 0
#         by_grade: S 42 / A 127 / B 297 / C 254 / D 127
curl -s -X POST localhost:8000/api/v1/demo/reset -H "X-Demo-Key: $DEMO_KEY"
# EXPECT: {"status": "success", ...}
curl -s -X POST localhost:8000/api/v1/demo/replay -H "X-Demo-Key: $DEMO_KEY"
# EXPECT: 202; dashboard/WS clients see the recorded cascade stream
```

## 6. Environment variables (see .env.example)

| Var | Default | Purpose |
|---|---|---|
| DATABASE_URL | sqlite:///./voltlife.db | Postgres URL on Railway; SQLite fallback locally |
| DEMO_KEY | volt_secret_key | header guard for /demo/reset and /demo/replay |
| PUBLIC_FRONTEND_URL | http://localhost:3000 | QR target base — MUST be the deployed frontend before the demo |
| PUBLIC_BASE_URL | http://localhost:8000 | backend's own public URL |
| PACE_S | 0.15 | cascade pacing (0 = unpaced) |
| AUTONOMY_MODE | true | deployments auto-approve vs queue as recommended |
| MODEL_PATH | app/ml/models/model_v1.pkl | ML bundle path (stub until ML phase) |

## Pass criteria (all of)

healthz ok ✓ · 27 sites ✓ · 11/11 tests ✓ · 847 accepted / 3 rejected ✓ · 0 stranded ✓ ·
reset 200 ✓ · replay streams ✓. Any failure → do not deploy from this machine; diff against a known-good clone.
