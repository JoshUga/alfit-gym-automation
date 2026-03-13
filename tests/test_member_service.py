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
from services.member_service.models import Member, MemberGroup, MemberGroupAssignment, MemberStatus


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
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "John Doe"
        assert data["data"]["status"] == "active"

    def test_add_member_without_email(self, client, auth_headers):
        response = client.post("/api/v1/members", json={
            "gym_id": 1,
            "name": "Jane Doe",
            "phone_number": "+0987654321",
        }, headers=auth_headers)
        assert response.status_code == 200

    def test_add_member_unauthorized(self, client):
        response = client.post("/api/v1/members", json={
            "gym_id": 1,
            "name": "Test",
            "phone_number": "+1111111111",
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
