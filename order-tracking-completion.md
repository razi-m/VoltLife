# VoltLife Marketplace — Phase 12: Order Tracking & Delivery Completion (buyer)

This plan outlines the steps to implement and verify Phase 12 of the VoltLife Marketplace, enabling buyers to confirm receipt of delivered orders and raise support tickets for issues.

## Project Type
- **WEB** (React/FastAPI Web Application)

## Success Criteria
- Buyers can click **"Confirm Receipt"** on delivered orders, transitioning the order's `tracking_status` to `"completed"`.
- Buyers can click **"Raise Issue"** on any order to submit a description text, creating a `SupportTicket` in the database.
- Database records for support tickets are verified.
- The UI reflects order tracking state updates and provides interactive buttons.
- All integration tests pass cleanly.

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy (PostgreSQL).
- **Frontend**: React, TypeScript, Tailwind CSS / Custom CSS.

## File Structure
- `backend/app/routers/logistics.py` — Add Confirm Receipt and Raise Issue routes.
- `backend/tests/test_order_completion.py` — New test suite for Phase 12.
- `frontend/src/lib/api.ts` — Add API helpers.
- `frontend/src/pages/Marketplace.tsx` — Add UI buttons, dialogs, and states.

---

## Proposed Changes

### [Backend] Phase 12: Order Tracking & Delivery Completion

#### [MODIFY] [logistics.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/logistics.py)
* Add `"completed"` to `VALID_STATES`.
* Add `POST /api/v1/logistics/orders/{order_id}/confirm-receipt`
  - Validates buyer authentication.
  - Verifies order exists and belongs to the buyer.
  - Ensures current status is `"delivered"`.
  - Transitions state to `"completed"`, adds a `ShipmentTrackingEvent`, and broadcasts the state change over WebSockets.
* Add `POST /api/v1/logistics/orders/{order_id}/raise-issue`
  - Body: `{"issue_text": str}`
  - Validates buyer authentication.
  - Verifies order exists and belongs to the buyer.
  - Creates and commits a `SupportTicket`.

### [Frontend] Phase 12: Client Integration

#### [MODIFY] [api.ts](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/lib/api.ts)
* Add client helpers:
  - `logistics.confirmReceipt(orderId)`: `POST /api/v1/logistics/orders/{orderId}/confirm-receipt`
  - `logistics.raiseIssue(orderId, issueText)`: `POST /api/v1/logistics/orders/{orderId}/raise-issue`

#### [MODIFY] [Marketplace.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/Marketplace.tsx)
* Update the "My Quotes & Orders" view.
* Show the active `tracking_status` on the order card.
* If `tracking_status` is `"delivered"`, show a **"Confirm Receipt"** button.
* If `tracking_status` is not `"completed"`, show a **"Raise Issue"** button.
* Add a simple Raise Issue modal/dialog that prompts the buyer for `issue_text` and submits it.
* Display support tickets associated with the order or a status indicator ("Issue Raised").

---

## Task Breakdown

### Task 12.1: Implement Backend Routes for Phase 12
- **Agent**: `backend-specialist`
- **Skill**: `api-patterns`
- **Priority**: High
- **Dependencies**: None
- **INPUT**: Existing order and support ticket models in DB.
- **OUTPUT**: Two new routes in `logistics.py` with auth protection.
- **VERIFY**: Check routes exist in Swagger docs at `http://localhost:8000/docs`.

### Task 12.2: Implement Frontend API and UI Elements
- **Agent**: `frontend-specialist`
- **Skill**: `frontend-design`
- **Priority**: High
- **Dependencies**: Task 12.1
- **INPUT**: React `Marketplace.tsx` and `api.ts`.
- **OUTPUT**: Confirm Receipt and Raise Issue actions wired to backend, UI stepper updated with `"completed"` state.
- **VERIFY**: Verify frontend loads in browser and compiles without TypeScript/lint warnings.

### Task 12.3: Integration Tests
- **Agent**: `test-engineer`
- **Skill**: `testing-patterns`
- **Priority**: High
- **Dependencies**: Task 12.1
- **INPUT**: New `backend/tests/test_order_completion.py` test suite.
- **OUTPUT**: Green tests for receipt confirmation, invalid state guards, unauthorized access, and support ticket creation.
- **VERIFY**: Run `pytest backend/tests/test_order_completion.py`.

---

## Phase X: Final Verification

- [ ] Run master checklist script: `python .agents/scripts/checklist.py .`
- [ ] No purple/violet color hex codes added.
- [ ] UI looks premium with Terminal Dark styling and sharp layouts.

## ✅ PHASE X COMPLETE
- Lint: [ ]
- Security: [ ]
- Build: [ ]
- Date: [Pending]
