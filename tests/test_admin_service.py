"""Tests for Admin Dashboard Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.admin_service.main import app
from services.admin_service.routes import get_session
from services.admin_service.models import AuditLog


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


class TestServiceAdminDashboard:
    def test_service_admin_login(self, client):
        response = client.post(
            "/api/v1/admin/service/login",
            json={"username": "service-admin", "password": "change-this-service-admin-password-now"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["authenticated"] is True

    def test_service_admin_overview_with_headers(self, client):
        response = client.get(
            "/api/v1/admin/service/overview",
            headers={
                "X-Admin-Username": "service-admin",
                "X-Admin-Password": "change-this-service-admin-password-now",
            },
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert "total_gyms" in payload
        assert "total_members" in payload

    def test_service_backup_create_and_list(self, client):
        headers = {
            "X-Admin-Username": "service-admin",
            "X-Admin-Password": "change-this-service-admin-password-now",
        }
        created = client.post(
            "/api/v1/admin/service/backups",
            json={"label": "test-backup"},
            headers=headers,
        )
        assert created.status_code == 200
        assert created.json()["data"]["status"] == "completed"

        listed = client.get("/api/v1/admin/service/backups", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()["data"]) >= 1

    def test_service_admin_gyms_fallback_query_returns_data(self, client, db):
        headers = {
            "X-Admin-Username": "service-admin",
            "X-Admin-Password": "change-this-service-admin-password-now",
        }
        db.execute(text(
            "CREATE TABLE gyms (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, is_active INTEGER)"
        ))
        db.execute(text(
            "CREATE TABLE members (id INTEGER PRIMARY KEY, gym_id INTEGER, status TEXT)"
        ))
        db.execute(text(
            "INSERT INTO gyms (id, name, email, phone, is_active) VALUES (1, 'Alpha Gym', 'alpha@example.com', '123', 1)"
        ))
        db.execute(text(
            "INSERT INTO members (id, gym_id, status) VALUES (1, 1, 'active')"
        ))
        db.commit()

        response = client.get("/api/v1/admin/service/gyms", headers=headers)
        assert response.status_code == 200
        gyms = response.json()["data"]
        assert len(gyms) == 1
        assert gyms[0]["name"] == "Alpha Gym"
        assert gyms[0]["member_count"] == 1

    def test_purge_data_and_restore_backup(self, client, db):
        headers = {
            "X-Admin-Username": "service-admin",
            "X-Admin-Password": "change-this-service-admin-password-now",
        }
        db.execute(text(
            "CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, hashed_password TEXT, full_name TEXT, role TEXT, is_active INTEGER, google_id TEXT)"
        ))
        db.execute(text(
            "CREATE TABLE gyms (id INTEGER PRIMARY KEY, name TEXT, email TEXT, phone TEXT, is_active INTEGER)"
        ))
        db.execute(text(
            "CREATE TABLE members (id INTEGER PRIMARY KEY, gym_id INTEGER, status TEXT)"
        ))
        db.execute(text(
            "INSERT INTO users (id, email, hashed_password, full_name, role, is_active, google_id) VALUES (1, 'owner@example.com', 'hash', 'Owner', 'gym_owner', 1, NULL)"
        ))
        db.execute(text(
            "INSERT INTO gyms (id, name, email, phone, is_active) VALUES (1, 'Alpha Gym', 'alpha@example.com', '123', 1)"
        ))
        db.execute(text(
            "INSERT INTO members (id, gym_id, status) VALUES (1, 1, 'active')"
        ))
        db.commit()

        created = client.post(
            "/api/v1/admin/service/backups",
            json={"label": "before-purge"},
            headers=headers,
        )
        assert created.status_code == 200
        backup_id = created.json()["data"]["id"]

        purged = client.post(
            "/api/v1/admin/service/data/purge",
            json={"include_backups": False},
            headers=headers,
        )
        assert purged.status_code == 200
        assert purged.json()["data"]["cleared_tables"] >= 1
        backups_after_purge = client.get("/api/v1/admin/service/backups", headers=headers)
        assert backups_after_purge.status_code == 200
        assert any(item["id"] == backup_id for item in backups_after_purge.json()["data"])

        users_after_purge = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        assert users_after_purge == 0

        gyms_after_purge = client.get("/api/v1/admin/service/gyms", headers=headers)
        assert gyms_after_purge.status_code == 200
        assert gyms_after_purge.json()["data"] == []

        restored = client.post(
            f"/api/v1/admin/service/backups/{backup_id}/restore",
            json={"clear_existing": True},
            headers=headers,
        )
        assert restored.status_code == 200
        assert restored.json()["data"]["restored_tables"] >= 1

        gyms_after_restore = client.get("/api/v1/admin/service/gyms", headers=headers)
        assert gyms_after_restore.status_code == 200
        gyms = gyms_after_restore.json()["data"]
        assert len(gyms) == 1
        assert gyms[0]["name"] == "Alpha Gym"

        users_after_restore = db.execute(text("SELECT email FROM users ORDER BY id")).fetchall()
        assert [row[0] for row in users_after_restore] == ["owner@example.com"]
