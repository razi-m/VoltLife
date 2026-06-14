import os
import uuid
import asyncio
import httpx
import threading
from datetime import datetime, timezone

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel


from app.db.database import get_db, SessionLocal
from app.models.marketplace_orm import Quote, Order, PaymentEvent, InventoryLot, BuyerAccount, ShipmentTrackingEvent
from app.routers.buyers import get_current_buyer
from app.core.logging import logger
from app.core.config import settings
from app.core.events import manager as ws_manager


try:
    import stripe
except ImportError:
    stripe = None

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# --- Schemas ---
class CheckoutSessionCreate(BaseModel):
    quote_id: int

class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str

class MockConfirmRequest(BaseModel):
    session_id: str

class OrderResponse(BaseModel):
    id: int
    buyer_id: int
    supplier_id: int
    inventory_lot_id: int
    quantity: int
    total_price: float
    payment_status: str
    tracking_status: str
    created_at: datetime

    class Config:
        from_attributes = True

def run_async_in_thread(coro):
    """
    Runs a coroutine in a new background daemon thread with its own event loop.
    """
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        finally:
            loop.close()
    threading.Thread(target=run, daemon=True).start()

async def simulate_in_app_logistics(order_id: int, delay: float = 2.0):

    """
    Background simulation looping through logistics states with a delay.
    """
    from app.routers.logistics import VALID_STATES
    
    # We skip "confirmed" as it is the starting status, and "completed" as it requires buyer confirmation
    states_to_simulate = [s for s in VALID_STATES[1:] if s != "completed"]
    
    logger.info(f"Starting in-app logistics simulation for order {order_id} with delay {delay}s per step...")
    for state in states_to_simulate:
        await asyncio.sleep(delay)
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                logger.error(f"[Simulator] Order {order_id} not found.")
                break
                
            order.tracking_status = state
            tracking_event = ShipmentTrackingEvent(
                order_id=order_id,
                event_type=state,
                notes=f"[Simulated] Order status advanced to {state}"
            )
            db.add(tracking_event)
            db.commit()
            logger.info(f"[Simulator] Advanced order {order_id} to '{state}'")
            
            # WebSocket Broadcast
            try:
                await ws_manager.broadcast({
                    "type": "order_tracking_update",
                    "payload": {
                        "order_id": order_id,
                        "tracking_status": state
                    }
                })
            except Exception as ws_err:
                logger.error(f"[Simulator] WebSocket broadcast error: {ws_err}")
                
        except Exception as e:
            logger.error(f"[Simulator] Error updating order {order_id} to state '{state}': {e}")
        finally:
            db.close()

async def trigger_n8n_webhook(order_id: int, total_cost: float, buyer_id: int):
    """
    Asynchronously posts order details to n8n webhook target.
    """
    url = settings.N8N_WEBHOOK_URL
    if not url:
        logger.warning("N8N_WEBHOOK_URL is empty. Falling back to in-app simulation.")
        # Trigger simulation instead
        delay = float(os.getenv("SIMULATION_DELAY", "2.0"))
        run_async_in_thread(simulate_in_app_logistics(order_id, delay))
        return

        
    payload = {
        "order_id": order_id,
        "amount": total_cost,
        "buyer_id": buyer_id
    }
    
    logger.info(f"Triggering n8n webhook at {url} with payload: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=5.0)
            logger.info(f"n8n webhook responded with status: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to post to n8n webhook: {e}")

# --- Helpers ---

def process_successful_payment(db: Session, session_id: str, quote_id: int, background_tasks: BackgroundTasks = None) -> Order:
    """
    Idempotently processes a successful payment transaction.
    Locks the inventory row, decrements quantity, and creates the order.
    """
    # 1. Idempotency Check
    existing_payment = db.query(PaymentEvent).filter(PaymentEvent.stripe_session_id == session_id).first()
    if existing_payment:
        logger.info(f"Payment session {session_id} has already been processed. Returning existing order.")
        existing_order = db.query(Order).filter(Order.id == existing_payment.order_id).first()
        return existing_order

    # 2. Fetch Quote
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "quote_not_found", "message": "Quote not found"}}
        )

    if quote.status == "accepted":
        # Quote is already accepted; find the linked order
        existing_order = db.query(Order).filter(
            Order.buyer_id == quote.buyer_id,
            Order.inventory_lot_id == quote.inventory_lot_id,
            Order.quantity == quote.quantity
        ).first()
        if existing_order:
            return existing_order

    # 3. Lock Inventory Lot to prevent race conditions
    lot = db.query(InventoryLot).filter(InventoryLot.id == quote.inventory_lot_id).with_for_update().first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )

    # 4. Check available stock at checkout completion
    if lot.available_quantity < quote.quantity:
        logger.warning(f"Insufficient quantity during checkout confirmation for lot {lot.id}. Requested: {quote.quantity}, Available: {lot.available_quantity}")
        # Create a failed order record for audit
        order = Order(
            buyer_id=quote.buyer_id,
            supplier_id=lot.supplier_id,
            inventory_lot_id=lot.id,
            quantity=quote.quantity,
            total_price=quote.total_cost,
            payment_status="failed",
            tracking_status="confirmed"
        )
        db.add(order)
        db.flush()

        payment_event = PaymentEvent(
            order_id=order.id,
            stripe_session_id=session_id,
            amount=quote.total_cost,
            status="failed"
        )
        db.add(payment_event)
        
        quote.status = "rejected"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "insufficient_stock", "message": "The inventory lot has been sold out. A demo refund has been initiated."}}
        )

    # 5. Decrement Stock, Update Quote, and Create Order
    lot.available_quantity -= quote.quantity
    quote.status = "accepted"

    order = Order(
        buyer_id=quote.buyer_id,
        supplier_id=lot.supplier_id,
        inventory_lot_id=lot.id,
        quantity=quote.quantity,
        total_price=quote.total_cost,
        payment_status="paid",
        tracking_status="confirmed"
    )
    db.add(order)
    db.flush()

    payment_event = PaymentEvent(
        order_id=order.id,
        stripe_session_id=session_id,
        amount=quote.total_cost,
        status="success"
    )
    db.add(payment_event)

    db.commit()
    logger.info(f"Order {order.id} created successfully and inventory decremented for lot {lot.id} (quantity: {quote.quantity})")

    # Trigger post-payment workflow
    if settings.N8N_ENABLED and settings.N8N_WEBHOOK_URL:
        if background_tasks:
            background_tasks.add_task(trigger_n8n_webhook, order.id, float(order.total_price), order.buyer_id)
        else:
            run_async_in_thread(trigger_n8n_webhook(order.id, float(order.total_price), order.buyer_id))
    else:
        simulation_delay = float(os.getenv("SIMULATION_DELAY", "2.0"))
        if background_tasks:
            background_tasks.add_task(simulate_in_app_logistics, order.id, simulation_delay)
        else:
            run_async_in_thread(simulate_in_app_logistics(order.id, simulation_delay))


    return order



