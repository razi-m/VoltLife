import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import Supplier, SupplierUser, BuyerAccount, InventoryLot, Order

def test_supplier_dashboard_demo_seeding_and_endpoints(client: TestClient, db_session: Session):
    # 1. Reset the demo to ensure database is seeded with demo users
    # We pass the demo key header if needed, but in test/local config it might not be verified or is set to empty.
    # Let's inspect demo verification. In test it uses settings.DEMO_KEY, which is default.
    headers = {"X-Demo-Key": "volt_secret_key"}
    reset_resp = client.post("/api/v1/demo/reset", headers=headers)
    assert reset_resp.status_code == 200

    # 2. Verify seeded Buyer Account exists
    buyer_db = db_session.query(BuyerAccount).filter(BuyerAccount.username == "demo_buyer").first()
    assert buyer_db is not None
    assert buyer_db.company_name == "Demo Buyer Inc"

    # 3. Verify seeded Supplier & User exists and is verified
    supplier_user_db = db_session.query(SupplierUser).filter(SupplierUser.username == "demo_supplier").first()
    assert supplier_user_db is not None
    supplier_db = db_session.query(Supplier).filter(Supplier.id == supplier_user_db.supplier_id).first()
    assert supplier_db is not None
    assert supplier_db.is_verified is True

    # 4. Login as demo_buyer
    buyer_login_payload = {
        "username": "demo_buyer",
        "password": "password123"
    }
    buyer_login_resp = client.post("/api/v1/buyers/login", json=buyer_login_payload)
    assert buyer_login_resp.status_code == 200
    buyer_token = buyer_login_resp.json()["access_token"]
    assert buyer_token is not None

    # 5. Login as demo_supplier
    supplier_login_payload = {
        "username": "demo_supplier",
        "password": "password123"
    }
    supplier_login_resp = client.post("/api/v1/suppliers/login", json=supplier_login_payload)
    assert supplier_login_resp.status_code == 200
    supplier_token = supplier_login_resp.json()["access_token"]
    assert supplier_token is not None

    # 6. Access stats as supplier (should succeed)
    supplier_headers = {"Authorization": f"Bearer {supplier_token}"}
    stats_resp = client.get("/api/v1/suppliers/dashboard/stats", headers=supplier_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert "active_lots_count" in stats
    assert "completed_orders_count" in stats
    assert "pending_orders_count" in stats
    assert "total_revenue_rupees" in stats

    # 7. Access inventory as supplier (should succeed)
    inv_resp = client.get("/api/v1/suppliers/dashboard/inventory", headers=supplier_headers)
    assert inv_resp.status_code == 200
    assert isinstance(inv_resp.json(), list)

    # 8. Access orders as supplier (should succeed)
    orders_resp = client.get("/api/v1/suppliers/dashboard/orders", headers=supplier_headers)
    assert orders_resp.status_code == 200
    assert isinstance(orders_resp.json(), list)

    # 9. Access requirements as supplier (should succeed)
    reqs_resp = client.get("/api/v1/suppliers/dashboard/requirements", headers=supplier_headers)
    assert reqs_resp.status_code == 200
    assert isinstance(reqs_resp.json(), list)

    # 10. Attempt to access supplier dashboard endpoints as a buyer (should fail with 401 or 403)
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    bad_stats_resp = client.get("/api/v1/suppliers/dashboard/stats", headers=buyer_headers)
    assert bad_stats_resp.status_code in [401, 403]

    bad_inv_resp = client.get("/api/v1/suppliers/dashboard/inventory", headers=buyer_headers)
    assert bad_inv_resp.status_code in [401, 403]

    # 11. Attempt to access supplier dashboard endpoints anonymously (should fail with 401)
    anon_stats_resp = client.get("/api/v1/suppliers/dashboard/stats")
    assert anon_stats_resp.status_code == 401
