from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.db.database import get_db
from app.models.marketplace_orm import Order, ShipmentTrackingEvent, SupportTicket
from app.core.events import manager as ws_manager
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/logistics", tags=["logistics"])

VALID_STATES = [
    "confirmed",
    "porter_booked",
    "seller_notified",
    "buyer_notified",
    "shipment_started",
    "in_transit",
    "delivered",
    "completed"
]

class CallbackRequest(BaseModel):
    order_id: int
    status: str

class CallbackResponse(BaseModel):
    status: str
    order_id: int
    new_state: str

class RaiseIssueRequest(BaseModel):
    issue_text: str

class IssueResponse(BaseModel):
    status: str
    ticket_id: int
    order_id: int
    issue_text: str

@router.post("/callback", response_model=CallbackResponse)
async def logistics_callback(data: CallbackRequest, db: Session = Depends(get_db)):
    """
    Callback endpoint used by n8n workflow or in-app simulator to advance order tracking status.
    """
    target_status = data.status.lower()
    if target_status not in VALID_STATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_status", "message": f"Invalid status: {data.status}. Must be one of {VALID_STATES}"}}
        )

    # Fetch order
    order = db.query(Order).filter(Order.id == data.order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "order_not_found", "message": f"Order {data.order_id} not found"}}
        )

    current_status = order.tracking_status or "confirmed"
    
    # Check indexes to prevent going backwards
    current_idx = VALID_STATES.index(current_status)
    target_idx = VALID_STATES.index(target_status)

    if target_idx < current_idx:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_transition", "message": f"Cannot transition backward from '{current_status}' to '{target_status}'"}}
        )

    # Idempotency check: if status is already updated, just return success
    if target_idx == current_idx:
        logger.info(f"Order {order.id} is already in state '{target_status}'. Ignoring duplicate transition.")
        return {
            "status": "success",
            "order_id": order.id,
            "new_state": current_status
        }

    # Update state and append a new tracking event
    order.tracking_status = target_status
    
    tracking_event = ShipmentTrackingEvent(
        order_id=order.id,
        event_type=target_status,
        notes=f"Order status advanced to {target_status}"
    )
    db.add(tracking_event)
    db.commit()
    db.refresh(order)

    logger.info(f"Order {order.id} tracking status updated to '{target_status}'")

    # Broadcast update to websocket clients
    try:
        await ws_manager.broadcast({
            "type": "order_tracking_update",
            "payload": {
                "order_id": order.id,
                "tracking_status": target_status
            }
        })
    except Exception as e:
        logger.error(f"Failed to broadcast websocket tracking event for order {order.id}: {e}")

    return {
        "status": "success",
        "order_id": order.id,
        "new_state": target_status
    }


from datetime import datetime
from app.routers.buyers import get_current_buyer
from app.models.marketplace_orm import BuyerAccount, Quote

class TrackingEventResponse(BaseModel):
    id: int
    event_type: str
    notes: str
    occurred_at: datetime

    class Config:
        from_attributes = True

class SupportTicketResponse(BaseModel):
    id: int
    issue_text: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class OrderTrackingResponse(BaseModel):
    order_id: int
    tracking_status: str
    porter_vehicle_type: str
    delivery_days: int
    transport_cost: float
    total_price: float
    quantity: int
    events: List[TrackingEventResponse]
    support_tickets: List[SupportTicketResponse] = []

@router.get("/orders/{order_id}/tracking", response_model=OrderTrackingResponse)
def get_order_tracking(
    order_id: int,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Retrieves the current tracking status and complete event history of an order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "order_not_found", "message": f"Order {order_id} not found"}}
        )

    # Security check: Ensure buyer owns this order
    if order.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unauthorized", "message": "You do not own this order"}}
        )

    # Find the quote to fetch Porter vehicle type, delivery days, and transport cost
    quote = db.query(Quote).filter(
        Quote.buyer_id == order.buyer_id,
        Quote.inventory_lot_id == order.inventory_lot_id,
        Quote.quantity == order.quantity,
        Quote.status == "accepted"
    ).first()

    vehicle = "Tata Ace (Chota Hathi)"
    days = 2
    cost = 150.0
    if quote:
        vehicle = quote.porter_vehicle_type
        days = quote.delivery_days
        cost = float(quote.transport_cost)

    # Fetch all tracking events
    events = db.query(ShipmentTrackingEvent).filter(ShipmentTrackingEvent.order_id == order.id).order_by(ShipmentTrackingEvent.occurred_at.asc()).all()

    # Fetch all support tickets
    tickets = db.query(SupportTicket).filter(SupportTicket.order_id == order.id).all()

    return {
        "order_id": order.id,
        "tracking_status": order.tracking_status,
        "porter_vehicle_type": vehicle,
        "delivery_days": days,
        "transport_cost": cost,
        "total_price": float(order.total_price),
        "quantity": order.quantity,
        "events": events,
        "support_tickets": tickets
    }

@router.post("/orders/{order_id}/confirm-receipt")
async def confirm_receipt(
    order_id: int,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Confirm receipt of delivery for an order. Can only be done when order status is 'delivered'.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "order_not_found", "message": f"Order {order_id} not found"}}
        )

    # Security check: Ensure buyer owns this order
    if order.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unauthorized", "message": "You do not own this order"}}
        )

    # State check: Must be in 'delivered' state
    if order.tracking_status != "delivered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_state", "message": f"Cannot confirm receipt. Order must be 'delivered', current status is '{order.tracking_status}'"}}
        )

    # Update tracking status to completed
    order.tracking_status = "completed"
    
    tracking_event = ShipmentTrackingEvent(
        order_id=order.id,
        event_type="completed",
        notes="Buyer confirmed delivery receipt. Order marked as completed."
    )
    db.add(tracking_event)
    db.commit()
    db.refresh(order)

    logger.info(f"Order {order.id} tracking status updated to 'completed' by buyer")

    # Broadcast update to WebSocket clients
    try:
        await ws_manager.broadcast({
            "type": "order_tracking_update",
            "payload": {
                "order_id": order.id,
                "tracking_status": "completed"
            }
        })
    except Exception as e:
        logger.error(f"Failed to broadcast websocket tracking event for completed order {order.id}: {e}")

    return {
        "status": "success",
        "order_id": order.id,
        "new_state": "completed"
    }

@router.post("/orders/{order_id}/raise-issue", response_model=IssueResponse)
def raise_issue(
    order_id: int,
    data: RaiseIssueRequest,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Raise a support ticket for an order.
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "order_not_found", "message": f"Order {order_id} not found"}}
        )

    # Security check: Ensure buyer owns this order
    if order.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unauthorized", "message": "You do not own this order"}}
        )

    # Create support ticket
    ticket = SupportTicket(
        order_id=order.id,
        buyer_id=buyer.id,
        issue_text=data.issue_text,
        status="open"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    logger.info(f"Support ticket {ticket.id} raised for order {order.id} by buyer {buyer.id}")

    return {
        "status": "success",
        "ticket_id": ticket.id,
        "order_id": order.id,
        "issue_text": ticket.issue_text
    }

