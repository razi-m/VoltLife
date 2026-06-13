# 02 — Database Design

**The schema is frozen in docs/03 (DDL, 6 tables, indexes) — this doc explains it for implementation and maps the mandated table names onto it. Do not redesign.** SQLAlchemy ORM, Postgres, Alembic baseline (01_*).

**Dialect rule (audit fix S1):** PostgreSQL is primary; SQLite is the documented fallback (docs/02) — so the ORM uses **generic SQLAlchemy types only**: `JSON` (renders as JSONB on Postgres) and `DateTime(timezone=True)` (renders as TIMESTAMPTZ). Never import from `sqlalchemy.dialects.postgresql`. Config branch: a `sqlite://` `DATABASE_URL` runs `metadata.create_all()` and skips Alembic entirely — the escape hatch must actually work at 2 a.m., not just exist on paper. The docs/03 DDL shows the Postgres rendering.

## Mandated names → actual schema (deliberate design, defend it)

| Mandated | Actual | Why |
|---|---|---|
| `batteries` | `batteries` ✔ | — |
| `assessments` | `assessments` ✔ | grade lives here, not on batteries → re-assessment is a feature; latest wins |
| `deployments` | `deployments` ✔ | — |
| `battery_passports` | **composed view, not a table** | The passport = batteries ⋈ latest assessment ⋈ deployment ⋈ lifecycle_events, assembled by `services/aadhaar`. A passport table would denormalize data that changes (SoH, status) — event-sourcing gives the timeline UI for free and can never disagree with the source rows. |
| `activity_logs` | `lifecycle_events` ✔ (same thing, better name) | It IS the activity log: append-only, typed events, payload JSONB. Powers timeline, audit trail, and the optional hash chain. |
| `impact_metrics` | **computed aggregates, not a table** | `SUM()` over 847 rows is sub-ms; a metrics table would be a cache that can drift from truth mid-demo. `/impact/summary` computes live. |

## Field-by-field intent (summary — types/constraints in docs/03 DDL)

- **batteries** — `aadhaar_id` (21-char BPAN, unique, NULL until issued); `external_ref` = operator's "BAT-001" (the mandated BAT-ID); `oem/model/chemistry/form_factor/rated_capacity_kwh/nominal_voltage/manufacture_date` = passport static section; `source_city/state/lat/lng` = map origin + distance calc; `status` = lifecycle state machine (`ingested → assessed → assigned → deployed → recycled`), advanced only by the pipeline.
- **telemetry_summaries** — 1:1 with batteries; display columns (cycle_count, temps, IR, …) for the UI + `features_json` = the canonical 14-key vector handed to `assess()` (ml-plan/03). Raw curves deliberately not stored (docs/03).
- **assessments** — model outputs verbatim: `soh_pct, rul_years, rul_low/high_years, grade (S–D), confidence, model_version, explanation_json`. Append-only; "latest per battery" is the read pattern (index on battery_id, created_at).
- **sites** — demand registry incl. new types `school_backup`, `health_center_backup` (docs/06 synced); `demand_kwh` decremented... no — `remaining_kwh` is **derived** (demand − SUM assigned) per integration_validation §2; `min_soh_pct/min_grade/priority` = engine gates/weights; `is_simulated` flag = honesty on the wire.
- **deployments** — `score` (raw 0–1 float; UI int = ×100), `reasoning_json` (top-3 recommendations incl. runner-ups → counterfactual panel), `distance_km`, `energy_unlocked_mwh`, `carbon_saved_kg` (0 for grade D), `status` (`recommended → approved → dispatched`).
- **lifecycle_events** — `event_type` enum-by-convention (docs/03 list), `payload_json`, `occurred_at`; backfilled history at ingestion (manufactured / first_life / retired). **Additive optional column:** `event_hash VARCHAR(64) NULL` — sha256(prev_hash + payload) for the tamper-evidence feature (innovation #8); nullable so it's a feature flag, not a dependency.

## Relationships & integrity

All FKs per docs/03 with `ON DELETE CASCADE` from batteries (demo reset truncates cleanly). One transaction per battery in the pipeline: assessment + deployment + events + (site decrement read) commit together — a battery is never half-processed in the DB even if the process dies mid-cascade.

## Indexes

As in docs/03 (status, battery_id lookups, events by battery+time) plus `batteries(aadhaar_id)` unique index serves the public passport route. Nothing else — 847 rows needs no tuning; indexes exist for correctness of access patterns, not speed.
