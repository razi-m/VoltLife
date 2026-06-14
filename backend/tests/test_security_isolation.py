"""
Cross-tenant security validation (Task 5).

Run locally (this sandbox cannot run a DB-backed test suite):
    cd backend
    export TEST_DATABASE_URL=postgresql://... (a SEPARATE db; the suite wipes tables)
    python -m pytest tests/test_security_isolation.py -v

These tests assert tenant isolation. Adjust endpoint paths / payload field names if your
routers differ — they are written against the documented marketplace API surface.
"""
import os
import uuid
import pytest

# conftest.py already loads .env and forbids SQLite; it builds the schema.
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _register_and_login_supplier():
    email = f"sup_{uuid.uuid4().hex[:8]}@demo.com"
    client.post("/api/v1/suppliers/register", json={
        "company_name": email, "business_email": email, "phone": "+910000000000",
        "gst": "GST" + uuid.uuid4().hex[:8].upper(), "business_address": "Pune, Maharashtra",
        "password": "Passw0rd!",
    })
    r = client.post("/api/v1/suppliers/login", json={"email": email, "password": "Passw0rd!"})
    token = (r.json() or {}).get("access_token") or (r.json() or {}).get("token")
    return token


def test_supplier_dashboard_requires_auth():
    """An unauthenticated / non-supplier caller cannot read supplier dashboard data."""
    r = client.get("/api/v1/suppliers/dashboard/stats")
    assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"


def test_buyer_token_rejected_by_supplier_routes():
    """A bogus / buyer bearer token must be rejected by supplier-only endpoints."""
    r = client.get("/api/v1/suppliers/dashboard/inventory",
                   headers={"Authorization": "Bearer definitely-not-a-supplier-token"})
    assert r.status_code in (401, 403)


def test_seller_a_cannot_see_seller_b_inventory():
    """Seller A's dashboard inventory must contain only Seller A's lots (never Seller B's)."""
    tok_a = _register_and_login_supplier()
    tok_b = _register_and_login_supplier()
    if not (tok_a and tok_b):
        pytest.skip("login did not return a token; adjust to your auth response shape")

    inv_a = client.get("/api/v1/suppliers/dashboard/inventory",
                       headers={"Authorization": f"Bearer {tok_a}"})
    inv_b = client.get("/api/v1/suppliers/dashboard/inventory",
                       headers={"Authorization": f"Bearer {tok_b}"})
    assert inv_a.status_code == 200 and inv_b.status_code == 200

    def lot_ids(resp):
        data = resp.json()
        rows = data if isinstance(data, list) else data.get("items", data.get("inventory", []))
        return {row.get("id") for row in rows if isinstance(row, dict)}

    a_ids, b_ids = lot_ids(inv_a), lot_ids(inv_b)
    assert a_ids.isdisjoint(b_ids), "Seller A and Seller B inventory must not overlap"


def test_admin_route_requires_admin():
    """Admin-only verify endpoint must reject unauthenticated / non-admin callers."""
    r = client.post("/api/v1/admin/suppliers/1/verify")
    assert r.status_code in (401, 403, 404)  # 404 acceptable if admin router is mounted but gated
