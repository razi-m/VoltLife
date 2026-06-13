import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="VoltLife Mock Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock databases
MOCK_AADHAAR = {
    "aadhaar_id": "INFOAN480415032400231",
    "decoded": {
        "country": "IN",
        "manufacturer": "FOA",
        "chemistry": "NMC",
        "voltage": "48V",
        "capacity_kwh": 4.0,
        "manufactured": "2024-03-15",
        "serial": "00231"
    },
    "qr_payload": "https://voltlife.app/b/INFOAN480415032400231",
    "static": {
        "chemistry": "NMC",
        "rated_capacity_kwh": 4.0,
        "mass_estimate_kg": 24
    },
    "dynamic": {
        "soh_pct": 82.4,
        "status": "repurposed",
        "grade": "A",
        "rul_years": 4.3
    },
    "timeline": [
        {"event_type": "manufactured", "occurred_at": "2024-03-15T00:00:00Z"},
        {"event_type": "first_life_started", "occurred_at": "2024-04-02T00:00:00Z", "payload": {"vehicle": "e-scooter, Pune"}},
        {"event_type": "retired_from_ev", "occurred_at": "2026-05-30T00:00:00Z"},
        {"event_type": "assessed", "occurred_at": "2026-06-12T18:00:00Z", "payload": {"soh_pct": 82.4, "grade": "A"}},
        {"event_type": "aadhaar_issued", "occurred_at": "2026-06-12T18:01:00Z"},
        {"event_type": "deployment_assigned", "occurred_at": "2026-06-12T18:02:00Z", "payload": {"site": "Bhadla Solar Park Storage, RJ"}}
    ],
    "life_story": "Born in a Pune factory, March 2024. Carried a commuter ~18,000 km on 412 charges. Retired with 82% of its heart intact — now it stores Rajasthan's sunlight.",
    "impact": {
        "energy_unlocked_mwh": 3.06,
        "carbon_saved_kg": 197.8
    }
}

MOCK_BATTERY = {
    "id": 42,
    "aadhaar_id": "INFOAN480415032400231",
    "external_ref": "BAT-042",
    "oem": "Fleet Operator A (2W)",
    "model": "VoltPack-4000",
    "chemistry": "NMC",
    "form_factor": "pack",
    "rated_capacity_kwh": 4.0,
    "nominal_voltage": 48.0,
    "manufacture_date": "2024-03-15",
    "source_city": "Pune",
    "source_state": "Maharashtra",
    "lat": 18.52,
    "lng": 73.85,
    "status": "assigned",
    "telemetry": {
        "cycle_count": 412,
        "capacity_now_kwh": 3.3,
        "capacity_fade_pct": 17.5,
        "avg_temp_c": 31.2,
        "max_temp_c": 42.5,
        "thermal_stress_hours": 12.0,
        "internal_resistance_mohm": 18.2,
        "ir_growth_pct": 15.4,
        "voltage_stability": 0.985,
        "coulombic_efficiency": 0.998
    },
    "assessment": {
        "soh_pct": 82.4,
        "rul_years": 4.3,
        "rul_range": [3.1, 5.2],
        "grade": "A",
        "confidence": "high",
        "reasons": [
            "Low thermal stress (avg 31°C)",
            "Stable voltage profile",
            "Moderate cycle count (412)"
        ],
        "explanation_json": [
            {"feature": "avg_temp_c", "value": 31.2, "impact": "+", "shap": 0.12, "label": "Low thermal stress (avg 31°C)"},
            {"feature": "voltage_stability", "value": 0.985, "impact": "+", "shap": 0.08, "label": "Stable voltage profile"},
            {"feature": "cycle_count", "value": 412, "impact": "+", "shap": 0.05, "label": "Moderate cycle count (412)"}
        ]
    },
    "deployment": {
        "site_id": 3,
        "site_name": "Bhadla Solar Park Storage, RJ",
        "site_type": "solar_storage",
        "score": 0.87,
        "distance_km": 1142.0,
        "reasons": [
            "Best capacity match (3.2 of 4.0 kWh needed)",
            "Grade A meets solar-storage bar",
            "High carbon offset vs new cells"
        ],
        "energy_unlocked_mwh": 3.06,
        "carbon_saved_kg": 197.8,
        "from": [18.52, 73.85],
        "to": [27.54, 71.91],
        "reasoning_json": [
            {"destination": "Bhadla Solar Park Storage, RJ", "site_id": 3, "score": 87, "factors": ["Best capacity match", "Grade A meets solar-storage bar", "High carbon offset"]},
            {"destination": "Hyderabad ORR Charging Hub, TS", "site_id": 9, "score": 81, "factors": ["Good capacity match", "Grade A meets charging bar"]},
            {"destination": "Gaya Rural Microgrid, BR", "site_id": 5, "score": 74, "factors": ["Priority applied", "Far distance"]}
        ]
    }
}

