"""Database connection helpers using SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
from shared.config import get_database_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


def get_engine(database_url: str | None = None):
    """Create a SQLAlchemy engine."""
    url = database_url or get_database_settings().database_url
    return create_engine(url, pool_pre_ping=True, pool_recycle=3600)


def get_session_factory(database_url: str | None = None) -> sessionmaker:
    """Create a session factory."""
    engine = get_engine(database_url)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(database_url: str | None = None) -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    SessionLocal = get_session_factory(database_url)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
