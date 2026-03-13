"""Tests for EvolutionAPI Proxy Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.evolution_service.main import app
from services.evolution_service.routes import get_session
from services.evolution_service.models import EvolutionInstance, InstanceStatus


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
    token = create_access_token({"sub": "1", "email": "owner@example.com", "roles": ["gym_owner"]})
    return {"Authorization": f"Bearer {token}"}


class TestInstances:
    def test_create_instance(self, client, auth_headers):
        response = client.post("/api/v1/evolution/instances", json={
            "gym_id": 1,
            "instance_name": "test-instance",
            "api_url": "https://evo.example.com",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_get_instance_status(self, client, db, auth_headers):
        instance = EvolutionInstance(
            gym_id=1, instance_name="status-test",
            status=InstanceStatus.CONNECTED, api_url="https://evo.example.com",
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)

        response = client.get(f"/api/v1/evolution/instances/{instance.id}/status", headers=auth_headers)
        assert response.status_code == 200


class TestMessaging:
    def test_send_message(self, client, db, auth_headers):
        instance = EvolutionInstance(
            gym_id=1, instance_name="msg-test",
            status=InstanceStatus.CONNECTED, api_url="https://evo.example.com",
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)

        response = client.post("/api/v1/evolution/send-message", json={
            "instance_id": instance.id,
            "to_number": "+1234567890",
            "message_content": "Hello from Alfit!",
        }, headers=auth_headers)
        assert response.status_code == 200


class TestWebhooks:
    def test_register_webhook(self, client, db, auth_headers):
        instance = EvolutionInstance(
            gym_id=1, instance_name="webhook-test",
            status=InstanceStatus.CONNECTED, api_url="https://evo.example.com",
        )
        db.add(instance)
        db.commit()
        db.refresh(instance)

        response = client.post("/api/v1/evolution/webhooks/register", json={
            "instance_id": instance.id,
            "webhook_url": "https://alfit.example.com/webhooks",
            "events": ["message.received", "message.sent"],
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_incoming_webhook(self, client):
        response = client.post("/api/v1/evolution/webhooks/incoming", json={
            "event_type": "message.received",
            "data": {"from": "+1234567890", "message": "Hi"},
        })
        assert response.status_code == 200
