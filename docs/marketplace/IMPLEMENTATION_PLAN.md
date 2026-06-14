# VoltLife Marketplace — Implementation Plan (PHASE 0)
**Status:** PLAN ONLY — no code written. Awaiting approval before Phase 1.
**Author:** Senior Full-Stack Engineer (Claude Opus 4.8)
**Date:** 2026-06-13

> Reminder of identity: VoltLife is **primarily a Battery Intelligence Platform**
> (AI Assessment + Grading + Use-Case Recommendation = the product and the moat).
> The marketplace is the **commercialization/distribution layer** on top. Demo-only:
> no real money, orders, or delivery. No media anywhere. Existing code is frozen.

---

## (a) Repo Audit — what exists vs. what's missing

**Backend (FastAPI, Postgres via `create_all(checkfirst=True)` — additive new tables auto-create; existing tables never altered):**
- ORM tables (FROZEN): `batteries, telemetry_summaries, assessments, sites, deployments, lifecycle_events`. `Assessment` carries `soh_pct, rul_years, rul_low/high_years, grade, confidence, model_version, explanation_json`. **No `soc` column anywhere** (see Open Questions).
- Routers registered in `main.py`: healthz, batteries, jobs, sites, impact, demo, dashboard, deployments, analytics, **ai**, **marketplace**.
- `marketplace.py` = an **auction/bids** demo view (`/marketplace/summary`, `/auctions`, `/auctions/{id}/bid`, `/lots`) with in-memory `BIDS_OVERRIDE`. This is NOT the supplier→inventory→quote→order commerce flow the spec describes → leave it untouched; build commerce as new routers.
- `ai.py` = mock chat (`/ai/chat`, `/ai/suggestions`).
- Assessment pipeline exists: `services/ingestion.py`, `services/pipeline.py`, `routers/batteries.py` (ingest→job→assessment). **Reuse this for battery upload + grading** — do not re-implement.
- **No auth** of any kind. **No** supplier/inventory/listing/quote/order/payment/logistics tables, services, or endpoints.

**Frontend (React + Vite + react-router + R3F; `recharts` present):**
- Pages: Dashboard, Assess, Registry, Deploy, Analytics, Impact, AI, **Marketplace** (auction view). Routes in `src/App.tsx`. API via `src/lib/api.ts` (`API_BASE = VITE_API_URL || http://localhost:8000`, fetch wrapper, `WS_URL`).
- **No map library, no Stripe library, no state lib** (zustand/react-query) installed.

**ML (FROZEN, `ml/`):** `predict()` returns the 11-field contract; outputs SoH/RUL/grade/confidence/recommendation/use-cases. Reached only via the existing backend pipeline.

**Missing (everything the marketplace needs):** supplier domain + auth, inventory auto-generation + listings + pricing, buyer accounts, Gemini requirement builder, discovery (map/search/profiles), quote engine, payment (test/mock), inventory locking, logistics simulation + optional n8n, order tracking/completion, seller dashboard, SaaS subscriptions.

---

## (b) Data Model — all NEW, additive (new module `backend/app/models/marketplace_orm.py`)

