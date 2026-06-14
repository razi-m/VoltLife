# PHASE 12 READINESS — Order Tracking & Delivery Completion (buyer)

## Phase Goal
- Allow buyers to view details of their orders, confirm receipt upon delivery (transitioning the order's tracking status to `"completed"`), and raise support tickets for issues (creating a `SupportTicket` entry).

## Prerequisites
- Completed phases: **Phase 11** (Logistics Simulation & Tracking UI).
- Existing database schema: `orders` and `support_tickets` in `marketplace_orm.py`.
- Available endpoints: `GET /api/v1/payments/orders` (list orders) and `GET /api/v1/logistics/orders/{order_id}/tracking` (tracking status).

## Required Inputs
- DB Models: `Order`, `SupportTicket`, `BuyerAccount`.
- API request payloads:
  - `POST /api/v1/logistics/orders/{order_id}/confirm-receipt`
    - Input: None (authenticated buyer context).
  - `POST /api/v1/logistics/orders/{order_id}/raise-issue`
    - Input: `{"issue_text": str}`
- API response contracts:
  - Confirm Receipt: `{"status": "success", "order_id": int, "new_state": "completed"}`
  - Raise Issue: `{"status": "success", "ticket_id": int, "order_id": int, "issue_text": str}`

## Team Ownership
- Backend Team (routers, endpoints, tests).
- Frontend Team (My Orders panel update, Confirm Receipt / Raise Issue CTAs, and issue modal form).

## External Dependencies (Required | Optional | Mockable)
- PostgreSQL database (Required).

## Blocking Risks
- Unauthenticated or unauthorized state changes: Let non-owners confirm receipt or raise tickets.
  - *Mitigation:* Enforce `get_current_buyer` and check `order.buyer_id == buyer.id`.
- Confirming receipt on orders that have not been delivered.
  - *Mitigation:* Enforce that `order.tracking_status` must be `"delivered"` before allowing receipt confirmation.

## Readiness Checklist
- [x] Verified `orders` and `support_tickets` tables exist in `marketplace_orm.py` with foreign keys to `buyer_accounts`.
- [x] Verified Phase 11 endpoints and WebSocket listeners are running.
- [x] Decided simple state machine transition: Add `"completed"` as a valid status in `logistics.py`.

## Phase Exit Criteria
- Buyers can successfully click "Confirm Receipt" on delivered orders to set the tracking status to `"completed"`.
- Buyers can successfully submit support tickets via "Raise Issue" at any state, creating a `SupportTicket` record.
- Backend integration tests verify status checks, ownership guards, state transitions, and DB updates.
- Frontend displays active order lists with interactive CTAs for Confirm Receipt (only on "delivered" status) and Raise Issue.
