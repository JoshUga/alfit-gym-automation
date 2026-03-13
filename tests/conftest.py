"""Shared test fixtures for all services."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from shared.database import Base
from shared.auth import create_access_token


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Session:
    """Create a database session for testing."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def auth_token():
    """Create a valid JWT token for testing."""
    token_data = {
        "sub": "1",
        "email": "test@example.com",
        "roles": ["gym_owner"],
    }
    return create_access_token(token_data)


@pytest.fixture
def admin_token():
    """Create a valid admin JWT token for testing."""
    token_data = {
        "sub": "1",
        "email": "admin@example.com",
        "roles": ["super_admin"],
    }
    return create_access_token(token_data)


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Create admin authorization headers for testing."""
    return {"Authorization": f"Bearer {admin_token}"}


def override_get_db(db_session):
    """Create a dependency override for get_db."""
    def _get_db():
        yield db_session
    return _get_db
