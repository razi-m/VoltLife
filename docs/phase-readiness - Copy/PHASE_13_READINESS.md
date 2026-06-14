# PHASE 13 READINESS — Seller Dashboard (BASIC ONLY)

## Phase Goal
- Provide verified suppliers (sellers) with a dedicated dashboard to monitor their current inventory levels, view active and completed orders, view a summary of their sales/revenue (total paid orders value in INR), and browse active buyer requirements.
- Strictly limit seller access: no competing sellers' listings, pricing, or details, and no advanced analytics, heatmaps, or forecasting.

## Prerequisites
- Completed phases: **Phase 2** (Supplier Registration & Auth), **Phase 3 & 4** (Inventory Upload & Config), and **Phase 9/11/12** (Payments, Logistics, and Order Completion).
- Existing database tables: `suppliers`, `supplier_users`, `inventory_lots`, `orders`, and `requirements` in `marketplace_orm.py`.

## Required Inputs
- DB Models: `Supplier`, `InventoryLot`, `Order`, `Requirement`, `BuyerAccount`.
- Endpoints to add:
  - `GET /api/v1/suppliers/dashboard/stats`
    - Input: Authenticated supplier user.
    - Output: `{ active_lots_count: int, completed_orders_count: int, pending_orders_count: int, available_batteries: int, total_revenue_rupees: float }`
    - **available_batteries** (FIX 6): total remaining batteries across all the supplier's ACTIVE inventory lots. Sellers need visibility into remaining stock.
    - **total_revenue_rupees** (FIX 1): sum of `order_value` for THIS supplier's orders where `payment_status = SUCCESS` **only**. Do NOT use "Delivered Orders Only", "Pending Orders", or "Draft Orders".
  - `GET /api/v1/suppliers/dashboard/inventory`
    - Input: Authenticated supplier user.
    - Output: List of lots owned by the supplier (ID, grade, chemistry, available_quantity, SOH, RUL, status, listing title/moq/is_published).
    - **capacity_per_battery_kwh** (FIX 4, MANDATORY): capacity of a single battery, e.g. `2.0` kWh.
    - **total_capacity_kwh** (FIX 5, MANDATORY): `capacity_per_battery_kwh × available_quantity`, e.g. `276` kWh.
  - `GET /api/v1/suppliers/dashboard/orders`
    - Input: Authenticated supplier user.
    - Output: List of orders matching the supplier (ID, quantity, total price, payment status, tracking status, created_at, buyer company, buyer email, lot chemistry, lot grade).
  - `GET /api/v1/suppliers/dashboard/requirements`
    - Input: Authenticated supplier user.
    - Output (FIX 2): **ACTIVE buyer requirements ONLY** — exclude expired, fulfilled, archived, and historical requirements. Sellers should only see current market demand.
    - Response fields (FIX 3 — EXACTLY these, with **NO `buyer_email`** or any personal buyer contact info): `requirement_id`, `use_case_text`, `parsed_grade`, `parsed_capacity_kwh`, `parsed_quantity`, `buyer_company`, `location`, `created_at`.

## Team Ownership
- Backend Team (routers, endpoints, tests).
- Frontend Team (Seller Dashboard UI, API integration, and Vanilla CSS styling).

## External Dependencies (Required | Optional | Mockable)
- PostgreSQL database (Required).
- JWT Authentication (Required).

## Blocking Risks
- Information leakage: A seller viewing another seller's orders, inventory, or pricing.
  - *Mitigation:* Restrict all dashboard endpoints using `get_current_supplier` and query only records where `supplier_id == supplier.id`.
- Scope creep: Adding graphs/charts or advanced forecast analytics.
  - *Mitigation:* Keep UI simple and text/table-based with clean metrics cards, strictly adhering to "BASIC ONLY".

## Readiness Checklist
- [x] Verified `suppliers`, `inventory_lots`, `orders`, and `requirements` tables exist and contain appropriate relationships in `marketplace_orm.py`.
- [x] Verified frontend authentication mechanisms retrieve and store the supplier token/access.
- [x] Designed the UI layout for Seller Dashboard: Inventory table, Orders log, Revenue panel, and Requirements feed.

## Phase Exit Criteria
- Verified suppliers can view their dashboard showing their inventory status (draft/listed/sold out).
- Suppliers can view their active and completed orders with correct payment/tracking status.
- Suppliers can see their total sales/revenue correctly calculated and displayed.
- Suppliers can view active buyer requirements to see market demand.
- Integration tests verify authentication, data scoping (sellers only see their own data), and endpoint outputs.

## Validation Requirement (PHASE 13 READINESS PATCH)
After implementing Phase 13, verify:
- [ ] Revenue (`total_revenue_rupees`) is based ONLY on successful payments (`payment_status = SUCCESS`).
- [ ] Requirements feed contains ONLY active requirements (no expired/fulfilled/archived/historical).
- [ ] No buyer email leakage — `/dashboard/requirements` exposes none of the buyer's personal contact info.
- [ ] Inventory returns BOTH `capacity_per_battery_kwh` and `total_capacity_kwh`.
- [ ] Dashboard stats include `available_batteries`.
- [ ] No other Phase 13 behavior is modified.
