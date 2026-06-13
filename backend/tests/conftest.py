"""
Shared test fixtures (Excellence Pass T4).
ONE test engine for the whole session, patched into the app exactly once,
eliminating the import-time engine collisions between test modules.
"""
import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_DB_FILE = "./test_voltlife_shared.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("PACE_S", "0")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
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
from app.seed.seed import seed_sites


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Create the schema once for the whole test session; drop at the end."""
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass


@pytest.fixture(scope="function")
def db_session(_test_database):
    """Function-scoped clean state: wipe fleet tables, reseed sites, clear job registry."""
    db = TestingSessionLocal()
    for model in (Deployment, Assessment, TelemetrySummary, LifecycleEvent, Battery):
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
