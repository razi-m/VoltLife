# Implementation Plan — Phase 14: SaaS Subscription Billing

Add SaaS subscription billing for suppliers (Monthly, Annual, and Enterprise plans) via simulated Razorpay checkouts, and enforce plans gating supplier access to the Seller Dashboard.

---

## User Review Required

Please review and confirm the following design and gating decisions:

> [!IMPORTANT]
> **Subscription Plans & Pricing Tiers:**
> 1. **Monthly Plan**: ₹5,000/month. Access to all standard dashboard features.
> 2. **Annual Plan**: ₹50,000/year (16% discount). Access to standard features.
> 3. **Enterprise Plan**: ₹1,500,000/year. Access to premium custom support.
> 
> **Access Gating Policy:**
> Suppliers must have an active subscription to access core seller actions. The following endpoints will require an active subscription (`get_current_active_subscriber` dependency):
> - Ingestion / Uploading batteries (`POST /api/v1/suppliers/inventory/upload`)
> - Listing publish (`POST /api/v1/suppliers/inventory/lots/{lot_id}/publish`)
> - Seller Dashboard aggregate stats (`GET /api/v1/suppliers/dashboard/stats`)
> - Seller Dashboard inventory lists (`GET /api/v1/suppliers/dashboard/inventory`)
> - Seller Dashboard orders log (`GET /api/v1/suppliers/dashboard/orders`)
> - Seller Dashboard demand/buyer requirements feed (`GET /api/v1/suppliers/dashboard/requirements`)
> 
> Verified suppliers *without* an active subscription can still log in, check their subscription status (`GET /api/v1/subscriptions/status`), view plans (`GET /api/v1/subscriptions/plans`), and purchase a subscription.
>
> **Design and Layout:**
> The plan selection cards will be integrated directly into the `SellerDashboard.tsx` view as a replacement overlay when no active subscription exists. This keeps navigation unified and avoids adding unnecessary routing complexities. It will match the Terminal Dark HUD aesthetic (sharp 2px corners, thin grid borders, zero purple, dynamic hover effects).

---

## Open Questions

> [!NOTE]
> **Subscription Expiry Simulation:**
> - To make testing and demonstration easy for judges, we will add an expiration date `expires_at` column to the `saas_subscriptions` table.
> - We will include a debug action / mock payment flow in the frontend that creates an active subscription, and a "Force Expiration / Reset" button on the billing interface to let judges test both subscribed and unsubscribed states instantly.

---

## Proposed Changes

### Database Layer

#### [MODIFY] [marketplace_orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/marketplace_orm.py)
- Update `SaaS_Subscription` ORM model:
  - Add `expires_at = Column(DateTime(timezone=True), nullable=True)` to represent subscription expiry.
  - Ensure the fields and relationships map correctly.

#### [MODIFY] [seed.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/seed/seed.py)
- Update `seed_marketplace_demo_users(db)`:
  - Automatically seed an active `SaaS_Subscription` (Annual plan, expiring in 1 year) for the default `demo_supplier` account so the dashboard works out-of-the-box.

---

### Backend API Surface

#### [NEW] [subscriptions.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/subscriptions.py)
- Create a new router for managing SaaS subscriptions:
  - `GET /api/v1/subscriptions/plans`: Return plans details.
  - `GET /api/v1/subscriptions/status`: Return current active subscription details (or null).
  - `POST /api/v1/subscriptions/create-session`: Create a mock or real-test Razorpay subscription payment checkout session.
  - `POST /api/v1/subscriptions/verify`: Verify the payment token and create/activate the subscription in the DB.
  - `POST /api/v1/subscriptions/cancel`: Cancel or force-expire the current active subscription (for demo purposes).

#### [MODIFY] [main.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/main.py)
- Register the new subscriptions router:
  ```python
  from app.routers import subscriptions
  app.include_router(subscriptions.router)
  ```

#### [MODIFY] [suppliers.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/suppliers.py)
- Implement `get_current_active_subscriber` dependency helper:
  - Checks if the authenticated supplier has a valid, active subscription.
  - Automatically updates database status to `"expired"` if current time exceeds `expires_at`.
  - Raises `403 Forbidden` with detail `{"error": {"code": "subscription_required", "message": "..."}}` if inactive.
- Update endpoints to use `Depends(get_current_active_subscriber)` instead of `Depends(get_current_verified_supplier)`:
  - `POST /inventory/upload`
  - `POST /inventory/lots/{lot_id}/listing`
  - `POST /inventory/lots/{lot_id}/pricing`
  - `POST /inventory/lots/{lot_id}/publish`
  - `GET /inventory/lots/{lot_id}/listing`
  - `GET /dashboard/stats`
  - `GET /dashboard/inventory`
  - `GET /dashboard/orders`
  - `GET /dashboard/requirements`

---

### Frontend Subsystem

#### [MODIFY] [api.ts](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/lib/api.ts)
- Add subscription API actions:
  - `api.subscriptions.plans()`: `GET /api/v1/subscriptions/plans`
  - `api.subscriptions.status(token)`: `GET /api/v1/subscriptions/status`
  - `api.subscriptions.createSession(planName, token)`: `POST /api/v1/subscriptions/create-session`
  - `api.subscriptions.verify(sessionId, token)`: `POST /api/v1/subscriptions/verify`
  - `api.subscriptions.cancel(token)`: `POST /api/v1/subscriptions/cancel`

#### [MODIFY] [SellerDashboard.tsx](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/SellerDashboard.tsx)
- Integrate subscription state check in `useEffect`:
  - Fetch `/api/v1/subscriptions/status`.
  - Store `subscriptionStatus` (`{ status: string, plan_name: string | null, expires_at: string | null }`) in component state.
- **Conditional Interface Rendering**:
  - If subscription status is NOT `"active"`, overlay the page contents with a pricing plans grid selection panel.
  - Display plan cards showing prices, specs, and a `"Choose Plan"` button.
  - Implement mock payment modal (simulating Razorpay flow) with quick confirmation options.
  - If subscription status IS `"active"`, render the normal dashboard layout and append a clean header banner showing `"Active Plan: [Monthly|Annual|Enterprise] (Expires: DD/MM/YYYY)"` alongside a debug `"Cancel/Expire Subscription"` button.

#### [MODIFY] [SellerDashboard.css](file:///c:/Users/Razi/Claude/Projects/VoltLife/frontend/src/pages/SellerDashboard.css)
- Implement custom styling for the pricing plan cards:
  - High-fidelity dark HUD container with glassmorphic cards.
  - Accent colors: Electric Blue (`--primary`), Cyber Green (`--success`) for active plan. Zero purple brand colors.
  - Add micro-animations on hovering plan cards (slight lift, outline glow).

---

## Verification Plan

### Automated Tests
- Create a new test suite: `backend/tests/test_subscriptions.py`
  - Verify subscription endpoints (`/plans`, `/status`, `/create-session`, `/verify`).
  - Verify access is gated (stats, uploads, publishing return `403 Forbidden` if unsubscribed).
  - Verify auto-expiry logic (setting `expires_at` in the past triggers `"expired"` status and blocks access).
  - Run full suite: `pytest backend`.

### Manual Verification
1. Login as `demo_supplier`. Verify they are subscribed by default (Annual plan) and can access the dashboard.
2. Click the debug `"Cancel/Expire Subscription"` button. Verify dashboard content disappears and is replaced by the pricing plan cards.
3. Attempt to bypass by manually visiting dashboard endpoints. Verify the backend rejects with `403 Forbidden`.
4. Click `"Choose Plan"` for the Monthly plan, complete the simulated checkout, and verify the dashboard content unlocks immediately.
