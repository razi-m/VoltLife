# 04 — API Contracts (Owner: Zaid · Implementer: Farhan)

**FROZEN AT HOUR 1.** Zaki builds against mocks of exactly these shapes; Farhan implements exactly these shapes. Changes require Zaid's sign-off + a message in the team chat. This contract is what makes parallel work possible.

Base: `/api/v1` · All responses `application/json` · Errors: `{"error": {"code": "string", "message": "string"}}` with proper HTTP status.

## 1. Ingestion

`POST /api/v1/batteries/ingest`
Multipart `file` (CSV) **or** JSON `{"batteries": [...]}`.

CSV columns (the ingestion template — publish `sample_fleet.csv` in the repo):
```
external_ref,oem,model,chemistry,rated_capacity_kwh,nominal_voltage,manufacture_date,
source_city,source_state,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,
thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,
fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency
```
The last 6 columns are **optional feature columns** (audit fix M1): they let the full 14-feature ML vector arrive via CSV. Missing → NaN (model handles natively) but knee detection and several explanations won't fire, and confidence degrades — the sample fleet always includes them.

→ `202 {"job_id": "j_8f3k", "accepted": 847, "rejected": 3, "rejects": [{"row": 14, "reason": "capacity_now_kwh > rated"}]}`

## 2. Job progress (also the polling fallback)

`GET /api/v1/jobs/{job_id}`
→ `{"job_id": "j_8f3k", "status": "running", "processed": 312, "total": 847, "recent_events": [/* last 20 WS-shaped events */]}`

## 3. WebSocket feed

`WS /ws/feed` — server pushes:

```json
{"type": "assessment", "payload": {"battery_id": 42, "aadhaar_id": "INFOAN480415032400231",
  "oem": "Fleet Operator A (2W)", "soh_pct": 82.4, "rul_years": 4.3, "rul_range": [3.1, 5.2],
  "grade": "A", "confidence": "high",
  "reasons": ["Low thermal stress (avg 31°C)", "Stable voltage profile", "Moderate cycle count (412)"],
  "lat": 18.52, "lng": 73.85}}

{"type": "deployment", "payload": {"battery_id": 42, "site_id": 3,
  "site_name": "Bhadla Solar Park Storage, RJ", "site_type": "solar_storage",
  "score": 0.87, "distance_km": 1142.0,
  "reasons": ["Best capacity match (3.2 of 4.0 kWh needed)", "Grade A meets solar-storage bar", "High carbon offset vs new cells"],
  "energy_unlocked_mwh": 3.06, "carbon_saved_kg": 197.8,
  "from": [18.52, 73.85], "to": [27.54, 71.91]}}

{"type": "impact", "payload": {"mwh_unlocked": 1059.2, "carbon_saved_tonnes": 69.8,
  "diverted_from_recycling": 312, "recycled_responsibly": 41, "processed": 353, "total": 847}}

{"type": "job_done", "payload": {"job_id": "j_8f3k", "duration_s": 126}}
```

Frontend flag `VITE_USE_POLLING=true` switches to `GET /jobs/{id}` every 1s and renders `recent_events` identically. **Zaki builds both paths on day one.**

## 4. Fleet & detail

`GET /api/v1/batteries?grade=A&status=assigned&page=1&page_size=50`
→ `{"items": [{battery summary + latest assessment + deployment site_name}], "total": 847, "page": 1}`

`GET /api/v1/batteries/{id}`
→ full object: battery, telemetry summary, latest assessment (incl. `explanation_json`), deployment (incl. `reasoning_json`).

## 5. Aadhaar passport

`GET /api/v1/batteries/{id}/aadhaar`
```json
{"aadhaar_id": "INFOAN480415032400231",
 "decoded": {"country": "IN", "manufacturer": "FOA", "chemistry": "NMC",
             "voltage": "48V", "capacity_kwh": 4.0, "manufactured": "2024-03-15", "serial": "00231"},
 "qr_payload": "https://voltlife.app/b/INFOAN480415032400231",
 "static": {"chemistry": "NMC", "rated_capacity_kwh": 4.0, "mass_estimate_kg": 24},
 "dynamic": {"soh_pct": 82.4, "status": "repurposed", "grade": "A", "rul_years": 4.3},
 "timeline": [
   {"event_type": "manufactured", "occurred_at": "2024-03-15"},
   {"event_type": "first_life_started", "occurred_at": "2024-04-02", "payload": {"vehicle": "e-scooter, Pune"}},
   {"event_type": "retired_from_ev", "occurred_at": "2026-05-30"},
   {"event_type": "assessed", "occurred_at": "...", "payload": {"soh_pct": 82.4, "grade": "A"}},
   {"event_type": "aadhaar_issued", "occurred_at": "..."},
   {"event_type": "deployment_assigned", "occurred_at": "...", "payload": {"site": "Bhadla Solar Park Storage, RJ"}}],
 "life_story": "Born in a Pune factory, March 2024. Carried a commuter ~18,000 km on 412 charges. Retired with 82% of its heart intact — now it stores Rajasthan's sunlight.",
 "impact": {"energy_unlocked_mwh": 3.06, "carbon_saved_kg": 197.8}}
```
`static`/`dynamic` split deliberately mirrors the BPAN draft — say so in the demo. QR rendered client-side (`qrcode.react`) from `qr_payload`. `life_story` is template-generated server-side from existing fields (see innovation_features.md #1).

**Public QR target (no auth, read-only):** `GET /api/v1/aadhaar/{aadhaar_id}` → same payload as above. This is what `qr_payload` resolves to (blueprint P5).

## 6. Sites, impact, demo ops

`GET /api/v1/sites` → `{"items": [{id, name, site_type, state, lat, lng, demand_kwh, remaining_kwh, min_grade, assigned_count}]}`

`GET /api/v1/impact/summary` → same shape as WS `impact` payload + `by_grade` histogram + `by_site_type` breakdown.

`POST /api/v1/demo/reset` (header `X-Demo-Key`) → wipes fleet, re-seeds sites, zeros counters.
`POST /api/v1/demo/replay` (header `X-Demo-Key`) → streams pre-computed results file through WS pacing. Nuclear fallback.
`GET /healthz` → `{"ok": true, "model_version": "v1.2", "db": "up"}` — check this before walking on stage.

## Mock plan (kills the integration bottleneck)

Hour 1–2: Farhan commits `mocks/` — one static JSON per endpoint above, served by a 20-line FastAPI stub. Zaki develops against the stub all day; swapping to real endpoints at H12 is a base-URL change. The WS mock replays 30 fake events on loop.
