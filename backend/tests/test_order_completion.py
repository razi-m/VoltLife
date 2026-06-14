import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import BuyerAccount, Supplier, InventoryLot, Order, SupportTicket, ShipmentTrackingEvent
from app.core.auth import create_access_token

def test_order_completion_and_support_tickets(client: TestClient, db_session: Session):
    # 1. Setup Buyer, Supplier, Lot, and Orders
    buyer = BuyerAccount(
        company_name="Order Completion Buyer Ltd", email="buyer_comp@test.com", phone="+917777777774",
        address="Mumbai", username="buyer_comp", password_hash="hash"
    )
    other_buyer = BuyerAccount(
        company_name="Other Completion Buyer Ltd", email="buyer_other_comp@test.com", phone="+917777777775",
        address="Delhi", username="buyer_other_comp", password_hash="hash"
    )
    supplier = Supplier(
        company_name="Apex Completion Suppliers", email="supp_comp@test.com", phone="+918888888884",
        gstin="27CCCCC1111C1Z5", address="Pune", is_verified=True
    )
    db_session.add_all([buyer, other_buyer, supplier])
    db_session.commit()

    lot = InventoryLot(
        supplier_id=supplier.id, grade="A", chemistry="NMC",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=90.0, avg_rul_years=4.5, status="listed"
    )
    db_session.add(lot)
    db_session.commit()

    # Create Order 1 in 'delivered' state
    order_delivered = Order(
        buyer_id=buyer.id,
        supplier_id=supplier.id,
        inventory_lot_id=lot.id,
        quantity=2,
        total_price=3000.0,
        payment_status="paid",
        tracking_status="delivered"
    )
    # Create Order 2 in 'confirmed' state
    order_confirmed = Order(
        buyer_id=buyer.id,
        supplier_id=supplier.id,
        inventory_lot_id=lot.id,
        quantity=3,
        total_price=4500.0,
        payment_status="paid",
        tracking_status="confirmed"
    )
    db_session.add_all([order_delivered, order_confirmed])
    db_session.commit()

    # Auth tokens
    token = create_access_token(data={"sub": buyer.username, "type": "buyer", "user_id": buyer.id})
    headers = {"Authorization": f"Bearer {token}"}

    other_token = create_access_token(data={"sub": other_buyer.username, "type": "buyer", "user_id": other_buyer.id})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # 2. Test confirm-receipt: fails if not owner
    unauth_resp = client.post(f"/api/v1/logistics/orders/{order_delivered.id}/confirm-receipt", headers=other_headers)
    assert unauth_resp.status_code == 403

    # 3. Test confirm-receipt: fails if order status is not 'delivered' (e.g. 'confirmed')
    bad_state_resp = client.post(f"/api/v1/logistics/orders/{order_confirmed.id}/confirm-receipt", headers=headers)
    assert bad_state_resp.status_code == 400
    assert "Cannot confirm receipt" in bad_state_resp.json()["error"]["message"]

    # 4. Test confirm-receipt: succeeds if owner and state is 'delivered'
    success_resp = client.post(f"/api/v1/logistics/orders/{order_delivered.id}/confirm-receipt", headers=headers)
    assert success_resp.status_code == 200
    assert success_resp.json()["new_state"] == "completed"

    # Verify database state
    db_session.refresh(order_delivered)
    assert order_delivered.tracking_status == "completed"
    
    # Verify tracking event appended
    event = db_session.query(ShipmentTrackingEvent).filter(
        ShipmentTrackingEvent.order_id == order_delivered.id,
        ShipmentTrackingEvent.event_type == "completed"
    ).first()
    assert event is not None
    assert "marked as completed" in event.notes

    # 5. Test raise-issue: fails if not owner
    issue_payload = {"issue_text": "Battery pack is dented."}
    unauth_issue_resp = client.post(f"/api/v1/logistics/orders/{order_delivered.id}/raise-issue", json=issue_payload, headers=other_headers)
    assert unauth_issue_resp.status_code == 403

    # 6. Test raise-issue: succeeds if owner
    success_issue_resp = client.post(f"/api/v1/logistics/orders/{order_delivered.id}/raise-issue", json=issue_payload, headers=headers)
    assert success_issue_resp.status_code == 200
    assert success_issue_resp.json()["status"] == "success"
    assert success_issue_resp.json()["issue_text"] == "Battery pack is dented."

    # Verify support ticket exists in DB
    ticket = db_session.query(SupportTicket).filter(SupportTicket.order_id == order_delivered.id).first()
    assert ticket is not None
    assert ticket.issue_text == "Battery pack is dented."
    assert ticket.status == "open"
