"""Tests for Email Service."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.email_service.main import app
from services.email_service.routes import get_session
from services.email_service.models import EmailLog, EmailStatus, SMTPAccount
from services.email_service import service as email_service


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


class TestSendEmail:
    def test_send_email(self, client, auth_headers):
        response = client.post("/api/v1/email/send", json={
            "recipient": "user@example.com",
            "subject": "Welcome!",
            "template_name": "welcome",
            "template_data": {"name": "John"},
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_list_email_logs(self, client, db, auth_headers):
        db.add(EmailLog(
            recipient="log@example.com",
            subject="Test",
            template_name="test",
            status=EmailStatus.SENT,
            provider="sendgrid",
        ))
        db.commit()

        response = client.get("/api/v1/email/logs", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1

    def test_preview_template(self, client, auth_headers):
        response = client.post("/api/v1/email/templates/preview", json={
            "template_name": "welcome",
            "template_data": {"name": "Jane"},
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_smtp_rotation_uses_multiple_accounts(self, client, auth_headers):
        first = client.post("/api/v1/email/smtp/accounts", json={
            "gym_id": 1,
            "name": "Primary",
            "emailengine_account_id": "primary-account",
        }, headers=auth_headers)
        second = client.post("/api/v1/email/smtp/accounts", json={
            "gym_id": 1,
            "name": "Backup",
            "emailengine_account_id": "backup-account",
        }, headers=auth_headers)
        assert first.status_code == 200
        assert second.status_code == 200

        with patch("services.email_service.service._send_via_emailengine", return_value="emailengine"):
            one = client.post("/api/v1/email/send/internal", json={
                "gym_id": 1,
                "recipient": "a@example.com",
                "subject": "One",
                "template_name": "reminder",
                "template_data": {"content": "one"},
            })
            two = client.post("/api/v1/email/send/internal", json={
                "gym_id": 1,
                "recipient": "b@example.com",
                "subject": "Two",
                "template_name": "reminder",
                "template_data": {"content": "two"},
            })
        assert one.status_code == 200
        assert two.status_code == 200

        logs = client.get("/api/v1/email/logs", headers=auth_headers)
        assert logs.status_code == 200
        assert len(logs.json()["data"]) >= 2

    def test_smtp_health_check_endpoint(self, client, auth_headers):
        account = client.post("/api/v1/email/smtp/accounts", json={
            "gym_id": 1,
            "name": "Health",
            "emailengine_account_id": "health-account",
        }, headers=auth_headers)
        assert account.status_code == 200
        account_id = account.json()["data"]["id"]

        with patch("services.email_service.service._check_smtp_account_health", return_value="healthy"):
            response = client.post("/api/v1/email/smtp/health-check", json={
                "gym_id": 1,
                "account_id": account_id,
            }, headers=auth_headers)
        assert response.status_code == 200
        payload = response.json()["data"]["results"]
        assert len(payload) == 1
        assert payload[0]["health_status"] == "healthy"

    def test_auto_initialize_emailengine_from_env(self, db, monkeypatch):
        monkeypatch.setenv("EMAILENGINE_AUTO_INIT", "true")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USERNAME", "noreply@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret")
        monkeypatch.setenv("SMTP_GYM_ID", "7")
        monkeypatch.setenv("SMTP_ACCOUNT_NAME", "Auto SMTP")
        monkeypatch.delenv("EMAILENGINE_API_TOKEN", raising=False)

        result = email_service.auto_initialize_emailengine(db)
        assert result["initialized"] is True
        assert result["token_generated"] is True

        account = db.query(SMTPAccount).filter(SMTPAccount.gym_id == 7).first()
        assert account is not None
        assert account.name == "Auto SMTP"
        assert account.emailengine_account_id == "bootstrap-noreplyexamplecom"
