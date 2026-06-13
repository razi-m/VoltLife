# VOLTLIFE — MARKETPLACE BUILD: MASTER PROMPT (for Claude Opus 4.8)

> Paste everything below the line into Claude Opus 4.8 (Claude Code / Antigravity).
> This prompt builds the VoltLife Marketplace on top of the **existing, frozen** codebase.

---

```
You are a Senior Full-Stack Engineer implementing the VoltLife Marketplace.

The repository ALREADY EXISTS and is partially built. Three subsystems are
DONE and FROZEN. Your job is to ADD the marketplace domain on top of them
WITHOUT disturbing anything that already works.

═══════════════════════════════════════════════════════════════
0. READ FIRST — GROUND TRUTH (do this before writing a single line)
═══════════════════════════════════════════════════════════════
1. Read the entire repository. Do NOT assume any file's contents — open and
   read the actual files.
2. At minimum, read:
   - backend/app/main.py, backend/app/models/orm.py, backend/app/db/database.py
   - every file in backend/app/routers/ and backend/app/services/ and backend/app/schemas/
   - ml/predict.py, ml/shared_constants.py (the OUTPUT_CONTRACT_FIELDS list)
   - frontend/package.json, frontend/src/** (pages, components, landing, lib, hooks)
   - docs/, backend-plan/, frontend-plan/, ml-plan/ for the architecture intent
3. The following ALREADY EXIST — confirm by reading before you touch anything:
   - backend routers: ai.py, analytics.py, batteries.py, dashboard.py, demo.py,
     deployments.py, healthz.py, impact.py, jobs.py, marketplace.py, sites.py
   - ORM tables: batteries, telemetry_summaries, assessments, sites, deployments,
     lifecycle_events
   - backend services: aadhaar.py, deployment.py, impact.py, ingestion.py, pipeline.py
   - the ML subsystem under ml/ (SoH/RUL/grade/confidence/recommend/explain/volt_ai)
   - a React+Vite+R3F frontend with an existing landing page / 3D scene and an
     in-progress marketplace
4. If the repo or any referenced file is inaccessible, STOP and ask. Do not invent.

═══════════════════════════════════════════════════════════════
1. ARCHITECTURE FREEZE — DO NOT DISTURB
═══════════════════════════════════════════════════════════════
PROTECTED ZONES (read-only — you may CALL them, never MODIFY them):
  A. ml/**  — the entire ML subsystem is FROZEN. Never edit any file in ml/.
     The only allowed interaction is calling the assessment via the existing
     backend pipeline, or `from ml.predict import predict` if/when explicitly
     wired. The 11-field output contract (ml/shared_constants.OUTPUT_CONTRACT_FIELDS)
     must not change.
  B. backend battery-assessment domain — existing ORM tables (batteries,
     telemetry_summaries, assessments, sites, deployments, lifecycle_events),
     existing services (pipeline.py, ingestion.py, aadhaar.py, deployment.py,
     impact.py), and the EXISTING endpoints in EXISTING routers.
     Do NOT rename, drop, or change the type/meaning of any existing column or
     endpoint. Do NOT change response shapes the frontend already consumes.
  C. frontend landing page / 3D R3F scene and any already-working pages.

ALLOWED ZONES (where new work lives):
  - NEW backend files: new ORM models in a SEPARATE module
    (e.g. backend/app/models/marketplace_orm.py), new routers
    (e.g. routers/suppliers.py, routers/inventory.py, routers/quotes.py,
    routers/orders.py, routers/payments.py, routers/logistics.py,
    routers/requirements.py), new services, new schemas, new seed data.
  - NEW endpoints ADDED to existing routers ONLY if it is the natural home and
    you do not alter existing handlers (e.g. extend marketplace.py with new
    routes; leave its existing routes untouched).
  - NEW frontend pages/components/routes under frontend/src/** that reuse the
    existing design system; do not rewrite existing pages.

CHANGE POLICY (the core rule the user cares about):
  - DEFAULT = ADD, never modify. Prefer new files/tables/endpoints/columns
    (nullable, additive) over editing existing ones.
  - You may modify an existing file ONLY IF it is strictly necessary to wire in
    new functionality (e.g. registering a new router in main.py, adding a nullable
    FK). For EVERY such modification you must, in the plan, justify it explicitly:
    file, exact change, why it is unavoidable, and why it cannot break existing
    behavior.
  - NEVER remove, rename, or rewrite working code "to clean it up."
  - NEVER change the ML contract, the existing DB schema semantics, or existing
    API response shapes.

═══════════════════════════════════════════════════════════════
2. ANTI-HALLUCINATION RULES
═══════════════════════════════════════════════════════════════
  - Quote real symbols. Before calling any function, model, column, endpoint, or
    frontend component, confirm it exists by reading the file. If it does not
    exist, say so and propose creating it — do not pretend it exists.
  - No invented dependencies. Do not import libraries that aren't in
    backend/requirements.txt or frontend/package.json without adding them in the
    plan and justifying them.
  - No invented data. Marketplace numbers/inventory must come from real assessed
    batteries (via the existing assessment pipeline) or clearly-labeled seed data,
    never fabricated inline.
  - If a spec detail is ambiguous, list it as an OPEN QUESTION in the plan and
    pick the lowest-risk, most additive default — state which default you chose.
  - Run the existing test suites (backend `pytest`, ml `pytest`, frontend build)
    after each phase and confirm they still pass. A green-before / green-after
    diff is required.

═══════════════════════════════════════════════════════════════
3. PLAN BEFORE CODE — HARD GATE
═══════════════════════════════════════════════════════════════
Do NOT generate any implementation code until you have produced and I have
approved an IMPLEMENTATION PLAN. The plan must contain:
  a. Repo audit summary — what already exists for each workflow step (supplier,
     inventory, buyer, quote, payment, logistics, orders) and what is missing.
  b. Data model design — every NEW table, its columns/types, and every FK into
     existing tables (additive, nullable). A migration strategy consistent with
     how the repo currently creates schema (read database.py / any Alembic).
  c. API surface — every NEW endpoint (method, path, request, response), and any
     existing endpoint you must extend (with justification).
  d. External integration adapters — Gemini, Stripe, Porter, n8n: interface +
     env vars + MOCK fallback (so the demo runs with no live keys).
  e. Frontend surface — new routes/pages/components and how they reuse existing
     design/system; no rewrite of existing pages.
  f. "Existing-code impact" table — every existing file you will modify, the exact
     change, and the no-break justification. If the list is empty, say "additive
     only."
  g. Phase order + acceptance tests per phase.
Deliver the plan, then STOP and wait for approval. Build phase-by-phase only
after approval, pausing for review at the end of each phase.

═══════════════════════════════════════════════════════════════
4. PHASES (dependency-ordered; build one at a time)
═══════════════════════════════════════════════════════════════
Each phase below lists GOAL and KEY DELIVERABLES. For each phase you must, in
the plan, attach: new files, modified files (+justification), data contracts,
external adapters, acceptance tests, and a "do-not-break" checklist.

PHASE 0 — Audit & Implementation Plan (NO CODE)
  Goal: produce Section 3 plan. Establish what exists vs. what's missing. No code.

PHASE 1 — Marketplace Data Model & Migrations (additive only)
  Goal: NEW tables in a separate module, additive FKs only. Suggested entities
  (confirm names against any existing ones first):
    supplier, supplier_user (auth), supplier_verification,
    inventory_lot (auto-generated, grade-bucketed, links to assessed batteries),
    pricing_tier (qty bands + price), listing (published inventory + MOQ + notes),
    buyer_account (auth), requirement (Gemini output), quote, quote_line,
    order, order_item, shipment/tracking_event, payment, subscription,
    support_ticket.
  Rule: do NOT alter existing tables. Link to batteries/assessments via new
  nullable FKs in the NEW tables only. Schema creation must follow the existing
  init pattern.
  Acceptance: tables create cleanly; existing backend pytest still green.

PHASE 2 — Supplier Registration, Verification & Auth (private/restricted)
  Goal: supplier sign-up (Company, Business Email, Phone, GST, Business Address),
  admin/auto verification → approved suppliers get dashboard access. Auth for
  suppliers (token/session consistent with repo conventions).
  Acceptance: only verified suppliers reach supplier-only endpoints.

PHASE 3 — Battery Upload → AI Assessment → Inventory Auto-Generation
  Goal: supplier uploads BMS telemetry / CSV / JSON. REUSE the EXISTING assessment
  pipeline (the existing batteries ingest → job → assessment flow / ML seam) — do
  NOT re-implement grading. After assessment, AUTO-generate inventory lots bucketed
  by grade (e.g., Grade A = N batteries). Supplier never hand-creates inventory.
  Rule: call the existing pipeline; do not modify it. If a thin adapter is needed,
  add a NEW service that calls the existing one.
  Acceptance: uploaded batteries get assessed and produce grade-bucketed inventory
  lots with SoH/SoC/RUL/grade/use-cases carried from the ML output.

PHASE 4 — Supplier Configuration & Publish
  Goal: supplier sets quantity-tier pricing, optional MOQ, listing description;
  publish makes inventory visible. Only VoltLife-assessed batteries may be listed;
  manual battery listings are forbidden (enforce server-side).
  Acceptance: published listing appears in marketplace read APIs; unassessed
  inventory cannot be published.

PHASE 5 — Buyer Access & Accounts (open/public)
  Goal: public browsing with NO login; account creation required only to purchase.
  Buyer auth. Public marketplace read endpoints (listings, seller profiles, map data).
  Acceptance: anonymous browse works; checkout requires a buyer account.

PHASE 6 — Gemini AI Requirement Builder + AI Marketplace Matching
  Goal: buyer free-text use case ("backup power for a school") → Gemini adapter →
  {recommended grade, capacity, quantity, use cases}; then auto-match to listings
  (grade/capacity/quantity/location). Provide a deterministic MOCK adapter so the
  demo works without a Gemini key; real key via env.
  Rule: matching uses real published listings; never fabricate sellers.
  Acceptance: requirement → recommendation → matched real listings.

PHASE 7 — Marketplace Discovery (map, search, seller profile, inventory display)
  Goal: India map (click seller → profile), search by grade/capacity/use-case/
  quantity/location, seller profile (company, location, inventory, grades, capacity,
  pricing), inventory listing card (Grade/SoH/SoC/RUL/chemistry; capacity per
  battery + total; available qty; pricing + tiers + MOQ; AI use cases).
  Rule: reuse existing frontend design system + existing map/marketplace work if
  present (read frontend/src first); extend, don't rewrite.
  Acceptance: discovery flows render from real APIs.

PHASE 8 — Quote Engine (pricing + n8n + Porter)
  Goal: buyer selects grade + quantity → compute battery cost from supplier tier
  rules → n8n trigger requests supplier+buyer locations → Porter adapter returns
  vehicle recommendation, delivery cost, ETA → assemble quote (battery cost +
  transport + total + delivery days). Inventory is NOT locked here.
  Adapters: n8n + Porter behind env-configured adapters with MOCK fallback.
  Acceptance: deterministic quote math; quote persisted; no inventory change.

PHASE 9 — Stripe Payment + Inventory Locking + Order Creation
  Goal: "Proceed to Payment" → Stripe Checkout (test mode) → on success ONLY:
  lock/decrement inventory (e.g., 138 → 100 for 38 purchased), create order,
  trigger logistics. Inventory must NEVER be locked at quote time — only after
  confirmed payment (idempotent webhook).
  Adapter: Stripe behind env keys; provide a test/mock success path for the demo.
  Acceptance: payment success decrements inventory exactly once; failure leaves
  inventory untouched.

PHASE 10 — Logistics Automation (n8n + Porter)
  Goal: post-payment n8n workflow: Porter booking → tracking created → seller
  notified → buyer notified → shipment started → in transit → delivered. Porter
  only in MVP.
  Acceptance: order advances through tracking states; notifications recorded.

PHASE 11 — Order Tracking & Delivery Completion
  Goal: buyer dashboard "My Orders" (Order ID, supplier, qty, grade, payment
  status, tracking status, ETA, order value). On delivery: Confirm Receipt →
  order completed; Raise Issue → support ticket created.
  Acceptance: status transitions and the two completion paths work.

PHASE 12 — Seller Dashboard (BASIC ONLY)
  Goal: inventory/current stock, active+completed orders, revenue/sales overview.
  Sellers see active buyer requirements only — never competing sellers.
  Explicitly NO advanced analytics, NO heatmaps, NO forecasting.
  Acceptance: basic dashboard reads from real data.

PHASE 13 — SaaS Subscription Billing
  Goal: platform revenue via Stripe subscriptions (Monthly / Annual / Enterprise).
  NO commissions, NO transaction fees, NO marketplace cuts anywhere in the code.
  Acceptance: subscription plans gate supplier access per policy.

PHASE 14 — Integration Tests, Demo Seed & Validation
  Goal: end-to-end happy-path tests (supplier→assess→inventory→publish→buyer→
  requirement→match→quote→pay→lock→logistics→deliver→complete). Demo seed so
  every screen is populated. Re-run backend + ml + frontend checks; confirm
  zero regression in existing suites.
  Acceptance: full flow passes; all pre-existing tests still green.

═══════════════════════════════════════════════════════════════
5. EXTERNAL INTEGRATIONS — POLICY
═══════════════════════════════════════════════════════════════
  - Gemini, Stripe, Porter, n8n each live behind a small ADAPTER interface with:
    (1) a real implementation driven by env vars (e.g. GEMINI_API_KEY,
    STRIPE_SECRET_KEY, PORTER_API_KEY, N8N_WEBHOOK_URL), and
    (2) a deterministic MOCK fallback used when the key is absent, matching the
    repo's existing mock/AUTONOMY_MODE conventions.
  - Never hardcode secrets. Add new env vars to backend/.env.example only
    (additive). Never print or commit real keys.
  - The demo must run end-to-end with NO live third-party keys (all mocks).

═══════════════════════════════════════════════════════════════
6. DEFINITION OF DONE (every phase)
═══════════════════════════════════════════════════════════════
  ✓ New code is additive; existing files modified only where justified in the plan.
  ✓ Existing backend pytest, ml pytest, and frontend build all PASS (green before
    AND after).
  ✓ ML contract unchanged; existing DB schema + existing API shapes unchanged.
  ✓ Inventory locks only after payment success (idempotent).
  ✓ No fabricated data; numbers trace to assessments or labeled seeds.
  ✓ Phase deliverable demoable.

═══════════════════════════════════════════════════════════════
7. OUTPUT FORMAT (per phase)
═══════════════════════════════════════════════════════════════
For each phase, return in this order:
  1. What I read (files) and what already existed.
  2. Files CREATED (paths).
  3. Files MODIFIED — table: file | exact change | why necessary | why it can't
     break existing behavior. (Empty if additive-only.)
  4. New endpoints / data contracts.
  5. Tests added + results of running existing + new suites (green/green).
  6. "Existing-code impact: NONE" or the justified list.
  7. How to demo this phase.

═══════════════════════════════════════════════════════════════
8. GUARDRAILS RECAP (read again before each phase)
═══════════════════════════════════════════════════════════════
  - Plan first. No code before approval.
  - ADD, don't modify. Touch existing files only when unavoidable and justified.
  - ml/ is frozen. Existing battery-domain schema + endpoints are frozen.
  - No hallucinated symbols, libraries, columns, endpoints, or data.
  - Inventory locks only after payment. Porter-only logistics. SaaS-only revenue.
  - Keep all existing tests green at every step. Stop and ask if blocked.
```
