# PHASE 02 READINESS — Supplier Registration, Verification & Auth

## Phase Goal
- Implement Supplier registration (signup with company details: name, email, phone, GSTIN, address) and SupplierUser creation (username/password).
- Implement JWT/Token-based authentication using standard Python libraries (`hashlib`, `hmac`, `secrets`) to keep requirements clean and dependency-free.
- Restrict access to supplier endpoints (profile, upload inventory, dashboard) only to verified suppliers.
- Implement an admin verification simulation endpoint to approve suppliers.

## Prerequisites
- Completed phases: **Phase 1** (Marketplace Database Tables registered and initialized).
- Required files:
  - [marketplace_orm.py](file:///c:/Users/Razi/Claude/Projects/VoltLife/backend/app/models/marketplace_orm.py)
- Required services: N/A (Standard HTTP request lifecycle).
- Required approvals: Phase 1 complete and validated.

## Required Inputs
- DB Models: `Supplier`, `SupplierUser`, `SupplierVerification` from `app.models.marketplace_orm`.
- Verification Rules: A supplier is created with `is_verified=False` by default. An admin must approve them (via a secure or mock verify endpoint) before they can list inventory or access supplier pages.

## Team Ownership
- Backend Team (Auth & Router design).

## External Dependencies
- PostgreSQL / SQLite (DB connection): Required.
- Standard libraries: `hashlib` (SHA-256 for password hashing), `hmac` & `base64` (secure session tokens).

## Blocking Risks
- Session state persistence (resolved by storing user session metadata or using signed stateless tokens).
- Cross-origin header passing for token auth (FastAPI CORS middleware is already configured for `*` in `main.py`).

## Readiness Checklist
- [x] Verified `marketplace_orm.py` models are successfully loaded in test suite.
- [x] Confirmed CORS setup in `app/main.py` permits custom headers (`Authorization`).
- [x] Designed HMAC-based token signature contract to prevent dependency bloat.

## Phase Exit Criteria
- Supplier registration (`POST /api/v1/suppliers/register`) creates a Supplier and SupplierUser and returns success.
- Supplier login (`POST /api/v1/suppliers/login`) checks credentials and returns a valid signed session token.
- Access to `GET /api/v1/suppliers/me` is blocked with a 401/403 status code unless a valid, verified supplier token is passed in the header.
- Admin verification endpoint (`POST /api/v1/suppliers/{id}/verify`) successfully updates supplier verification status.
