"""Tests for Notification Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.notification_service.main import app
from services.notification_service.routes import get_session
from services.notification_service.models import NotificationTemplate, ScheduledNotification


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


class TestTemplates:
    def test_create_template(self, client, auth_headers):
        response = client.post("/api/v1/templates", json={
            "gym_id": 1,
            "name": "Welcome Message",
            "content": "Hello {{member_name}}, welcome to {{gym_name}}!",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Welcome Message"

    def test_get_template(self, client, db, auth_headers):
        template = NotificationTemplate(gym_id=1, name="Test", content="Hello!")
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.get(f"/api/v1/templates/{template.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_list_templates(self, client, db, auth_headers):
        db.add(NotificationTemplate(gym_id=1, name="T1", content="Content 1"))
        db.add(NotificationTemplate(gym_id=1, name="T2", content="Content 2"))
        db.commit()

        response = client.get("/api/v1/gyms/1/templates", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2

    def test_update_template(self, client, db, auth_headers):
        template = NotificationTemplate(gym_id=1, name="Old", content="Old content")
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.put(f"/api/v1/templates/{template.id}", json={
            "name": "Updated",
            "content": "New content",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Updated"

    def test_delete_template(self, client, db, auth_headers):
        template = NotificationTemplate(gym_id=1, name="Del", content="Delete me")
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.delete(f"/api/v1/templates/{template.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_preview_template(self, client, db, auth_headers):
        template = NotificationTemplate(gym_id=1, name="Preview", content="Hello {{member_name}}, welcome to {{gym_name}}!")
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.post("/api/v1/templates/preview", json={
            "template_id": template.id,
            "variables": {"member_name": "John", "gym_name": "FitClub"},
        }, headers=auth_headers)
        assert response.status_code == 200
        assert "John" in response.json()["data"]["rendered_content"]
        assert "FitClub" in response.json()["data"]["rendered_content"]


class TestScheduling:
    def test_schedule_notification(self, client, db, auth_headers):
        template = NotificationTemplate(gym_id=1, name="Sched", content="Scheduled message")
        db.add(template)
        db.commit()
        db.refresh(template)

        response = client.post("/api/v1/notifications/schedule", json={
            "gym_id": 1,
            "template_id": template.id,
            "target_type": "member",
            "target_id": 1,
            "schedule_type": "one_time",
            "send_time": "2025-12-31T10:00:00",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_list_scheduled(self, client, auth_headers):
        response = client.get("/api/v1/notifications/scheduled", headers=auth_headers)
        assert response.status_code == 200
