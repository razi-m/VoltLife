"""Refactored (Excellence Pass T4): fixtures now come from tests/conftest.py."""
from app.models.orm import Battery, Assessment, Deployment, TelemetrySummary, LifecycleEvent, Site


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["ok"] is True
    assert json_data["db"] == "up"
    assert "model_version" in json_data


def test_ingest_and_pipeline_smoke(client, db_session):
    # CSV file content representing 5 batteries (with optional columns present)
    csv_data = """external_ref,oem,model,chemistry,rated_capacity_kwh,nominal_voltage,manufacture_date,source_city,source_state,lat,lng,cycle_count,capacity_now_kwh,avg_temp_c,max_temp_c,thermal_stress_hours,internal_resistance_mohm,ir_growth_pct,coulombic_efficiency,fade_rate,fade_acceleration,cv_phase_fraction,voltage_slope,voltage_variance,discharge_efficiency
BAT-T1,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,100,3.7,30.5,38.0,5.0,15.0,8.0,0.999,0.01,0.001,0.10,0.05,0.002,0.98
BAT-T2,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,400,3.3,31.2,42.5,12.0,18.2,15.4,0.998,0.03,0.005,0.15,0.06,0.004,0.96
BAT-T3,FOB,Pack-2,LFP,5.0,60.0,2023-08-10,Bengaluru,Karnataka,12.9716,77.5946,800,3.8,33.1,48.2,25.0,24.5,28.0,0.995,0.06,0.008,0.18,0.09,0.006,0.95
BAT-T4,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,1400,2.8,34.0,48.0,35.0,32.0,48.0,0.992,0.09,0.014,0.24,0.10,0.007,0.93
BAT-T5,FOA,Pack-1,NMC,4.0,48.0,2024-03-15,Pune,Maharashtra,18.5208,73.8567,900,2.6,38.5,58.2,65.0,35.0,55.0,0.988,0.12,0.018,0.26,0.15,0.012,0.91
"""
    # 1. Post Ingestion request
    response = client.post(
        "/api/v1/batteries/ingest",
        files={"file": ("test_fleet.csv", csv_data, "text/csv")}
    )
    
    assert response.status_code == 202
    json_data = response.json()
    assert "job_id" in json_data
    assert json_data["accepted"] == 5
    assert json_data["rejected"] == 0
    
    job_id = json_data["job_id"]

    # In FastAPI TestClient, background tasks run synchronously when the request ends.
    # Therefore, the pipeline execution task has already run completely by this point.
    
    # 2. Query Job status
    job_response = client.get(f"/api/v1/jobs/{job_id}")
    assert job_response.status_code == 200
    job_data = job_response.json()
    assert job_data["status"] in ("done", "failed")
    assert job_data["processed"] == 5

    # 3. Verify Database records are written correctly
    batteries = db_session.query(Battery).all()
    assert len(batteries) == 5
    
    # Ensure they got Aadhaar IDs generated
    for b in batteries:
        assert b.aadhaar_id is not None
        assert len(b.aadhaar_id) == 21
        assert b.status in ("assigned", "recycled", "error")

    # 4. Check that telemetry, assessments, deployments and events exist
    telemetries = db_session.query(TelemetrySummary).all()
    assert len(telemetries) == 5
    
    assessments = db_session.query(Assessment).all()
    assert len(assessments) == 5
    
    # Telemetry should parse Coulombic Efficiency
    for t in telemetries:
        assert t.coulombic_efficiency is not None
        assert t.features_json is not None
        assert "discharge_efficiency" in t.features_json

    # Deployment checks
    deployments = db_session.query(Deployment).all()
    # At least some should be deployed (Grade S, A, B, C). Grade D (BAT-T5 has max_temp 58.2 > 55 override) will route to recycler
    assert len(deployments) > 0
    
    # Find the recycled one (BAT-T5)
    bat5 = db_session.query(Battery).filter(Battery.external_ref == "BAT-T5").first()
    assert bat5.status == "recycled"
    
    # Verify public Aadhaar route matches
    aadhaar_response = client.get(f"/api/v1/aadhaar/{bat5.aadhaar_id}")
    assert aadhaar_response.status_code == 200
    passport = aadhaar_response.json()
    assert passport["aadhaar_id"] == bat5.aadhaar_id
    assert passport["dynamic"]["status"] == "recycled"
    assert "recycled" in passport["life_story"]

    # 5. Verify impact summary
    impact_response = client.get("/api/v1/impact/summary")
    assert impact_response.status_code == 200
    impact = impact_response.json()
    assert impact["processed"] == 5
    assert impact["recycled_responsibly"] == 1
    assert "by_grade" in impact
    assert "by_site_type" in impact
