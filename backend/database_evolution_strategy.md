# Database Evolution & Migration Strategy

This document outlines the database schema initialization and evolution strategy for VoltLife, specifically addressing the transition to PostgreSQL (Supabase).

## 1. Schema Initialization (Greenfield)
VoltLife uses SQLAlchemy's metadata schema definitions in `[orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py)`. The application initializes the database programmatically on startup via `init_db()` in `[database.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/db/database.py)`:

* **Method**: Calls `OrmBase.metadata.create_all(bind=engine, checkfirst=True)`.
* **Behavior**: Idempotently creates tables if they do not exist.

---

## 2. Schema Evolution (Brownfield / Live DB)
Since VoltLife does not currently utilize Alembic, `metadata.create_all()` **cannot** alter existing tables or columns (such as changing column types, adding columns, or updating indexes). 

For modifying or migrating live schemas:

### A. Non-Destructive Migrations (Manual SQL)
For production instances where data must be preserved, DDL migrations must be executed manually using the **Supabase SQL Editor** (or another pg client).

* **Example (Converting generic JSON to PostgreSQL JSONB)**:
  ```sql
  ALTER TABLE telemetry_summaries ALTER COLUMN features_json TYPE jsonb USING features_json::jsonb;
  ALTER TABLE assessments ALTER COLUMN explanation_json TYPE jsonb USING explanation_json::jsonb;
  ALTER TABLE deployments ALTER COLUMN reasoning_json TYPE jsonb USING reasoning_json::jsonb;
  ALTER TABLE lifecycle_events ALTER COLUMN payload_json TYPE jsonb USING payload_json::jsonb;
  ```

* **Example (Adding columns)**:
  ```sql
  ALTER TABLE batteries ADD COLUMN IF NOT EXISTS model varchar(80);
  ```

### B. Destructive Migrations (Reset & Recreate)
For development, staging, or testing instances where data loss is acceptable, a schema reset can be triggered by calling the demo reset endpoint (`POST /api/v1/demo/reset`), which drops and recreates tables in dependency order:

1. Wipes the database tables.
2. Re-runs `metadata.create_all()`.
3. Seeds default site configurations.
