# PHASE 03 READINESS — Battery Upload → AI Assessment → Inventory Auto-Generation

## Phase Goal
- Allow verified suppliers to upload battery telemetry data (via CSV/JSON) and run it through the existing assessment and grading pipeline.
- Automatically group successfully assessed batteries (non-Grade D) into grade-bucketed draft inventory lots (`InventoryLot`) grouped by `(supplier_id, grade, chemistry)`.
- Increment quantities and update average health metrics (SoH, RUL, total capacity) inside the draft inventory lots as batteries complete assessment.
- Link batteries to inventory lots using the many-to-many `battery_inventory_lot_associations` table.

## Prerequisites
- Completed phases required: **Phase 1** (Data Model & Migrations), **Phase 2** (Supplier Registration, Verification & Auth).
- Required files:
  - [marketplace_orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/marketplace_orm.py) (includes `InventoryLot` and association tables).
  - [orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py) (includes `Battery` and `Assessment` tables).
  - [pipeline.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/services/pipeline.py) (handles the asynchronous background grading tasks).
  - [ingestion.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/services/ingestion.py) (handles telemetry parsing and validation).
- Required approvals: Phase 2 backend tests are green, and the auth strategy is approved.

## Required Inputs
- DB Models: `Battery`, `TelemetrySummary`, `Assessment`, `Supplier`, `InventoryLot`, `BatteryInventoryLotAssociation`.
- CSV Schema: Standard ingestion CSV format containing `external_ref`, `oem`, `chemistry`, `rated_capacity_kwh`, `cycle_count`, `capacity_now_kwh`, `lat`, `lng`, etc.
- Ingestion Seam: Update `process_ingestion` in `ingestion.py` to optionally accept `supplier_id: Optional[int]`.
- Auto-generation Trigger: Update `process_single_battery` in `pipeline.py` to check for `supplier_id` and create/update draft `InventoryLot` records before committing.

## Team Ownership
- Backend Team (Ingestion router & pipeline update, tests).

## External Dependencies
- PostgreSQL / SQLite (DB connection): Required.
- ML Predictor (`app/ml/predictor.py`): Required (Frozen, but called by pipeline).

## Blocking Risks
- Database lock contention or race conditions if multiple batteries update the same draft `InventoryLot` in parallel threads.
  - *Mitigation:* The existing pipeline processes batteries sequentially (paced by `settings.PACE_S`) per ingestion job, using a single synchronous transaction thread, minimizing lock overlap.
- Handling Grade D batteries.
  - *Mitigation:* Filter out Grade D batteries from auto-inventory lots; they are routed straight to recycling.

## Readiness Checklist
- [x] Verified `Battery` ORM model has the nullable `supplier_id` foreign key column.
- [x] Confirmed the existing assessment pipeline works cleanly when triggered manually.
- [x] Verified SQLite/PostgreSQL metadata structure includes the `battery_inventory_lot_associations` table.

## Phase Exit Criteria
- Verified supplier authentication is enforced on `POST /api/v1/suppliers/inventory/upload`.
- Battery records created through the upload route are tagged with the authenticated `supplier_id`.
- The background lifecycle pipeline is kicked off for the uploaded batteries.
- Graded batteries (non-Grade D) are linked to a draft `InventoryLot` grouped by `(supplier_id, grade, chemistry)`.
- Draft inventory lots dynamically aggregate metrics (`avg_soh`, `avg_rul_years`, `total_capacity_kwh`, `available_quantity`) correctly as batteries complete processing.
- Integration tests in `backend/tests/test_inventory.py` cover the upload, assessment, and lot aggregation, and pass cleanly.
