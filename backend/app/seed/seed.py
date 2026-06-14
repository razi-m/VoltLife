import os
import json
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, init_db
from app.models.orm import Site
from app.core.logging import logger

def seed_sites(db: Session):
    """
    Seeds the sites table with demand registry data from sites.json.
    Wipes existing sites first to ensure idempotency.
    """
    # Load sites.json
    # Determine the directory where this file resides
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sites_json_path = os.path.join(current_dir, "sites.json")
    
    if not os.path.exists(sites_json_path):
        logger.error(f"sites.json not found at {sites_json_path}")
        return
        
    with open(sites_json_path, "r") as f:
        sites_data = json.load(f)
        
    logger.info(f"Loaded {len(sites_data)} sites from sites.json. Seeding database...")
    
    # Wipe old sites
    db.query(Site).delete()
    db.commit()
    
    # Insert new sites
    for s_dict in sites_data:
        site = Site(
            name=s_dict["name"],
            site_type=s_dict["site_type"],
            state=s_dict.get("state"),
            lat=s_dict["lat"],
            lng=s_dict["lng"],
            demand_kwh=s_dict["demand_kwh"],
            min_soh_pct=s_dict["min_soh_pct"],
            min_grade=s_dict["min_grade"],
            priority=s_dict.get("priority", 1.0),
            is_simulated=s_dict.get("is_simulated", True)
        )
        db.add(site)
        
    db.commit()
    logger.info("Successfully seeded sites table.")

def seed_marketplace_demo_users(db: Session):
    """
    Seeds the database with a default verified Supplier and a default Buyer
    for role-based authentication testing.
    """
    from app.models.marketplace_orm import Supplier, SupplierUser, BuyerAccount
    from app.core.auth import hash_password

    # 1. Seed default buyer
    existing_buyer = db.query(BuyerAccount).filter(BuyerAccount.username == "demo_buyer").first()
    if not existing_buyer:
        buyer = BuyerAccount(
            company_name="Demo Buyer Inc",
            email="buyer@demovolt.com",
            phone="+918888888888",
            address="Mumbai, Maharashtra",
            username="demo_buyer",
            password_hash=hash_password("password123")
        )
        db.add(buyer)
        logger.info("Seeding default buyer account (demo_buyer)...")

    # 2. Seed default supplier
    existing_supplier_user = db.query(SupplierUser).filter(SupplierUser.username == "demo_supplier").first()
    from app.models.marketplace_orm import SaaS_Subscription
    from datetime import datetime, timedelta, timezone

    if not existing_supplier_user:
        # Create supplier first
        supplier = Supplier(
            company_name="Demo Supplier Ltd",
            email="supplier@demovolt.com",
            phone="+919999999999",
            gstin="27AAAAA0000A1Z5",
            address="Pune, Maharashtra",
            is_verified=True
        )
        db.add(supplier)
        db.flush()
        
        # Create user
        supplier_user = SupplierUser(
            supplier_id=supplier.id,
            username="demo_supplier",
            password_hash=hash_password("password123"),
            role="admin"
        )
        db.add(supplier_user)
        logger.info("Seeding default supplier account (demo_supplier)...")
        
        # Create subscription
        subscription = SaaS_Subscription(
            supplier_id=supplier.id,
            plan_name="Annual",
            status="active",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365)
        )
        db.add(subscription)
        logger.info("Seeding default subscription for demo_supplier...")
    else:
        # Check if subscription exists for the existing supplier
        existing_sub = db.query(SaaS_Subscription).filter(
            SaaS_Subscription.supplier_id == existing_supplier_user.supplier_id
        ).first()
        if not existing_sub:
            subscription = SaaS_Subscription(
                supplier_id=existing_supplier_user.supplier_id,
                plan_name="Annual",
                status="active",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365)
            )
            db.add(subscription)
            logger.info("Seeding missing default subscription for demo_supplier...")
        
    db.commit()



if __name__ == "__main__":
    # If run directly, initialize DB (SQLite fallback support) and run seeding
    init_db()
    db = SessionLocal()
    try:
        seed_sites(db)
        seed_marketplace_demo_users(db)
    finally:
        db.close()

