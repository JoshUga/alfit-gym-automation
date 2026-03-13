"""Tests for Admin Dashboard Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.admin_service.main import app
from services.admin_service.routes import get_session
from services.admin_service.models import AuditLog


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(db):
    def override():
        yield db
    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    token = create_access_token({"sub": "1", "email": "admin@example.com", "roles": ["super_admin"]})
    return {"Authorization": f"Bearer {token}"}


class TestAuditLogs:
    def test_get_audit_logs(self, client, db, auth_headers):
        db.add(AuditLog(admin_id=1, action="user_update", resource_type="user", resource_id="1"))
        db.commit()

        response = client.get("/api/v1/admin/audit-logs", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1


class TestSystemHealth:
    def test_get_system_health(self, client, auth_headers):
        response = client.get("/api/v1/admin/health-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "services" in data
