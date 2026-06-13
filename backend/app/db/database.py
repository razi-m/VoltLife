from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

from sqlalchemy.pool import NullPool

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

DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

# Database connection options and engine setup
if not is_sqlite:
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 10
    }
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args=connect_args,
        pool_pre_ping=True,
        json_serializer=custom_serializer
    )
else:
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        json_serializer=custom_serializer
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database tables.
    If database URL is SQLite, metadata.create_all() creates tables directly.
    """
    # ORM models must be imported before metadata.create_all
    from app.models.orm import Base as OrmBase
    if is_sqlite:
        logger.info("SQLite database detected. Running metadata.create_all().")
    else:
        logger.info("PostgreSQL database detected. Running idempotent metadata.create_all() (checkfirst).")
        # Schema is frozen (docs/03); models use postgresql.JSONB and DateTime(timezone=True) -> TIMESTAMPTZ.
        # create_all(checkfirst=True) creates missing tables only. For column changes see
        # database_evolution_strategy.md (no migration tooling at the hackathon).
    OrmBase.metadata.create_all(bind=engine)
