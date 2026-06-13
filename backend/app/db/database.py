from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

# SQLite connection options
connect_args = {}
if is_sqlite:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args
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
        # Schema is frozen (docs/03); generic JSON/DateTime types render as JSONB/TIMESTAMPTZ on PG.
        # create_all(checkfirst=True) is the formal init path for both engines - no migration tooling
        # required at the hackathon. If incremental migrations are ever needed, add an Alembic baseline.
    OrmBase.metadata.create_all(bind=engine)
