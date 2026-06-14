# VoltLife Master Issue Report — Local Workspace Only

This report documents the results of a comprehensive local-only audit of the VoltLife codebase to identify missing features, broken integrations, incomplete workflows, route gaps, UI issues, backend bugs, marketplace vulnerabilities, and architectural violations.

---

## SECTION 1 — Workspace Verification

* **Current Workspace Path**: `c:\Users\Razi\Claude\Projects\VoltLife`
* **Current Git Branch**: `master`
* **Latest Commit Hash**: `078757c341c581544b941448b0f3f0000fdf1682`
* **Local Uncommitted Changes**: Yes, local uncommitted modifications are visible (specifically the fix made to [Assess.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Assess.tsx)).
* **Audit Target**: The audit was performed strictly against the local files present in the current workspace.

---

## SECTION 2 — Feature Completeness Audit

### Battery Assessment
* **SOH Calculation**: Verified. SOH is calculated dynamically in [stub_predictor.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/stub_predictor.py) as `100.0 - capacity_fade_pct` (derived from the ratio between current capacity `capacity_now_kwh` and `rated_capacity_kwh`).
* **SOC Calculation**: **MISSING**. State of Charge is entirely absent from the database ORM models ([orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py)) and backend telemetry processing. In the marketplace UI ([Marketplace.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Marketplace.tsx) line 1131), it is static/hardcoded as `"SoC (Sim) 100%"`.
* **RUL Prediction**: Verified. Remaining Useful Life (RUL) cycles are predicted using a linear interpolation factor `(soh_pct - 60.0) / 40.0` scaled to a maximum of 2,400 cycles, and converted to years using `rul_cycles / 300.0` in [stub_predictor.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/stub_predictor.py).
* **Grade Generation**: Verified. Employs grading rules assigning grades S, A, B, C, or D based on SOH, cycle counts, thermal stress hours, internal resistance growth, and prediction confidence.
* **Confidence Score**: Verified. Employs rules assigning `high`, `medium`, or `low` based on the number of missing/NaN telemetry features and cycle count thresholds.
* **Assessment Details Page**: Verified. Accessible and functional in [Assess.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Assess.tsx).

---

### Deployment Engine
* **Deployment Recommendation Generation**: Verified. Executed in [recommend.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/recommend.py) using a multi-criteria scoring algorithm considering capacity match, grade headroom, proximity, carbon benefit, and site priority.
* **Use Case Recommendation Generation**: Verified. Maps graded batteries to site types (e.g., `solar_storage`, `industrial_backup`, `rural_microgrid`, `ev_charging_buffer`) matching the site's min-SOH and min-grade constraints.
* **Recommendation Display UI**: Verified in [Assess.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Assess.tsx).
* **Recommendation API Integration**: Verified via `/api/v1/batteries/ingest` and `/api/v1/batteries/{id}` detail routes.
* **Recommendation Data Flow**: Traced from frontend ingest submission -> parsing -> telemetry summary insert -> ML pipeline -> `decide_deployment` -> DB write -> detail retrieval.

#### Investigation: "No deployment recommendation yet" Fallback
* **Root Cause**: The default frontend `DEMO_BATTERY` object in [Assess.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Assess.tsx) lacked 6 optional telemetry keys: `fade_rate`, `fade_acceleration`, `cv_phase_fraction`, `voltage_slope`, `voltage_variance`, and `discharge_efficiency`. 
  - During intake, the feature builder in [features.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/features.py) mapped these missing keys to `NaN`.
  - In [stub_predictor.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/stub_predictor.py), any intake featureset with more than 3 `NaN` values is demoted to `low` confidence.
  - In [deployment.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/services/deployment.py), a battery with `low` confidence is status-routed to `"inspection"` instead of matching a site. No `Deployment` record is inserted.
  - As a result, the API returned `deployment: null` and the UI fell back to `"No deployment recommendation yet."`
* **Fix Applied**: Patched [Assess.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Assess.tsx) to include realistic mock values for all 6 telemetry fields in the `DEMO_BATTERY` object, restoring the high-confidence classification and successful site matching.

---

### BPAN Registry
* **Registry Page**: Verified in [Registry.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Registry.tsx).
* **Registry APIs**: Verified via `/api/v1/aadhaar/{id}` decoding and timeline endpoints.
* **Registry Records Display**: Lists all registered batteries with their status and identity codes.
* **Search Functionality**: Supports searching records by external reference or Aadhaar/BPAN ID.
* **Details Page**: Decodes and displays QR-code payload, static/dynamic telemetry parameters, and lifecycle ledger logs.

