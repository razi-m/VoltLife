# PHASE 15 READINESS — Integration Tests, Demo Seed & Validation

## Phase Goal
The objective of Phase 15 is to establish complete end-to-end quality confidence for the VoltLife Marketplace before release. This includes:
- Writing and executing a full happy-path integration test that simulates the entire marketplace transaction lifecycle (supplier sign-up, AI ingestion/grading, lot creation, pricing configuration, listing publication, buyer requirements mapping, AI-matching, quote generation, simulated payment, quantity locking, logistics simulation, shipment tracking, buyer receipt, and support ticket creation).
- Expanding the demo reset endpoint (`POST /api/v1/demo/reset`) to completely reset all marketplace tables and re-seed a rich, realistic database state that fully populates every screen (telemetry, active/completed orders, requirements, quotes, support tickets, and subscription plans).
- Validating the codebase with the full verification suite (pytest backend, frontend build, and the master `checklist.py`) to confirm zero regressions.

## Prerequisites
- Completed phases: Phase 1 through Phase 14 must be fully implemented and integrated.
- Key files required:
  - Backend database schema: [orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/orm.py) and [marketplace_orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/marketplace_orm.py).
  - Main app registration: [main.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/main.py).
  - Seed system: [seed.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/seed/seed.py).
  - Demo router: [demo.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/routers/demo.py).

## Required Inputs
- Standard local development settings: no external third-party keys are required (Stripe, Porter, and Gemini are mocked/simulated in test mode).
- Existing test runner suite: `pytest` and `checklist.py`.

## Team Ownership
- Shared Responsibility (Frontend, Backend, and QA teams).

## External Dependencies
- PostgreSQL / SQLite: Required (using SQLite locally for E2E tests).
- Stripe / Porter / Gemini / n8n: Mocked / Simulated (no external API calls/dependencies).

## Blocking Risks
- Database FK constraint violations when wiping data. The reset endpoint must delete rows in the correct reverse dependency order.
- Hardcoded keys/URLs causing E2E tests or demo seeding to fail.
- Any regression in the core battery intelligence / AI grading functionality (which must remain frozen).

## Readiness Checklist
- [x] All 14 previous phases are completed, and their respective unit tests pass.
- [x] The `test_e2e_marketplace.py` file has been created and covers all key lifecycle milestones.
- [x] The `seed_demo_marketplace_data(db)` method is written in `seed.py`.
- [x] The `/demo/reset` endpoint handles full marketplace table deletion safely without foreign key conflicts.
- [x] All mock endpoints/adapters fall back gracefully when external credentials are not set.

## Phase Exit Criteria
- The E2E integration test runs and passes successfully: `pytest backend/tests/test_e2e_marketplace.py`.
- The full test suite runs and passes cleanly: `pytest backend`.
- Calling `POST /api/v1/demo/reset` succeeds and seeds a representative marketplace demo dataset (sufficient to populate all screens), pricing tiers, requirements, quotes, active and completed orders, tracking events, and support tickets.
- The master checklist `python .agents/scripts/checklist.py .` executes successfully with zero errors.
