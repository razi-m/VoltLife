# Razorpay Migration Report (additive — Stripe preserved)
**Date:** 2026-06-14 · **Approach:** parallel Razorpay path; **Stripe NOT removed until verified**

> Environment caveat: this sandbox cannot boot/validate (stale-mount). The two NEW backend
> files were compile-checked (pass); the end-to-end run must be done locally.

## 1. Stripe touchpoints identified (live code)
| File | Touchpoint |
|---|---|
| `routers/payments.py` | `import stripe`; `stripe.checkout.Session.create(...)`; `/checkout-session` endpoint; `process_successful_payment(db, session_id, quote_id)` helper (order + inventory lock + logistics) |
| `models/marketplace_orm.py:204` | `stripe_session_id` column on `PaymentEvent` (used as the idempotency/session id) |
| `routers/subscriptions.py` | Stripe references (SaaS billing) |
| frontend | mock-confirm checkout (no Stripe JS dep) |

## 2. Migration plan (followed)
Razorpay is added **alongside** Stripe (no rip-and-replace). The Razorpay verify endpoint reuses
the **existing** `process_successful_payment()` so **order creation + inventory locking + logistics
are unchanged**. The Razorpay order id is passed as the provider-agnostic `session_id`, so **no
database schema change** was required (it stores in the existing `PaymentEvent` session-id column).
Stripe code is left intact until the Razorpay path is verified locally.

## 3. Implemented (this pass)
| Item | File | Status |
|---|---|---|
| Razorpay adapter (Orders API + signature verify; mock fallback, INR/paise) | `backend/app/services/razorpay_service.py` (NEW) | ✅ compiles |
| Razorpay endpoints — `POST /api/v1/payments/razorpay/create-order`, `/verify` | `backend/app/routers/razorpay_payments.py` (NEW) | ✅ compiles |
| Reuse of order/inventory-lock/logistics | imports `process_successful_payment` (unchanged) | ✅ |
| Router registration | `backend/app/main.py` (import + `include_router`) | ✅ verified in file |
| Razorpay Checkout (frontend, checkout.js script — no npm dep; keyless mock fallback) | `frontend/src/components/RazorpayCheckout.tsx` (NEW) | ✅ written |
| Env vars | `backend/.env.example` (`RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`) | ✅ added (verify locally) |
| Dependency | `backend/requirements.txt` already lists `razorpay` | ✅ present |
| Stripe code | untouched (14 refs intact in `payments.py`) | ✅ preserved (per directive #8) |

## 4. Razorpay flow
```
Frontend "Pay with Razorpay"
   → POST /payments/razorpay/create-order {quote_id}
   → backend: razorpay_service.create_order(total, receipt) -> {razorpay_order_id, key_id, amount(paise), currency:INR, demo_mode}
   → Razorpay Checkout modal (real test) OR keyless MOCK confirm (demo)
   → POST /payments/razorpay/verify {quote_id, razorpay_order_id, razorpay_payment_id, razorpay_signature}
   → backend: verify_signature(...) -> process_successful_payment(session_id=razorpay_order_id, quote_id)
       → locks InventoryLot (with_for_update), decrements qty, creates Order(paid), PaymentEvent, triggers logistics  (UNCHANGED)
```
Demo runs with **no keys** (mock order id accepted by `verify_signature`). No real money.

## 5. Local verification checklist (do BEFORE removing Stripe)
1. `cd backend && pip install -r requirements.txt && uvicorn app.main:app` → `/docs` shows `/api/v1/payments/razorpay/create-order` + `/verify`.
2. Buyer logs in → create a quote → `create-order` returns a `razorpay_order_id` (mock id with no keys).
3. `verify` (mock payload) → returns `{order_id, payment_status:"paid", tracking_status:"confirmed"}`.
4. Confirm the inventory lot `available_quantity` decremented exactly once (idempotent: re-POST `verify` → same order, no double-decrement).
5. Confirm logistics simulation/tracking advances.
6. Optionally set `rzp_test_` keys and test the real modal.
7. **Only after 1–6 pass:** remove Stripe (`payments.py` Stripe branch, `subscriptions.py` Stripe, `stripe_session_id` rename if desired) and delete `razorpay_payment_patch_prompt.md`.

## 6. Remaining Option-B tasks (NOT done this pass — honest status)
- **India Map (Task 1):** still a placeholder; `package.json` has no map lib. Pending: add `react-leaflet`+`leaflet`, render markers from `GET /api/v1/marketplace/suppliers`. Could not build/verify here.
- **Marketplace N+1 (Task 4):** `marketplace.py` listings loop still does per-lot `Listing`/`Supplier`/`PricingTier` queries — pending `joinedload`/batched fix.
- **Cross-tenant security tests (Task 5):** pending a new `tests/` file (seller-A vs seller-B, buyer vs supplier routes, admin gating).
- **Boot / E2E validation (Tasks 2–3):** cannot be trustably run in this sandbox (stale mount) — must run locally.

## 7. Readiness
- **Payment migration:** Razorpay path implemented additively, compiles, reuses business logic, Stripe preserved → **ready for local verification** (not yet runtime-verified here).
- **HackPrix demo ready? → NOT YET (honest).** Gated on: a local boot pass, the India map, the N+1 fix, and verifying the Razorpay path locally per §5. None require redesign; all are bounded. The **ML subsystem remains demo-ready**.
