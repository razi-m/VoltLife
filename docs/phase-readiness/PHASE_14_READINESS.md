# PHASE 14 READINESS — SaaS Subscription Billing (demo)

## Phase Goal
- Provide simulated SaaS subscription billing for suppliers (Monthly, Annual, Enterprise plans) via a mock or test-mode Stripe checkout.
- Enforce plan gating: suppliers must have an active subscription to access core seller actions (uploading batteries, publishing listings, viewing dashboard details, or browsing buyer requirements).
- Ensure zero commissions, transaction fees, or marketplace cuts are taken on battery sales (VoltLife makes revenue solely through fixed SaaS subscriptions).

## Prerequisites
- Completed Phase 13 (Seller Dashboard & Role-Based Auth) with functional `demo_supplier` account.
- Existing database tables: `suppliers`, `saas_subscriptions` in `marketplace_orm.py`.

## Required Inputs
- DB Models: `Supplier`, `SaaS_Subscription` from `marketplace_orm.py`.
- Endpoints to add under `/api/v1/subscriptions`:
  - `GET /api/v1/subscriptions/plans`
    - Output: Available plans (`Monthly`: ₹5,000/mo, `Annual`: ₹50,000/yr, `Enterprise`: ₹1,500,000/yr custom) and features list.
  - `POST /api/v1/subscriptions/create-session`
    - Input: Authenticated supplier user, `{"plan_name": "Monthly" | "Annual" | "Enterprise"}`.
    - Output: `{ "session_id": str, "checkout_url": str }` (simulating Stripe checkout redirect or returning mock checkout params).
  - `POST /api/v1/subscriptions/verify`
    - Input: `{"session_id": str}`.
    - Output: Updated subscription status details (`{ "status": "active", "plan_name": str }`).
  - `GET /api/v1/subscriptions/status`
    - Input: Authenticated supplier user.
    - Output: Subscription status details (`{ "status": "active" | "inactive" | "expired", "plan_name": str | null, "expires_at": datetime | null }`).

## Team Ownership
- **Backend Team**: Implement subscription endpoints, mock Stripe payment adapters, database persistence, and integration of subscription gating checks.
- **Frontend Team**: Implement the subscription plans selection UI, subscription checkout flow modal, and route guards redirecting unsubscribed sellers to `/subscribe`.

## External Dependencies (Required | Optional | Mockable)
- PostgreSQL database (Required).
- Stripe Subscriptions (Mockable / TEST mode only via public keys).

## Blocking Risks
- **Supplier Lockout Circular Dependency**: Gating subscription creation endpoints behind subscription checks.
  - *Mitigation*: Ensure subscription management endpoints (`/plans`, `/create-session`, `/verify`, `/status`) are accessible to all verified suppliers, regardless of active subscription status.
- **Mock vs. Real Test mode transition**:
  - *Mitigation*: Provide a fallback mock mode when `STRIPE_SECRET_KEY` is not set. The mock flow must operate cleanly and automatically update the database state to `"active"`.

## Readiness Checklist
- [ ] Database model `SaaS_Subscription` exists and has appropriate relationships mapped to the `Supplier` model.
- [ ] Supplier authentication flow retrieves and exposes verified supplier roles in the frontend.
- [ ] Designed Vanilla CSS pricing cards and subscriptions workspace layout.

## Phase Exit Criteria
- Suppliers without active subscriptions are locked out of dashboard stats, upload, and publish actions, showing a premium warning banner.
- Suppliers can purchase a subscription using simulated Stripe flow (test mode checkout or mock checkout).
- DB updates successfully and unlocks dashboard access immediately after payment success.
- Integration tests confirm subscription status updates, expiration checks, and endpoint gating.
