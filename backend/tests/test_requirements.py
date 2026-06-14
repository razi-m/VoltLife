import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.models.marketplace_orm import (
    BuyerAccount, Supplier, InventoryLot, Listing, Requirement, PricingTier
)
from app.services.gemini import parse_use_case_fallback, parse_use_case

def test_local_fallback_parser():
    # Test cases for the local regex parser
    
    # 1. Full matches
    res1 = parse_use_case_fallback("Need 50 kWh of Grade A batteries, quantity 10 units")
    assert res1["grade"] == "A"
    assert res1["capacity_kwh"] == 50.0
    assert res1["quantity"] == 10
    
    # 2. Grade only
    res2 = parse_use_case_fallback("Looking for grade-S cells")
    assert res2["grade"] == "S"
    assert res2["capacity_kwh"] is None
    assert res2["quantity"] is None
    
    # 3. Capacity & quantity
    res3 = parse_use_case_fallback("Need 120 kw with 5 packs")
    assert res3["grade"] is None
    assert res3["capacity_kwh"] == 120.0
    assert res3["quantity"] == 5

    # 4. Empty/unstructured text
    res4 = parse_use_case_fallback("Just want standard backup batteries")
    assert res4["grade"] is None
    assert res4["capacity_kwh"] is None
    assert res4["quantity"] is None


def test_gemini_api_fallback_on_failure():
    # Test that parse_use_case falls back to local parser when API fails
    with patch("httpx.Client.post") as mock_post:
        mock_post.side_effect = Exception("API Connection Timeout")
        
        # Should still parse successfully using local fallback
        res = parse_use_case("Need 35 kWh Grade B, 2 units")
        assert res["grade"] == "B"
        assert res["capacity_kwh"] == 35.0
        assert res["quantity"] == 2
        assert res["source"] == "local_fallback"