# --- Routes ---

@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    data: CheckoutSessionCreate,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Creates a Stripe Checkout Session or a Local Mock Session for purchasing a quote.
    """
    # 1. Fetch and validate quote
    quote = db.query(Quote).filter(Quote.id == data.quote_id, Quote.buyer_id == buyer.id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "quote_not_found", "message": "Quote not found"}}
        )

    if quote.status == "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "quote_already_accepted", "message": "This quote has already been paid and processed"}}
        )

    # 2. Check 24-hour expiration window
    if quote.created_at:
        now = datetime.now(timezone.utc)
        created_at = quote.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        
        age_hours = (now - created_at).total_seconds() / 3600.0
        if age_hours > 24.0:
            quote.status = "expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "quote_expired", "message": "This quote has expired (validity is 24 hours)"}}
            )

    # 3. Check inventory lot availability
    lot = db.query(InventoryLot).filter(InventoryLot.id == quote.inventory_lot_id).first()
    if not lot or lot.available_quantity < quote.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "insufficient_inventory", "message": "The inventory lot does not have enough packs remaining to complete this order"}}
        )

    # 4. Initialize Stripe Checkout or Fallback to Mock Session
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    backend_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

    if stripe_key and stripe:
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Bulk Battery Packs (Lot #{lot.id})",
                            "description": f"Quantity: {quote.quantity} units, Chemistry: {lot.chemistry}, Grade: {lot.grade}",
                        },
                        "unit_amount": int(quote.total_cost * 100), # in cents
                    },
                    "quantity": 1,
                }],
                mode="payment",
                metadata={"quote_id": str(quote.id)},
                success_url=f"{backend_url}/payments/checkout-success?session_id={{CHECKOUT_SESSION_ID}}&quote_id={quote.id}",
                cancel_url=f"{backend_url}/payments/checkout-cancel?quote_id={quote.id}",
            )
            logger.info(f"Stripe checkout session created: {session.id}")
            return {
                "session_id": session.id,
                "checkout_url": session.url
            }
        except Exception as e:
            logger.error(f"Stripe session creation failed, falling back to mock checkout: {str(e)}")

    # Mock Checkout Session Fallback
    mock_session_id = f"MOCK_SESSION_{quote.id}_{uuid.uuid4().hex}"
    # Redirect URL to backend mock success completion handler
    mock_checkout_url = f"{backend_url}/payments/checkout-success?session_id={mock_session_id}&quote_id={quote.id}"
    
    logger.info(f"Mock checkout session generated: {mock_session_id}")
    return {
        "session_id": mock_session_id,
        "checkout_url": mock_checkout_url
    }


@router.post("/mock-confirm", response_model=OrderResponse)
def mock_confirm_payment(
    data: MockConfirmRequest,
    background_tasks: BackgroundTasks,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Simulates a successful payment webhook/callback for mock sessions.
    Validates idempotency and updates inventory/orders.
    """
    session_id = data.session_id
    if not session_id.startswith("MOCK_SESSION_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_session", "message": "Only mock checkout sessions can be confirmed via this route"}}
        )

    # Extract quote_id from the structured mock session string
    # Pattern: MOCK_SESSION_{quote_id}_{uuid}
    parts = session_id.split("_")
    if len(parts) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_session", "message": "Invalid mock session ID format"}}
        )
    
    try:
        quote_id = int(parts[2])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_session", "message": "Invalid quote ID in session ID"}}
        )

    order = process_successful_payment(db, session_id, quote_id, background_tasks)
    return order



@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Stripe Webhook endpoint to catch checkout.session.completed events.
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not stripe_key or not stripe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe is not configured")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session["id"]
        metadata = session.get("metadata", {})
        quote_id_str = metadata.get("quote_id")
        
        if quote_id_str:
            try:
                quote_id = int(quote_id_str)
                process_successful_payment(db, session_id, quote_id, background_tasks)
            except Exception as e:
                logger.error(f"Error processing webhook payment: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing error")

    return {"status": "success"}


from typing import List

@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Retrieves all purchased orders for the authenticated buyer.
    """
    logger.info(f"Retrieving orders for buyer {buyer.username}")
    orders = db.query(Order).filter(Order.buyer_id == buyer.id).order_by(Order.created_at.desc()).all()
    return orders