class IngestRequest(BaseModel):
    batteries: Optional[List[dict]] = None

@app.get("/healthz")
def healthz():
    return {"ok": True, "model_version": "v1.2-mock", "db": "up"}

@app.post("/api/v1/batteries/ingest")
def ingest(payload: Optional[IngestRequest] = None):
    # Mocking ingestion success
    return {
        "job_id": "j_8f3k",
        "accepted": 847,
        "rejected": 3,
        "rejects": [{"row": 14, "reason": "capacity_now_kwh > rated"}]
    }

@app.get("/api/v1/jobs/{job_id}")
def get_job(job_id: str):
    if job_id != "j_8f3k":
        raise HTTPException(status_code=404, detail={"error": {"code": "job_not_found", "message": f"Job {job_id} not found"}})
    return {
        "job_id": "j_8f3k",
        "status": "running",
        "processed": 312,
        "total": 847,
        "recent_events": [
            {
                "type": "assessment",
                "payload": {
                    "battery_id": 42,
                    "aadhaar_id": "INFOAN480415032400231",
                    "oem": "Fleet Operator A (2W)",
                    "soh_pct": 82.4,
                    "rul_years": 4.3,
                    "rul_range": [3.1, 5.2],
                    "grade": "A",
                    "confidence": "high",
                    "reasons": [
                        "Low thermal stress (avg 31°C)",
                        "Stable voltage profile",
                        "Moderate cycle count (412)"
                    ],
                    "lat": 18.52,
                    "lng": 73.85
                }
            },
            {
                "type": "deployment",
                "payload": {
                    "battery_id": 42,
                    "site_id": 3,
                    "site_name": "Bhadla Solar Park Storage, RJ",
                    "site_type": "solar_storage",
                    "score": 0.87,
                    "distance_km": 1142.0,
                    "reasons": [
                        "Best capacity match (3.2 of 4.0 kWh needed)",
                        "Grade A meets solar-storage bar",
                        "High carbon offset vs new cells"
                    ],
                    "energy_unlocked_mwh": 3.06,
                    "carbon_saved_kg": 197.8,
                    "from": [18.52, 73.85],
                    "to": [27.54, 71.91]
                }
            },
            {
                "type": "impact",
                "payload": {
                    "mwh_unlocked": 1059.2,
                    "carbon_saved_tonnes": 69.8,
                    "diverted_from_recycling": 312,
                    "recycled_responsibly": 41,
                    "processed": 353,
                    "total": 847
                }
            }
        ]
    }

@app.get("/api/v1/batteries")
def get_batteries(grade: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 50):
    item = {
        "id": MOCK_BATTERY["id"],
        "aadhaar_id": MOCK_BATTERY["aadhaar_id"],
        "external_ref": MOCK_BATTERY["external_ref"],
        "oem": MOCK_BATTERY["oem"],
        "chemistry": MOCK_BATTERY["chemistry"],
        "rated_capacity_kwh": MOCK_BATTERY["rated_capacity_kwh"],
        "status": status or MOCK_BATTERY["status"],
        "soh_pct": MOCK_BATTERY["assessment"]["soh_pct"],
        "rul_years": MOCK_BATTERY["assessment"]["rul_years"],
        "grade": grade or MOCK_BATTERY["assessment"]["grade"],
        "confidence": MOCK_BATTERY["assessment"]["confidence"],
        "site_name": MOCK_BATTERY["deployment"]["site_name"]
    }
    return {
        "items": [item],
        "total": 847,
        "page": page
    }

