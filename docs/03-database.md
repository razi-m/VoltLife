# 03 — Database Schema (Owners: Zaid design · Farhan implementation)

Postgres + SQLAlchemy. Six tables. JSONB for anything flexible — do not normalize explanation payloads at a hackathon. Store telemetry **summaries**, not raw cycle curves (847 packs × thousands of cycles would bloat the DB for zero demo value; raw curves live in the ML training repo only).

## DDL

```sql
CREATE TABLE batteries (
    id              SERIAL PRIMARY KEY,
    aadhaar_id      VARCHAR(21) UNIQUE,          -- BPAN-style, set after assessment
    oem             VARCHAR(50)  NOT NULL,        -- 'Fleet Operator A (2W)' etc.
    model           VARCHAR(80),
    chemistry       VARCHAR(20)  NOT NULL,        -- NMC | LFP | LCO
    form_factor     VARCHAR(20)  DEFAULT 'pack',
    rated_capacity_kwh NUMERIC(6,2) NOT NULL,
    nominal_voltage NUMERIC(5,1),
    manufacture_date DATE,
    source_city     VARCHAR(60),
    source_state    VARCHAR(40),
    lat             NUMERIC(9,6),
    lng             NUMERIC(9,6),
    status          VARCHAR(20) DEFAULT 'ingested',
    -- ingested → assessed → assigned → deployed → recycled
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE telemetry_summaries (
    battery_id      INT PRIMARY KEY REFERENCES batteries(id) ON DELETE CASCADE,
    cycle_count     INT NOT NULL,
    capacity_now_kwh NUMERIC(6,2),
    capacity_fade_pct NUMERIC(5,2),
    fade_rate_pct_per_100cyc NUMERIC(6,3),
    avg_temp_c      NUMERIC(5,2),
    max_temp_c      NUMERIC(5,2),
    thermal_stress_hours NUMERIC(8,1),
    internal_resistance_mohm NUMERIC(7,2),
    ir_growth_pct   NUMERIC(6,2),
    voltage_stability NUMERIC(4,3),              -- 0..1, derived
    coulombic_efficiency NUMERIC(5,4),
    features_json   JSONB                         -- full feature vector for ML
);

CREATE TABLE assessments (
    id              SERIAL PRIMARY KEY,
    battery_id      INT NOT NULL REFERENCES batteries(id) ON DELETE CASCADE,
    soh_pct         NUMERIC(5,2) NOT NULL,
    rul_years       NUMERIC(4,1) NOT NULL,
    rul_low_years   NUMERIC(4,1),                -- quantile band
    rul_high_years  NUMERIC(4,1),
    grade           CHAR(1) NOT NULL CHECK (grade IN ('S','A','B','C','D')),
    -- 5 tiers (ml-plan/10): S=premium · A · B · C · D renders as "Recycle" in all UI
    confidence      VARCHAR(6) NOT NULL,          -- high | medium | low
    model_version   VARCHAR(20) NOT NULL,
    explanation_json JSONB NOT NULL,
    -- [{"feature":"avg_temp_c","value":31.2,"impact":"+","label":"Low thermal stress"}...]
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE sites (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,        -- 'Bhadla Solar Park Storage, RJ'
    site_type       VARCHAR(30) NOT NULL,
    -- solar_storage | rural_microgrid | telecom_tower | ev_charging_buffer | street_lighting | recycler
    state           VARCHAR(40),
    lat             NUMERIC(9,6) NOT NULL,
    lng             NUMERIC(9,6) NOT NULL,
    demand_kwh      NUMERIC(10,2) NOT NULL,       -- remaining capacity wanted
    min_soh_pct     NUMERIC(5,2) NOT NULL,
    min_grade       CHAR(1) NOT NULL,
    priority        NUMERIC(3,2) DEFAULT 1.0,     -- microgrids > telecom etc.
    is_simulated    BOOLEAN DEFAULT TRUE
);

CREATE TABLE deployments (
    id              SERIAL PRIMARY KEY,
    battery_id      INT NOT NULL REFERENCES batteries(id) ON DELETE CASCADE,
    site_id         INT NOT NULL REFERENCES sites(id),
    score           NUMERIC(6,3) NOT NULL,
    reasoning_json  JSONB NOT NULL,               -- per-factor contributions
    distance_km     NUMERIC(8,1),
    energy_unlocked_mwh NUMERIC(10,3) NOT NULL,   -- lifetime throughput
    carbon_saved_kg NUMERIC(12,1) NOT NULL,
    status          VARCHAR(20) DEFAULT 'recommended',  -- recommended | approved | dispatched
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE lifecycle_events (
    id              SERIAL PRIMARY KEY,
    battery_id      INT NOT NULL REFERENCES batteries(id) ON DELETE CASCADE,
    event_type      VARCHAR(40) NOT NULL,
    -- manufactured | first_life_started | retired_from_ev | ingested | assessed
    -- | aadhaar_issued | deployment_assigned | dispatched | recycled
    payload_json    JSONB,
    occurred_at     TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_batteries_status ON batteries(status);
CREATE INDEX idx_assessments_battery ON assessments(battery_id);
CREATE INDEX idx_deployments_battery ON deployments(battery_id);
CREATE INDEX idx_events_battery ON lifecycle_events(battery_id, occurred_at);
```

## Conventions

- The Aadhaar "passport" is **not a table** — it's a view assembled from `batteries` + latest `assessments` + `deployments` + `lifecycle_events`. Event-sourced history = the timeline UI for free.
- Backfill `manufactured` / `first_life_started` / `retired_from_ev` events at ingestion (dates derived from `manufacture_date`) so every passport timeline starts populated.
- Impact totals: compute with `SUM()` on demand (`/impact/summary`). 847 rows — no caching table needed.
- Grade is stored on `assessments`, not `batteries` — re-assessment is a feature ("health re-checked after 6 months in field"), and the latest one wins.

## Aadhaar ID format (BPAN-style, 21 chars)

```
[2 country][3 mfr][1 chemistry][2 voltage][2 capacity][6 date DDMMYY][5 serial]
 IN         FOA    N(MC)        48         04          150324         00231
→ INFOAN480415032400231     (FOA = "Fleet Operator A" — no real brand codes, per doc 01)
```

Mirrors the structure of MoRTH's draft example (`MY008A6FKKKLC1DH80001`): manufacturer identifier, chemistry, voltage, date, serial. Exact field layout is ours; the *spirit* (offline-decodable 21-char ID) is the draft's. Implement encode + decode — decoding it live on the passport page ("the ID itself tells a recycler what's inside, even offline") is a great 10-second demo beat.