---

### Volt AI
* **Gemini Integration**: Verified in [ai.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/ai.py) and [gemini.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/services/gemini.py).
* **Requirement Builder**: Verified. Converts free-form text input into SOH/Grade/Capacity structures.
* **Prompt Flow**: Formulates prompts matching JSON templates and feeds them to the Gemini API.
* **Response Rendering**: Displays parsed results on the frontend Volt AI page.
* **Error Handling**: Implements a regex-based `parse_use_case_fallback` to parse text locally if the Gemini API fails or is unreachable.

---

### Marketplace
* **Marketplace Page**: Verified in [Marketplace.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Marketplace.tsx).
* **India Map**: Verified in [IndiaMap.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/components/IndiaMap.tsx) showing site demand densities.
* **Seller Discovery**: Verified; lists active registered sellers.
* **Seller Profiles**: Verified; lists listings and lots filtered by supplier.
* **Inventory Listings**: Verified; lists published listings.
* **Buyer Requirements**: Verified; submits new requirements.
* **Quote Flow**: Verified; allows requesting quotes from matching listings.
* **Payment Flow**: Verified; uses Stripe mock checkouts or Razorpay order verification.
* **Tracking Flow**: Verified; updates logistics tracking events in real time.

---

## SECTION 3 — Seller Portal Audit

* **Seller / Supplier Login**: Verified in [LoginPage.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/LoginPage.tsx) using the `/api/v1/suppliers/login` endpoint.
* **Role-Based Access Control**: Verified. Frontend implements `<SellerOnly>` and `<BuyerOnly>` route guards in [App.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/App.tsx).
* **Seller Dashboard Page**: Verified in [SellerDashboard.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/SellerDashboard.tsx).
* **Seller Dashboard Route**: Registered at `/seller-dashboard`.
* **Seller Dashboard Navigation**: Enforced in [Sidebar.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/components/layout/Sidebar.tsx).
* **Seller Inventory View**: Displays available lots, drafts, and listing states.
* **Seller Orders View**: Displays orders, payment status, and order details.
* **Seller Requirements Feed**: Displays active buyer requirements in the marketplace.
* **Seller Revenue Display**: Shows total earnings in Rupees based on paid orders.

#### Audit Observations
1. **Sidebar Link Visibility**: The `Seller Panel` link is only visible when the user is logged in as a supplier (`supplier_token` in localStorage). When not logged in, the link is hidden, which is the expected behavior.
2. **Missing Logout/Login Buttons**: The sidebar has no Login or Logout button. Once logged in, there is no visual way to log out or switch roles without typing `/login` in the address bar or manually clearing localStorage.

---

## SECTION 4 — Buyer Portal Audit

* **Buyer Access**: Accesses `/marketplace` through the sidebar.
* **Requirement Submission**: Verified via the VoltAI requirement form.
* **Requirement Editing**: **MISSING**. No PUT/PATCH endpoints exist in [requirements.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/requirements.py).
* **Requirement Tracking**: **MISSING**. Buyers cannot list their past requirements or track their status; once they navigate away, the active requirement ID is lost.
* **Order Tracking**: Verified. Renders tracking events and allows buyers to mark orders as delivered/completed.
* **Marketplace Browsing**: Lists all active published lots and listings.

---

## SECTION 5 — Navigation Audit

All sidebar links map to active, compiled components:
* `Mission Control` -> `/dashboard` (Dashboard.tsx) — Functional.
* `Battery Intake` -> `/assess` (Assess.tsx) — Functional (fixed fallback).
* `BPAN Registry` -> `/registry` (Registry.tsx) — Functional.
* `Deployment` -> `/deploy` (Deploy.tsx) — Functional.
* `Analytics` -> `/analytics` (Analytics.tsx) — Functional.
* `Impact` -> `/impact` (Impact.tsx) — Functional.
* `Volt AI` -> `/ai` (AI.tsx) — Functional.
* `Marketplace` -> `/marketplace` (Marketplace.tsx) — Functional (visible by default to guests/buyers).
* `Seller Panel` -> `/seller-dashboard` (SellerDashboard.tsx) — Functional (visible only to logged-in suppliers).

#### Broken Links & Navigation Gaps
* **Guest Sidebar Access**: Guests/anonymous users can click on all shared sidebar items (e.g., Mission Control, Battery Intake) despite not being authenticated. While the views render, API calls fail with 401 errors.
* **Missing Gateway Entry**: No header or sidebar link allows navigating to `/login`.
* **Missing Logout Trigger**: No sign-out button exists in the sidebar.

