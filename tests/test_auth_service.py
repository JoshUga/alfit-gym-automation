"""Tests for Auth Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token, create_refresh_token
from services.auth_service.main import app
from services.auth_service.routes import get_session
from services.auth_service.models import User, UserRole
from services.auth_service.service import hash_password


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


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-service"


class TestUserRegistration:
    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"]
        assert data["data"]["refresh_token"]
        assert data["data"]["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "securepassword123",
        })
        response = client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "anotherpassword123",
        })
        assert response.status_code == 409

    def test_register_invalid_email(self, client):
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "securepassword123",
        })
        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post("/auth/register", json={
            "email": "user@example.com",
            "password": "short",
        })
        assert response.status_code == 422


class TestUserLogin:
    def test_login_success(self, client, db):
        user = User(
            email="login@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Login User",
            role=UserRole.GYM_OWNER,
        )
        db.add(user)
        db.commit()

        response = client.post("/auth/login", json={
            "email": "login@example.com",
            "password": "testpassword123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["access_token"]

    def test_login_wrong_password(self, client, db):
        user = User(
            email="wrong@example.com",
            hashed_password=hash_password("correctpassword"),
            full_name="User",
            role=UserRole.GYM_OWNER,
        )
        db.add(user)
        db.commit()

        response = client.post("/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "anypassword",
        })
        assert response.status_code == 401

    def test_login_disabled_account(self, client, db):
        user = User(
            email="disabled@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Disabled User",
            role=UserRole.GYM_OWNER,
            is_active=False,
        )
        db.add(user)
        db.commit()

        response = client.post("/auth/login", json={
            "email": "disabled@example.com",
            "password": "testpassword123",
        })
        assert response.status_code == 401


class TestTokenRefresh:
    def test_refresh_token(self, client):
        refresh = create_refresh_token({"sub": "1", "email": "test@example.com", "roles": ["gym_owner"]})
        response = client.post("/auth/token/refresh", json={
            "refresh_token": refresh,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["access_token"]

    def test_refresh_with_access_token_fails(self, client):
        access = create_access_token({"sub": "1", "email": "test@example.com"})
        response = client.post("/auth/token/refresh", json={
            "refresh_token": access,
        })
        assert response.status_code == 422


class TestGetCurrentUser:
    def test_get_me(self, client, db):
        user = User(
            email="me@example.com",
            hashed_password=hash_password("testpassword"),
            full_name="Current User",
            role=UserRole.GYM_OWNER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "email": user.email, "roles": ["gym_owner"]})
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["email"] == "me@example.com"
        assert data["data"]["owner_id"] == user.id

    def test_get_me_unauthorized(self, client):
        response = client.get("/auth/me")
        assert response.status_code in [401, 403]


class TestChangePassword:
    def test_change_password_success(self, client, db):
        user = User(
            email="change@example.com",
            hashed_password=hash_password("oldpassword123"),
            full_name="Password User",
            role=UserRole.GYM_OWNER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "email": user.email, "roles": ["gym_owner"]})
        response = client.post(
            "/auth/change-password",
            json={"old_password": "oldpassword123", "new_password": "newpassword123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_change_password_wrong_old(self, client, db):
        user = User(
            email="wrongold@example.com",
            hashed_password=hash_password("oldpassword123"),
            full_name="User",
            role=UserRole.GYM_OWNER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "email": user.email, "roles": ["gym_owner"]})
        response = client.post(
            "/auth/change-password",
            json={"old_password": "wrongpassword", "new_password": "newpassword123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestTrainerManagement:
    def test_create_and_list_trainers(self, client, db):
        owner = User(
            email="owner@example.com",
            hashed_password=hash_password("ownerpassword123"),
            full_name="Owner",
            role=UserRole.GYM_OWNER,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)

        owner_token = create_access_token(
            {"sub": str(owner.id), "email": owner.email, "roles": ["gym_owner"], "owner_id": owner.id}
        )
        headers = {"Authorization": f"Bearer {owner_token}"}

        create_response = client.post(
            "/auth/trainers",
            json={
                "email": "trainer@example.com",
                "password": "trainerpassword123",
                "full_name": "Trainer One",
            },
            headers=headers,
        )
        assert create_response.status_code == 200
        created = create_response.json()["data"]
        assert created["email"] == "trainer@example.com"
        assert created["role"] == "gym_staff"
        assert created["owner_id"] == owner.id

        list_response = client.get("/auth/trainers", headers=headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) == 1

    def test_create_trainer_forbidden_for_non_owner(self, client, db):
        staff = User(
            email="staff@example.com",
            hashed_password=hash_password("staffpassword123"),
            full_name="Staff",
            role=UserRole.GYM_STAFF,
        )
        db.add(staff)
        db.commit()
        db.refresh(staff)

        staff_token = create_access_token(
            {"sub": str(staff.id), "email": staff.email, "roles": ["gym_staff"], "owner_id": staff.id}
        )
        response = client.post(
            "/auth/trainers",
            json={
                "email": "newtrainer@example.com",
                "password": "trainerpassword123",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert response.status_code == 403
