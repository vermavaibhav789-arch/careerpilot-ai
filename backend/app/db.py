"""
Database setup. SQLite by default (see DATABASE_URL in config.py) - a
single file, zero extra infrastructure, which is the right tradeoff for a
project like this. Swapping to Postgres later is a one-line config change;
nothing in db_models.py or the store layer is SQLite-specific.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# check_same_thread=False is needed for SQLite specifically, since FastAPI
# can use the same connection from different threads across requests. This
# is a no-op / ignored for other database backends.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency - yields a DB session, always closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
