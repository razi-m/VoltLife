# VoltLife — Database Migration Validation Report
## SQLite → PostgreSQL (Supabase)

**Validator:** Senior Backend Validation Engineer (Claude Opus 4.8)
**Date:** 2026-06-13
**Phase:** Post-migration full re-validation
**Scope audited:** Local working directory `VoltLife/backend` (entire tree read; `.venv` excluded)

---

## ACCESS NOTE (read first)

The GitHub remote `https://github.com/razi-m/VoltLife.git` was **not reachable** — the fetch returned empty (private repo / auth wall). This audit was therefore performed against the **local working folder only**, which was fully readable. If the remote diverges from local, re-run against the pushed commit. Every finding below is grounded in a file I actually read — nothing is assumed.

---

## VERDICT: ❌ FAIL — CHANGES REQUIRED

The migration is **incomplete and not safely wired up**. The code still resolves to **SQLite by default**, the Postgres connection is never loaded from `.env` by the app itself, JSONB is not actually applied, SSL is not enforced, and the test suite still runs on SQLite. You can connect to Supabase manually, but a plain `uvicorn app.main:app` start will silently run on a local SQLite file. That is a production-grade trap, not a finished migration.

**Blockers: 2 · High: 3 · Medium: 3 · Low/Housekeeping: 5**

---

## BLOCKERS (must fix before this can be called "migrated")

### B1 — App never loads `.env`; default path silently falls back to SQLite
`app/core/config.py`:
```python
self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voltlife.db")
```
- `python-dotenv` is **not** in `requirements.txt`.
- There is **no `load_dotenv()`** call anywhere in the codebase (grep confirmed: zero hits).
- There is **no** Dockerfile, docker-compose, Procfile, or `uvicorn --env-file` runner that injects the `.env`.

**Consequence:** unless an operator manually `export DATABASE_URL=...` into the shell before launch, `os.getenv` returns the **SQLite fallback**. The app boots green, `/healthz` reports `db: up`, and you are talking to `voltlife.db` — not Supabase. The migration is invisible-failure-prone by construction.

**Fix:** add `python-dotenv` to requirements and call `load_dotenv()` at the top of `config.py` (or run via `uvicorn --env-file .env`), AND remove the SQLite fallback (see B2).

### B2 — SQLite connection string still present in code (violates scope §1)
Same line as B1 hard-codes `sqlite:///./voltlife.db` as the default. Scope explicitly requires *"No SQLite connection strings remain anywhere in codebase."* Failing closed is mandatory here: if `DATABASE_URL` is unset the app should **raise**, not quietly pick SQLite.

**Fix:**
```python
self.DATABASE_URL = os.environ["DATABASE_URL"]  # raises if missing — no silent SQLite
```

---

## HIGH

### H1 — SSL not enforced for Supabase (scope §1: `sslmode=require`)
The `DATABASE_URL` in `.env` has no `?sslmode=require`, and `app/db/database.py` passes **no** `connect_args` on the Postgres branch (only the SQLite `check_same_thread` branch). psycopg2 defaults to `sslmode=prefer`, so the connection will *probably* negotiate TLS — but it is **not required**, which is exactly what the scope forbids.

**Fix:** append `?sslmode=require` to the URL, or:
```python
if not is_sqlite:
    connect_args = {"sslmode": "require"}
```

### H2 — JSONB is NOT actually used (deviates from frozen schema docs/03)
`app/models/orm.py` imports the **generic** `JSON` type:
```python
from sqlalchemy import ... JSON
features_json   = Column(JSON, ...)
explanation_json = Column(JSON, ...)
reasoning_json  = Column(JSON, ...)
payload_json    = Column(JSON, ...)
```
On the PostgreSQL dialect, generic `JSON` compiles to column type **`JSON`**, *not* `JSONB`. The comment in `database.py` — *"generic JSON/DateTime types render as JSONB/TIMESTAMPTZ on PG"* — is **half wrong**: `DateTime(timezone=True)` does render as `TIMESTAMPTZ` ✅, but `JSON` does **not** become `JSONB`. The approved schema (`docs/03-database.md`) specifies **JSONB** for all four columns. You lose JSONB indexing/operators and silently violate the frozen schema.

**Fix:**
```python
from sqlalchemy.dialects.postgresql import JSONB
... Column(JSONB, ...)
```
(Note: because init uses `create_all(checkfirst=True)`, this will **not** auto-correct on a DB where the table already exists — see M3.)

### H3 — Test suite runs on SQLite, so it validates nothing about Postgres
`tests/conftest.py` forces:
```python
TEST_DATABASE_URL = "sqlite:///./test_voltlife_shared.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
```
Every test exercises SQLite, where FK constraints are not enforced by default, types are loosely coerced, `CheckConstraint` on `grade` is ignored, and JSONB/`server_default now()` behave differently. **Green tests give false post-migration confidence.** At minimum, add a Postgres-backed CI run (Supabase test branch or a throwaway PG service) so the suite actually exercises the production dialect.

