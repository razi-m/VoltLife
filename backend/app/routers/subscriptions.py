import os
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.models.marketplace_orm import Supplier, SaaS_Subscription
from app.routers.suppliers import get_current_verified_supplier

try:
    import stripe
except ImportError:
    stripe = None

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Subscription Plans Config
PLANS = {
    "Monthly": {
        "name": "Monthly",
        "price_inr": 5000.0,
        "duration_days": 30,
        "description": "Standard monthly access for fleet operators and battery sellers."
    },
    "Annual": {
        "name": "Annual",
        "price_inr": 50000.0,
        "duration_days": 365,
        "description": "Recommended annual pass with 16% discount."
    },
    "Enterprise": {
        "name": "Enterprise",
        "price_inr": 1500000.0,
        "duration_days": 36500, # ~100 years
        "description": "Full enterprise capability, dedicated custom support, and offline contracts."
    }
}

class SessionCreate(BaseModel):
    plan_name: str

class VerifyRequest(BaseModel):
    plan_name: str
    session_id: str  # For mock or Stripe verification

@router.get("/plans")
def get_plans():
    return [
        {
            "name": k,
            "price_rupees": v["price_inr"],
            "description": v["description"],
            "duration_days": v["duration_days"]
        }
        for k, v in PLANS.items()
    ]

@router.get("/status")
def get_subscription_status(
    supplier: Supplier = Depends(get_current_verified_supplier),
    db: Session = Depends(get_db)
):
    # Find any active subscription
    sub = db.query(SaaS_Subscription).filter(
        SaaS_Subscription.supplier_id == supplier.id,
        SaaS_Subscription.status == "active"
    ).first()

    if not sub:
        # Check if they have an expired/cancelled one to display
        sub = db.query(SaaS_Subscription).filter(
            SaaS_Subscription.supplier_id == supplier.id
        ).order_by(SaaS_Subscription.created_at.desc()).first()

    if not sub:
        return {
            "status": "inactive",
            "plan_name": None,
            "expires_at": None
        }

    # Dynamically check for expiry
    if sub.expires_at:
        now = datetime.now(timezone.utc)
        expires_at = sub.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if now > expires_at:
            if sub.status == "active":
                sub.status = "expired"
                db.commit()

    return {
        "status": sub.status,
        "plan_name": sub.plan_name,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None
    }

@router.post("/create-session")
def create_subscription_session(
    data: SessionCreate,
    supplier: Supplier = Depends(get_current_verified_supplier),
    db: Session = Depends(get_db)
):
    plan_name = data.plan_name
    if plan_name not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_plan", "message": "Subscription plan not found"}}
        )

    plan = PLANS[plan_name]
    amount_paise = int(plan["price_inr"] * 100)

    # Check for Stripe credentials
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    backend_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")

    if stripe_key and stripe:
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "inr",
                        "product_data": {
                            "name": f"VoltLife Battery SaaS - {plan_name} Plan",
                            "description": plan["description"],
                        },
                        "unit_amount": amount_paise,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                metadata={
                    "plan_name": plan_name,
                    "supplier_id": str(supplier.id)
                },
                success_url=f"{backend_url}/subscriptions/checkout-success?session_id={{CHECKOUT_SESSION_ID}}&plan_name={plan_name}",
                cancel_url=f"{backend_url}/subscriptions/checkout-cancel?plan_name={plan_name}",
            )
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "amount_paise": amount_paise,
                "key_id": os.getenv("STRIPE_PUBLISHABLE_KEY", "stripe_test_key"),
                "is_mock": False
            }
        except Exception as e:
            # Fallback to mock on failure
            pass

    # Mock Session Fallback
    mock_session_id = f"MOCK_SUB_SESS_{uuid.uuid4().hex[:8]}"
    return {
        "session_id": mock_session_id,
        "checkout_url": f"/verify-mock-sub?session_id={mock_session_id}&plan={plan_name}",
        "amount_paise": amount_paise,
        "key_id": "stripe_test_mockkey",
        "is_mock": True
    }

@router.post("/verify")
def verify_subscription(
    data: VerifyRequest,
    supplier: Supplier = Depends(get_current_verified_supplier),
    db: Session = Depends(get_db)
):
    plan_name = data.plan_name
    if plan_name not in PLANS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_plan", "message": "Subscription plan not found"}}
        )

    # 1. Verification of Payment (Real or Mock)
    is_verified = False
    sub_id = data.session_id

    stripe_key = os.getenv("STRIPE_SECRET_KEY")

    if stripe_key and stripe and not sub_id.startswith("MOCK_SUB_SESS_"):
        try:
            stripe.api_key = stripe_key
            session = stripe.checkout.Session.retrieve(sub_id)
            if (session.payment_status == "paid" and 
                session.metadata.get("plan_name") == plan_name and 
                session.metadata.get("supplier_id") == str(supplier.id)):
                is_verified = True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "signature_verification_failed", "message": "Stripe session verification failed"}}
            )
    else:
        # Mock payment verification
        if sub_id.startswith("MOCK_SUB_SESS_"):
            is_verified = True

    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_session", "message": "Failed to verify subscription session"}}
        )

    # 2. Update/create subscription
    plan = PLANS[plan_name]
    expires_at = datetime.now(timezone.utc) + timedelta(days=plan["duration_days"])

    # Deactivate any active subscriptions first
    db.query(SaaS_Subscription).filter(
        SaaS_Subscription.supplier_id == supplier.id,
        SaaS_Subscription.status == "active"
    ).update({"status": "cancelled"})

    # Create new active subscription
    new_sub = SaaS_Subscription(
        supplier_id=supplier.id,
        stripe_subscription_id=sub_id, # store Stripe/Mock ID in stripe_subscription_id column
        plan_name=plan_name,
        status="active",
        expires_at=expires_at
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)

    return {
        "status": "success",
        "subscription": {
            "id": new_sub.id,
            "plan_name": new_sub.plan_name,
            "status": new_sub.status,
            "expires_at": new_sub.expires_at.isoformat() if new_sub.expires_at else None
        }
    }

@router.post("/cancel")
def cancel_subscription(
    supplier: Supplier = Depends(get_current_verified_supplier),
    db: Session = Depends(get_db)
):
    # Find active subscription
    sub = db.query(SaaS_Subscription).filter(
        SaaS_Subscription.supplier_id == supplier.id,
        SaaS_Subscription.status == "active"
    ).first()

    if not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "no_active_subscription", "message": "No active SaaS subscription found"}}
        )

    # Cancel/Force Expire it (set expires_at to now for instant expiration testing)
    sub.status = "expired"
    sub.expires_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(sub)

    return {
        "status": "success",
        "message": "Subscription force-expired for demo testing",
        "subscription": {
            "id": sub.id,
            "plan_name": sub.plan_name,
            "status": sub.status,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None
        }
    }
