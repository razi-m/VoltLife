from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import Quote, InventoryLot, Listing, PricingTier, Supplier, BuyerAccount
from app.routers.buyers import get_current_buyer
from app.services.porter import calculate_delivery
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/quotes", tags=["quotes"])

# --- Schemas ---
class QuoteCreate(BaseModel):
    inventory_lot_id: int
    quantity: int

class QuoteResponse(BaseModel):
    id: int
    buyer_id: int
    inventory_lot_id: int
    quantity: int
    battery_cost: float
    transport_cost: float
    total_cost: float
    delivery_days: int
    porter_vehicle_type: str
    status: str
    created_at: str

    class Config:
        from_attributes = True

# --- Routes ---

@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    data: QuoteCreate,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Creates a new formal price quote for a published bulk inventory lot.
    """
    logger.info(f"Quote requested by buyer {buyer.username} for lot {data.inventory_lot_id}, quantity {data.quantity}")
    
    # 1. Fetch inventory lot
    lot = db.query(InventoryLot).filter(InventoryLot.id == data.inventory_lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )
        
    # 2. Check listing and published state
    listing = db.query(Listing).filter(Listing.inventory_lot_id == lot.id).first()
    if not listing or not listing.is_published or lot.status != "listed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "listing_not_published", "message": "This lot is not listed for sale"}}
        )
        
    # 3. MOQ check
    if data.quantity < listing.moq:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_quantity", "message": f"Requested quantity {data.quantity} is below Minimum Order Quantity of {listing.moq}"}}
        )
        
    # 4. Availability check
    if data.quantity > lot.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "insufficient_quantity", "message": f"Requested quantity {data.quantity} exceeds available quantity of {lot.available_quantity}"}}
        )
        
    # 5. Resolve pricing tier
    tiers = db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).order_by(PricingTier.min_quantity.asc()).all()
    if not tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "no_pricing_tiers", "message": "No pricing tiers are configured for this lot"}}
        )
        
    applicable_tier = None
    for tier in tiers:
        if data.quantity >= tier.min_quantity:
            applicable_tier = tier
            
    if not applicable_tier:
        applicable_tier = tiers[0] # Default fallback to first tier
        
    # Calculate battery cost
    capacity_per_pack = float(lot.total_capacity_kwh) / float(lot.available_quantity)
    price_per_kwh = float(applicable_tier.price_per_kwh)
    battery_cost = data.quantity * capacity_per_pack * price_per_kwh
    
    # 6. Resolve Porter logistics
    supplier = db.query(Supplier).filter(Supplier.id == lot.supplier_id).first()
    origin = supplier.address if supplier else "Pune"
    destination = buyer.address
    
    delivery = calculate_delivery(origin, destination, data.quantity, capacity_per_pack)
    
    transport_cost = delivery["transport_cost"]
    total_cost = battery_cost + transport_cost
    delivery_days = delivery["delivery_days"]
    porter_vehicle = delivery["porter_vehicle_type"]
    
    # 7. Create Quote record
    quote = Quote(
        buyer_id=buyer.id,
        inventory_lot_id=lot.id,
        quantity=data.quantity,
        battery_cost=battery_cost,
        transport_cost=transport_cost,
        total_cost=total_cost,
        delivery_days=delivery_days,
        porter_vehicle_type=porter_vehicle,
        status="pending"
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    logger.info(f"Quote {quote.id} created successfully. Total cost: ${quote.total_cost:.2f}")
    
    return {
        "id": quote.id,
        "buyer_id": quote.buyer_id,
        "inventory_lot_id": quote.inventory_lot_id,
        "quantity": quote.quantity,
        "battery_cost": float(quote.battery_cost),
        "transport_cost": float(quote.transport_cost),
        "total_cost": float(quote.total_cost),
        "delivery_days": quote.delivery_days,
        "porter_vehicle_type": quote.porter_vehicle_type,
        "status": quote.status,
        "created_at": quote.created_at.isoformat()
    }


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: int,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Retrieves detail of a formal price quote.
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "quote_not_found", "message": "Quote not found"}}
        )
        
    # Security check: Ensure buyer owns this quote
    if quote.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unauthorized", "message": "You do not own this quote"}}
        )
        
    return {
        "id": quote.id,
        "buyer_id": quote.buyer_id,
        "inventory_lot_id": quote.inventory_lot_id,
        "quantity": quote.quantity,
        "battery_cost": float(quote.battery_cost),
        "transport_cost": float(quote.transport_cost),
        "total_cost": float(quote.total_cost),
        "delivery_days": quote.delivery_days,
        "porter_vehicle_type": quote.porter_vehicle_type,
        "status": quote.status,
        "created_at": quote.created_at.isoformat()
    }


@router.get("", response_model=List[QuoteResponse])
def list_quotes(
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Retrieves all quotes for the authenticated buyer.
    """
    logger.info(f"Retrieving quotes for buyer {buyer.username}")
    quotes = db.query(Quote).filter(Quote.buyer_id == buyer.id).order_by(Quote.created_at.desc()).all()
    
    result = []
    for q in quotes:
        result.append({
            "id": q.id,
            "buyer_id": q.buyer_id,
            "inventory_lot_id": q.inventory_lot_id,
            "quantity": q.quantity,
            "battery_cost": float(q.battery_cost),
            "transport_cost": float(q.transport_cost),
            "total_cost": float(q.total_cost),
            "delivery_days": q.delivery_days,
            "porter_vehicle_type": q.porter_vehicle_type,
            "status": q.status,
            "created_at": q.created_at.isoformat()
        })
    return result

