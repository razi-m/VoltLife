"""Refactored (Excellence Pass T4): fixtures now come from tests/conftest.py."""
from app.models.orm import Battery, Assessment, Deployment, TelemetrySummary, LifecycleEvent, Site


def test_m1_grade_filtering(client, db_session):
    # Insert a dummy battery and assessment to filter
    b = Battery(
        external_ref="BAT-M1",
        oem="FOA",
        chemistry="NMC",
        rated_capacity_kwh=4.0,
        lat=18.52,
        lng=73.85,
        status="assessed"
    )
    db_session.add(b)
    db_session.flush()

    ass = Assessment(
        battery_id=b.id,
        soh_pct=85.0,
        rul_years=4.5,
        grade="A",
        confidence="high",
        model_version="v1.2",
        explanation_json=[]
    )
    db_session.add(ass)
    db_session.commit()

    # Call endpoint with grade=A
    response = client.get("/api/v1/batteries?grade=A")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["external_ref"] == "BAT-M1"


def test_m2_http_exception_envelope(client):
    # Trigger a 404 which raises HTTPException
    response = client.get("/api/v1/batteries/99999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "detail" not in data
    assert data["error"]["code"] == "battery_not_found"


def test_m3_demo_reset_async(client):
    # Trigger demo reset
    headers = {"X-Demo-Key": "volt_secret_key"}
    response = client.post("/api/v1/demo/reset", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"


def test_m4_json_ingestion(client):
    payload = {
        "batteries": [
            {
                "external_ref": "BAT-JSON-1",
                "oem": "FOA",
                "chemistry": "NMC",
                "rated_capacity_kwh": 4.0,
                "nominal_voltage": 48.0,
                "lat": 18.5208,
                "lng": 73.8567,
                "cycle_count": 100,
                "capacity_now_kwh": 3.7,
                "avg_temp_c": 30.5
            }
        ]
    }
    response = client.post("/api/v1/batteries/ingest", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 0


def test_m5_sites_aggregation(client, db_session):
    # Verify sites endpoint responds correctly
    response = client.get("/api/v1/sites")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    # Remaining capacity matches demand when no deployments exist
    for site in data["items"]:
        assert site["remaining_kwh"] == site["demand_kwh"]


def test_m6_csv_ingestion_blanks(client):
    # CSV file with empty optional cells (e.g. cv_phase_fraction, voltage_slope)
    csv_data = """external_ref,oem,chemistry,rated_capacity_kwh,nominal_voltage,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency
BAT-BLANK,FOA,NMC,4.0,,18.5208,73.8567,100,3.7,30.5,,,,,,,,,,
"""
    response = client.post(
        "/api/v1/batteries/ingest",
        files={"file": ("test_blank.csv", csv_data, "text/csv")}
    )
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 0


def test_m7_replay_demo(client):
    headers = {"X-Demo-Key": "volt_secret_key"}
    response = client.post("/api/v1/demo/replay", headers=headers)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "success"


def test_s1_qr_payload_frontend_url(client, db_session):
    b = Battery(
        external_ref="BAT-QR",
        oem="FOA",
        chemistry="NMC",
        rated_capacity_kwh=4.0,
        lat=18.52,
        lng=73.85,
        status="assessed",
        aadhaar_id="INFOAN480415032400999"
    )
    db_session.add(b)
    db_session.commit()

    response = client.get(f"/api/v1/batteries/{b.id}/aadhaar")
    assert response.status_code == 200
    data = response.json()
    assert "http://localhost:3000/b/INFOAN480415032400999" in data["qr_payload"]


def test_s2_safety_overrides_confidence(db_session):
    from app.services.deployment import decide_deployment
    # Setup battery
    b = Battery(
        external_ref="BAT-S2",
        oem="FOA",
        chemistry="NMC",
        rated_capacity_kwh=4.0,
        lat=18.52,
        lng=73.85,
        status="ingested"
    )
    db_session.add(b)
    db_session.flush()

    # Grade D and low confidence
    ass = Assessment(
        battery_id=b.id,
        soh_pct=50.0,
        rul_years=1.0,
        grade="D",
        confidence="low",
        model_version="v1.2",
        explanation_json=[]
    )
    db_session.add(ass)
    db_session.commit()

    ass.rul_cycles = 100

    payload = decide_deployment(db_session, b, ass)
    # Status should be "recycled" because Grade D (safety) overrides confidence (inspection)
    assert b.status == "recycled"
    assert payload["site_type"] == "recycler"
