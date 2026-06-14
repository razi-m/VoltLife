import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import Supplier, SupplierUser, SupplierVerification

def test_supplier_registration_and_login(client: TestClient, db_session: Session):
    # 1. Register a supplier
    payload = {
        "company_name": "Test Battery Corp",
        "email": "test@batterycorp.com",
        "phone": "+919999999999",
        "gstin": "27AAAAA1111A1Z1",
        "address": "123 Industrial Area, Pune",
        "username": "testcorp",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/suppliers/register", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "success"
    supplier_id = response.json()["supplier_id"]

    # Verify Supplier is created in DB and is not verified
    supplier = db_session.query(Supplier).filter(Supplier.id == supplier_id).first()
    assert supplier is not None
    assert supplier.is_verified is False

    # 2. Try accessing /me without token
    me_resp = client.get("/api/v1/suppliers/me")
    assert me_resp.status_code == 401

    # 3. Login with correct credentials
    login_payload = {
        "username": "testcorp",
        "password": "securepassword123"
    }
    login_resp = client.post("/api/v1/suppliers/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None

    # 4. Access /me with token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/suppliers/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["company_name"] == "Test Battery Corp"
    assert me_resp.json()["is_verified"] is False

    # 5. Access unverified endpoint (should return 403 or fail verification check)
    # Note: We haven't implemented verified-only endpoints yet, but we will in Phase 3.
    # For now, let's verify supplier status changes to approved
    verify_resp = client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true&notes=Approved by test")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_verified"] is True

    # 6. Re-query profile, should be verified now
    me_resp = client.get("/api/v1/suppliers/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["is_verified"] is True

def test_supplier_login_invalid_credentials(client: TestClient, db_session: Session):
    # Try logging in with non-existent user
    payload = {
        "username": "nonexistent",
        "password": "password"
    }
    response = client.post("/api/v1/suppliers/login", json=payload)
    assert response.status_code == 401
