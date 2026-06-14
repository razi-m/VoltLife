# PHASE 10 READINESS — n8n Orchestration (Post-Payment Automations)

## Phase Goal
- Set up the post-payment automation using an importable n8n workflow file and a backend notification/callback structure.
- Support two execution paths:
  1. **DEFAULT — In-app simulation:** Run a mock sequence/background task in the FastAPI backend when `N8N_ENABLED=false` or `N8N_WEBHOOK_URL` is unset, simulating the logistics state transitions.
  2. **OPTIONAL — Real n8n instance integration:** If `N8N_ENABLED=true` and `N8N_WEBHOOK_URL` is set, trigger a POST webhook payload to n8n upon payment confirmation. Provide a callback endpoint (`POST /api/v1/logistics/callback`) for n8n to advance the order tracking states.
- Generate the n8n importable JSON workflow file (`n8n/voltlife_logistics_workflow.json`) and setup documentation (`n8n/README_SETUP.md`).

## Prerequisites
- Completed phases: **Phase 9** (Payment and Stock Locking).
- Existing tables/models: `Order` and `PaymentEvent` (to trace paid orders).
- The test suite is fully passing (30/30).

## Required Inputs
- Endpoint logic:
  - Trigger webhook inside payment processing: When payment succeeds, check if n8n is enabled and trigger the POST call.
  - Endpoint `POST /api/v1/logistics/callback`
    - Input: `{"order_id": int, "status": str}`
    - Return: `{"status": "success", "order_id": int, "new_state": str}`
- Env Variables (additive in `.env.example` and `.env`):
  - `N8N_ENABLED` (boolean, default: `false`)
  - `N8N_WEBHOOK_URL` (string, optional webhook target)
- Files to create:
  - `n8n/voltlife_logistics_workflow.json`
  - `n8n/README_SETUP.md`

## Team Ownership
- Backend Team (Webhook dispatcher, callback endpoints, mock background/in-app state advance simulator, and automated test cases).

## External Dependencies (Required | Optional | Mockable)
- n8n instance (Optional / Mockable via the fallback in-app simulation path).
- PostgreSQL database (Required for updating order states).

## Blocking Risks
- **Network timeouts & failures in n8n triggers:** If the n8n server is down or slow, it shouldn't block the HTTP request confirming payment.
  - *Mitigation:* Fire the n8n webhook call asynchronously (e.g., using FastAPI background tasks) so that any network errors or latency do not affect payment confirmation responsiveness.
- **Unauthorized callbacks to state-machine:** A malicious client calling `/api/v1/logistics/callback` to change order states.
  - *Mitigation:* Implement a demo-guard or mock-auth token validation on the callback route, or limit callback state transitions to valid next states.

## Readiness Checklist
- [x] Verified Phase 9 tests passed.
- [x] Checked existing order tracking status fields in database ORM (`Order.tracking_status` supports states like `confirmed`).
- [x] Defined dual-execution design (in-app fallback vs real n8n webhook/callback).

## Phase Exit Criteria
- Webhook trigger code successfully fires when payment is confirmed (asynchronously via background tasks).
- Callback endpoint `POST /api/v1/logistics/callback` is fully operational and advances the order tracking state in database.
- An importable `n8n/voltlife_logistics_workflow.json` is generated with the Webhook node, Mock Porter booking payload constructor, and callback HTTP request node.
- Setup instructions are documented in `n8n/README_SETUP.md`.
- Automated test coverage verifies:
  - Webhook dispatch logic (mocked HTTP client).
  - Callback endpoint state transition validation and idempotency.
  - In-app fallback state simulation triggers correctly.
