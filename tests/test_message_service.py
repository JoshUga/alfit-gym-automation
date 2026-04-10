"""Tests for Message Processing Service."""

import pytest
from unittest.mock import patch
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


class TestEvolutionUpsertWebhook:
    def test_processes_messages_upsert_event(self, client):
        with patch("services.message_service.service._generate_ai_reply", return_value={"response_text": "Thanks!"}), patch(
            "services.message_service.service._send_whatsapp_reply", return_value=None
        ):
            response = client.post(
                "/api/v1/messages/evolution-upsert",
                json={
                    "event": "messages.upsert",
                    "instance": "gym-1",
                    "data": {
                        "key": {"id": "upsert-1", "remoteJid": "5511999999999@s.whatsapp.net"},
                        "message": {"conversation": "Hello from Evolution"},
                    },
                },
            )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["status"] == "processed"
        assert payload["message_id"] == "upsert-1"
        assert payload["reply_status"] == "sent"

    def test_ignores_unsupported_event(self, client):
        response = client.post(
            "/api/v1/messages/evolution-upsert",
            json={
                "event": "connection.update",
                "instance": "gym-1",
                "data": {},
            },
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ignored"

    def test_idempotent_single_reply_for_same_message(self, client):
        with patch("services.message_service.service._generate_ai_reply", return_value={"response_text": "Thanks!"}), patch(
            "services.message_service.service._send_whatsapp_reply", return_value=None
        ) as send_reply_mock:
            payload = {
                "event": "messages.upsert",
                "instance": "gym-1",
                "data": {
                    "key": {"id": "upsert-idem-1", "remoteJid": "5511888888888@s.whatsapp.net"},
                    "message": {"conversation": "Hi coach"},
                },
            }
            first = client.post("/api/v1/messages/evolution-upsert", json=payload)
            second = client.post("/api/v1/messages/evolution-upsert", json=payload)

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["data"]["reply_status"] == "sent"
        assert second.json()["data"]["status"] == "ignored"
        assert send_reply_mock.call_count == 1

    def test_skips_reply_for_from_me_messages(self, client):
        with patch("services.message_service.service._send_whatsapp_reply", return_value=None) as send_reply_mock:
            response = client.post(
                "/api/v1/messages/evolution-upsert",
                json={
                    "event": "messages.upsert",
                    "instance": "gym-1",
                    "data": {
                        "key": {
                            "id": "upsert-from-me-1",
                            "remoteJid": "5511777777777@s.whatsapp.net",
                            "fromMe": True,
                        },
                        "message": {"conversation": "Outbound echo"},
                    },
                },
            )
        assert response.status_code == 200
        assert response.json()["data"]["reply_status"] == "skipped_from_me"
        assert send_reply_mock.call_count == 0


class TestOutboundWhatsApp:
    def test_send_outbound_whatsapp_internal(self, client):
        with patch("services.message_service.service._send_whatsapp_reply", return_value=None) as send_reply_mock:
            response = client.post(
                "/api/v1/messages/send/internal",
                json={
                    "gym_id": 1,
                    "phone_number": "5511888888888",
                    "content": "Reminder message",
                },
            )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "sent"
        assert send_reply_mock.call_count == 1
