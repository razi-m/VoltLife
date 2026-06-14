import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import BuyerAccount, Supplier, InventoryLot

def test_buyer_registration_and_login(client: TestClient, db_session: Session):
    # 1. Register a new buyer
    payload = {
        "company_name": "Grid operator Inc",
        "email": "buyer1@grid.com",
        "phone": "+917777777777",
        "address": "789 Power Grid St, Pune",
        "username": "grid_operator",
        "password": "buyerpassword123"
    }
    response = client.post("/api/v1/buyers/register", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    buyer_id = response.json()["buyer_id"]

    # Verify Buyer is created in DB
    buyer = db_session.query(BuyerAccount).filter(BuyerAccount.id == buyer_id).first()
    assert buyer is not None
    assert buyer.username == "grid_operator"

    # 2. Try accessing /me without token
    me_resp = client.get("/api/v1/buyers/me")
    assert me_resp.status_code == 401

    # 3. Login with correct credentials
    login_payload = {
        "username": "grid_operator",
        "password": "buyerpassword123"
    }
    login_resp = client.post("/api/v1/buyers/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None

    # 4. Access /me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/buyers/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["company_name"] == "Grid operator Inc"
    assert me_resp.json()["username"] == "grid_operator"

def test_buyer_duplicate_registration(client: TestClient, db_session: Session):
    payload = {
        "company_name": "Grid operator Inc",
        "email": "buyer2@grid.com",
        "phone": "+917777777777",
        "address": "789 Power Grid St, Pune",
        "username": "grid_operator2",
        "password": "buyerpassword123"
    }
    # First registration
    client.post("/api/v1/buyers/register", json=payload)
    
    # Try registering again with same username/email
    response = client.post("/api/v1/buyers/register", json=payload)
    assert response.status_code == 400
    assert "taken" in response.json()["error"]["code"]

def test_buyer_login_invalid_credentials(client: TestClient):
    payload = {
        "username": "non_existent_buyer",
        "password": "password"
    }
    response = client.post("/api/v1/buyers/login", json=payload)
    assert response.status_code == 401

def test_buyer_token_cannot_access_supplier_routes(client: TestClient, db_session: Session):
    # 1. Register and Login a Buyer
    payload = {
        "company_name": "Grid operator Inc",
        "email": "buyer3@grid.com",
        "phone": "+917777777777",
        "address": "789 Power Grid St, Pune",
        "username": "grid_operator3",
        "password": "buyerpassword123"
    }
    client.post("/api/v1/buyers/register", json=payload)
    login_resp = client.post("/api/v1/buyers/login", json={"username": "grid_operator3", "password": "buyerpassword123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register, verify, and log in a Supplier to get a valid lot ID
    supplier_payload = {
        "company_name": "Supp A",
        "email": "supp_a_test@test.com",
        "phone": "+919999999999",
        "gstin": "27AAAAA1111A1Z1",
        "address": "Pune",
        "username": "supp_a",
        "password": "password123"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=supplier_payload)
    supplier_id = reg_resp.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true")

    # Seed a lot
    lot = InventoryLot(
        supplier_id=supplier_id,
        grade="A",
        chemistry="NMC",
        total_capacity_kwh=10.0,
        available_quantity=2,
        avg_soh=80.0,
        avg_rul_years=3.0,
        status="draft"
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    # 3. Buyer attempts to access Supplier configuration endpoint (should fail with 401 Unauthorized or 403 Forbidden)
    response = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot.id}/listing",
        headers=headers,
        json={"moq": 1, "description": "Attempted edit by buyer"}
    )
    # Token validation should fail since it's a buyer token in supplier dependency
    assert response.status_code == 401
    assert "Could not validate" in response.json()["error"]["message"]
