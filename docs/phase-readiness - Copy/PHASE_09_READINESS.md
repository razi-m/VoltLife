# PHASE 09 READINESS — Payment (Stripe TEST/MOCK) + Inventory Locking + Order Creation

## Phase Goal
- Enable buyers to purchase bulk battery lots from generated quotes by entering simulated payment details (Stripe Test Checkout or local mock checkout).
- Atomically decrement/lock the inventory available quantity on successful payment confirmation.
- Create the Order record in the database (`orders` and `payment_events` tables) and transition quote status to `accepted`.
- Prevent double-allocation of inventory by ensuring payment confirmation is strictly idempotent.

## Prerequisites
- Completed phases: **Phase 8** (Quote Engine).
- Existing tables: `quotes`, `orders`, `payment_events`, `inventory_lots` (in `marketplace_orm.py`).
- Active auth middleware `get_current_buyer`.

## Required Inputs
- DB Models: `Quote`, `Order`, `PaymentEvent`, `InventoryLot`.
- API request payload:
  - `POST /api/v1/payments/checkout-session`
    - Input: `{"quote_id": int}`
    - Return: `{"session_id": str, "checkout_url": str}` (reaches Stripe test checkout or mock success url)
  - `POST /api/v1/payments/webhook` (or `/api/v1/payments/mock-confirm`)
    - Input: Webhook payload containing session ID, status.
    - Return: `{"status": "success", "order_id": int}`
- Env Variables (additive):
  - `STRIPE_SECRET_KEY` (optional, for test mode).
  - `STRIPE_WEBHOOK_SECRET` (optional, for test mode webhook validation).
  - `BACKEND_BASE_URL` (optional, defaults to `http://localhost:8000`).

## Team Ownership
- Backend Team (Payments router, Stripe integration service, checkout simulation, database transactions for inventory locking, and integration tests).

## External Dependencies (Required | Optional | Mockable)
- Stripe (Mockable/TEST: If `STRIPE_SECRET_KEY` is missing, the backend runs a local simulated checkout that does not require any external connections).
- PostgreSQL (Required).

## Blocking Risks
- Over-allocation / Race Conditions: Two buyers paying for the same inventory.
  - *Mitigation:* Perform available capacity checks before redirecting to checkout, and perform a final atomic quantity decrement inside the checkout completion transaction. If stock is exhausted at completion time, rollback, set order to failed, and simulate a refund.
- Non-Idempotent Webhooks: Duplicate webhook calls decrementing inventory twice.
  - *Mitigation:* Check for existing `PaymentEvent` records using the unique `stripe_session_id` as an idempotency key. Return 200 OK without processing if already completed.

## Readiness Checklist
- [x] Confirmed `orders` and `payment_events` tables are active in `marketplace_orm.py`.
- [x] Verified that pytest suite is 100% green from Phase 8.
- [x] Verified Stripe library is included or can be mock-simulated locally without installation.

## Phase Exit Criteria
- Buyers can request a checkout session for a pending quote.
- Successful simulated checkout creates an order and decrements available inventory quantity exactly once.
- Submitting the same checkout completion multiple times is idempotent (does not double-decrement stock or duplicate orders).
- Failed or cancelled payments leave inventory untouched.
- Integration tests in `backend/tests/test_payments.py` verify checkout creation, successful confirmation, inventory decrement, idempotency check, and failure scenarios.
