import pytest
import asyncio
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.marketplace_orm import (
    BuyerAccount, Supplier, InventoryLot, Listing, PricingTier, Quote, Order, ShipmentTrackingEvent
)
from app.routers.payments import simulate_in_app_logistics

def test_logistics_callback_flow(client: TestClient, db_session: Session):
    # 1. Setup Buyer, Supplier, Lot, and Order
    buyer = BuyerAccount(
        company_name="Logistics Buyer Ltd", email="buyer_log@test.com", phone="+917777777772",
        address="Bangalore", username="buyer_log", password_hash="hash"
    )
    supplier = Supplier(
        company_name="Apex Logistics Suppliers", email="supp_log@test.com", phone="+918888888882",
        gstin="27CCCCC1111C1Z3", address="Chennai", is_verified=True
    )
    db_session.add_all([buyer, supplier])
    db_session.commit()

    lot = InventoryLot(
        supplier_id=supplier.id, grade="A", chemistry="LFP",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=88.0, avg_rul_years=4.0, status="listed"
    )
    db_session.add(lot)
    db_session.commit()

    # Create a confirmed order
    order = Order(
        buyer_id=buyer.id,
        supplier_id=supplier.id,
        inventory_lot_id=lot.id,
        quantity=5,
        total_price=6500.0,
        payment_status="paid",
        tracking_status="confirmed"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    # 2. Test callback: valid transition to porter_booked
    callback_resp = client.post("/api/v1/logistics/callback", json={
        "order_id": order.id,
        "status": "porter_booked"
    })
    assert callback_resp.status_code == 200
    assert callback_resp.json()["new_state"] == "porter_booked"

    # Verify order state and tracking events
    db_session.refresh(order)
    assert order.tracking_status == "porter_booked"
    events = db_session.query(ShipmentTrackingEvent).filter(ShipmentTrackingEvent.order_id == order.id).all()
    assert len(events) == 1
    assert events[0].event_type == "porter_booked"

    # 3. Test callback idempotency: send same status again
    callback_resp2 = client.post("/api/v1/logistics/callback", json={
        "order_id": order.id,
        "status": "porter_booked"
    })
    assert callback_resp2.status_code == 200
    assert callback_resp2.json()["new_state"] == "porter_booked"
    # No duplicate tracking event should be added
    events2 = db_session.query(ShipmentTrackingEvent).filter(ShipmentTrackingEvent.order_id == order.id).all()
    assert len(events2) == 1

    # 4. Test callback: invalid status
    callback_invalid = client.post("/api/v1/logistics/callback", json={
        "order_id": order.id,
        "status": "invalid_status_xyz"
    })
    assert callback_invalid.status_code == 400
    assert "Invalid status" in callback_invalid.json()["error"]["message"]

    # 5. Test callback: backward transition (porter_booked -> confirmed)
    callback_backward = client.post("/api/v1/logistics/callback", json={
        "order_id": order.id,
        "status": "confirmed"
    })
    assert callback_backward.status_code == 400
    assert "Cannot transition backward" in callback_backward.json()["error"]["message"]


@pytest.mark.anyio
async def test_logistics_simulation_flow(db_session: Session):
    # Setup Buyer, Supplier, Lot, and Order
    buyer = BuyerAccount(
        company_name="Logistics Sim Buyer Ltd", email="buyer_log_sim@test.com", phone="+917777777773",
        address="Bangalore", username="buyer_log_sim", password_hash="hash"
    )
    supplier = Supplier(
        company_name="Apex Logistics Sim Suppliers", email="supp_log_sim@test.com", phone="+918888888883",
        gstin="27CCCCC1111C1Z4", address="Chennai", is_verified=True
    )
    db_session.add_all([buyer, supplier])
    db_session.commit()

    lot = InventoryLot(
        supplier_id=supplier.id, grade="A", chemistry="LFP",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=88.0, avg_rul_years=4.0, status="listed"
    )
    db_session.add(lot)
    db_session.commit()

    # Create a confirmed order
    order = Order(
        buyer_id=buyer.id,
        supplier_id=supplier.id,
        inventory_lot_id=lot.id,
        quantity=5,
        total_price=6500.0,
        payment_status="paid",
        tracking_status="confirmed"
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    # Run the in-app simulation helper directly with 0.0 delay
    await simulate_in_app_logistics(order.id, delay=0.0)

    # Fetch updated order and verify status is 'delivered'
    db_session.refresh(order)
    assert order.tracking_status == "delivered"

    # Check tracking events (6 events: porter_booked, seller_notified, buyer_notified, shipment_started, in_transit, delivered)
    events = db_session.query(ShipmentTrackingEvent).filter(ShipmentTrackingEvent.order_id == order.id).order_by(ShipmentTrackingEvent.id).all()
    assert len(events) == 6
    assert events[0].event_type == "porter_booked"
    assert events[5].event_type == "delivered"
