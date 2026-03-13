"""Tests for Email Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.email_service.main import app
from services.email_service.routes import get_session
from services.email_service.models import EmailLog, EmailStatus


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
