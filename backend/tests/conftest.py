"""
Shared test fixtures (Excellence Pass T4).
ONE test engine for the whole session, patched into the app exactly once,
eliminating the import-time engine collisions between test modules.
"""
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

_EXPLICIT_TEST_URL = os.getenv("TEST_DATABASE_URL")
_PROD_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = _EXPLICIT_TEST_URL or _PROD_URL

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL or DATABASE_URL must be set in environment to run tests on PostgreSQL")

if "sqlite" in TEST_DATABASE_URL:
    raise ValueError("SQLite is forbidden in tests. Please configure a PostgreSQL database URL for testing.")

# Safety guard: the fixtures below run drop_all() and DELETE on the fleet tables. The suite must
# never point at production. Require a dedicated TEST_DATABASE_URL that is distinct from DATABASE_URL.
if _EXPLICIT_TEST_URL is None:
    raise RuntimeError(
        "Refusing to run tests against DATABASE_URL (production). "
        "Set a dedicated TEST_DATABASE_URL pointing at a separate test database."
    )
if _PROD_URL and _EXPLICIT_TEST_URL == _PROD_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL must not equal DATABASE_URL (production). Use a separate test database."
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["PACE_S"] = "0"

import json
import math

def custom_serializer(obj):
    """
    Traverses the object and replaces float('nan') values with None
    to prevent invalid JSON token exceptions (e.g. unquoted NaN) in PostgreSQL.
    """
    def clean_nan(o):
        if isinstance(o, dict):
            return {k: clean_nan(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [clean_nan(v) for v in o]
        elif isinstance(o, float) and math.isnan(o):
            return None
        return o
    return json.dumps(clean_nan(obj))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

connect_args = {
    "sslmode": "require",
    "connect_timeout": 10
}
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    connect_args=connect_args,
    pool_pre_ping=True,
    json_serializer=custom_serializer
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Patch BEFORE any app import binds the real engine
import app.db.database
app.db.database.engine = engine
app.db.database.SessionLocal = TestingSessionLocal

import app.services.pipeline
app.services.pipeline.SessionLocal = TestingSessionLocal

from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.db.database import Base, get_db
from app.models.orm import Battery, Assessment, Deployment, TelemetrySummary, LifecycleEvent, Site
from app.models.marketplace_orm import (
    SupportTicket, PaymentEvent, ShipmentTrackingEvent, Order, Quote,
    Requirement, Listing, PricingTier, InventoryLot, SupplierVerification,
    SupplierUser, Supplier, BuyerAccount
)
from app.seed.seed import seed_sites


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Create the schema once for the whole test session; drop at the end."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()



@pytest.fixture(scope="function")
def db_session(_test_database):
    """Function-scoped clean state: wipe fleet tables, reseed sites, clear job registry."""
    db = TestingSessionLocal()
    
    from app.models.marketplace_orm import (
        SupportTicket, PaymentEvent, ShipmentTrackingEvent, Order, Quote,
        Requirement, Listing, PricingTier, InventoryLot, SupplierVerification,
        SupplierUser, Supplier, BuyerAccount
    )
    
    # Delete in reverse topological order to satisfy foreign key dependencies
    for model in (
        SupportTicket, PaymentEvent, ShipmentTrackingEvent, Order, Quote,
        Requirement, Listing, PricingTier, InventoryLot, SupplierVerification,
        SupplierUser, Supplier, BuyerAccount,
        Deployment, Assessment, TelemetrySummary, LifecycleEvent, Battery
    ):
        db.query(model).delete()
        
    db.commit()
    seed_sites(db)
    app.services.pipeline.JOBS.clear()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()