**Rule:** new tables link **FROM** themselves **TO** existing tables (e.g. `inventory_lot_battery.battery_id → batteries.id`). **Never** add columns to or alter existing tables (`create_all(checkfirst)` won't ALTER them, and the freeze forbids it).

| Table | Key columns | FKs (→ existing or new) |
|---|---|---|
| `supplier` | company_name, business_email (unique), phone, gst, business_address, status(pending/approved/rejected), demo_mode | — |
| `supplier_user` | email, password_hash, role | supplier_id → supplier |
| `supplier_verification` | status, notes, decided_at | supplier_id → supplier |
| `inventory_lot` | grade, battery_count, capacity_per_kwh, total_capacity_kwh, soh_avg, rul_avg_years, chemistry, use_cases_json, soc_nominal*, status(draft/published/locked) | supplier_id → supplier |
| `inventory_lot_battery` (join) | — | lot_id → inventory_lot, **battery_id → batteries.id** (link only, no alter) |
| `pricing_tier` | min_qty, max_qty(nullable), unit_price | lot_id → inventory_lot |
| `listing` | moq(nullable), description(text), is_published, published_at | lot_id → inventory_lot |
| `buyer_account` | name, email(unique), password_hash | — |
| `requirement` | raw_text, rec_grade, rec_capacity_kwh, rec_quantity, rec_use_cases_json, source(gemini/mock) | buyer_id → buyer_account (nullable) |
| `quote` | grade, quantity, battery_cost, transport_cost, total_cost, delivery_days, porter_vehicle, status | buyer_id, listing_id |
| `order` | grade, quantity, order_value, payment_status, tracking_status, eta, demo_mode | quote_id, buyer_id, supplier_id, listing_id |
| `payment` | provider(stripe-test/mock), amount_cents, currency(USD), status, stripe_session_id, stripe_payment_intent, idempotency_key(unique) | order_id |
| `tracking_event` | state, note, created_at | order_id |
| `notification` | audience(seller/buyer), message | order_id |
| `subscription` | plan(monthly/annual/enterprise), status, demo_mode | supplier_id |
| `support_ticket` | issue_text, status | order_id, buyer_id |

\* `soc_nominal` only if SoC is confirmed in scope (Open Question 1).

---

## (c) API Surface — all NEW endpoints (new routers under `/api/v1`)

- `routers/suppliers.py` — POST `/suppliers/register`, POST `/suppliers/login`, GET `/suppliers/me`, GET `/suppliers/{id}`, POST `/admin/suppliers/{id}/verify` (demo approval).
- `routers/inventory.py` — POST `/suppliers/{id}/batteries/upload` (delegates to existing ingestion/pipeline), POST `/inventory/generate` (auto-build grade-bucketed lots from assessed batteries), GET `/suppliers/{id}/inventory`, POST `/inventory/{lot}/pricing`, PATCH `/inventory/{lot}/config` (moq, description), POST `/inventory/{lot}/publish` (enforces: only VoltLife-assessed batteries; no manual listings; no media).
- `routers/discovery.py` (public, no auth) — GET `/listings` (search by grade/capacity/use_case/quantity/location), GET `/listings/{id}`, GET `/sellers` (map data), GET `/sellers/{id}`.
- `routers/requirements.py` — POST `/requirements` (Gemini adapter → grade/capacity/qty/use-cases), GET `/requirements/{id}/matches` (match to real published listings).
- `routers/buyers.py` — POST `/buyers/register`, POST `/buyers/login`, GET `/buyers/me`, GET `/buyers/orders`.
- `routers/quotes.py` — POST `/quotes` (tier pricing + Porter mock → transport/eta; **no inventory lock**), GET `/quotes/{id}`.
- `routers/payments.py` — POST `/payments/create-order` (Stripe test or mock), POST `/payments/verify` (signature check), POST `/payments/webhook` (idempotent → lock/decrement inventory + create order + trigger logistics).
- `routers/orders.py` — GET `/orders/{id}`, POST `/orders/{id}/confirm-receipt`, POST `/orders/{id}/raise-issue`.
- `routers/logistics.py` — POST `/logistics/callback` (n8n or simulator advances tracking state, idempotent), POST `/logistics/{order}/advance` (demo manual step).
- `routers/subscriptions.py` — GET `/subscriptions/plans`, POST `/subscriptions/subscribe` (demo).
- Seller dashboard reads (in suppliers.py): GET `/suppliers/{id}/orders`, GET `/suppliers/{id}/revenue`, GET `/suppliers/{id}/requirements` (active buyer requirements only — never competing sellers).

New Pydantic schemas live in a NEW module `backend/app/schemas/marketplace.py` (existing `schemas/api.py` untouched).

---

## (d) Integration Adapters (new `services/` modules; env-driven + mock fallback; demo runs with NO keys)

| Adapter | Real driver (env) | Fallback |
|---|---|---|
| Gemini | `GEMINI_API_KEY` | deterministic mock: use-case text → grade/capacity/qty/use-cases |
| Stripe | `STRIPE_PUBLISHABLE_KEY`+`STRIPE_SECRET_KEY` (TEST) | mock "payment success" path (USD (test mode)) |
| Porter | (always mock for demo) | distance-heuristic vehicle/cost/ETA |
| n8n | `N8N_WEBHOOK_URL` + `N8N_ENABLED` | in-app logistics simulation |

`.env.example` additions (additive only): `GEMINI_API_KEY=`, `STRIPE_PUBLISHABLE_KEY=`, `STRIPE_SECRET_KEY=`, `STRIPE_WEBHOOK_SECRET=`, `PORTER_API_KEY=`, `N8N_WEBHOOK_URL=`, `N8N_ENABLED=false`, `BACKEND_BASE_URL=`.

---

## (e) Frontend Surface (new pages/components under `frontend/src/**`; reuse existing design system)

- Supplier: `/supplier/register`, `/supplier/login`, `/supplier/dashboard` (upload → inventory → pricing → publish; orders; revenue).
- Buyer/public: `/shop` (marketplace + India map + search + AI Requirement Builder), `/shop/seller/:id`, `/shop/listing/:id`, `/checkout`, `/buyer/orders`.
- Reuse `components/ui`, `components/layout`, `lib/api.ts`. **Do not touch** existing `Marketplace.tsx` (auction view) — new commerce lives under `/shop`.
- New deps to add (justified in plan, not yet installed): `react-leaflet` + `leaflet` (OSS India map, no token); Stripe Checkout via `checkout.js` script tag (NO npm dep) for test mode — otherwise a mock checkout page.

---

## (f) Existing-Code Impact Table (the ONLY existing files to be modified — each additive & justified)

| File | Exact change | Why necessary | Why it can't break existing behavior |
|---|---|---|---|
| `backend/app/main.py` | add `include_router(...)` lines for each new router | new endpoints must be mounted | additive lines only; existing routers/handlers untouched |
| `backend/app/models/__init__`/import site | ensure new ORM module is imported before `create_all` | new tables must register | additive import; existing models unchanged |
| `backend/.env.example` | append new env vars | adapters need config keys | additive; no existing var changed |
| `backend/requirements.txt` | add (if used) `passlib[bcrypt]`, `python-jose` (demo auth), `stripe` | auth + payment adapters | additive deps; httpx already present |
| `frontend/src/App.tsx` | add `<Route>` entries for new pages | new pages must be reachable | additive routes; existing routes untouched |
| `frontend/package.json` | add `react-leaflet`,`leaflet` (Stripe Checkout loads via `checkout.js` script — no npm dep) | map + India geo | additive deps |

**Everything else is NEW files.** No existing table/column/endpoint/response shape is altered. `ml/` is not touched.

---

## (g) Phase Order + Acceptance Tests (1 line each)

1. **Data model & migrations** — new tables create cleanly; existing pytest green.
2. **Supplier registration/verification/auth** — only verified suppliers reach supplier endpoints.
3. **Upload → AI assessment → inventory auto-gen** — uploads get assessed (existing pipeline) → grade-bucketed lots.
4. **Supplier config & publish** — published listings appear; unassessed/manual cannot publish; no media fields.
5. **Buyer access & accounts** — anon browse works; checkout requires buyer account.
6. **Gemini requirement builder + matching** — text → recommendation → matched real listings (mock works keyless).
7. **Discovery (map/search/profiles/inventory cards)** — renders from real APIs; data-only cards.
8. **Quote engine (pricing + mock Porter)** — deterministic quote; persisted; zero inventory change.
9. **Payment (Stripe test/mock) + inventory lock + order** — success decrements inventory exactly once (idempotent); failure leaves it untouched.
10. **n8n orchestration (standalone)** — order advances via in-app sim by default; same callback works with real n8n + imported workflow JSON.
11. **Logistics simulation/tracking** — order walks all states; notifications recorded.
12. **Order tracking & completion** — Confirm Receipt → completed; Raise Issue → support ticket.
13. **Seller dashboard (basic)** — inventory/orders/revenue + active buyer requirements only.
14. **SaaS subscriptions (demo)** — plans gate supplier access (simulated billing).
15. **Integration tests + demo seed** — full simulated flow passes; all pre-existing suites still green.

Each phase will be preceded by `docs/phase-readiness/PHASE_<nn>_READINESS.md` (validated + confirmed) and followed by `reports/PHASE_<nn>_REPORT.md`, per the gates.

---

## Open Questions (lowest-risk defaults chosen — please confirm or override)

1. **SoC (State of Charge):** the ML assessment outputs SoH/RUL/grade but **NOT SoC** (SoC is a live measurement, not produced by the grading model). Default: display SoC as a clearly-labeled **nominal/demo** value (or omit), not a fabricated prediction. Confirm: show nominal SoC, or drop SoC from listings?
2. **Auth depth:** demo-grade auth (passlib hash + simple bearer token) vs full JWT/refresh. Default: lightweight demo auth.
3. **Map library:** `react-leaflet`+`leaflet` (OSS, no token) vs Mapbox (needs token). Default: react-leaflet.
4. **Stripe:** real **test-mode** Checkout (sk_test_ keys, INR) vs **fully mocked** checkout (zero dependency). Default: adapter supports both; demo uses mock unless test keys present. Currency INR, amounts in paise.
5. **Existing `/marketplace` auction view:** keep untouched; new commerce flow under `/shop`. Default: keep both.

---

## Phase 0 verdict
Plan complete. **No code written.** ML and existing battery-domain remain untouched. Per the master prompt's gates, I will not start Phase 1 until you approve this plan and the open questions.