@app.get("/api/v1/batteries/{battery_id}")
def get_battery(battery_id: int):
    if battery_id != 42:
        raise HTTPException(status_code=404, detail={"error": {"code": "battery_not_found", "message": f"Battery {battery_id} not found"}})
    return MOCK_BATTERY

@app.get("/api/v1/batteries/{battery_id}/aadhaar")
def get_battery_aadhaar(battery_id: int):
    if battery_id != 42:
        raise HTTPException(status_code=404, detail={"error": {"code": "battery_not_found", "message": f"Battery {battery_id} not found"}})
    return MOCK_AADHAAR

@app.get("/api/v1/aadhaar/{aadhaar_id}")
def get_aadhaar_public(aadhaar_id: str):
    if aadhaar_id != "INFOAN480415032400231":
        raise HTTPException(status_code=404, detail={"error": {"code": "aadhaar_not_found", "message": f"Aadhaar {aadhaar_id} not found"}})
    return MOCK_AADHAAR

@app.get("/api/v1/sites")
def get_sites():
    return {
        "items": [
            {
                "id": 3,
                "name": "Bhadla Solar Park Storage, RJ",
                "site_type": "solar_storage",
                "state": "Rajasthan",
                "lat": 27.54,
                "lng": 71.91,
                "demand_kwh": 1000.0,
                "remaining_kwh": 996.0,
                "min_grade": "A",
                "assigned_count": 1
            }
        ]
    }

@app.get("/api/v1/impact/summary")
def get_impact_summary():
    return {
        "mwh_unlocked": 1059.2,
        "carbon_saved_tonnes": 69.8,
        "diverted_from_recycling": 312,
        "recycled_responsibly": 41,
        "processed": 353,
        "total": 847,
        "by_grade": {"S": 15, "A": 150, "B": 110, "C": 37, "D": 41},
        "by_site_type": {
            "solar_storage": 120,
            "rural_microgrid": 85,
            "school_backup": 40,
            "health_center_backup": 25,
            "industrial_backup": 30,
            "recycler": 41
        }
    }

@app.post("/api/v1/demo/reset")
def demo_reset(x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key")):
    return {"status": "success", "message": "Demo reset complete"}

@app.post("/api/v1/demo/replay")
def demo_replay(x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key")):
    return {"status": "success", "message": "Demo replay initiated"}

@app.websocket("/ws/feed")
async def ws_feed(websocket: WebSocket):
    await websocket.accept()
    # Stream simulated events in a loop
    events = [
        {
            "type": "assessment",
            "payload": {
                "battery_id": 42,
                "aadhaar_id": "INFOAN480415032400231",
                "oem": "Fleet Operator A (2W)",
                "soh_pct": 82.4,
                "rul_years": 4.3,
                "rul_range": [3.1, 5.2],
                "grade": "A",
                "confidence": "high",
                "reasons": ["Low thermal stress (avg 31°C)", "Stable voltage profile", "Moderate cycle count (412)"],
                "lat": 18.52,
                "lng": 73.85
            }
        },
        {
            "type": "deployment",
            "payload": {
                "battery_id": 42,
                "site_id": 3,
                "site_name": "Bhadla Solar Park Storage, RJ",
                "site_type": "solar_storage",
                "score": 0.87,
                "distance_km": 1142.0,
                "reasons": ["Best capacity match (3.2 of 4.0 kWh needed)", "Grade A meets solar-storage bar", "High carbon offset vs new cells"],
                "energy_unlocked_mwh": 3.06,
                "carbon_saved_kg": 197.8,
                "from": [18.52, 73.85],
                "to": [27.54, 71.91]
            }
        },
        {
            "type": "impact",
            "payload": {
                "mwh_unlocked": 1059.2,
                "carbon_saved_tonnes": 69.8,
                "diverted_from_recycling": 312,
                "recycled_responsibly": 41,
                "processed": 353,
                "total": 847
            }
        }
    ]
    try:
        while True:
            for event in events:
                await websocket.send_json(event)
                await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
