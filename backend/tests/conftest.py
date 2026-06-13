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
os.environ.setdefault("PACE_S", "0")

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


# Patch BEFORE any app import binds the real e