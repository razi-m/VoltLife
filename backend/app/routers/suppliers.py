from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import Supplier, SupplierUser, SupplierVerification, InventoryLot, PricingTier, Listing
from app.core.auth import hash_password, verify_password, create_access_token, verify_token
# Note: Rest of existing code remains unchanged...

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])
security = HTTPBearer(auto_error=False)

# --- Schemas ---
class SupplierRegister(BaseModel):
    company_name: str
    email: str
    phone: str
    gstin: str
    address: str
    username: str
    password: str

class SupplierLogin(BaseModel):
    username: str
    password: str

class ListingUpdate(BaseModel):
    moq: int
    description: str

class PricingTierInput(BaseModel):
    min_quantity: int
    price_per_kwh: float

class PricingTiersUpdate(BaseModel):
    tiers: List[PricingTierInput]

# --- Security Dependencies ---
def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security), db: Session = Depends(get_db)) -> SupplierUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Not authenticated"}}
        )
    token = credentials.credentials
    payload = verify_token(token)
    if not payload or "supplier_id" not in payload or payload.get("type") == "buyer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Could not validate credentials"}}
        )
    user_id = payload.get("user_id")
    user = db.query(SupplierUser).filter(SupplierUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "User not found"}}
        )
    return user

def get_current_supplier(user: SupplierUser = Depends(get_current_user), db: Session = Depends(get_db)) -> Supplier:
    supplier = db.query(Supplier).filter(Supplier.id == user.supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "supplier_not_found", "message": "Supplier not found"}}
        )
    return supplier

def get_current_verified_supplier(supplier: Supplier = Depends(get_current_supplier)) -> Supplier:
    if not supplier.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "unverified_supplier", "message": "Supplier account is pending verification"}}
        )
    return supplier

def get_current_active_subscriber(
    supplier: Supplier = Depends(get_current_verified_supplier),
    db: Session = Depends(get_db)
) -> Supplier:
    from app.models.marketplace_orm import SaaS_Subscription
    from datetime import datetime, timezone
    
    # 1. Fetch active subscription
    sub = db.query(SaaS_Subscription).filter(
        SaaS_Subscription.supplier_id == supplier.id,
        SaaS_Subscription.status == "active"
    ).first()
    
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "subscription_required", "message": "An active SaaS subscription is required to perform this action"}}
        )
        
    # 2. Check expiry if set
    if sub.expires_at:
        now = datetime.now(timezone.utc)
        expires_at = sub.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            # Mark it as expired
            sub.status = "expired"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "subscription_required", "message": "SaaS subscription has expired"}}
            )
            
    return supplier


# --- Routes ---
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_supplier(data: SupplierRegister, db: Session = Depends(get_db)):
    # Check if supplier company email already exists
    existing_supplier = db.query(Supplier).filter(Supplier.email == data.email).first()
    if existing_supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "email_taken", "message": "Supplier email is already registered"}}
        )
    
    # Check if username is taken
    existing_user = db.query(SupplierUser).filter(SupplierUser.username == data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "username_taken", "message": "Username is already taken"}}
        )
    
    # Create Supplier
    supplier = Supplier(
        company_name=data.company_name,
        email=data.email,
        phone=data.phone,
        gstin=data.gstin,
        address=data.address,
        is_verified=False
    )
    db.add(supplier)
    db.flush()  # populate supplier.id
    
    # Create SupplierUser
    pw_hash = hash_password(data.password)
    user = SupplierUser(
        supplier_id=supplier.id,
        username=data.username,
        password_hash=pw_hash,
        role="admin"
    )
    db.add(user)
    
    # Create a pending Verification log
    verification = SupplierVerification(
        supplier_id=supplier.id,
        verifier_notes="Auto-created on registration",
        status="pending"
    )
    db.add(verification)
    
    db.commit()
    return {
        "status": "success",
        "message": "Supplier registration successful. Pending verification.",
        "supplier_id": supplier.id
    }

