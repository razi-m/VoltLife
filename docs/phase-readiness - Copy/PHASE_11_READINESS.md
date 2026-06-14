# PHASE 11 READINESS — Logistics Simulation & Tracking UI (End-to-End Visualizer)

## Phase Goal
- Implement the frontend client interface for VoltLife's transaction flow: Quote checkout, payment confirmation, and real-time logistics tracking.
- Provide a dedicated order list and tracking view within the Marketplace dashboard.
- Display a real-time tracking progress stepper supporting sequential states: `confirmed` ➔ `porter_booked` ➔ `seller_notified` ➔ `buyer_notified` ➔ `shipment_started` ➔ `in_transit` ➔ `delivered`.
- Update state dynamically on the frontend via WebSocket feed broadcasts when events trigger on the backend.
- Build a simulation controller panel on the order tracking view to manually advance states or kick off the full n8n/in-app simulation, providing a complete interactive demo experience.

## Prerequisites
- Completed phases: **Phase 10** (n8n Orchestration / Post-Payment Logistics callback backend).
- Available backend endpoints:
  - `POST /api/v1/quotes` & `GET /api/v1/quotes/{quote_id}`
  - `POST /api/v1/payments/checkout-session` & `POST /api/v1/payments/mock-confirm`
  - `POST /api/v1/logistics/callback`
- WebSockets active on `/ws/feed`.
- Standard test suite fully green (32/32).

## Required Inputs
- Frontend Pages/Components to build or update:
  - Update `api.ts` to support Quotes, Payments, and Callback actions.
  - Create/Update Marketplace tab or Modal to view active Quotes, pay them (redirect to Stripe or trigger Mock checkout confirm), and list Orders.
  - Create a dedicated **Order Tracker Component** containing:
    - Order summary (Lot purchased, price, quantity).
    - Simulated Porter details (Vehicle recommended, estimated weight, transit cost).
    - Interactive Stepper component showing active status with color-coded steps.
    - **Simulation Control Panel** containing:
      - "Run Auto-Simulation" button (triggers background transition loop).
      - "Advance State Manually" dropdown/buttons (triggers callback endpoint directly for manual step-by-step testing).
  - WebSocket handler to catch `order_tracking_update` and update state in real-time.

## Team Ownership
- Frontend Team (API helper extensions, Marketplace tab UI integration, visual tracking stepper, WebSocket live listener, and simulation controls).
- Backend/QA Team (Manual end-to-end sandbox validation).

## External Dependencies (Required | Optional | Mockable)
- PostgreSQL database (Required).
- WebSocket connection (Required for live update feeds).

## Blocking Risks
- **WebSocket connection state drops:** If the WebSocket client loses connection during a simulation, updates will not be received.
  - *Mitigation:* Ensure the UI periodically polls the database order status or has a manual refresh button to fetch the latest state from the API.
- **Stripe redirect loops:** Navigating back from stripe checkout.
  - *Mitigation:* Implement standard mock checkout session that operates entirely in-app, allowing developers and users to bypass external Stripe redirection and complete checkout in a single click.

## Readiness Checklist
- [x] Verified Phase 10 logistics callback and simulation tests pass cleanly.
- [x] Defined all tracking states on backend (`confirmed`, `porter_booked`, `seller_notified`, `buyer_notified`, `shipment_started`, `in_transit`, `delivered`).
- [x] Confirmed WebSocket feed broadcasts events correctly in `logistics.py`.

## Phase Exit Criteria
- Frontend API helper supports full checkout, payment confirmation, and logistics manual callback endpoints.
- Marketplace UI has a clear way to see quotes, trigger mock checkout, and list purchased orders.
- Clicking an order shows the **Order Tracker View** with a progress stepper reflecting the current logistics state.
- Triggering the auto-simulation updates the progress stepper in real-time without reloading the page, powered by WebSocket broadcasts.
- The manual simulation controller is fully operational, permitting step-by-step state advancement.
- E2E manual walkthrough is verified and documented.
