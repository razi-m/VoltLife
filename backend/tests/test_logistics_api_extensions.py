import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.marketplace_orm import (
    BuyerAccount, Supplier, InventoryLot, Quote, Order, ShipmentTrackingEvent
)
from app.core.auth import create_access_token

def test_list_quotes_and_orders_and_tracking(client: TestClient, db_session: Session):
    # 1. Setup Buyer, Supplier, Lot, Quote, Order, and Tracking Event
    buyer = BuyerAccount(
        company_name="API Extensions Buyer Ltd", email="buyer_ext@test.com", phone="+917777777779",
        address="Mumbai", username="buyer_ext", password_hash="hash"
    )
    supplier = Supplier(
        company_name="Apex Extensions Suppliers", email="supp_ext@test.com", phone="+918888888889",
        gstin="27CCCCC1111C1Z9", address="Delhi", is_verified=True
    )
    db_session.add_all([buyer, supplier])
    db_session.commit()

    lot = InventoryLot(
        supplier_id=supplier.id, grade="B", chemistry="NMC",
        total_capacity_kwh=80.0, available_quantity=8, avg_soh=82.0, avg_rul_years=3.0, status="listed"
    )
    db_session.add(lot)
    db_session.commit()

    # Create a Quote
    quote = Quote(
        buyer_id=buyer.id,
        inventory_lot_id=lot.id,
        quantity=4,
        battery_cost=4000.0,
        transport_cost=200.0,
        total_cost=4200.0,
        delivery_days=3,
        porter_vehicle_type="Tata Ace (Chota Hathi)",
        status="accepted"
    )
    db_session.add(quote)
    db_session.commit()

    # Create an Order
    order = Order(
        buyer_id=buyer.id,
        supplier_id=supplier.id,
        inventory_lot_id=lot.id,
        quantity=4,
        total_price=4200.0,
        payment_status="paid",
        tracking_status="porter_booked"
    )
    db_session.add(order)
    db_session.commit()

    # Create a Tracking Event
    event = ShipmentTrackingEvent(
        order_id=order.id,
        event_type="porter_booked",
        notes="Order status advanced to porter_booked"
    )
    db_session.add(event)
    db_session.commit()

    # Auth Token
    token = create_access_token(data={"sub": buyer.username, "type": "buyer", "user_id": buyer.id})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test GET /api/v1/quotes
    quotes_resp = client.get("/api/v1/quotes", headers=headers)
    assert quotes_resp.status_code == 200
    quotes_data = quotes_resp.json()
    assert len(quotes_data) == 1
    assert quotes_data[0]["id"] == quote.id
    assert quotes_data[0]["status"] == "accepted"

    # 3. Test GET /api/v1/payments/orders
    orders_resp = client.get("/api/v1/payments/orders", headers=headers)
    assert orders_resp.status_code == 200
    orders_data = orders_resp.json()
    assert len(orders_data) == 1
    assert orders_data[0]["id"] == order.id
    assert orders_data[0]["tracking_status"] == "porter_booked"

    # 4. Test GET /api/v1/logistics/orders/{order_id}/tracking
    tracking_resp = client.get(f"/api/v1/logistics/orders/{order.id}/tracking", headers=headers)
    assert tracking_resp.status_code == 200
    tracking_data = tracking_resp.json()
    assert tracking_data["order_id"] == order.id
    assert tracking_data["tracking_status"] == "porter_booked"
    assert tracking_data["porter_vehicle_type"] == "Tata Ace (Chota Hathi)"
    assert tracking_data["delivery_days"] == 3
    assert len(tracking_data["events"]) == 1
    assert tracking_data["events"][0]["event_type"] == "porter_booked"

    # 5. Test unauthorized tracking fetch
    other_buyer = BuyerAccount(
        company_name="Other Buyer Ltd", email="other@test.com", phone="+917777777771",
        address="Delhi", username="buyer_other", password_hash="hash"
    )
    db_session.add(other_buyer)
    db_session.commit()
    other_token = create_access_token(data={"sub": other_buyer.username, "type": "buyer", "user_id": other_buyer.id})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    tracking_unauth = client.get(f"/api/v1/logistics/orders/{order.id}/tracking", headers=other_headers)
    assert tracking_unauth.status_code == 403
