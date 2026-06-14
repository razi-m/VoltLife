# PHASE 04 READINESS — Supplier Configuration & Publish

## Phase Goal
- Allow verified suppliers to configure quantity-tier pricing, optional Minimum Order Quantity (MOQ), and plain-text listing descriptions for their auto-generated draft inventory lots.
- Expose endpoints to publish/unpublish listings and check configured pricing/listing details.
- Enforce the server-side constraint that only VoltLife-assessed batteries associated with the lot can be listed (manual or arbitrary creation of listings without assessed inventory is strictly forbidden).
- Make published listings available via public read-only APIs for downstream buyer discovery.

## Prerequisites
- Completed phases: **Phase 1** (Data Model), **Phase 2** (Supplier Auth), **Phase 3** (Battery Ingestion & Auto-Inventory).
- Required tables: `suppliers`, `inventory_lots`, `pricing_tiers`, `listings`, `batteries`, and the association table `battery_inventory_lot_associations`.
- Existing auth middleware `get_current_verified_supplier`.

## Required Inputs
- DB Models: `InventoryLot`, `PricingTier`, `Listing`, `Battery`.
- API request payloads for configuring listing descriptions, MOQ, and a list of pricing tiers (`min_quantity` and `price_per_kwh`).
- Route definitions:
  - `POST /api/v1/suppliers/inventory/lots/{lot_id}/listing` (configure description and MOQ).
  - `POST /api/v1/suppliers/inventory/lots/{lot_id}/pricing` (configure pricing tiers).
  - `POST /api/v1/suppliers/inventory/lots/{lot_id}/publish` (publish/unpublish listing).
  - `GET /api/v1/suppliers/inventory/lots/{lot_id}/listing` (retrieve listing details).
  - `GET /api/v1/marketplace/listings` (public discovery route for published listings).

## Team Ownership
- Backend Team (Endpoint routing, business logic validation, database transactions, integration tests).

## External Dependencies
- PostgreSQL (Supabase / local test database).
- Mockable/Optional: None needed (standard CRUD and validation rules only).

## Blocking Risks
- Overlapping, negative, or invalid pricing tiers (e.g., price per kWh <= 0 or MOQ <= 0).
  - *Mitigation:* Enforce input schema validation using Pydantic; check that `min_quantity` is positive and tiers are sorted correctly.
- Security/Data isolation leaks: A supplier trying to configure or publish an inventory lot belonging to another supplier.
  - *Mitigation:* Query the `InventoryLot` by ID and raise a `403 Forbidden` or `404 Not Found` if `lot.supplier_id != current_supplier.id`.
- Manual listing bypass: Bypassing the auto-generated inventory lot structure and creating a listing for non-assessed batteries.
  - *Mitigation:* Require a valid `inventory_lot_id` for configuring/publishing, ensuring the lot has associated batteries in the many-to-many relationship, and block any manual standalone Listing creations.

## Readiness Checklist
- [x] Confirmed `Listing` and `PricingTier` tables exist in `marketplace_orm.py` and are registered in database metadata.
- [x] Confirmed verified supplier auth dependency (`get_current_verified_supplier`) is active and can be used on protected configuration routes.
- [x] Confirmed the test suite has clean database setup and cleanup for the new marketplace tables.

## Phase Exit Criteria
- Suppliers can configure or update listing descriptions and MOQ on draft lots.
- Suppliers can define one or more pricing tiers for an inventory lot.
- Suppliers can publish/unpublish their lots.
- Only lots that are published are returned by the public discovery endpoint (`GET /api/v1/marketplace/listings`).
- Access rules are enforced: unverified suppliers or other suppliers cannot configure or publish a lot.
- Integration tests in `backend/tests/test_listings.py` cover unauthorized access, validation errors, successful listing configuration, pricing tier updates, publishing, and public listing queries, and all tests pass cleanly.