@router.post("/login")
def login_supplier(data: SupplierLogin, db: Session = Depends(get_db)):
    user = db.query(SupplierUser).filter(SupplierUser.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Invalid username or password"}}
        )
    
    supplier = db.query(Supplier).filter(Supplier.id == user.supplier_id).first()
    
    # Generate token
    token_payload = {
        "user_id": user.id,
        "username": user.username,
        "supplier_id": user.supplier_id,
        "role": user.role
    }
    token = create_access_token(token_payload)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "supplier": {
            "id": supplier.id,
            "company_name": supplier.company_name,
            "email": supplier.email,
            "is_verified": supplier.is_verified
        }
    }

@router.get("/me")
def get_supplier_me(supplier: Supplier = Depends(get_current_supplier)):
    return {
        "id": supplier.id,
        "company_name": supplier.company_name,
        "email": supplier.email,
        "phone": supplier.phone,
        "gstin": supplier.gstin,
        "address": supplier.address,
        "is_verified": supplier.is_verified,
        "created_at": supplier.created_at
    }

@router.post("/{supplier_id}/verify")
def verify_supplier(supplier_id: int, approved: bool, notes: Optional[str] = "Admin review", db: Session = Depends(get_db)):
    """
    Verification simulation endpoint. In a live system, this would be admin-only.
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "supplier_not_found", "message": "Supplier not found"}}
        )
    
    status_str = "approved" if approved else "rejected"
    supplier.is_verified = approved
    
    verification = SupplierVerification(
        supplier_id=supplier.id,
        verifier_notes=notes,
        status=status_str
    )
    db.add(verification)

    if approved:
        from app.models.marketplace_orm import SaaS_Subscription
        from datetime import datetime, timedelta, timezone
        
        # Check if supplier has an active subscription
        existing_sub = db.query(SaaS_Subscription).filter(
            SaaS_Subscription.supplier_id == supplier.id,
            SaaS_Subscription.status == "active"
        ).first()
        
        if not existing_sub:
            new_sub = SaaS_Subscription(
                supplier_id=supplier.id,
                plan_name="Annual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365)
            )
            db.add(new_sub)
            
    db.commit()
    
    return {
        "status": "success",
        "message": f"Supplier verification status updated to {status_str}",
        "is_verified": supplier.is_verified
    }

@router.post("/inventory/upload", status_code=202)
async def upload_supplier_inventory(
    request: Request,
    background_tasks: BackgroundTasks,
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    """
    Ingests a fleet of batteries for the authenticated, verified supplier.
    Spawns background lifecycle pipeline processing.
    """
    from app.services.pipeline import JOBS, run_pipeline_task
    import uuid
    from datetime import datetime
    
    # Guard: One job at a time globally
    for job in JOBS.values():
        if job["status"] == "running":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "job_already_running", "message": "Another ingestion job is already running"}}
            )

    content_type = request.headers.get("content-type", "")
    rows = []

    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if not file or not hasattr(file, "read"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "empty_file", "message": "No CSV file provided in multipart/form-data"}}
            )
        content = await file.read()
        from app.services.ingestion import parse_csv_file, process_ingestion
        try:
            rows = parse_csv_file(content.decode("utf-8"))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_csv", "message": f"Failed to parse CSV: {str(e)}"}}
            )
    elif "application/json" in content_type:
        try:
            data = await request.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_json", "message": f"Failed to parse JSON: {str(e)}"}}
            )
        if not isinstance(data, dict) or "batteries" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "empty_file", "message": "JSON payload must contain a 'batteries' list"}}
            )
        rows = data["batteries"]
        from app.services.ingestion import process_ingestion
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "unsupported_media_type", "message": "Unsupported Content-Type. Use multipart/form-data or application/json"}}
        )

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "empty_file", "message": "No records found in upload"}}
        )

    try:
        inserted_ids, rejects = process_ingestion(db, rows, supplier_id=supplier.id)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": {"code": "too_large", "message": str(ve)}}
        )

    # Job ID generation
    job_id = f"j_{uuid.uuid4().hex[:6]}"

    if inserted_ids:
        # Spawn the BackgroundTask pacing processing
        background_tasks.add_task(run_pipeline_task, job_id, inserted_ids)
    else:
        # Empty job
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "processed": 0,
            "total": 0,
            "failed_ids": [],
            "started_at": datetime.utcnow()
        }

    return {
        "job_id": job_id,
        "accepted": len(inserted_ids),
        "rejected": len(rejects),
        "rejects": rejects
    }


# --- Listing Configuration Routes ---

@router.post("/inventory/lots/{lot_id}/listing")
def configure_listing(
    lot_id: int,
    data: ListingUpdate,
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    lot = db.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )
    if lot.supplier_id != supplier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "forbidden_lot", "message": "You do not own this inventory lot"}}
        )
    
    if data.moq < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_moq", "message": "Minimum Order Quantity must be at least 1"}}
        )

    # Find or create listing
    listing = db.query(Listing).filter(Listing.inventory_lot_id == lot.id).first()
    if not listing:
        listing = Listing(
            inventory_lot_id=lot.id,
            title=f"GRADE {lot.grade} {lot.chemistry} Lot",
            description=data.description,
            moq=data.moq,
            is_published=False
        )
        db.add(listing)
    else:
        listing.description = data.description
        listing.moq = data.moq
    
    db.commit()
    db.refresh(listing)
    return {
        "status": "success",
        "message": "Listing details updated successfully",
        "listing": {
            "id": listing.id,
            "title": listing.title,
            "description": listing.description,
            "moq": listing.moq,
            "is_published": listing.is_published
        }
    }


@router.post("/inventory/lots/{lot_id}/pricing")
def configure_pricing_tiers(
    lot_id: int,
    data: PricingTiersUpdate,
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    lot = db.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )
    if lot.supplier_id != supplier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "forbidden_lot", "message": "You do not own this inventory lot"}}
        )

    if not data.tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_pricing", "message": "At least one pricing tier must be configured"}}
        )

    # Validate tiers
    for tier in data.tiers:
        if tier.min_quantity < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_pricing", "message": "Minimum quantity in pricing tiers must be at least 1"}}
            )
        if tier.price_per_kwh <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "invalid_pricing", "message": "Price per kWh must be positive"}}
            )

    # Sort pricing tiers by min_quantity
    sorted_tiers = sorted(data.tiers, key=lambda x: x.min_quantity)

    # Remove existing pricing tiers
    db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).delete()

    # Insert new tiers
    new_tiers = []
    for t in sorted_tiers:
        pt = PricingTier(
            inventory_lot_id=lot.id,
            min_quantity=t.min_quantity,
            price_per_kwh=t.price_per_kwh
        )
        db.add(pt)
        new_tiers.append(pt)

    db.commit()

    return {
        "status": "success",
        "message": "Pricing tiers updated successfully",
        "tiers": [
            {"min_quantity": t.min_quantity, "price_per_kwh": float(t.price_per_kwh)}
            for t in new_tiers
        ]
    }


@router.post("/inventory/lots/{lot_id}/publish")
def publish_listing(
    lot_id: int,
    publish: bool = True,
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    lot = db.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )
    if lot.supplier_id != supplier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "forbidden_lot", "message": "You do not own this inventory lot"}}
        )

    # Check if a listing exists
    listing = db.query(Listing).filter(Listing.inventory_lot_id == lot.id).first()
    if not listing and publish:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "missing_listing_details", "message": "Please configure listing details (MOQ, description) before publishing"}}
        )

    # Check if pricing tiers exist
    pricing_count = db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).count()
    if pricing_count == 0 and publish:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "missing_pricing", "message": "Please configure at least one pricing tier before publishing"}}
        )

    if publish:
        if lot.available_quantity == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "empty_lot", "message": "Cannot publish an inventory lot with 0 batteries"}}
            )
        listing.is_published = True
        lot.status = "listed"
    else:
        if listing:
            listing.is_published = False
        lot.status = "draft"

    db.commit()

    return {
        "status": "success",
        "message": f"Inventory lot has been successfully {'published' if publish else 'unpublished'}",
        "is_published": listing.is_published if listing else False,
        "lot_status": lot.status
    }


@router.get("/inventory/lots/{lot_id}/listing")
def get_listing_configuration(
    lot_id: int,
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    lot = db.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "lot_not_found", "message": "Inventory lot not found"}}
        )
    if lot.supplier_id != supplier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "forbidden_lot", "message": "You do not own this inventory lot"}}
        )

    listing = db.query(Listing).filter(Listing.inventory_lot_id == lot.id).first()
    tiers = db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).order_by(PricingTier.min_quantity).all()

    return {
        "lot_id": lot.id,
        "grade": lot.grade,
        "chemistry": lot.chemistry,
        "available_quantity": lot.available_quantity,
        "total_capacity_kwh": float(lot.total_capacity_kwh),
        "avg_soh": float(lot.avg_soh),
        "avg_rul_years": float(lot.avg_rul_years),
        "status": lot.status,
        "listing": {
            "id": listing.id if listing else None,
            "title": listing.title if listing else f"GRADE {lot.grade} {lot.chemistry} Lot",
            "description": listing.description if listing else "",
            "moq": listing.moq if listing else 1,
            "is_published": listing.is_published if listing else False
        } if listing else None,
        "pricing_tiers": [
            {"min_quantity": t.min_quantity, "price_per_kwh": float(t.price_per_kwh)}
            for t in tiers
        ]
    }


# --- Dashboard Routes ---

@router.get("/dashboard/stats")
def get_dashboard_stats(
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    """
    Returns aggregate KPI metrics for the verified supplier.
    """
    from app.models.marketplace_orm import Order
    from sqlalchemy.sql import func
    
    # 1. Active Lots (Listed status)
    active_lots_count = db.query(InventoryLot).filter(
        InventoryLot.supplier_id == supplier.id,
        InventoryLot.status == "listed"
    ).count()

    # 2. Completed Orders (delivered or completed tracking status)
    completed_orders_count = db.query(Order).filter(
        Order.supplier_id == supplier.id,
        Order.tracking_status.in_(["delivered", "completed"])
    ).count()

    # 3. Pending Orders (paid and in-progress tracking status)
    pending_orders_count = db.query(Order).filter(
        Order.supplier_id == supplier.id,
        Order.payment_status == "paid",
        ~Order.tracking_status.in_(["delivered", "completed"])
    ).count()

    # 4. Total Revenue (sum of total_price for paid/completed orders)
    revenue_sum = db.query(func.sum(Order.total_price)).filter(
        Order.supplier_id == supplier.id,
        Order.payment_status == "paid"
    ).scalar()
    
    total_revenue_rupees = float(revenue_sum) if revenue_sum is not None else 0.0

    # 5. Available Batteries — total remaining units across all ACTIVE lots (FIX 5)
    available_batteries_sum = db.query(func.sum(InventoryLot.available_quantity)).filter(
        InventoryLot.supplier_id == supplier.id,
        InventoryLot.status.in_(["draft", "listed"])
    ).scalar()
    available_batteries = int(available_batteries_sum) if available_batteries_sum is not None else 0

    return {
        "active_lots_count": active_lots_count,
        "completed_orders_count": completed_orders_count,
        "pending_orders_count": pending_orders_count,
        "total_revenue_rupees": total_revenue_rupees,
        "available_batteries": available_batteries
    }


@router.get("/dashboard/inventory")
def get_dashboard_inventory(
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    """
    Returns all inventory lots belonging to the authenticated supplier, 
    with their detailed status, specs, pricing tiers, and listing details.
    """
    lots = db.query(InventoryLot).filter(
        InventoryLot.supplier_id == supplier.id
    ).order_by(InventoryLot.created_at.desc()).all()
    
    results = []
    for lot in lots:
        # Find listing if configured
        listing = db.query(Listing).filter(Listing.inventory_lot_id == lot.id).first()
        # Find pricing tiers
        tiers = db.query(PricingTier).filter(PricingTier.inventory_lot_id == lot.id).order_by(PricingTier.min_quantity).all()
        
        # Compute per-battery capacity (FIX 4)
        total_cap = float(lot.total_capacity_kwh)
        cap_per_battery = round(total_cap / lot.available_quantity, 2) if lot.available_quantity > 0 else total_cap

        results.append({
            "id": lot.id,
            "grade": lot.grade,
            "chemistry": lot.chemistry,
            "available_quantity": lot.available_quantity,
            "capacity_per_battery_kwh": cap_per_battery,
            "total_capacity_kwh": total_cap,
            "avg_soh": float(lot.avg_soh),
            "avg_rul_years": float(lot.avg_rul_years),
            "status": lot.status,
            "created_at": lot.created_at.isoformat() if lot.created_at else None,
            "listing": {
                "id": listing.id if listing else None,
                "title": listing.title if listing else f"GRADE {lot.grade} {lot.chemistry} Lot",
                "description": listing.description if listing else "",
                "moq": listing.moq if listing else 1,
                "is_published": listing.is_published if listing else False
            } if listing else None,
            "pricing_tiers": [
                {"min_quantity": t.min_quantity, "price_per_kwh": float(t.price_per_kwh)}
                for t in tiers
            ]
        })
        
    return results


@router.get("/dashboard/orders")
def get_dashboard_orders(
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    """
    Returns all paid orders received by this supplier, including buyer metadata 
    and lot descriptors.
    """
    from app.models.marketplace_orm import Order, BuyerAccount
    
    orders = db.query(Order).filter(
        Order.supplier_id == supplier.id
    ).order_by(Order.created_at.desc()).all()
    
    results = []
    for o in orders:
        buyer = db.query(BuyerAccount).filter(BuyerAccount.id == o.buyer_id).first()
        lot = o.inventory_lot
        
        results.append({
            "id": o.id,
            "quantity": o.quantity,
            "total_price": float(o.total_price),
            "payment_status": o.payment_status,
            "tracking_status": o.tracking_status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "buyer": {
                "company_name": buyer.company_name if buyer else "Unknown Buyer",
                "email": buyer.email if buyer else ""
            },
            "lot": {
                "id": lot.id if lot else None,
                "grade": lot.grade if lot else "",
                "chemistry": lot.chemistry if lot else ""
            }
        })
        
    return results


@router.get("/dashboard/requirements")
def get_dashboard_requirements(
    supplier: Supplier = Depends(get_current_active_subscriber),
    db: Session = Depends(get_db)
):
    """
    Returns all active buyer requirements in the marketplace.
    Sellers cannot see competing offers/quotes, but can browse what buyers want.
    """
    from app.models.marketplace_orm import Requirement, BuyerAccount
    
    requirements = db.query(Requirement).order_by(Requirement.created_at.desc()).all()
    
    results = []
    for r in requirements:
        buyer = db.query(BuyerAccount).filter(BuyerAccount.id == r.buyer_id).first()
        
        results.append({
            "id": r.id,
            "use_case_text": r.use_case_text,
            "parsed_grade": r.parsed_grade,
            "parsed_capacity_kwh": float(r.parsed_capacity_kwh) if r.parsed_capacity_kwh is not None else None,
            "parsed_quantity": r.parsed_quantity,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "buyer": {
                "company_name": buyer.company_name if buyer else "Anonymous Buyer"
            }
        })
        
    return results


