# PHASE 06 READINESS — Gemini AI Requirement Builder & AI Marketplace Matching

## Phase Goal
- Implement a natural language requirement builder where buyers can submit free-text use case requests (e.g. "Need batteries for 100 kWh solar backup in Pune").
- Parse the request using a Gemini API adapter into structured requirements: `parsed_grade`, `parsed_capacity_kwh`, and `parsed_quantity`.
- Ensure the Gemini adapter supports a deterministic mock fallback when `GEMINI_API_KEY` is not present, allowing the entire application to run offline/keyless.
- Create an intelligent matching engine to filter and score real published listings based on the parsed requirements (grade compatibility, capacity matching, available quantity).
- Persist parsed buyer requirements in the database.

## Prerequisites
- Completed phases: **Phase 1** (Data Model), **Phase 5** (Buyer Access & Accounts).
- Existing tables: `buyer_accounts`, `requirements`, `inventory_lots`, `listings`, `pricing_tiers`, and `suppliers` (all in `marketplace_orm.py`).
- Existing auth middleware `get_current_buyer`.

## Required Inputs
- DB Models: `BuyerAccount`, `Requirement`, `InventoryLot`, `Listing`, `PricingTier`.
- API request payload for creating requirements: `{"use_case_text": str}`.
- Route definitions:
  - `POST /api/v1/requirements` (creates a buyer requirement, parses it using Gemini or Mock adapter, and saves to DB).
  - `GET /api/v1/requirements/{requirement_id}/matches` (retrieves ranked published listings matching the requirement).
- Env Variables (additive):
  - `GEMINI_API_KEY` (optional, for live Gemini parsing).

## Team Ownership
- Backend Team (Gemini adapter service, local keyword parser, matching/filtering database logic, routers, integration tests).

## External Dependencies
- PostgreSQL (Supabase / local test database).
- Gemini API (Optional / Mockable when `GEMINI_API_KEY` is missing).

## Blocking Risks
- API call failures or timeouts during live Gemini parsing.
  - *Mitigation:* Catch any Gemini API exception, log the error, and automatically fall back to the deterministic local keyword parser so the route never fails.
- Keyless demo failure.
  - *Mitigation:* Ensure the local keyword parser is fully tested and triggers automatically if `GEMINI_API_KEY` is empty/null.
- Bypassing published filters or fabricating sellers.
  - *Mitigation:* The matching engine must only query `Listing` records where `is_published == True` and `InventoryLot.available_quantity > 0`, referencing real suppliers.

## Readiness Checklist
- [x] Verified `requirements` table exists in `marketplace_orm.py` with foreign key to `buyer_accounts`.
- [x] Verified `get_current_buyer` dependency is active to protect buyer routes.
- [x] Confirmed mock/production environment handles keyless operation gracefully.

## Phase Exit Criteria
- Buyers can submit a natural language string and receive a successfully parsed requirement with structured `parsed_grade`, `parsed_capacity_kwh`, and `parsed_quantity`.
- The Gemini adapter successfully calls Google's Gemini API when `GEMINI_API_KEY` is set.
- The local keyword parser accurately parses key terms (e.g. "100 kWh", "grade A", "50 units") when `GEMINI_API_KEY` is not set.
- The matching endpoint (`GET /api/v1/requirements/{id}/matches`) retrieves published listings, ranks them with a match score (0-100%), and never returns unpublished lots or fabricated sellers.
- Integration tests in `backend/tests/test_requirements.py` verify parsing (both mock and fallback), storage, matching, and proper error handling.
