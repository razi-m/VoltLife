# 05 — Deployment Engine (backend side)

**No ML here** — the scoring math is the pure engine in `ml/recommend.py` (ml-plan/11: gates → weighted score → top-3 → factor templates). This doc specifies what the backend wraps around it.

## Destination registry (the mandated list, mapped to site types)

| Mandated destination | site_type (docs/03) | min_grade | Note |
|---|---|---|---|
| Solar Farm | solar_storage | A | S preferred via grade_headroom |
| Industrial Backup | industrial_backup | A | added in ml-plan round |
| Microgrid / Rural Electrification | rural_microgrid | B | priority 1.3 — "policy is a parameter" |
| **School Backup** | school_backup | B | NEW — non-critical hours, emotional demo value |
| **Health Center Backup** | health_center_backup | A | NEW — critical load (vaccine refrigeration) → stricter bar + confidence high required |
| Recycler | recycler | accepts all | the ONLY destination for grade D |

The two new types are seed-registry additions (docs/06 + ml-plan/10 synced): ~3 school sites (Bihar, Jharkhand, Odisha; 8–20 kWh) and ~2 primary health centers (UP, Assam; 10–25 kWh, min_grade A, priority 1.2). A grade-A pack routed to a PHC vaccine fridge is the single most quotable deployment in the cascade — seed it so it fires.

## services/deployment.py responsibilities (the stateful wrapper)

1. Load eligible sites with live `remaining_kwh` (derived: demand − assigned).
2. Call `recommend()` → ranked top-3 + selected.
3. Persist deployment row: `site_id`, raw `score`, `reasoning_json` (all 3 ranks — feeds the counterfactual panel), `distance_km`, impact fields.
4. Decrement site capacity **in the same transaction** as the deployment insert (02_* integrity rule).
5. Advance battery status → `assigned`; append `deployment_assigned` lifecycle event.
6. Return the WS-shaped deployment payload to the pipeline for broadcast.

Edge cases: all sites full for an eligible battery → status stays `assessed`, event `awaiting_demand`, no deployment row (the QA harness seeds enough demand that this never happens at 847 — but the code path exists and doesn't crash). Confidence low → skip engine entirely, status `inspection` (ml-plan/08).

## Selection semantics

Selected = rank 1 (capacity-checked). `status='recommended'` on creation; the approve flow (`recommended → approved → dispatched`) exists in the status enum for the autonomy-toggle story but auto-advances to `approved` in Autonomous mode — one config flag, zero extra endpoints.
