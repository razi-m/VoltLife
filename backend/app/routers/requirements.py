from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import Requirement, InventoryLot, Listing, PricingTier, Supplier, BuyerAccount
from app.routers.buyers import get_current_buyer
from app.services.gemini import parse_use_case
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/requirements", tags=["requirements"])

# --- Schemas ---
class RequirementCreate(BaseModel):
    use_case_text: str

class RequirementResponse(BaseModel):
    id: int
    buyer_id: int
    use_case_text: str
    parsed_grade: Optional[str]
    parsed_capacity_kwh: Optional[float]
    parsed_quantity: Optional[int]
    created_at: str

    class Config:
        from_attributes = True

class MatchListingResponse(BaseModel):
    listing_id: int
    lot_id: int
    title: str
    description: str
    moq: int
    grade: str
    chemistry: str
    total_capacity_kwh: float
    available_quantity: int
    avg_soh: float
    avg_rul_years: float
    supplier_name: str
    supplier_address: str
    price_range: str
    match_score: float

# --- Routes ---

@router.post("", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
def create_requirement(
    data: RequirementCreate,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Submits a buyer requirement, parses it using Gemini/local parser, and stores it in the database.
    """
    logger.info(f"Buyer {buyer.username} submitted requirement: '{data.use_case_text}'")
    
    # Parse natural language via Gemini service
    parsed = parse_use_case(data.use_case_text)
    
    # Create requirement record
    requirement = Requirement(
        buyer_id=buyer.id,
        use_case_text=data.use_case_text,
        parsed_grade=parsed.get("grade"),
        parsed_capacity_kwh=parsed.get("capacity_kwh"),
        parsed_quantity=parsed.get("quantity")
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    
    # Return formatted response
    return {
        "id": requirement.id,
        "buyer_id": requirement.buyer_id,
        "use_case_text": requirement.use_case_text,
        "parsed_grade": requirement.parsed_grade,
        "parsed_capacity_kwh": float(requirement.parsed_capacity_kwh) if requirement.parsed_capacity_kwh is not None else None,
        "parsed_quantity": requirement.parsed_quantity,
        "created_at": requirement.created_at.isoformat()
    }


@router.get("/{requirement_id}/matches", response_model=List[MatchListingResponse])
def get_requirement_matches(
    requirement_id: int,
    buyer: BuyerAccount = Depends(get_current_buyer),
    db: Session = Depends(get_db)
):
    """
    Retrieves matching published listings ranked by compatibility score.
    """
    # Fetch requirement
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "requirement_not_found", "message": "Requirement not found"}}
        )
        
    # Security check: Ensure buyer owns this requirement
    if req.buyer_id != buyer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unauthorized", "message": "You do not own this requirement"}}
        )
        
    # Query all active published listings
    active_listings = db.query(Listing).join(
        InventoryLot, Listing.inventory_lot_id == InventoryLot.id
    ).filter(
        Listing.is_published == True,
        InventoryLot.status == "listed",
        InventoryLot.available_quantity > 0
    ).all()
    
    matches = []
    
    # Grade rankings for distance check
    grade_rank = {"S": 4, "A": 3, "B": 2, "C": 1}
    
    req_grade = req.parsed_grade
    req_capacity = float(req.parsed_capacity_kwh) if req.parsed_capacity_kwh is not None else 100.0
    req_quantity = req.parsed_quantity if req.parsed_quantity is not None else 10
    
    for listing in active_listings:
        lot = listing.inventory_lot
        supplier = db.query(Supplier).filter(Supplier.id == lot.supplier_id).first()
        
        # Calculate compatibility match score (starting at 100.0)
        score = 100.0
        
        # 1. Grade Compatibility
        if req_grade:
            req_rank = grade_rank.get(req_grade, 3)
            lot_rank = grade_rank.get(lot.grade, 2)
            diff = req_rank - lot_rank
            if diff > 0:
                # Lot is lower grade than requested: penalize 30% per level
                score -= diff * 30.0
            # If lot_rank >= req_rank, it meets or exceeds requirement, no penalty
            
        # 2. Capacity Proximity
        lot_total_cap = float(lot.total_capacity_kwh)
        capacity_ratio = lot_total_cap / req_capacity
        if capacity_ratio < 0.8 or capacity_ratio > 1.5:
            # Penalize deviation from target capacity (cap at 40.0)
            score -= min(40.0, abs(1.0 - capacity_ratio) * 50.0)
            
        # 3. Quantity / MOQ Compatibility
        if lot.available_quantity < req_quantity:
            # Penalize if listing cannot fulfill requested units fully
            score -= 15.0
        if listing.moq > req_quantity:
            # Penalize if requested units is below supplier's MOQ
            score -= 25.0
            
        # Bound match score between 0 and 100
        final_score = max(0.0, min(100.0, score))
        
        # Retrieve pricing range
        tiers = db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).order_by(PricingTier.min_quantity).all()
        if tiers:
            min_price = min(float(t.price_per_kwh) for t in tiers)
            max_price = max(float(t.price_per_kwh) for t in tiers)
            if min_price == max_price:
                price_str = f"${min_price:,.0f}/kWh"
            else:
                price_str = f"${min_price:,.0f}-${max_price:,.0f}/kWh"
        else:
            price_str = "$--/kWh"
            
        matches.append(MatchListingResponse(
            listing_id=listing.id,
            lot_id=lot.id,
            title=listing.title,
            description=listing.description,
            moq=listing.moq,
            grade=lot.grade,
            chemistry=lot.chemistry,
            total_capacity_kwh=float(lot.total_capacity_kwh),
            available_quantity=lot.available_quantity,
            avg_soh=float(lot.avg_soh),
            avg_rul_years=float(lot.avg_rul_years),
            supplier_name=supplier.company_name if supplier else "Unknown Supplier",
            supplier_address=supplier.address if supplier else "India",
            price_range=price_str,
            match_score=round(final_score, 1)
        ))
        
    # Sort matches by match_score in descending order
    matches.sort(key=lambda x: x.match_score, reverse=True)
    
    return matches
