"""Tests for Analytics & Reporting Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.analytics_service.main import app
from services.analytics_service.routes import get_session
from services.analytics_service.models import MessageLog, MessageType


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


class TestKPIs:
    def test_get_kpis(self, client, auth_headers):
        response = client.get("/api/v1/analytics/kpis?gym_id=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert "messages_sent_7d" in data
        assert "messages_sent_30d" in data


class TestMessageVolume:
    def test_get_message_volume(self, client, auth_headers):
        response = client.get("/api/v1/analytics/message-volume?gym_id=1", headers=auth_headers)
        assert response.status_code == 200


class TestMessageLogs:
    def test_get_message_logs(self, client, db, auth_headers):
        db.add(MessageLog(
            gym_id=1, phone_number_id=1, sender="+111", recipient="+222",
            content="Test", message_type=MessageType.OUTGOING, status="sent",
        ))
        db.commit()

        response = client.get("/api/v1/logs/messages?gym_id=1", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1
