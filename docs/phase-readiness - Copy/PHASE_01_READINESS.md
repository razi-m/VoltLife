# PHASE 01 READINESS — Marketplace Data Model & Migrations

## Phase Goal
- Define and create the new database tables required for the VoltLife Marketplace (suppliers, listings, lots, buyers, quotes, orders, logistics, subscriptions, etc.) in a separate, isolated ORM module.
- Ensure that the database schemas are created cleanly via SQLAlchemy `create_all()` without breaking the existing database tables, migrations, or tests.

## Prerequisites
- Completed phases: N/A (Phase 1 is the starting phase for the marketplace build).
- Required files: 
  - [database.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/db/database.py) (exists)
  - [orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py) (exists)
- Required services: Local/test database connection configured in `backend/.env`.
- Required approvals: skipped Phase 0 per user instruction.

## Required Inputs
- Existing Tables to interface with: `batteries`, `assessments`, `lifecycle_events`.
- Database URLs: Loaded from `.env` (`DATABASE_URL` / `TEST_DATABASE_URL`).
- Environment variables: `DATABASE_URL` (configured for Supabase pooler / SQLite in tests).

## Team Ownership
- Backend Team (Shared / DB Architects).

## External Dependencies
- PostgreSQL (Supabase) / SQLite (tests): Required (Mockable: No).
- Stripe / Porter / Gemini: N/A for Phase 1.

## Blocking Risks
- Database connection timeouts to remote Supabase DB (mitigated by checkfirst = True and NullPool in `database.py`).
- Schema collisions with existing tables (mitigated by using `marketplace_` prefix or strictly separate table names).

## Readiness Checklist
- [x] Verified existing `pytest` passes with 11/11 tests.
- [x] Verified `Base` declaration in `backend/app/db/database.py` is ready to register new subclasses.
- [x] Confirmed table names in `backend/app/models/orm.py` to prevent duplicate registration.

## Phase Exit Criteria
- The new module `backend/app/models/marketplace_orm.py` is defined with the required marketplace models.
- Running `init_db()` or launching the app creates the new tables cleanly in SQLite / PostgreSQL.
- Running `pytest` continues to return green on all 11 existing smoke/remediation tests.
