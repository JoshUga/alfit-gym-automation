"""Tests for AI Auto-Responder Service."""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.ai_service.main import app
from services.ai_service.routes import get_session
from services.ai_service.models import AIConfig, AIProvider


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


class TestAIConfig:
    def test_create_config_disabled(self, client, auth_headers):
        response = client.post("/api/v1/ai/configs", json={
            "gym_id": 1,
            "provider": "openai",
            "api_key": "test-key-123",
            "model_name": "gpt-4",
            "base_prompt": "You are a helpful gym assistant.",
        }, headers=auth_headers)
        assert response.status_code == 422

    def test_runtime_config(self, client, auth_headers, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "openrouter")
        monkeypatch.setenv("AI_MODEL", "openai/gpt-4o-mini")
        monkeypatch.setenv("OPENROUTER_API_KEY", "dummy-key")
        monkeypatch.setenv("AI_BASE_PROMPT", "You are the assistant.")

        response = client.get("/api/v1/ai/runtime-config", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["provider"] == "openrouter"
        assert data["configured"] is True

    def test_list_configs(self, client, db, auth_headers):
        db.add(AIConfig(gym_id=1, provider=AIProvider.OPENAI, api_key_encrypted="enc", model_name="gpt-4", base_prompt="Hi"))
        db.commit()

        response = client.get("/api/v1/gyms/1/ai/configs", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"] == []

    def test_generate_response(self, client, auth_headers, monkeypatch):
        monkeypatch.setenv("AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
        monkeypatch.setenv("AI_BASE_PROMPT", "You are a gym assistant.")

        response = client.post("/api/v1/ai/generate-response", json={
            "gym_id": 1,
            "phone_number_id": 1,
            "incoming_message": "What are your hours?",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["response_text"]