---

## MEDIUM

### M1 — No connection pooling / timeout config against the Supabase *transaction* pooler
`.env` points at the pooler on port **6543** (`...pooler.supabase.com:6543`) — that is pgbouncer in **transaction mode**. `create_engine` is called with **no** `pool_pre_ping`, `pool_size`, `connect_timeout`, or `poolclass`. Two risks: (a) SQLAlchemy's default `QueuePool` layered on top of a server-side pooler, and (b) server-side prepared statements under pgbouncer transaction mode can error. Scope §1 requires pooling + connection timeout to be configured; neither is.

**Fix (typical Supabase pattern):**
```python
from sqlalchemy.pool import NullPool
engine = create_engine(DATABASE_URL, poolclass=NullPool,
                       connect_args={"sslmode": "require", "connect_timeout": 10})
```
(Let Supabase's pooler own pooling; or use the direct 5432 endpoint with a real pool.)

### M2 — `.env.example` was never updated (scope §1)
`backend/.env.example` contains only a single commented `MODEL_PATH` line. It is missing `DATABASE_URL`, `DEMO_KEY`, `PUBLIC_BASE_URL`, `PUBLIC_FRONTEND_URL`, `PACE_S`, `AUTONOMY_MODE`. A teammate cloning the repo has no template for the Supabase variables. Scope explicitly requires this file be updated.

### M3 — No migration tooling; `create_all(checkfirst=True)` cannot evolve schema
`init_db()` relies on `metadata.create_all(checkfirst=True)`. This only creates **missing** tables — it will never `ALTER` an existing column. So the JSON→JSONB fix (H2) and any future schema change will **not** apply to an already-created Supabase DB without manual SQL or a drop/recreate. Acceptable for a hackathon *only if* the team knows to drop+recreate; otherwise add an Alembic baseline.

---

## LOW / HOUSEKEEPING

- **L1 — Live Supabase password sits in plaintext `.env`.** Correctly **gitignored** (verified: `git ls-files` shows only `.env.example`, not `.env`) ✅, so it is not committed. But the password is weak and is present in the working tree. Rotate it before/after the demo and never share the folder with `.env` included.
- **L2 — Leftover SQLite artifacts** in the tree: `voltlife.db` (65 KB), `backend/test_voltlife.db`, `test_remediation.db`, `*-journal`. Gitignored via `*.db` ✅ but they invite confusion about which DB is live. Delete them.
- **L3 — `deployments.site_id` FK has no `ondelete` rule** while every other FK uses `ondelete="CASCADE"`. On SQLite this was silently ignored; on Postgres FKs are enforced, so deleting a `Site` that has deployments will now raise. Decide intended behavior (RESTRICT vs SET NULL vs CASCADE) explicitly.
- **L4 — Deprecated `@app.on_event("startup")`** in `app/main.py`. Not migration-related; FastAPI recommends the lifespan handler. FYI only.
- **L5 — CORS misconfig (not migration-related, but a real bug):** `allow_origins=["*"]` together with `allow_credentials=True` is rejected by browsers per the CORS spec. Set explicit origins if credentials are needed.

---

## WHAT PASSED (credit where due)

- `DATABASE_URL` format is a valid PostgreSQL URL and lives in env, not hard-coded in source. ✅
- The only raw SQL (`healthz.py`: `db.execute(text("SELECT 1"))`) is dialect-neutral. No `strftime`, `PRAGMA`, `AUTOINCREMENT`, or SQLite-only functions in any query (the `strftime` grep hits are Python `datetime.strftime`, not SQL). ✅
- `DateTime(timezone=True)` → `TIMESTAMPTZ`, `Boolean` → `BOOLEAN`, `Integer` PK → `SERIAL/IDENTITY`, `Numeric` → `NUMERIC`: all map correctly on PG. ✅
- No `BLOB` columns; nothing needing `BYTEA`. ✅
- `CheckConstraint("grade IN (...)")` is valid Postgres. ✅
- FK `ondelete="CASCADE"` is declared at the DB level on all child tables except `site_id` (L3) — and PG will now actually enforce them. ✅
- `.env` correctly excluded from git. ✅

---

## REQUIRED ACTIONS TO REACH "PASS"

1. **(B1/B2)** Add `python-dotenv`, call `load_dotenv()` (or use `--env-file`), and make `DATABASE_URL` mandatory — remove the SQLite default.
2. **(H1)** Enforce `sslmode=require`.
3. **(H2)** Switch the four JSON columns to `postgresql.JSONB`; drop+recreate the Supabase tables so it takes effect.
4. **(H3)** Add a Postgres-backed test run.
5. **(M1)** Configure pool/timeout for the Supabase pooler (`NullPool` + `connect_timeout`).
6. **(M2)** Fill in `.env.example` with all Supabase variables.

Re-submit after 1–3 at minimum; those are the true blockers to calling this a Postgres deployment.
