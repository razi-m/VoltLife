# VOLTLIFE — PAYMENT PROVIDER PATCH: STRIPE → RAZORPAY

> Paste below the line into Claude Opus 4.8. This is a targeted patch — it only
> changes the payment provider. Do NOT regenerate the full spec. Do NOT touch the
> existing backend (battery-assessment domain, `ml/`, existing routers/tables/
> endpoints). Additive only. Demo-only.

---

```
Apply ONE change to the VoltLife Marketplace spec/implementation: replace the
payment provider STRIPE with RAZORPAY. Everything else stays exactly as planned.

CONTEXT
- Payment is NOT yet implemented (it is still plan/prompt text). This patch swaps
  the chosen provider so nothing in the existing backend is touched or broken.
- All prior rules still apply: plan-before-code, the readiness file BEFORE each
  phase, the report + STOP-AND-ASK AFTER each phase, no media, AI-first identity.

NON-NEGOTIABLES (unchanged)
- DO NOT modify ml/ or the existing battery-assessment domain / existing routers /
  tables / endpoints / response shapes. ADD only. The single justified existing-file
  edits remain: main.py router mount, backend/.env.example, backend/requirements.txt,
  frontend App.tsx route, frontend package.json (only if a dep is truly needed).
- DEMO ONLY: Razorpay runs in TEST MODE (rzp_test_ keys) OR fully mocked. NEVER live
  keys, NEVER real money. The whole flow MUST run end-to-end with NO keys configured
  (mock success path). Label simulated artifacts (demo_mode:true, MOCK-/DEMO- ids).
- Inventory locks ONLY after a verified (or mocked) successful payment — never at
  quote time. The lock is IDEMPOTENT.

1) PROVIDER SWAP
   - Replace every "Stripe" reference in the marketplace plan / payment phase with
     "Razorpay". Remove all Stripe SDK usage (backend `stripe`, frontend
     `@stripe/stripe-js`).
   - Currency = INR; amounts are integer PAISE (₹1 = 100 paise). Fits the India
     context (Porter, GST).

2) BACKEND ADAPTER — NEW file `backend/app/services/razorpay_adapter.py`
   Two modes behind one interface:
   - REAL (test): if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are set, use the
     official `razorpay` Python SDK:
       * create_order(amount_paise, receipt, notes) ->
         client.order.create({"amount": amount_paise, "currency": "INR",
         "receipt": receipt, "payment_capture": 1}) -> {razorpay_order_id, amount, currency}
       * verify_payment(order_id, payment_id, signature) ->
         client.utility.verify_payment_signature({...})  # HMAC-SHA256 w/ key_secret
       * verify_webhook(raw_body, x_razorpay_signature) using RAZORPAY_WEBHOOK_SECRET
   - MOCK (default, no keys): create_order returns a "MOCK-<uuid>" order id;
     verify_payment / verify_webhook return success for the simulated path; mark
     demo_mode=true. NO network calls.
   - Add `razorpay` to backend/requirements.txt (additive).

3) PAYMENT ENDPOINTS — NEW `backend/app/routers/payments.py`
   - POST /api/v1/payments/create-order: compute amount in paise from the quote
     (battery_cost + transport_cost) -> adapter.create_order ->
     return {razorpay_order_id, key_id (public RAZORPAY_KEY_ID or "" in mock),
     amount, currency:"INR", demo_mode}.
   - POST /api/v1/payments/verify: body {razorpay_order_id, razorpay_payment_id,
     razorpay_signature} -> adapter.verify_payment -> on success ONLY and IDEMPOTENT
     (key = razorpay_order_id/payment_id): lock/decrement inventory + create order +
     trigger logistics (n8n or in-app sim). On failure: leave inventory untouched.
   - POST /api/v1/payments/webhook: verify X-Razorpay-Signature, handle
     `payment.captured` with the SAME idempotent lock-once logic (safe if called
     twice or alongside /verify).

4) DATA MODEL (additive — `payment` table)
   Columns: razorpay_order_id, razorpay_payment_id, razorpay_signature_verified(bool),
   amount_paise(int), currency("INR"), status, idempotency_key (= razorpay_order_id,
   unique), provider ("razorpay-test" | "razorpay-mock"). Remove any stripe_session_id.

5) FRONTEND (additive, demo)
   - REAL test mode: load Razorpay Checkout via the script tag
     `https://checkout.razorpay.com/v1/checkout.js` (NO npm dependency). On
     "Proceed to Payment": POST /payments/create-order ->
     `new Razorpay({ key, order_id, amount, currency:"INR", handler })`; in handler,
     POST /payments/verify. Use rzp_test_ key + Razorpay test cards.
   - MOCK mode (default, no keys): a clearly-labeled "SIMULATED PAYMENT (Razorpay test)"
     button that POSTs /payments/verify with a mock-success payload.
   - Delete any Stripe component/page. No Stripe npm package.

6) ENV VARS (backend/.env.example — additive; replace STRIPE_* with):
     RAZORPAY_KEY_ID=
     RAZORPAY_KEY_SECRET=
     RAZORPAY_WEBHOOK_SECRET=
   (All blank => mock mode, demo runs keyless.)

7) SUBSCRIPTIONS (Phase 14): if kept, use Razorpay Subscriptions in test/mock mode;
   otherwise simulate. Still SaaS-only revenue — NO commissions / transaction fees /
   marketplace cuts.

VERIFY AFTER PATCH
- Existing backend pytest + ml pytest + frontend build still GREEN (nothing existing
  broken).
- Full demo works with NO Razorpay keys: mock success -> inventory locks exactly once
  (idempotent); failure leaves inventory untouched.
- No "Stripe" / `@stripe/stripe-js` / `stripe` references remain in the marketplace
  plan or payment phase.

OUTPUT: only the modified sections + a summary of changes. Do not regenerate the full
specification. Then STOP and ask before continuing (honor the stop-and-ask gate).
```
