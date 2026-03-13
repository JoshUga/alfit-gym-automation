"""Tests for Gym Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.gym_service.main import app
from services.gym_service.routes import get_session
from services.gym_service.models import Gym


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
    token = create_access_token({"sub": "1", "email": "owner@example.com", "roles": ["gym_owner"]})
    return {"Authorization": f"Bearer {token}"}


class TestGymRegistration:
    def test_register_gym(self, client, auth_headers):
        response = client.post("/api/v1/gyms/register", json={
            "name": "Test Gym",
            "address": "123 Main St",
            "phone": "+1234567890",
            "email": "gym@example.com",
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Gym"
        assert data["data"]["owner_id"] == 1

    def test_register_gym_unauthorized(self, client):
        response = client.post("/api/v1/gyms/register", json={
            "name": "Test Gym",
            "address": "123 Main St",
            "phone": "+1234567890",
            "email": "gym@example.com",
        })
        assert response.status_code in [401, 403]


class TestGymCRUD:
    def test_get_gym(self, client, db, auth_headers):
        gym = Gym(name="Get Gym", address="456 Oak Ave", phone="+1111111111", email="get@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.get(f"/api/v1/gyms/{gym.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Get Gym"

    def test_get_gym_not_found(self, client, auth_headers):
        response = client.get("/api/v1/gyms/999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_gym(self, client, db, auth_headers):
        gym = Gym(name="Old Name", address="123 St", phone="+1111111111", email="old@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.put(f"/api/v1/gyms/{gym.id}", json={"name": "New Name"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "New Name"

    def test_delete_gym(self, client, db, auth_headers):
        gym = Gym(name="Delete Gym", address="789 St", phone="+2222222222", email="del@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.delete(f"/api/v1/gyms/{gym.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_delete_gym_not_found(self, client, auth_headers):
        response = client.delete("/api/v1/gyms/999", headers=auth_headers)
        assert response.status_code == 404


class TestPhoneNumbers:
    def test_add_phone_number(self, client, db, auth_headers):
        gym = Gym(name="Phone Gym", address="123 St", phone="+1111111111", email="phone@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.post(f"/api/v1/gyms/{gym.id}/phone-numbers", json={
            "phone_number": "+9876543210",
            "label": "Main Line",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["phone_number"] == "+9876543210"

    def test_list_phone_numbers(self, client, db, auth_headers):
        gym = Gym(name="List Gym", address="123 St", phone="+1111111111", email="list@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.get(f"/api/v1/gyms/{gym.id}/phone-numbers", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    def test_remove_phone_number(self, client, db, auth_headers):
        gym = Gym(name="Remove Gym", address="123 St", phone="+1111111111", email="rm@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        # First add a phone
        add_response = client.post(f"/api/v1/gyms/{gym.id}/phone-numbers", json={
            "phone_number": "+1112223333",
            "label": "To Remove",
        }, headers=auth_headers)
        phone_id = add_response.json()["data"]["id"]

        # Then remove it
        response = client.delete(f"/api/v1/gyms/{gym.id}/phone-numbers/{phone_id}", headers=auth_headers)
        assert response.status_code == 200


class TestEvolutionCredentials:
    def test_set_credentials(self, client, db, auth_headers):
        gym = Gym(name="Cred Gym", address="123 St", phone="+1111111111", email="cred@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.post(f"/api/v1/gyms/{gym.id}/evolution-credentials", json={
            "api_key": "test-api-key-123",
            "instance_name": "test-instance",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_get_credentials(self, client, db, auth_headers):
        gym = Gym(name="Get Cred Gym", address="123 St", phone="+1111111111", email="getcred@gym.com", owner_id=1)
        db.add(gym)
        db.commit()
        db.refresh(gym)

        response = client.get(f"/api/v1/gyms/{gym.id}/evolution-credentials", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)
