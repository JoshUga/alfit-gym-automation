"""Tests for Message Processing Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.message_service.main import app
from services.message_service.routes import get_session
from services.message_service.models import ProcessedMessage


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


class TestProcessMessage:
    def test_process_message(self, client, auth_headers):
        response = client.post("/api/v1/messages/process", json={
            "message_id": "msg-001",
            "gym_id": 1,
            "phone_number_id": 1,
            "sender": "+1234567890",
            "content": "Hello, I want to join",
            "timestamp": "2025-01-01T10:00:00",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_process_duplicate_message(self, client, db, auth_headers):
        db.add(ProcessedMessage(
            message_id="msg-dup",
            gym_id=1,
            phone_number_id=1,
            sender="+111",
            content="Dup",
            is_processed=True,
        ))
        db.commit()

        response = client.post("/api/v1/messages/process", json={
            "message_id": "msg-dup",
            "gym_id": 1,
            "phone_number_id": 1,
            "sender": "+111",
            "content": "Dup",
            "timestamp": "2025-01-01T10:00:00",
        }, headers=auth_headers)
        assert response.status_code in [200, 409]

    def test_list_processed(self, client, db, auth_headers):
        db.add(ProcessedMessage(
            message_id="msg-list",
            gym_id=1,
            phone_number_id=1,
            sender="+222",
            content="List test",
            is_processed=True,
        ))
        db.commit()

        response = client.get("/api/v1/messages/processed?gym_id=1", headers=auth_headers)
        assert response.status_code == 200
