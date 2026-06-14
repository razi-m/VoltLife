# PHASE 05 READINESS — Buyer Access & Accounts

## Phase Goal
- Allow buyers to register accounts, log in, and view their profile details.
- Public read-only endpoints (e.g. `/api/v1/marketplace/lots` and `/api/v1/marketplace/auctions`) must remain fully open to anonymous browsing without login.
- Establish secure session tokens for buyer accounts, separating them cryptographically from supplier privileges.

## Prerequisites
- Completed phases: **Phase 1** (Data Model), **Phase 4** (Supplier Config & Publish).
- Existing tables: `buyer_accounts` (defined in `marketplace_orm.py`).
- Security helpers (`hash_password`, `verify_password`, `create_access_token`, `verify_token`) in `auth.py`.

## Required Inputs
- DB Models: `BuyerAccount`.
- Schemas for buyer registration and login.
- Endpoint definitions:
  - `POST /api/v1/buyers/register` (creates a new buyer account).
  - `POST /api/v1/buyers/login` (checks password and returns access token).
  - `GET /api/v1/buyers/me` (requires verified buyer token).

## Team Ownership
- Backend Team (Router implementation, password hashing, token validation, integration tests).

## External Dependencies
- PostgreSQL.

## Blocking Risks
- Token mixing: A buyer token being accepted on supplier routes, or a supplier token being accepted on buyer routes.
  - *Mitigation:* Include `"type": "buyer"` in the buyer token payload and verify it in the buyer security dependency.
- Duplicate credentials: Multiple buyers registering with the same username or email.
  - *Mitigation:* Perform duplicate check on the database before creating the account and raise `400 Bad Request`.

## Readiness Checklist
- [x] Verified `buyer_accounts` table exists in `marketplace_orm.py`.
- [x] Confirmed `auth.py` functions are fully reusable.
- [x] Verified that pytest database cleanup fixture deletes from `buyer_accounts`.

## Phase Exit Criteria
- Public discovery endpoints are queryable without any credentials.
- Registration creates buyer records with salt-hashed passwords.
- Login successfully validates passwords and issues session tokens.
- Secure buyer dependency blocks invalid/non-buyer tokens.
- Integration tests in `backend/tests/test_buyers.py` cover registration, duplicate registration checks, login, and profile retrieval, and all tests pass cleanly.
