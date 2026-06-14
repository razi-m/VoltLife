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


def seed_demo_marketplace_data(db: Session):
    """
    Seeds the database with full demo marketplace transactions and active listings
    so that every dashboard, requirements, quotes, orders, and telemetry page
    is populated with realistic data on demo reset.
    """
    from app.models.marketplace_orm import (
        Supplier, SupplierUser, BuyerAccount, InventoryLot, PricingTier, Listing,
        Requirement, Quote, Order, ShipmentTrackingEvent, PaymentEvent, SupportTicket
    )
    from app.models.orm import Battery, TelemetrySummary, Assessment
    from app.core.auth import hash_password
    from datetime import datetime, timedelta, timezone
    import random

    logger.info("Seeding full demo marketplace data...")

    # 1. Fetch default users (pre-seeded by seed_marketplace_demo_users)
    buyer = db.query(BuyerAccount).filter(BuyerAccount.username == "demo_buyer").first()
    supplier_user = db.query(SupplierUser).filter(SupplierUser.username == "demo_supplier").first()
    
    if not buyer or not supplier_user:
        logger.error("Demo users missing. Cannot seed marketplace data.")
        return

    supplier_id = supplier_user.supplier_id

    # 2. Seed 12 Batteries for Supplier
    battery_configs = [
        # Grade S LFP
        {"chemistry": "LFP", "grade": "S", "soh": 96.5, "rul": 5.2, "rated": 5.0, "ext": "BAT-DEMO-01", "cycles": 80},
        {"chemistry": "LFP", "grade": "S", "soh": 95.0, "rul": 5.0, "rated": 5.0, "ext": "BAT-DEMO-02", "cycles": 120},
        {"chemistry": "LFP", "grade": "S", "soh": 97.2, "rul": 5.5, "rated": 5.0, "ext": "BAT-DEMO-03", "cycles": 50},
        
        # Grade A NMC
        {"chemistry": "NMC", "grade": "A", "soh": 88.5, "rul": 4.5, "rated": 4.0, "ext": "BAT-DEMO-04", "cycles": 350},
        {"chemistry": "NMC", "grade": "A", "soh": 89.0, "rul": 4.6, "rated": 4.0, "ext": "BAT-DEMO-05", "cycles": 300},
        {"chemistry": "NMC", "grade": "A", "soh": 87.8, "rul": 4.2, "rated": 4.0, "ext": "BAT-DEMO-06", "cycles": 420},
        {"chemistry": "NMC", "grade": "A", "soh": 88.0, "rul": 4.3, "rated": 4.0, "ext": "BAT-DEMO-07", "cycles": 400},
        {"chemistry": "NMC", "grade": "A", "soh": 89.2, "rul": 4.7, "rated": 4.0, "ext": "BAT-DEMO-08", "cycles": 280},
        
        # Grade B NMC
        {"chemistry": "NMC", "grade": "B", "soh": 79.5, "rul": 3.1, "rated": 4.0, "ext": "BAT-DEMO-09", "cycles": 720},
        {"chemistry": "NMC", "grade": "B", "soh": 81.0, "rul": 3.3, "rated": 4.0, "ext": "BAT-DEMO-10", "cycles": 650},
        {"chemistry": "NMC", "grade": "B", "soh": 78.8, "rul": 3.0, "rated": 4.0, "ext": "BAT-DEMO-11", "cycles": 780},
        {"chemistry": "NMC", "grade": "B", "soh": 80.2, "rul": 3.2, "rated": 4.0, "ext": "BAT-DEMO-12", "cycles": 680},
    ]

    batteries = []
    for cfg in battery_configs:
        # Check if already exists to prevent duplicate seeding
        existing_bat = db.query(Battery).filter(Battery.external_ref == cfg["ext"]).first()
        if existing_bat:
            batteries.append(existing_bat)
            continue

        aadhaar_hash = f"AADHAARDEMO{cfg['ext'][-2:]}{random.randint(100000, 999999)}"
        bat = Battery(
            aadhaar_id=aadhaar_hash[:21],
            external_ref=cfg["ext"],
            oem="FOA" if cfg["chemistry"] == "NMC" else "FOB",
            model="Pack-1" if cfg["chemistry"] == "NMC" else "Pack-2",
            chemistry=cfg["chemistry"],
            rated_capacity_kwh=cfg["rated"],
            nominal_voltage=48.0 if cfg["chemistry"] == "NMC" else 60.0,
            manufacture_date=datetime.now().date() - timedelta(days=cfg["cycles"] * 2),
            source_city="Pune",
            source_state="Maharashtra",
            lat=18.5208,
            lng=73.8567,
            status="assessed",
            supplier_id=supplier_id
        )
        db.add(bat)
        db.flush()

        # Telemetry Summary
        telemetry = TelemetrySummary(
            battery_id=bat.id,
            cycle_count=cfg["cycles"],
            capacity_now_kwh=float(cfg["rated"]) * (cfg["soh"] / 100.0),
            capacity_fade_pct=100.0 - cfg["soh"],
            fade_rate_pct_per_100cyc=(100.0 - cfg["soh"]) / max(1.0, (cfg["cycles"] / 100.0)),
            avg_temp_c=31.5,
            max_temp_c=42.0,
            thermal_stress_hours=12.5,
            internal_resistance_mohm=18.5,
            ir_growth_pct=14.2,
            voltage_stability=0.995,
            coulombic_efficiency=0.998,
            features_json={"discharge_efficiency": 0.97}
        )
        db.add(telemetry)

        # Assessment
        assessment = Assessment(
            battery_id=bat.id,
            soh_pct=cfg["soh"],
            rul_years=cfg["rul"],
            rul_low_years=cfg["rul"] - 0.5,
            rul_high_years=cfg["rul"] + 0.5,
            grade=cfg["grade"],
            confidence="high",
            model_version="model_v1.0",
            explanation_json={"grade_reason": "Based on SOH and RUL model threshold constraints."}
        )
        db.add(assessment)
        batteries.append(bat)

    # 3. Create 3 Inventory Lots
    s_lfp_bats = [b for b in batteries if b.chemistry == "LFP" and b.external_ref in ("BAT-DEMO-01", "BAT-DEMO-02", "BAT-DEMO-03")]
    a_nmc_bats = [b for b in batteries if b.chemistry == "NMC" and b.external_ref in ("BAT-DEMO-04", "BAT-DEMO-05", "BAT-DEMO-06", "BAT-DEMO-07", "BAT-DEMO-08")]
    b_nmc_bats = [b for b in batteries if b.chemistry == "NMC" and b.external_ref in ("BAT-DEMO-09", "BAT-DEMO-10", "BAT-DEMO-11", "BAT-DEMO-12")]

    # Lot 1: Grade A NMC (Total capacity: 5 * 4 = 20 kWh, initially 5 packs)
    # Available packs will be 3 (after completed order of 2 units)
    lot1 = db.query(InventoryLot).filter(InventoryLot.grade == "A", InventoryLot.chemistry == "NMC", InventoryLot.supplier_id == supplier_id).first()
    if not lot1:
        lot1 = InventoryLot(
            supplier_id=supplier_id,
            grade="A",
            chemistry="NMC",
            total_capacity_kwh=20.0,
            available_quantity=3,
            avg_soh=88.5,
            avg_rul_years=4.5,
            status="listed"
        )
        lot1.batteries = a_nmc_bats
        db.add(lot1)
        db.flush()

        listing1 = Listing(
            inventory_lot_id=lot1.id,
            title="Premium Grade A NMC Power Packs",
            description="Verified second-life batteries with high SOH. Optimal for grid-tied solar backup or ESS setups.",
            moq=2,
            is_published=True
        )
        db.add(listing1)

        tier1 = PricingTier(
            inventory_lot_id=lot1.id,
            min_quantity=1,
            price_per_kwh=150.0
        )
        db.add(tier1)

    # Lot 2: Grade B NMC (Total capacity: 4 * 4 = 16 kWh, initially 4 packs)
    # Available packs will be 2 (after active order of 2 units)
    lot2 = db.query(InventoryLot).filter(InventoryLot.grade == "B", InventoryLot.chemistry == "NMC", InventoryLot.supplier_id == supplier_id).first()
    if not lot2:
        lot2 = InventoryLot(
            supplier_id=supplier_id,
            grade="B",
            chemistry="NMC",
            total_capacity_kwh=16.0,
            available_quantity=2,
            avg_soh=79.9,
            avg_rul_years=3.1,
            status="listed"
        )
        lot2.batteries = b_nmc_bats
        db.add(lot2)
        db.flush()

        listing2 = Listing(
            inventory_lot_id=lot2.id,
            title="Second-Life Grade B NMC Battery Modules",
            description="Tested NMC battery modules. Ideal for low-discharge residential solar backups and secondary power backups.",
            moq=1,
            is_published=True
        )
        db.add(listing2)

        tier2_1 = PricingTier(
            inventory_lot_id=lot2.id,
            min_quantity=1,
            price_per_kwh=120.0
        )
        tier2_2 = PricingTier(
            inventory_lot_id=lot2.id,
            min_quantity=5,
            price_per_kwh=110.0
        )
        db.add_all([tier2_1, tier2_2])

    # Lot 3: Grade S LFP (Total capacity: 3 * 5 = 15 kWh, initially 3 packs)
    lot3 = db.query(InventoryLot).filter(InventoryLot.grade == "S", InventoryLot.chemistry == "LFP", InventoryLot.supplier_id == supplier_id).first()
    if not lot3:
        lot3 = InventoryLot(
            supplier_id=supplier_id,
            grade="S",
            chemistry="LFP",
            total_capacity_kwh=15.0,
            available_quantity=3,
            avg_soh=96.2,
            avg_rul_years=5.2,
            status="draft"
        )
        lot3.batteries = s_lfp_bats
        db.add(lot3)
        db.flush()

        listing3 = Listing(
            inventory_lot_id=lot3.id,
            title="Brand New Grade S LFP Cell Packs",
            description="Premium ultra-health LFP packs with zero cycle wear. Ideal for heavy industrial and high-rate EV forklift charging.",
            moq=1,
            is_published=False
        )
        db.add(listing3)

    # 4. Seed Buyer Requirements
    existing_req = db.query(Requirement).filter(Requirement.buyer_id == buyer.id).first()
    if not existing_req:
        req1 = Requirement(
            buyer_id=buyer.id,
            use_case_text="Require 50 kWh capacity solar backup storage system, Grade A batteries, quantity 4 packs",
            parsed_grade="A",
            parsed_capacity_kwh=50.0,
            parsed_quantity=4
        )
        req2 = Requirement(
            buyer_id=buyer.id,
            use_case_text="Looking for high-health Grade S LFP packs for warehouse EV forklift charging station, approx 3 packs",
            parsed_grade="S",
            parsed_capacity_kwh=30.0,
            parsed_quantity=3
        )
        db.add_all([req1, req2])

    # 5. Seed Quotes
    existing_quote = db.query(Quote).filter(Quote.buyer_id == buyer.id).first()
    if not existing_quote and lot1:
        quote = Quote(
            buyer_id=buyer.id,
            inventory_lot_id=lot1.id,
            quantity=3,
            battery_cost=1800.0,
            transport_cost=550.0,
            total_cost=2350.0,
            delivery_days=2,
            porter_vehicle_type="Piaggio Ape",
            status="pending"
        )
        db.add(quote)

    # 6. Seed Orders & Tracking
    existing_order = db.query(Order).filter(Order.buyer_id == buyer.id).first()
    if not existing_order and lot1 and lot2:
        # Order 1: Active Order (In Transit) - Lot 2
        order_active = Order(
            buyer_id=buyer.id,
            supplier_id=supplier_id,
            inventory_lot_id=lot2.id,
            quantity=2,
            total_price=1310.0,
            payment_status="paid",
            tracking_status="in_transit"
        )
        db.add(order_active)
        db.flush()

        payment_active = PaymentEvent(
            order_id=order_active.id,
            stripe_session_id="mock_session_active_order_reset",
            amount=1310.0,
            status="success"
        )
        db.add(payment_active)

        events_active = [
            ShipmentTrackingEvent(order_id=order_active.id, event_type="confirmed", notes="Order accepted by seller Apex Logistics."),
            ShipmentTrackingEvent(order_id=order_active.id, event_type="porter_booked", notes="Porter delivery vehicle Tata Ace booked successfully."),
            ShipmentTrackingEvent(order_id=order_active.id, event_type="shipment_started", notes="Logistics dispatcher has verified battery Aadhaar credentials."),
            ShipmentTrackingEvent(order_id=order_active.id, event_type="in_transit", notes="Shipment departed supplier facility. Current location: Pune highway.")
        ]
        db.add_all(events_active)

        # Order 2: Completed Order - Lot 1
        order_completed = Order(
            buyer_id=buyer.id,
            supplier_id=supplier_id,
            inventory_lot_id=lot1.id,
            quantity=2,
            total_price=1750.0,
            payment_status="paid",
            tracking_status="completed"
        )
        db.add(order_completed)
        db.flush()

        payment_completed = PaymentEvent(
            order_id=order_completed.id,
            stripe_session_id="mock_session_completed_order_reset",
            amount=1750.0,
            status="success"
        )
        db.add(payment_completed)

        events_completed = [
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="confirmed", notes="Order accepted by seller."),
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="porter_booked", notes="Porter vehicle Piaggio Ape booked."),
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="shipment_started", notes="Shipment verified by dispatcher."),
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="in_transit", notes="In transit."),
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="delivered", notes="Delivered at buyer destination."),
            ShipmentTrackingEvent(order_id=order_completed.id, event_type="completed", notes="Receipt confirmed by buyer. Order closed.")
        ]
        db.add_all(events_completed)

        # Create support ticket for completed order
        ticket = SupportTicket(
            order_id=order_completed.id,
            buyer_id=buyer.id,
            issue_text="One of the plastic terminal covers is loose on the second pack.",
            status="open"
        )
        db.add(ticket)

    db.commit()
    logger.info("Demo marketplace seeding completed successfully!")


if __name__ == "__main__":
    # If run directly, initialize DB (SQLite fallback support) and run seeding
    init_db()
    db = SessionLocal()
    try:
        seed_sites(db)
        seed_marketplace_demo_users(db)
        seed_demo_marketplace_data(db)
    finally:
        db.close()