---

## SECTION 6 — Backend Audit

* **FastAPI Startup**: Successful on port 8000.
* **Database Connectivity**: Successful. Connected to Supabase PostgreSQL database.
* **ORM Models**: Consistent column types and indices.
* **Authentication / Authorization**: Verified using JWT bearers for both buyers and suppliers.
* **Marketplace & Dashboard Endpoints**: Verified.

#### Audit Observations
* **Test Database Lock Contention**: Running the pytest suite in the sandbox while the FastAPI dev server is active causes test fixtures to hang on `Base.metadata.drop_all(bind=engine)`. This occurs because uvicorn maintains active connection pools that hold table locks.
* **Database Host IPv6 Issue**: The direct connection database URL `db.lzflstkuwyhxujmalpoe.supabase.co` resolves strictly to IPv6 addresses. In environments without IPv6 routing/DNS resolution (such as sandbox containers), connection attempts fail with `OperationalError: could not translate host name`. (Workaround: Use the IPv4 connection pooler address `aws-1-ap-southeast-1.pooler.supabase.com` on port 5432).

---

## SECTION 7 — Frontend Audit

* **Compilation**: Successful compilation using Vite React TS.
* **Rendering**: Clean HSL theme styling, modern layout, no default unstyled templates.
* **Placeholder Content**: Minimal placeholders except for `SoC (Sim) 100%` in the marketplace listing lot cards.
* **Dead Buttons**: None identified.
* **Missing Integrations**:
  - Razorpay checkout component is present in [RazorpayCheckout.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/components/RazorpayCheckout.tsx) but is unused in the main checkout flow if Stripe checkout is triggered.

---

## SECTION 8 — Architecture Compliance Audit

* **ML Model Integration Mismatch**: The trained `model_v1.pkl` resides under `ml/models/`, but [predictor.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/ml/predictor.py) delegates all calls to the simulated stub predictor instead of loading the pickle file and running inference.
* **Payment Redundancy**: Both Stripe and Razorpay integrations exist in parallel, contrary to the documentation stating Razorpay was purged.
* **Subscription Gating**: Gating for SaaS subscriptions is actively enforced on supplier endpoints via `get_current_active_subscriber`, although SaaS billing was documented as out-of-scope for the core demo platform.
* **State of Charge (SOC) Omission**: No database fields or API logic exist for State of Charge, violating the full battery parameter tracking requirement.

---

## SECTION 9 — Critical Issues

### P0 — Demo Blocking
1. **Missing Login/Logout Sidebar Buttons**: Judges cannot switch roles or sign out without manually typing `/login` in the URL or clearing browser data.
   - *Impact*: High risk of confusion during the live demo walk-through.
   - *Recommended Fix*: Add a "Log Out" button at the bottom of the sidebar when a role is active, and a "Sign In" button when guest mode is active.
2. **Database Host IPv6 Only (Local Run)**: Running backend tests or starting uvicorn in local sandboxes without IPv6 support crashes the application.
   - *Impact*: Dev environment cannot boot or test database features.
   - *Recommended Fix*: Configure `DATABASE_URL` in `.env` to point to the IPv4 pooler connection string.

### P1 — High Priority
1. **ML Inference Bypassed**: Model predictions are processed using mock logic in `stub_predictor.py` rather than loading the trained `model_v1.pkl` model.
   - *Recommended Fix*: Update `predictor.py` to load the pickle file using `pickle.load()` and run model inference on the 14-key feature vector.
2. **No Buyer Requirement Listing/Management**: Buyers cannot edit, delete, or list previously submitted requirements.
   - *Recommended Fix*: Implement GET, PUT, and DELETE endpoints in [requirements.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/requirements.py) and render a "My Requirements" tab in the marketplace.

### P2 — Medium Priority
1. **Hardcoded State of Charge (SOC)**: Omission of dynamic SOC tracking from the database schema and telemetry summaries.
   - *Recommended Fix*: Add a `state_of_charge_pct` column to `TelemetrySummary` and expose it in the marketplace API and UI.
2. **Razorpay and Stripe Code Redundancy**: Redundant payment adapters and routes increase complexity.
   - *Recommended Fix*: Refactor payments to cleanly expose a single provider or maintain the current fallback documentation.

### P3 — Nice To Have
1. **Unprotected Shared Pages**: Guests can access shared dashboard analytics pages and trigger failed 401 API calls.
   - *Recommended Fix*: Add an authentication check in `AppLayout` to redirect guests to `/login` if no valid token exists.
