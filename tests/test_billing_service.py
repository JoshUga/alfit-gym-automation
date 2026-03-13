"""Tests for Billing Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.billing_service.main import app
from services.billing_service.routes import get_session
from services.billing_service.models import SubscriptionPlan, Subscription, SubscriptionStatus


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


class TestPlans:
    def test_create_plan(self, client, auth_headers):
        response = client.post("/api/v1/plans", json={
            "name": "Basic Plan",
            "price": 29.99,
            "features": {"feature1": True},
            "max_phone_numbers": 1,
            "max_ai_messages": 100,
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Basic Plan"

    def test_list_plans(self, client, db, auth_headers):
        plan = SubscriptionPlan(name="Pro", price=79.99, features={"feature1": True}, max_phone_numbers=5, max_ai_messages=1000)
        db.add(plan)
        db.commit()

        response = client.get("/api/v1/plans", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) >= 1


class TestSubscriptions:
    def test_create_subscription(self, client, db, auth_headers):
        plan = SubscriptionPlan(name="Test Plan", price=49.99, features={}, max_phone_numbers=3, max_ai_messages=500)
        db.add(plan)
        db.commit()
        db.refresh(plan)

        response = client.post("/api/v1/subscriptions", json={
            "gym_id": 1,
            "plan_id": plan.id,
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_get_subscription(self, client, db, auth_headers):
        plan = SubscriptionPlan(name="Get Plan", price=29.99, features={}, max_phone_numbers=1, max_ai_messages=100)
        db.add(plan)
        db.commit()
        db.refresh(plan)

        sub = Subscription(gym_id=1, plan_id=plan.id, status=SubscriptionStatus.ACTIVE)
        db.add(sub)
        db.commit()
        db.refresh(sub)

        response = client.get(f"/api/v1/subscriptions/{sub.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_cancel_subscription(self, client, db, auth_headers):
        plan = SubscriptionPlan(name="Cancel Plan", price=29.99, features={}, max_phone_numbers=1, max_ai_messages=100)
        db.add(plan)
        db.commit()
        db.refresh(plan)

        sub = Subscription(gym_id=1, plan_id=plan.id, status=SubscriptionStatus.ACTIVE)
        db.add(sub)
        db.commit()
        db.refresh(sub)

        response = client.put(f"/api/v1/subscriptions/{sub.id}/cancel", headers=auth_headers)
        assert response.status_code == 200
