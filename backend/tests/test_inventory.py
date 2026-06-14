import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.models.marketplace_orm import Supplier, SupplierUser, InventoryLot
from app.models.orm import Battery, Assessment

def test_supplier_upload_unauthorized(client: TestClient):
    # Try uploading without token
    response = client.post("/api/v1/suppliers/inventory/upload")
    assert response.status_code == 401

def test_supplier_upload_unverified(client: TestClient, db_session: Session):
    # 1. Register a supplier
    payload = {
        "company_name": "Unverified Battery Corp",
        "email": "unverified@battery.com",
        "phone": "+919999999991",
        "gstin": "27BBBBB1111B1Z1",
        "address": "123 Industrial Area, Pune",
        "username": "unverified_corp",
        "password": "password123"
    }
    client.post("/api/v1/suppliers/register", json=payload)
    
    # 2. Login
    login_resp = client.post("/api/v1/suppliers/login", json={"username": "unverified_corp", "password": "password123"})
    token = login_resp.json()["access_token"]
    
    # 3. Attempt to upload
    headers = {"Authorization": f"Bearer {token}"}
    csv_data = "external_ref,oem,model,chemistry,rated_capacity_kwh,nominal_voltage,manufacture_date,source_city,source_state,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency\nBAT-1,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,100,3.7,30.5,38.0,5.0,15.0,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98\n"
    response = client.post(
        "/api/v1/suppliers/inventory/upload",
        headers=headers,
        files={"file": ("test_fleet.csv", csv_data, "text/csv")}
    )
    assert response.status_code == 403
    assert "pending verification" in response.json()["error"]["message"]

def test_supplier_upload_verified_success(client: TestClient, db_session: Session):
    # 1. Register
    reg_payload = {
        "company_name": "Verified Battery Corp",
        "email": "verified@battery.com",
        "phone": "+919999999992",
        "gstin": "27CCCCC1111C1Z1",
        "address": "123 Industrial Area, Pune",
        "username": "verified_corp",
        "password": "password123"
    }
    reg_resp = client.post("/api/v1/suppliers/register", json=reg_payload)
    supplier_id = reg_resp.json()["supplier_id"]

    # 2. Admin Verification
    verify_resp = client.post(f"/api/v1/suppliers/{supplier_id}/verify?approved=true&notes=Approved for tests")
    assert verify_resp.status_code == 200

    # 3. Login
    login_resp = client.post("/api/v1/suppliers/login", json={"username": "verified_corp", "password": "password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Upload CSV (5 batteries)
    # BAT-T5 is Grade D / recycled (max_temp_c = 58.2 > 55 override)
    csv_data = """external_ref,oem,model,chemistry,rated_capacity_kwh,nominal_voltage,manufacture_date,source_city,source_state,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency
BAT-T1,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,100,3.7,30.5,38.0,5.0,15.0,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98
BAT-T2,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,150,3.6,30.5,38.0,5.0,15.0,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98
BAT-T3,FOB,Pack-2,LFP,5.0,60.0,2023-08-10,Bengaluru,Karnataka,12.9716,77.5946,800,3.8,33.1,48.2,25.0,24.5,28.0,0.995,0.06,0.008,0.18,0.09,0.006,0.95
BAT-T4,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,1400,2.8,34.0,48.0,35.0,32.0,48.0,0.992,0.09,0.014,0.24,0.10,0.007,0.93
BAT-T5,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,900,2.6,38.5,58.2,65.0,35.0,55.0,0.988,0.12,0.018,0.26,0.15,0.012,0.91
"""
    response = client.post(
        "/api/v1/suppliers/inventory/upload",
        headers=headers,
        files={"file": ("supplier_fleet.csv", csv_data, "text/csv")}
    )
    assert response.status_code == 202
    assert response.json()["accepted"] == 5

    # 5. Verify the DB structures
    # Assess that 5 batteries are uploaded with correct supplier_id
    batteries = db_session.query(Battery).filter(Battery.supplier_id == supplier_id).all()
    assert len(batteries) == 5
    for b in batteries:
        assert b.supplier_id == supplier_id
        # Assessments should be present (FastAPI test client processes background task synchronously)
        assert b.aadhaar_id is not None
        assert b.status in ("assigned", "recycled", "error")

    # 6. Verify Auto-Inventory Lot Generation
    # Graded S/A/B/C batteries should group into lots. Let's inspect the created draft lots.
    lots = db_session.query(InventoryLot).filter(
        InventoryLot.supplier_id == supplier_id,
        InventoryLot.status == "draft"
    ).all()
    
    # Let's check: BAT-T1, BAT-T2, BAT-T4 are NMC. BAT-T3 is LFP.
    # BAT-T5 is Grade D / recycled (so excluded from inventory lots).
    # This means at least one lot should be created.
    assert len(lots) > 0
    
    # Check that none of the lots include Grade D
    for lot in lots:
        assert lot.grade != "D"
        assert lot.available_quantity > 0
        assert len(lot.batteries) == lot.available_quantity
        # Check that chemistry matches the batteries in the lot
        for bat in lot.batteries:
            assert bat.chemistry == lot.chemistry
            
            # Check assessment grade matches lot grade
            ass = db_session.query(Assessment).filter(Assessment.battery_id == bat.id).order_by(Assessment.created_at.desc()).first()
            assert ass.grade == lot.grade
            
    # Verify the many-to-many relationship loaded correctly
    total_associated_batteries = sum(len(lot.batteries) for lot in lots)
    # Total successfully graded non-Grade D batteries should equal the associated count (should be 4, as BAT-T5 is Grade D)
    assert total_associated_batteries == 4
