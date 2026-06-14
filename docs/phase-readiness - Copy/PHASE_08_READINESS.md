# PHASE 08 READINESS — Quote Engine (Pricing + Mock Porter)

## Phase Goal
- Enable buyers to request formal price quotes for bulk battery lots by choosing a desired quantity of packs.
- Calculate battery costs dynamically based on the supplier's configured quantity pricing tiers.
- Mock transport logistics using a simulated Porter adapter that accepts supplier and buyer locations, returning a deterministic vehicle type recommendation, transport cost, and transit ETA.
- Save the calculated quote in the database (`Quote` model in `marketplace_orm.py`) without modifying/locking inventory at this stage.

## Prerequisites
- Completed phases: **Phase 1** (Data Model), **Phase 5** (Buyer Access & Accounts), **Phase 7** (Marketplace Discovery).
- Existing tables: `quotes`, `buyer_accounts`, `inventory_lots`, `pricing_tiers`, `listings`, and `suppliers` (in `marketplace_orm.py`).
- Existing auth middleware `get_current_buyer`.

## Required Inputs
- DB Models: `Quote`, `InventoryLot`, `PricingTier`, `BuyerAccount`, `Supplier`.
- API request payload:
  - `POST /api/v1/quotes`
    - Input: `{"inventory_lot_id": int, "quantity": int}`
- API response contract:
  - Return: `{"id": int, "battery_cost": float, "transport_cost": float, "total_cost": float, "delivery_days": int, "porter_vehicle_type": str, "status": str}`
- Env Variables (additive):
  - `PORTER_API_KEY` (optional/unused mock indicator).

## Team Ownership
- Backend Team (Quote router, pricing tier calculation, mock Porter adapter service, database transactions, integration tests).

## External Dependencies
- PostgreSQL.
- Porter API (Mocked only—deterministic distance/weight logic, no real logistics api).

## Blocking Risks
- Incorrect pricing tier resolution (e.g. not matching the highest applicable quantity tier).
  - *Mitigation:* Ensure tiers are sorted by `min_quantity` and lookup the highest tier where `quantity >= min_quantity`. If no tiers match, default to a fallback price.
- Bypassing Minimum Order Quantity (MOQ).
  - *Mitigation:* Verify `quantity >= listing.moq` before generating the quote. Raise `400 Bad Request` if violated.
- Inventory leaking: Locking inventory at quote creation rather than payment time.
  - *Mitigation:* The quote endpoint must not modify `available_quantity` or create locks. It only calculates costs and persists the quote record.

## Readiness Checklist
- [x] Verified `quotes` table exists in `marketplace_orm.py` with foreign keys to `buyer_accounts` and `inventory_lots`.
- [x] Verified `get_current_buyer` is active for route protection.
- [x] Confirmed mock Porter transport cost is deterministic and runs without requiring external credentials.

## Phase Exit Criteria
- Buyers can submit a request with a lot ID and quantity to get a calculated quote.
- Battery cost matches the quantity pricing tier correctly (e.g., if 10 units are requested and tier 10+ is $145/kWh, it computes `10 * capacity * 145.0`).
- Mock Porter returns a valid vehicle selection (e.g. "Tata Ace", "Mahindra Bolero Pickup" depending on weight/quantity) and transit ETA (e.g. 2-4 days depending on location).
- Quotes are successfully persisted in the database.
- Database available quantity is unchanged after a quote is generated.
- Integration tests in `backend/tests/test_quotes.py` cover quantity checks, MOQ validations, pricing tier lookups, mock Porter returns, and DB persistence.
