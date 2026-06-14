import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import Supplier, SupplierUser, InventoryLot, Listing, PricingTier
from app.models.orm import Battery, Assessment

def test_listings_unauthorized(client: TestClient):
    # Try getting or configuring listing details without a token
    resp1 = client.post("/api/v1/suppliers/inventory/lots/1/listing", json={"moq": 5, "description": "NMC pack"})
    assert resp1.status_code == 401

    resp2 = client.post("/api/v1/suppliers/inventory/lots/1/pricing", json={"tiers": []})
    assert resp2.status_code == 401

    resp3 = client.post("/api/v1/suppliers/inventory/lots/1/publish")
    assert resp3.status_code == 401

def test_listings_unverified(client: TestClient, db_session: Session):
    # Register unverified supplier
    payload = {
        "company_name": "Unverified Corp",
        "email": "unverified@test.com",
        "phone": "+918888888888",
        "gstin": "27DDDDD1111D1Z1",
        "address": "456 Industrial Area, Pune",
        "username": "unverified_user",
        "password": "password123"
    }
    client.post("/api/v1/suppliers/register", json=payload)
    
    # Login
    login_resp = client.post("/api/v1/suppliers/login", json={"username": "unverified_user", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt listing update on a mock lot ID
    resp = client.post("/api/v1/suppliers/inventory/lots/1/listing", headers=headers, json={"moq": 5, "description": "NMC pack"})
    assert resp.status_code == 403
    assert "pending verification" in resp.json()["error"]["message"]

def test_listings_verified_flow(client: TestClient, db_session: Session):
    # 1. Register & Verify Supplier A
    reg_payload = {
        "company_name": "Supplier A Corp",
        "email": "supplier_a@test.com",
        "phone": "+918888888881",
        "gstin": "27AAAAA1111A1Z1",
        "address": "123 Ind Area, Pune",
        "username": "supplier_a",
        "password": "password123"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=reg_payload)
    supplier_id = reg_resp.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true")

    # 2. Login
    login_resp = client.post("/api/v1/suppliers/login", json={"username": "supplier_a", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Seed a draft InventoryLot belonging to Supplier A
    lot = InventoryLot(
        supplier_id=supplier_id,
        grade="A",
        chemistry="NMC",
        total_capacity_kwh=20.0,
        available_quantity=5,
        avg_soh=85.5,
        avg_rul_years=4.5,
        status="draft"
    )
    db_session.add(lot)
    db_session.commit()
    db_session.refresh(lot)

    # 4. GET listing config (should be empty but return defaults)
    get_resp = client.get(f"/api/v1/suppliers/inventory/lots/{lot.id}/listing", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["listing"] is None
    assert len(get_resp.json()["pricing_tiers"]) == 0

    # 5. Try publishing without details configured
    pub_resp1 = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/publish?publish=true", headers=headers)
    assert pub_resp1.status_code == 400
    assert "configure listing details" in pub_resp1.json()["error"]["message"]

    # 6. Configure Listing details
    listing_payload = {
        "moq": 2,
        "description": "Premium NMC second-life battery packs."
    }
    list_resp = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/listing", headers=headers, json=listing_payload)
    assert list_resp.status_code == 200
    assert list_resp.json()["status"] == "success"
    assert list_resp.json()["listing"]["moq"] == 2
    assert list_resp.json()["listing"]["is_published"] is False

    # 7. Try publishing without pricing configured
    pub_resp2 = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/publish?publish=true", headers=headers)
    assert pub_resp2.status_code == 400
    assert "configure at least one pricing tier" in pub_resp2.json()["error"]["message"]

    # 8. Configure Pricing Tiers (Invalid ones first)
    invalid_pricing_payload = {
        "tiers": [
            {"min_quantity": 0, "price_per_kwh": 150.0},
            {"min_quantity": 1, "price_per_kwh": -10.0}
        ]
    }
    pr_resp_fail = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/pricing", headers=headers, json=invalid_pricing_payload)
    assert pr_resp_fail.status_code == 400

    # Valid pricing tiers
    valid_pricing_payload = {
        "tiers": [
            {"min_quantity": 5, "price_per_kwh": 120.0},
            {"min_quantity": 1, "price_per_kwh": 150.0}  # unsorted to test sorting logic
        ]
    }
    pr_resp = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/pricing", headers=headers, json=valid_pricing_payload)
    assert pr_resp.status_code == 200
    assert len(pr_resp.json()["tiers"]) == 2
    # Ensure they are sorted by min_quantity
    assert pr_resp.json()["tiers"][0]["min_quantity"] == 1
    assert pr_resp.json()["tiers"][0]["price_per_kwh"] == 150.0
    assert pr_resp.json()["tiers"][1]["min_quantity"] == 5
    assert pr_resp.json()["tiers"][1]["price_per_kwh"] == 120.0

    # 9. Query configuration again
    get_resp = client.get(f"/api/v1/suppliers/inventory/lots/{lot.id}/listing", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["listing"]["moq"] == 2
    assert len(get_resp.json()["pricing_tiers"]) == 2

    # 10. Verify lot does NOT show up in public discovery endpoint yet
    public_lots_before = client.get("/api/v1/marketplace/lots")
    # Public lots should either be fallback (length 3) or not contain our lot
    for plot in public_lots_before.json():
        assert plot["id"] != f"lot-{lot.id}"

    # 11. Publish the Listing
    pub_resp_success = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/publish?publish=true", headers=headers)
    assert pub_resp_success.status_code == 200
    assert pub_resp_success.json()["is_published"] is True
    assert pub_resp_success.json()["lot_status"] == "listed"

    # 12. Verify lot shows up in public discovery endpoint now
    public_lots_after = client.get("/api/v1/marketplace/lots")
    found_lot = None
    for plot in public_lots_after.json():
        if plot["id"] == f"lot-{lot.id}":
            found_lot = plot
            break
    assert found_lot is not None
    assert found_lot["title"] == f"GRADE {lot.grade} {lot.chemistry} Lot"
    # price should show the range
    assert "$120-$150/kWh" in found_lot["price"]
    assert found_lot["units"] == "5x UNITS"
    assert "Supplier A Corp" in found_lot["origin"]

    # 13. Unpublish the listing
    unpub_resp = client.post(f"/api/v1/suppliers/inventory/lots/{lot.id}/publish?publish=false", headers=headers)
    assert unpub_resp.status_code == 200
    assert unpub_resp.json()["is_published"] is False
    assert unpub_resp.json()["lot_status"] == "draft"

    # 14. Ensure lot is removed from public discovery endpoint
    public_lots_end = client.get("/api/v1/marketplace/lots")
    for plot in public_lots_end.json():
        assert plot["id"] != f"lot-{lot.id}"

def test_listings_ownership_separation(client: TestClient, db_session: Session):
    # 1. Register & Verify Supplier A
    reg_payload_a = {
        "company_name": "Supplier A Corp",
        "email": "supplier_a_own@test.com",
        "phone": "+918888888810",
        "gstin": "27AAAAA1111A1Z1",
        "address": "123 Ind Area, Pune",
        "username": "supplier_a_own",
        "password": "password123"
    }
    resp_a = client.post("/api/v1/suppliers/register", json=reg_payload_a)
    supplier_a_id = resp_a.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_a_id}/verify?approved=true")

    # 2. Register & Verify Supplier B
    reg_payload_b = {
        "company_name": "Supplier B Corp",
        "email": "supplier_b_own@test.com",
        "phone": "+918888888820",
        "gstin": "27BBBBB1111B1Z1",
        "address": "123 Ind Area, Pune",
        "username": "supplier_b_own",
        "password": "password123"
    }
    resp_b = client.post("/api/v1/suppliers/register", json=reg_payload_b)
    supplier_b_id = resp_b.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_b_id}/verify?approved=true")

    # 3. Log in as Supplier B
    login_resp_b = client.post("/api/v1/suppliers/login", json={"username": "supplier_b_own", "password": "password123"})
    token_b = login_resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. Seed a lot belonging to Supplier A
    lot_a = InventoryLot(
        supplier_id=supplier_a_id,
        grade="A",
        chemistry="NMC",
        total_capacity_kwh=20.0,
        available_quantity=5,
        avg_soh=85.5,
        avg_rul_years=4.5,
        status="draft"
    )
    db_session.add(lot_a)
    db_session.commit()
    db_session.refresh(lot_a)

    # 5. Supplier B attempts to configure Supplier A's lot details (should return 403 Forbidden)
    resp = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot_a.id}/listing",
        headers=headers_b,
        json={"moq": 3, "description": "Supplier B attempting hijack"}
    )
    assert resp.status_code == 403
    assert "do not own" in resp.json()["error"]["message"]

    # 6. Supplier B attempts to configure Supplier A's lot pricing (should return 403 Forbidden)
    resp_pr = client.post(
        f"/api/v1/suppliers/inventory/lots/{lot_a.id}/pricing",
        headers=headers_b,
        json={"tiers": [{"min_quantity": 1, "price_per_kwh": 100.0}]}
    )
    assert resp_pr.status_code == 403

    # 7. Supplier B attempts to publish Supplier A's lot (should return 403 Forbidden)
    resp_pub = client.post(f"/api/v1/suppliers/inventory/lots/{lot_a.id}/publish?publish=true", headers=headers_b)
    assert resp_pub.status_code == 403
