# PHASE 07 READINESS — Marketplace Discovery (Map, Search, Seller Profile)

## Phase Goal
- Add interactive buyer discovery to the frontend, allowing buyers to search, filter, and discover batteries.
- Implement an interactive vector-based India map showing supplier locations. Clicking a supplier highlights their profile and displays their active inventory.
- Implement a search and filtering panel supporting filtering by: grade (S, A, B, C), chemistry (NMC, LFP), total capacity, quantity, and supplier location.
- Render detailed data-driven inventory cards showing battery specs: Grade, SoH, SoC (nominal), RUL years, chemistry, capacity per pack, total capacity, MOQ, quantity, quantity-based pricing tiers, and AI use cases.
- Integrate the AI Requirement Matcher (Phase 6) into the shop interface, allowing buyers to type a use case, retrieve matches, and view them immediately.

## Prerequisites
- Completed phases: **Phase 4** (Supplier Config & Publish), **Phase 5** (Buyer Access & Accounts), **Phase 6** (Gemini AI Requirement Builder & Matching).
- Existing backend routes:
  - `GET /api/v1/marketplace/lots` (lists published inventory lots).
  - `GET /api/v1/requirements/{id}/matches` (retrieves matches for a requirement).
  - `GET /api/v1/suppliers` or `/api/v1/suppliers/{id}` (to read supplier profile info). Wait, let's verify if a backend route to list suppliers exists.

## Required Inputs
- DB Models: `Supplier`, `InventoryLot`, `Listing`, `PricingTier`.
- Backend endpoints:
  - `GET /api/v1/marketplace/lots`: Ensure search/filter parameters can be passed (or handled client-side).
  - `GET /api/v1/suppliers` (list all verified suppliers with locations for the map). Wait, we should verify if this endpoint exists on the backend. Let's check `suppliers.py` to see if there is an endpoint to list suppliers.
- Frontend components:
  - Integration within `Marketplace.tsx` or a new path `/shop` (under `src/pages/Shop.tsx`). The plan suggests putting new commerce flow under `/shop`.

## Team Ownership
- Frontend Team (India map visualization, search panel, seller profile modal, inventory card display, integration with backend).
- Backend Team (Adding query parameters for filters on listings if needed, list suppliers route).

## External Dependencies
- React + Vite.
- Custom vector SVG (No external mapping key required, runs 100% keyless and offline).

## Blocking Risks
- Slow loading or missing tile maps.
  - *Mitigation:* Use a custom vector SVG outline of India with plotted coordinates representing cities. This is self-contained, offline-compatible, matches the dark HUD styling, and has zero external dependencies.
- Missing endpoints to query suppliers list for map markers.
  - *Mitigation:* Ensure a `GET /api/v1/suppliers` endpoint is exposed to retrieve all suppliers with their locations.

## Readiness Checklist
- [x] Backend test suite is fully green.
- [x] Database contains `Supplier`, `InventoryLot`, and `Listing` data models.
- [x] Local environment supports keyless vector rendering.

## Phase Exit Criteria
- Frontend renders an interactive India vector map displaying supplier hubs (Mumbai, Pune, Bangalore, Delhi, Chennai, Hyderabad).
- Clicking a seller highlights their location, displays a seller profile card, and filters the listed inventory.
- Filters (grade, chemistry, MOQ, capacity) instantly filter the active listings in real time.
- Inventory cards display all battery metrics (SoH, nominal SoC, RUL, chemistry, capacity per battery + total, MOQ, quantity, quantity pricing tiers, and AI use cases).
- Natural language requirement builder is functional, allowing text input and showing matched listings with compatibility scores (0-100%).
