"""Tests for Member Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.member_service.main import app
from services.member_service.routes import get_session
from services.member_service.models import (
    Member,
    MemberGroup,
    MemberGroupAssignment,
    MemberTrainerAssignment,
    MemberStatus,
)


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


class TestAddMember:
    def test_add_member(self, client, auth_headers):
        response = client.post("/api/v1/members", json={
            "gym_id": 1,
            "name": "John Doe",
            "phone_number": "+1234567890",
            "email": "john@example.com",
            "training_days": ["Monday", "Wednesday", "Friday"],
            "target": "Lose 5kg",
            "monthly_payment_amount": 120,
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "John Doe"
        assert data["data"]["status"] == "active"
        assert data["data"]["target"] == "Lose 5kg"
        assert data["data"]["monthly_payment_amount"] == 120

    def test_add_member_without_email(self, client, auth_headers):
        response = client.post("/api/v1/members", json={
            "gym_id": 1,
            "name": "Jane Doe",
            "phone_number": "+0987654321",
            "training_days": ["Tuesday", "Thursday"],
            "target": "Build muscle",
            "monthly_payment_amount": 150,
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_add_member_unauthorized(self, client):
        response = client.post("/api/v1/members", json={
            "gym_id": 1,
            "name": "Test",
            "phone_number": "+1111111111",
            "training_days": ["Monday"],
            "target": "Stay active",
            "monthly_payment_amount": 99,
        })
        assert response.status_code in [401, 403]


class TestGetMember:
    def test_get_member(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Get Member", phone_number="+1111111111", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        response = client.get(f"/api/v1/members/{member.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Get Member"

    def test_get_member_not_found(self, client, auth_headers):
        response = client.get("/api/v1/members/999", headers=auth_headers)
        assert response.status_code == 404


class TestListMembers:
    def test_list_gym_members(self, client, db, auth_headers):
        for i in range(3):
            db.add(Member(gym_id=1, name=f"Member {i}", phone_number=f"+111{i}", status=MemberStatus.ACTIVE))
        db.commit()

        response = client.get("/api/v1/gyms/1/members", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 3

    def test_list_gym_members_empty(self, client, auth_headers):
        response = client.get("/api/v1/gyms/999/members", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 0


class TestUpdateMember:
    def test_update_member(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Old Name", phone_number="+1111111111", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        response = client.put(f"/api/v1/members/{member.id}", json={"name": "New Name"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "New Name"


class TestDeleteMember:
    def test_soft_delete_member(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Delete Me", phone_number="+1111111111", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        response = client.delete(f"/api/v1/members/{member.id}", headers=auth_headers)
        assert response.status_code == 200

        db.refresh(member)
        assert member.status == MemberStatus.SUSPENDED

    def test_delete_not_found(self, client, auth_headers):
        response = client.delete("/api/v1/members/999", headers=auth_headers)
        assert response.status_code == 404


class TestGroups:
    def test_create_group(self, client, auth_headers):
        response = client.post("/api/v1/gyms/1/groups", json={
            "name": "Morning Class",
            "description": "Morning workout group",
        }, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["data"]["name"] == "Morning Class"

    def test_list_groups(self, client, db, auth_headers):
        db.add(MemberGroup(gym_id=1, name="Group A"))
        db.add(MemberGroup(gym_id=1, name="Group B"))
        db.commit()

        response = client.get("/api/v1/gyms/1/groups", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 2


class TestGroupAssignment:
    def test_assign_member_to_group(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Assign Me", phone_number="+1111111111", status=MemberStatus.ACTIVE)
        group = MemberGroup(gym_id=1, name="Test Group")
        db.add(member)
        db.add(group)
        db.commit()
        db.refresh(member)
        db.refresh(group)

        response = client.post(f"/api/v1/groups/{group.id}/members/{member.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_assign_duplicate(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Dup Me", phone_number="+2222222222", status=MemberStatus.ACTIVE)
        group = MemberGroup(gym_id=1, name="Dup Group")
        db.add(member)
        db.add(group)
        db.commit()
        db.refresh(member)
        db.refresh(group)

        client.post(f"/api/v1/groups/{group.id}/members/{member.id}", headers=auth_headers)
        response = client.post(f"/api/v1/groups/{group.id}/members/{member.id}", headers=auth_headers)
        assert response.status_code == 409

    def test_remove_member_from_group(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Remove Me", phone_number="+3333333333", status=MemberStatus.ACTIVE)
        group = MemberGroup(gym_id=1, name="Remove Group")
        db.add(member)
        db.add(group)
        db.commit()
        db.refresh(member)
        db.refresh(group)

        assignment = MemberGroupAssignment(member_id=member.id, group_id=group.id)
        db.add(assignment)
        db.commit()

        response = client.delete(f"/api/v1/groups/{group.id}/members/{member.id}", headers=auth_headers)
        assert response.status_code == 200


class TestMemberPayments:
    def test_create_member_payment(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Pay Me", phone_number="+4444444444", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        response = client.post(
            f"/api/v1/members/{member.id}/payments",
            json={
                "amount": 120,
                "currency": "USD",
                "payment_method": "card",
                "status": "completed",
                "billing_month": "2026-04",
                "note": "Monthly plan",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["member_id"] == member.id
        assert payload["amount"] == 120
        assert payload["billing_month"] == "2026-04"

    def test_create_member_payment_balance_left(self, client, db, auth_headers):
        member = Member(
            gym_id=1,
            name="Balance Check",
            phone_number="+4444000000",
            status=MemberStatus.ACTIVE,
            monthly_payment_amount=200,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

        first = client.post(
            f"/api/v1/members/{member.id}/payments",
            json={"amount": 120, "currency": "USD", "status": "completed", "billing_month": "2026-04"},
            headers=auth_headers,
        )
        assert first.status_code == 200
        assert first.json()["data"]["balance_left"] == 80

        second = client.post(
            f"/api/v1/members/{member.id}/payments",
            json={"amount": 60, "currency": "USD", "status": "completed", "billing_month": "2026-04"},
            headers=auth_headers,
        )
        assert second.status_code == 200
        assert second.json()["data"]["balance_left"] == 20

    def test_list_member_payments(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Pay List", phone_number="+5555555555", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        client.post(
            f"/api/v1/members/{member.id}/payments",
            json={"amount": 90, "currency": "USD", "status": "completed"},
            headers=auth_headers,
        )

        response = client.get(f"/api/v1/members/{member.id}/payments", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1


class TestTrainerAssignments:
    def test_assign_and_list_trainer_assignments(self, client, db, auth_headers):
        member = Member(gym_id=1, name="Assigned Member", phone_number="+6666666666", status=MemberStatus.ACTIVE)
        db.add(member)
        db.commit()
        db.refresh(member)

        assign_response = client.post(
            f"/api/v1/members/{member.id}/trainer-assignments",
            json={"trainer_user_id": 42},
            headers=auth_headers,
        )
        assert assign_response.status_code == 200
        assert assign_response.json()["data"]["trainer_user_id"] == 42

        list_response = client.get("/api/v1/gyms/1/trainer-assignments", headers=auth_headers)
        assert list_response.status_code == 200
        assert len(list_response.json()["data"]) == 1

    def test_trainer_only_sees_assigned_members(self, client, db):
        member_a = Member(gym_id=1, name="Assigned", phone_number="+7777000000", status=MemberStatus.ACTIVE)
        member_b = Member(gym_id=1, name="Unassigned", phone_number="+7777000001", status=MemberStatus.ACTIVE)
        db.add(member_a)
        db.add(member_b)
        db.commit()
        db.refresh(member_a)
        db.refresh(member_b)

        db.add(MemberTrainerAssignment(member_id=member_a.id, trainer_user_id=99))
        db.commit()

        trainer_token = create_access_token(
            {"sub": "99", "email": "trainer@example.com", "roles": ["gym_staff"], "owner_id": 1}
        )
        trainer_headers = {"Authorization": f"Bearer {trainer_token}"}

        list_response = client.get("/api/v1/gyms/1/members", headers=trainer_headers)
        assert list_response.status_code == 200
        payload = list_response.json()["data"]
        assert len(payload) == 1
        assert payload[0]["name"] == "Assigned"