def test_requirement_creation_and_parsing_endpoint(client: TestClient, db_session: Session):
    # 1. Register and Login a Buyer
    buyer_payload = {
        "company_name": "Grid Ops Corp",
        "email": "buyer_req@grid.com",
        "phone": "+917777777777",
        "address": "Mumbai",
        "username": "buyer_req_user",
        "password": "buyerpassword"
    }
    client.post("/api/v1/buyers/register", json=buyer_payload)
    login_resp = client.post("/api/v1/buyers/login", json={"username": "buyer_req_user", "password": "buyerpassword"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit a requirement
    req_payload = {
        "use_case_text": "Solar backup system in Bangalore requiring 80 kWh Grade A batteries, 4 units"
    }
    response = client.post("/api/v1/requirements", json=req_payload, headers=headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["use_case_text"] == req_payload["use_case_text"]
    assert data["parsed_grade"] == "A"
    assert data["parsed_capacity_kwh"] == 80.0
    assert data["parsed_quantity"] == 4
    
    # 3. Verify it is saved in the database
    req_id = data["id"]
    db_req = db_session.query(Requirement).filter(Requirement.id == req_id).first()
    assert db_req is not None
    assert db_req.parsed_grade == "A"
    assert float(db_req.parsed_capacity_kwh) == 80.0
    assert db_req.parsed_quantity == 4


def test_requirement_matching_and_scoring(client: TestClient, db_session: Session):
    # 1. Register and Login a Buyer
    buyer_payload = {
        "company_name": "Grid Ops Corp",
        "email": "buyer_match@grid.com",
        "phone": "+917777777777",
        "address": "Delhi",
        "username": "buyer_match_user",
        "password": "buyerpassword"
    }
    client.post("/api/v1/buyers/register", json=buyer_payload)
    login_resp = client.post("/api/v1/buyers/login", json={"username": "buyer_match_user", "password": "buyerpassword"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Register, verify, and log in a Supplier to create listings
    supplier_payload = {
        "company_name": "Super Cell Ltd",
        "email": "supplier_match@test.com",
        "phone": "+918888888888",
        "gstin": "27BBBBB1111B1Z1",
        "address": "Pune",
        "username": "supplier_match",
        "password": "password123"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=supplier_payload)
    supplier_id = reg_resp.json()["supplier_id"]
    client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true")

    # 3. Create three inventory lots with listings
    # Lot 1: Exact match (Grade A, NMC, capacity 100, qty 10) -> Score should be 100
    lot1 = InventoryLot(
        supplier_id=supplier_id, grade="A", chemistry="NMC",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=85.0, avg_rul_years=3.0, status="listed"
    )
    # Lot 2: Higher grade, slightly higher capacity, higher qty (Grade S, LFP, capacity 120, qty 15) -> High score
    lot2 = InventoryLot(
        supplier_id=supplier_id, grade="S", chemistry="LFP",
        total_capacity_kwh=120.0, available_quantity=15, avg_soh=95.0, avg_rul_years=5.0, status="listed"
    )
    # Lot 3: Lower grade, lower capacity, lower qty (Grade B, NMC, capacity 50, qty 5) -> Lower score
    lot3 = InventoryLot(
        supplier_id=supplier_id, grade="B", chemistry="NMC",
        total_capacity_kwh=50.0, available_quantity=5, avg_soh=78.0, avg_rul_years=2.0, status="listed"
    )
    # Lot 4: Draft/Unpublished (Grade A, NMC, capacity 100, qty 10) -> Should NOT appear
    lot4 = InventoryLot(
        supplier_id=supplier_id, grade="A", chemistry="NMC",
        total_capacity_kwh=100.0, available_quantity=10, avg_soh=85.0, avg_rul_years=3.0, status="draft"
    )
    
    db_session.add_all([lot1, lot2, lot3, lot4])
    db_session.commit()
    db_session.refresh(lot1)
    db_session.refresh(lot2)
    db_session.refresh(lot3)
    db_session.refresh(lot4)

    # Add pricing tiers and listings
    list1 = Listing(inventory_lot_id=lot1.id, title="Premium NMC Batch A", description="Ready to deploy", moq=5, is_published=True)
    list2 = Listing(inventory_lot_id=lot2.id, title="Ultra Grade S Lot", description="High health LFP", moq=10, is_published=True)
    list3 = Listing(inventory_lot_id=lot3.id, title="Standard Lot B", description="Energy storage B", moq=2, is_published=True)
    list4 = Listing(inventory_lot_id=lot4.id, title="Draft Lot", description="Draft", moq=5, is_published=False)
    
    tier1 = PricingTier(inventory_lot_id=lot1.id, min_quantity=1, price_per_kwh=150.0)
    tier2 = PricingTier(inventory_lot_id=lot2.id, min_quantity=1, price_per_kwh=180.0)
    tier3 = PricingTier(inventory_lot_id=lot3.id, min_quantity=1, price_per_kwh=120.0)
    
    db_session.add_all([list1, list2, list3, list4, tier1, tier2, tier3])
    db_session.commit()

    # 4. Create a requirement (Grade A, 100 kWh, 10 units)
    req_payload = {
        "use_case_text": "Need 100 kWh capacity, Grade A batteries, qty 10 units"
    }
    req_resp = client.post("/api/v1/requirements", json=req_payload, headers=headers)
    req_id = req_resp.json()["id"]

    # 5. Retrieve matches
    matches_resp = client.get(f"/api/v1/requirements/{req_id}/matches", headers=headers)
    assert matches_resp.status_code == 200
    
    matches = matches_resp.json()
    # Should only return active/published listings (Lot 1, Lot 2, Lot 3). Lot 4 is draft/unpublished.
    assert len(matches) == 3
    
    # Verify unpublished lot is not present
    listing_ids = [m["listing_id"] for m in matches]
    assert list4.id not in listing_ids
    
    # Verify sorting (descending match score)
    assert matches[0]["match_score"] >= matches[1]["match_score"]
    assert matches[1]["match_score"] >= matches[2]["match_score"]
    
    # Lot 1 (Exact match) should have a perfect/highest score
    assert matches[0]["lot_id"] == lot1.id
    assert matches[0]["match_score"] == 100.0
    
    # Lot 3 (Lower grade, lower capacity, lower qty) should be the lowest score
    assert matches[2]["lot_id"] == lot3.id
    assert matches[2]["match_score"] < 100.0
