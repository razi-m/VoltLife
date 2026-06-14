import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import SaaS_Subscription

def test_subscriptions_flow_and_gating(client: TestClient, db_session: Session, monkeypatch):
    # Mock environment keys to force mock mode in tests
    monkeypatch.setenv("STRIPE_SECRET_KEY", "")

    # 1. Reset demo to seed initial data
    headers = {"X-Demo-Key": "volt_secret_key"}
    reset_resp = client.post("/api/v1/demo/reset", headers=headers)
    assert reset_resp.status_code == 200


    # 2. Login as supplier
    login_payload = {
        "username": "demo_supplier",
        "password": "password123"
    }
    login_resp = client.post("/api/v1/suppliers/login", json=login_payload)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    supplier_headers = {"Authorization": f"Bearer {token}"}

    # 3. Check status (should be active from seeding)
    status_resp = client.get("/api/v1/subscriptions/status", headers=supplier_headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "active"
    assert status_data["plan_name"] == "Annual"

    # 4. Access dashboard (should succeed)
    stats_resp = client.get("/api/v1/suppliers/dashboard/stats", headers=supplier_headers)
    assert stats_resp.status_code == 200

    # 5. Cancel subscription to simulate expiration
    cancel_resp = client.post("/api/v1/subscriptions/cancel", headers=supplier_headers)
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["subscription"]["status"] == "expired"

    # 6. Check status (should show expired)
    status_resp = client.get("/api/v1/subscriptions/status", headers=supplier_headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "expired"

    # 7. Access dashboard (should now fail with 403)
    stats_resp = client.get("/api/v1/suppliers/dashboard/stats", headers=supplier_headers)
    assert stats_resp.status_code == 403
    assert stats_resp.json()["error"]["code"] == "subscription_required"

    # 8. Get plans
    plans_resp = client.get("/api/v1/subscriptions/plans", headers=supplier_headers)
    assert plans_resp.status_code == 200
    plans = plans_resp.json()
    assert len(plans) == 3
    plan_names = [p["name"] for p in plans]
    assert "Monthly" in plan_names
    assert "Annual" in plan_names
    assert "Enterprise" in plan_names

    # 9. Create subscription session
    session_payload = {"plan_name": "Monthly"}
    session_resp = client.post("/api/v1/subscriptions/create-session", json=session_payload, headers=supplier_headers)
    assert session_resp.status_code == 200
    session_data = session_resp.json()
    assert "session_id" in session_data
    assert session_data["is_mock"] is True  # In tests, default is mock

    # 10. Verify subscription
    verify_payload = {
        "plan_name": "Monthly",
        "session_id": session_data["session_id"]
    }
    verify_resp = client.post("/api/v1/subscriptions/verify", json=verify_payload, headers=supplier_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["subscription"]["status"] == "active"
    assert verify_resp.json()["subscription"]["plan_name"] == "Monthly"

    # 11. Access dashboard (should be unlocked again!)
    stats_resp2 = client.get("/api/v1/suppliers/dashboard/stats", headers=supplier_headers)
    assert stats_resp2.status_code == 200
