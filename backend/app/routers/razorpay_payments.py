"""
razorpay_payments.py — Razorpay checkout endpoints (ADDITIVE; Stripe untouched).

Flow (Task 6):
  POST /api/v1/payments/razorpay/create-order  -> create Razorpay order (or mock)
                                                  returns {order_id, key_id, amount, currency}
  POST /api/v1/payments/razorpay/verify         -> verify signature, then REUSE the existing
                                                  process_successful_payment() helper to create
                                                  the order, lock+decrement inventory, and trigger
                                                  the logistics workflow (no business-logic change).

The Razorpay order id is used as the idempotency `session_id` for
process_successful_payment(), so NO database schema change is required (it is stored in the
existing PaymentEvent session-id column, which is provider-agnostic).
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import Quote, BuyerAccount
from app.routers.buyers import get_current_buyer
from app.routers.payments import process_successful_payment  # REUSE existing order/inventory logic
from app.services import razorpay_service
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/payments/razorpay", tags=["payments-razorpay"])


class CreateOrderRequest(BaseModel):
    quote_id: int


class VerifyRequest(BaseModel):
    quote_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def _get_owned_quote(db: Session, quote_id: int, buyer: BuyerAccount) -> Quote:
    quote = db.query(Quote).filter(Quote.id == quote_id, Quote.buyer_id == buyer.id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "quote_not_found", "message": "Quote not found"}},
        )
    return quote


@router.post("/create-order")
def create_razorpay_order(
    data: CreateOrderRequest,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db),
):
    """Create a Razorpay Order for the buyer's quote. Returns checkout params for the frontend."""
    quote = _get_owned_quote(db, data.quote_id, buyer)
    result = razorpay_service.create_order(float(quote.total_cost), receipt=f"quote_{quote.id}")
    logger.info(f"[razorpay] create-order quote={quote.id} -> {result['razorpay_order_id']} (demo_mode={result['demo_mode']})")
    return result


@router.post("/verify")
def verify_razorpay_payment(
    data: VerifyRequest,
    background_tasks: BackgroundTasks,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db),
):
    """Verify the Razorpay signature, then run the EXISTING payment-success workflow."""
    quote = _get_owned_quote(db, data.quote_id, buyer)

    if not razorpay_service.verify_signature(
        data.razorpay_order_id, data.razorpay_payment_id, data.razorpay_signature
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "signature_invalid", "message": "Razorpay signature verification failed"}},
        )

    # Preserve existing order creation + inventory locking + logistics trigger (idempotent).
    order = process_successful_payment(
        db, session_id=data.razorpay_order_id, quote_id=quote.id, background_tasks=background_tasks
    )
    return {
        "order_id": order.id,
        "payment_status": order.payment_status,
        "tracking_status": order.tracking_status,
        "provider": "razorpay",
    }
