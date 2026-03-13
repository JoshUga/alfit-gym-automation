"""Tests for Storage Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from shared.database import Base
from shared.auth import create_access_token
from services.storage_service.main import app
from services.storage_service.routes import get_session
from services.storage_service.models import StoredFile


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


class TestFileInfo:
    def test_get_file_info(self, client, db, auth_headers):
        stored = StoredFile(
            original_name="photo.jpg",
            stored_name="uuid-photo.jpg",
            mime_type="image/jpeg",
            size_bytes=12345,
            uploader_id=1,
            is_deleted=False,
        )
        db.add(stored)
        db.commit()
        db.refresh(stored)

        response = client.get(f"/api/v1/files/{stored.id}", headers=auth_headers)
        assert response.status_code == 200

    def test_get_deleted_file(self, client, db, auth_headers):
        stored = StoredFile(
            original_name="deleted.jpg",
            stored_name="uuid-deleted.jpg",
            mime_type="image/jpeg",
            size_bytes=100,
            uploader_id=1,
            is_deleted=True,
        )
        db.add(stored)
        db.commit()
        db.refresh(stored)

        response = client.get(f"/api/v1/files/{stored.id}", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_file(self, client, db, auth_headers):
        stored = StoredFile(
            original_name="todelete.jpg",
            stored_name="uuid-todelete.jpg",
            mime_type="image/jpeg",
            size_bytes=100,
            uploader_id=1,
            is_deleted=False,
        )
        db.add(stored)
        db.commit()
        db.refresh(stored)

        response = client.delete(f"/api/v1/files/{stored.id}", headers=auth_headers)
        assert response.status_code == 200
