import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.marketplace_orm import (
    BuyerAccount, Supplier, InventoryLot, Listing, PricingTier, Quote, Order, PaymentEvent
)

def test_payment_and_locking_flow(client: TestClient, db_session: Session):
    # 1. Register and Login a Buyer
    buyer_payload = {
        "company_name": "Grid Energy Ltd",
        "email": "buyer_pay@grid.com",
        "phone": "+917777777771",
        "address": "Delhi",
        "username": "buyer_pay_user",
        "password": "buyerpassword1"
    }
    client.post("/api/v1/buyers/register", json=buyer_payload)
    login_resp = client.post("/api/v1/buyers/login", json={"username": "buyer_pay_user", "password": "buyerpassword1"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register, verify, and log in a Supplier
    supplier_payload = {
        "company_name": "Apex Volt Suppliers",
        "email": "supp_pay@test.com",
        "phone": "+918888888881",
        "gstin": "27CCCCC1111C1Z2",
        "address": "Mumbai",
        "username": "supplier_pay",
        "password": "password1234"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=supplier_payload)
    supplier_id = reg_resp.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true")

    # 3. Create a lot with total capacity 100.0 kWh and available qty 10 (each pack is 10.0 kWh)
    lot = InventoryLot(
        supplier_id=supplier_id, grade="A", chemistry="LFP",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=88.0, avg_rul_years=4.0, status="listed"
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    # 4. Create listing with MOQ 3
    listing = Listing(
        inventory_lot_id=lot.id, title="LFP Power Packs", 
        description="Great for solar microgrids", moq=3, is_published=True
    )
    tier1 = PricingTier(inventory_lot_id=lot.id, min_quantity=1, price_per_kwh=150.0)
    db_session.add_all([listing, tier1])
    db_session.commit()

    # 5. Create a quote for 4 units (should resolve to $6,000 battery cost)
    quote_resp = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 4}, headers=headers)
    assert quote_resp.status_code == 201
    quote_data = quote_resp.json()
    quote_id = quote_data["id"]

    # Ensure quantity in lot remains 10 (not locked yet)
    db_session.refresh(lot)
    assert lot.available_quantity == 10

    # 6. Create checkout session
    session_resp = client.post("/api/v1/payments/checkout-session", json={"quote_id": quote_id}, headers=headers)
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert "session_id" in session_data
    assert "checkout_url" in session_data
    session_id = session_data["session_id"]

    # 7. Confirm payment via mock endpoint
    confirm_resp = client.post("/api/v1/payments/mock-confirm", json={"session_id": session_id}, headers=headers)
    assert confirm_resp.status_code == 200
    order_data = confirm_resp.json()
    assert order_data["payment_status"] == "paid"
    assert order_data["quantity"] == 4

    # 8. Check that available quantity was locked/decremented to 6
    db_session.refresh(lot)
    assert lot.available_quantity == 6

    # Verify order and payment event in DB
    db_order = db_session.query(Order).filter(Order.id == order_data["id"]).first()
    assert db_order is not None
    assert db_order.payment_status == "paid"
    
    payment_event = db_session.query(PaymentEvent).filter(PaymentEvent.order_id == db_order.id).first()
    assert payment_event is not None
    assert payment_event.status == "success"

    # 9. Test Idempotency: re-submit the same mock confirm request
    confirm_resp2 = client.post("/api/v1/payments/mock-confirm", json={"session_id": session_id}, headers=headers)
    assert confirm_resp2.status_code == 200
    assert confirm_resp2.json()["id"] == order_data["id"]

    # Quantity should still be 6 (no double-decrement)
    db_session.refresh(lot)
    assert lot.available_quantity == 6

    # 10. Test Insufficient Inventory: create a new quote for 7 units (which exceeds available quantity of 6)
    # Note: Quote router checks lot.available_quantity at quote creation, so we must manually force a quote in DB
    # or create a quote while quantity is 10, then perform payment after quantity is reduced.
    # Let's create quote for 5 units while lot.available_quantity is 6 (which is valid):
    quote_resp_extra = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 5}, headers=headers)
    assert quote_resp_extra.status_code == 201
    quote_extra_id = quote_resp_extra.json()["id"]

    # Now simulate another buyer purchasing the remaining 6 units first
    # So lot.available_quantity becomes 0
    lot.available_quantity = 0
    db_session.commit()

    # Now attempt to pay/checkout for our 5 unit quote (which was created when stock was available)
    session_resp_extra = client.post("/api/v1/payments/checkout-session", json={"quote_id": quote_extra_id}, headers=headers)
    # Checkout creation checks availability, so it should fail now:
    assert session_resp_extra.status_code == 400
    assert "does not have enough packs remaining" in session_resp_extra.json()["error"]["message"]

    # Manually check direct mock-confirm processing error handling
    # Create mock session ID for the quote to test mock-confirm route bypass check
    mock_session_extra = f"MOCK_SESSION_{quote_extra_id}_some_random_uuid"
    confirm_resp_fail = client.post("/api/v1/payments/mock-confirm", json={"session_id": mock_session_extra}, headers=headers)
    assert confirm_resp_fail.status_code == 400
    assert "sold out" in confirm_resp_fail.json()["error"]["message"]
