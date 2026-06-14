import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import (
    Supplier, SupplierUser, InventoryLot, Listing, PricingTier,
    BuyerAccount, Requirement, Quote, Order, ShipmentTrackingEvent, PaymentEvent, SupportTicket
)
from app.models.orm import Battery, TelemetrySummary, Assessment

def test_voltlife_marketplace_end_to_end_flow(client: TestClient, db_session: Session):
    """
    End-to-End happy path marketplace flow:
    1. Supplier Register & Verify
    2. Supplier Login
    3. Upload Telemetry CSV (Intake & Grading Pipeline)
    4. Fetch generated draft lot
    5. Configure and Publish Listing & Pricing
    6. Buyer Register & Login
    7. Buyer submits use case requirement
    8. Buyer retrieves matching listings
    9. Buyer negotiates Quote
    10. Checkout Session & Simulated Payment
    11. Inventory lock validation
    12. Logistics Simulation (Transit Tracking)
    13. Buyer receipt confirmation (Order completion)
    14. Support ticket raise
    """
    # -------------------------------------------------------------
    # 1. Supplier Register & Verify
    # -------------------------------------------------------------
    reg_payload = {
        "company_name": "E2E Tesla Volt Corp",
        "email": "supplier_e2e@teslavolt.com",
        "phone": "+919999991234",
        "gstin": "27E2EVOLT121Z9",
        "address": "456 Auto Hub, Pune",
        "username": "supplier_e2e",
        "password": "password123"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=reg_payload)
    assert reg_resp.status_code == 201
    supplier_id = reg_resp.json()["supplier_id"]

    # Admin verification updates verification logs and seeds active subscription
    verify_resp = client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true&notes=Verified E2E supplier")
    assert verify_resp.status_code == 200

    # -------------------------------------------------------------
    # 2. Supplier Login
    # -------------------------------------------------------------
    login_resp = client.post("/api/v1/suppliers/login", json={"username": "supplier_e2e", "password": "password123"})
    assert login_resp.status_code == 200
    supplier_token = login_resp.json()["access_token"]
    supplier_headers = {"Authorization": f"Bearer {supplier_token}"}

    # -------------------------------------------------------------
    # 3. Upload Telemetry CSV (Intake & Grading Pipeline)
    # -------------------------------------------------------------
    csv_data = """external_ref,oem,model,chemistry,rated_capacity_kwh,nominal_voltage,manufacture_date,source_city,source_state,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency
BAT-E1,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,100,3.4,30.5,38.0,5.0,15.0,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98
BAT-E2,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,120,3.42,30.2,37.8,4.8,14.8,7.9,0.999,0.01,0.001,0.10,0.05,0.002,0.98
BAT-E3,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,105,3.38,30.4,37.9,4.9,14.9,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98
"""
    upload_resp = client.post(
        "/api/v1/suppliers/inventory/upload",
        headers=supplier_headers,
        files={"file": ("e2e_fleet.csv", csv_data, "text/csv")}
    )
    assert upload_resp.status_code == 202
    assert upload_resp.json()["accepted"] == 3

    # -------------------------------------------------------------
    # 4. Fetch Generated Draft Lot
    # -------------------------------------------------------------
    inv_resp = client.get("/api/v1/suppliers/dashboard/inventory", headers=supplier_headers)
    assert inv_resp.status_code == 200
    lots = inv_resp.json()
    assert len(lots) == 1
    lot = lots[0]
    assert lot["grade"] == "A"
    assert lot["chemistry"] == "NMC"
    assert lot["available_quantity"] == 3
    assert lot["status"] == "draft"

    # -------------------------------------------------------------
    # 5. Configure and Publish Listing & Pricing
    # -------------------------------------------------------------
    lot_id = lot["id"]
    
    # Configure description and MOQ
    meta_resp = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot_id}/listing",
        headers=supplier_headers,
        json={"moq": 2, "description": "Highly consistent Grade A NMC battery modules."}
    )
    assert meta_resp.status_code == 200

    # Configure pricing tiers
    pricing_resp = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot_id}/pricing",
        headers=supplier_headers,
        json={"tiers": [{"min_quantity": 1, "price_per_kwh": 140.0}]}
    )
    assert pricing_resp.status_code == 200

    # Publish listing
    publish_resp = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot_id}/publish?publish=true",
        headers=supplier_headers
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["is_published"] is True
    assert publish_resp.json()["lot_status"] == "listed"

    # -------------------------------------------------------------
    # 6. Buyer Register & Login
    # -------------------------------------------------------------
    buyer_reg_payload = {
        "company_name": "E2E Green Power Ltd",
        "email": "buyer_e2e@greenpower.com",
        "phone": "+917777771234",
        "address": "789 Solar Boulevard, Bangalore",
        "username": "buyer_e2e",
        "password": "buyerpassword"
    }
    buyer_reg_resp = client.post("/api/v1/buyers/register", json=buyer_reg_payload)
    assert buyer_reg_resp.status_code == 201

    buyer_login_resp = client.post("/api/v1/buyers/login", json={"username": "buyer_e2e", "password": "buyerpassword"})
    assert buyer_login_resp.status_code == 200
    buyer_token = buyer_login_resp.json()["access_token"]
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}

    # -------------------------------------------------------------
    # 7. Buyer Submits Use Case Requirement
    # -------------------------------------------------------------
    req_payload = {
        "use_case_text": "Require 12 kWh capacity backup storage, Grade A batteries, quantity 3 packs"
    }
    req_resp = client.post("/api/v1/requirements", json=req_payload, headers=buyer_headers)
    assert req_resp.status_code == 201
    requirement_id = req_resp.json()["id"]

    # -------------------------------------------------------------
    # 8. Buyer Retrieves Matching Listings
    # -------------------------------------------------------------
    matches_resp = client.get(f"/api/v1/requirements/{requirement_id}/matches", headers=buyer_headers)
    assert matches_resp.status_code == 200
    matches = matches_resp.json()
    assert len(matches) >= 1
    
    # Locate our published lot in matching listings
    match_lot = next((m for m in matches if m["lot_id"] == lot_id), None)
    assert match_lot is not None
    assert match_lot["match_score"] == 100.0  # Perfect fit

    # -------------------------------------------------------------
    # 9. Buyer Negotiates Quote
    # -------------------------------------------------------------
    quote_resp = client.post(
        "/api/v1/quotes",
        headers=buyer_headers,
        json={"inventory_lot_id": lot_id, "quantity": 3}
    )
    assert quote_resp.status_code == 201
    quote = quote_resp.json()
    assert quote["quantity"] == 3
    # 3 packs * 4.0 kWh/pack * ₹140 = ₹1,680.0
    assert quote["battery_cost"] == 1680.0
    assert quote["total_cost"] == quote["battery_cost"] + quote["transport_cost"]
    quote_id = quote["id"]

    # -------------------------------------------------------------
    # 10. Checkout Session & Simulated Payment
    # -------------------------------------------------------------
    checkout_resp = client.post(
        "/api/v1/payments/checkout-session",
        headers=buyer_headers,
        json={"quote_id": quote_id}
    )
    assert checkout_resp.status_code == 200
    session_id = checkout_resp.json()["session_id"]

    confirm_resp = client.post(
        "/api/v1/payments/mock-confirm",
        headers=buyer_headers,
        json={"session_id": session_id}
    )
    assert confirm_resp.status_code == 200
    order = confirm_resp.json()
    assert order["payment_status"] == "paid"
    assert order["tracking_status"] == "confirmed"
    order_id = order["id"]

    # -------------------------------------------------------------
    # 11. Inventory Lock Validation (Quantity decremented to 0)
    # -------------------------------------------------------------
    db_lot = db_session.query(InventoryLot).filter(InventoryLot.id == lot_id).first()
    assert db_lot.available_quantity == 0
    assert db_lot.status == "sold_out"

    # Idempotency check: Confirming same session doesn't lock double
    confirm_resp2 = client.post(
        "/api/v1/payments/mock-confirm",
        headers=buyer_headers,
        json={"session_id": session_id}
    )
    assert confirm_resp2.status_code == 200
    assert confirm_resp2.json()["id"] == order_id
    
    db_session.refresh(db_lot)
    assert db_lot.available_quantity == 0

    # -------------------------------------------------------------
    # 12. Logistics Simulation (Transit Tracking)
    # -------------------------------------------------------------
    # Simulate Porter booking callbacks via the backend background simulation
    # Let's run callback manually to step it forward to porter_booked
    callback_resp = client.post(
        "/api/v1/logistics/callback",
        json={"order_id": order_id, "status": "porter_booked"}
    )
    assert callback_resp.status_code == 200
    assert callback_resp.json()["new_state"] == "porter_booked"

    # Advancing through in-transit to delivered state
    # Calling in-app logistics helper directly to complete delivery
    from app.routers.payments import simulate_in_app_logistics
    import asyncio
    
    # Run simulation helper
    asyncio.run(simulate_in_app_logistics(order_id, delay=0.0))

    # Verify order is in delivered state
    db_order = db_session.query(Order).filter(Order.id == order_id).first()
    assert db_order.tracking_status == "delivered"

    # Verify tracking events got recorded
    events = db_session.query(ShipmentTrackingEvent).filter(ShipmentTrackingEvent.order_id == order_id).all()
    event_types = [e.event_type for e in events]
    assert "porter_booked" in event_types
    assert "in_transit" in event_types
    assert "delivered" in event_types

    # -------------------------------------------------------------
    # 13. Buyer Receipt Confirmation (Order Completion)
    # -------------------------------------------------------------
    receipt_resp = client.post(
        f"/api/v1/logistics/orders/{order_id}/confirm-receipt",
        headers=buyer_headers
    )
    assert receipt_resp.status_code == 200
    assert receipt_resp.json()["new_state"] == "completed"

    # -------------------------------------------------------------
    # 14. Support Ticket Raise
    # -------------------------------------------------------------
    ticket_payload = {
        "issue_text": "One pack has minor scratches on casing, but operational checks pass."
    }
    ticket_resp = client.post(
        f"/api/v1/logistics/orders/{order_id}/raise-issue",
        headers=buyer_headers,
        json=ticket_payload
    )
    assert ticket_resp.status_code == 200
    assert ticket_resp.json()["status"] == "success"

    # Check database persistence
    ticket = db_session.query(SupportTicket).filter(SupportTicket.order_id == order_id).first()
    assert ticket is not None
    assert ticket.issue_text == ticket_payload["issue_text"]
    assert ticket.status == "open"
