"""
razorpay_service.py — Razorpay payment adapter (ADDITIVE; does not touch Stripe).

Two modes behind one interface:
  - REAL (test): if RAZORPAY_KEY_ID + RAZORPAY_KEY_SECRET are set, use the official
    `razorpay` SDK (Orders API + signature verification).
  - MOCK (default, no keys): returns a MOCK order id and accepts it on verify, so the
    demo runs end-to-end with NO Razorpay keys (no real money).

Currency: INR, amounts in paise (₹1 = 100 paise).
"""
import os
import uuid

from app.core.logging import logger

try:
    from app.core.config import settings
except Exception:  # pragma: no cover
    settings = None

try:
    import razorpay
except ImportError:
    razorpay = None


def _creds():
    kid = (getattr(settings, "RAZORPAY_KEY_ID", None) if settings else None) or os.getenv("RAZORPAY_KEY_ID")
    ksec = (getattr(settings, "RAZORPAY_KEY_SECRET", None) if settings else None) or os.getenv("RAZORPAY_KEY_SECRET")
    return kid, ksec


def _client():
    kid, ksec = _creds()
    if razorpay and kid and ksec:
        return razorpay.Client(auth=(kid, ksec)), kid, ksec
    return None, kid, ksec


def create_order(amount_rupees: float, receipt: str) -> dict:
    """Create a Razorpay Order (real) or a MOCK order (no keys).

    Returns: {razorpay_order_id, key_id, amount (paise), currency, demo_mode}
    """
    client, kid, ksec = _client()
    amount_paise = int(round(float(amount_rupees) * 100))
    if client:
        order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        })
        logger.info(f"[razorpay] order created {order['id']} amount={amount_paise} paise")
        return {"razorpay_order_id": order["id"], "key_id": kid,
                "amount": amount_paise, "currency": "INR", "demo_mode": False}

    mock_id = f"order_MOCK{uuid.uuid4().hex[:16]}"
    logger.info(f"[razorpay] MOCK order {mock_id} (no keys) amount={amount_paise} paise")
    return {"razorpay_order_id": mock_id, "key_id": "rzp_test_mock",
            "amount": amount_paise, "currency": "INR", "demo_mode": True}


def verify_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify the Razorpay payment signature (real) or accept MOCK orders (no keys)."""
    client, kid, ksec = _client()
    if client:
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except Exception as e:
            logger.warning(f"[razorpay] signature verification FAILED: {e}")
            return False
    # MOCK mode: accept only ids minted by our mock create_order
    return str(razorpay_order_id).startswith("order_MOCK")
