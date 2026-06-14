import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.marketplace_orm import (
    BuyerAccount, Supplier, InventoryLot, Listing, PricingTier, Quote
)

def test_quote_creation_flow(client: TestClient, db_session: Session):
    # 1. Register and Login a Buyer
    buyer_payload = {
        "company_name": "Power Grid Inc",
        "email": "buyer_quote@grid.com",
        "phone": "+917777777777",
        "address": "Mumbai",
        "username": "buyer_quote_user",
        "password": "buyerpassword"
    }
    client.post("/api/v1/buyers/register", json=buyer_payload)
    login_resp = client.post("/api/v1/buyers/login", json={"username": "buyer_quote_user", "password": "buyerpassword"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register, verify, and log in a Supplier
    supplier_payload = {
        "company_name": "Eco Volt Suppliers",
        "email": "supp_quote@test.com",
        "phone": "+918888888888",
        "gstin": "27CCCCC1111C1Z1",
        "address": "Pune",
        "username": "supplier_quote",
        "password": "password123"
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
    # Add quantity pricing tiers:
    # 1+ units: $150/kWh
    # 5+ units: $130/kWh
    tier1 = PricingTier(inventory_lot_id=lot.id, min_quantity=1, price_per_kwh=150.0)
    tier2 = PricingTier(inventory_lot_id=lot.id, min_quantity=5, price_per_kwh=130.0)
    
    db_session.add_all([listing, tier1, tier2])
    db_session.commit()

    # 5. Try creating a quote below MOQ (quantity = 2)
    response = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 2}, headers=headers)
    assert response.status_code == 400
    assert "Minimum Order Quantity" in response.json()["error"]["message"]

    # 6. Try creating a quote above available quantity (quantity = 12)
    response = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 12}, headers=headers)
    assert response.status_code == 400
    assert "exceeds available quantity" in response.json()["error"]["message"]

    # 7. Create a quote for 4 units (should resolve to tier 1: $150/kWh)
    # 4 packs * 10.0 kWh/pack * $150 = $6,000 battery cost
    response = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 4}, headers=headers)
    assert response.status_code == 201
    
    quote_data = response.json()
    assert quote_data["quantity"] == 4
    assert quote_data["battery_cost"] == 6000.0
    assert quote_data["transport_cost"] > 0
    assert quote_data["total_cost"] == quote_data["battery_cost"] + quote_data["transport_cost"]
    assert quote_data["delivery_days"] in [1, 2, 3, 4]
    assert "Piaggio Ape" in quote_data["porter_vehicle_type"] or "Tata Ace" in quote_data["porter_vehicle_type"]
    assert quote_data["status"] == "pending"

    # 8. Create a quote for 8 units (should resolve to tier 2: $130/kWh)
    # 8 packs * 10.0 kWh/pack * $130 = $10,400 battery cost
    response2 = client.post("/api/v1/quotes", json={"inventory_lot_id": lot.id, "quantity": 8}, headers=headers)
    assert response2.status_code == 201
    
    quote_data2 = response2.json()
    assert quote_data2["battery_cost"] == 10400.0
    # 80 kWh * 8 kg/kWh = 640 kg -> Tata Ace should be recommended
    assert "Tata Ace" in quote_data2["porter_vehicle_type"]

    # 9. Verify quote persistence in DB and retrieval endpoint
    quote_id = quote_data2["id"]
    get_resp = client.get(f"/api/v1/quotes/{quote_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["total_cost"] == quote_data2["total_cost"]

    # 10. Guard check: Available inventory quantity should not change/lock
    db_session.refresh(lot)
    assert lot.available_quantity == 10
