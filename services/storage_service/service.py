"""Storage Service business logic."""

import uuid
import logging
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException
from services.storage_service.models import StoredFile
from services.storage_service.schemas import FileUploadResponse

logger = logging.getLogger(__name__)


def upload_file(
    db: Session,
    original_name: str,
    mime_type: str | None,
    size_bytes: int | None,
    uploader_id: int,
) -> FileUploadResponse:
    """Store a file record."""
    stored_name = f"{uuid.uuid4().hex}_{original_name}"

    record = StoredFile(
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size_bytes=size_bytes,
        uploader_id=uploader_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return FileUploadResponse(
        id=record.id,
        original_name=record.original_name,
        mime_type=record.mime_type,
        size_bytes=record.size_bytes,
        url=f"/files/{record.id}",
        created_at=record.created_at,
    )


def get_file_info(db: Session, file_id: int) -> FileUploadResponse:
    """Get file info by ID."""
    record = db.query(StoredFile).filter(StoredFile.id == file_id, StoredFile.is_deleted.is_(False)).first()
    if not record:
        raise NotFoundException("File", file_id)

    return FileUploadResponse(
        id=record.id,
        original_name=record.original_name,
        mime_type=record.mime_type,
        size_bytes=record.size_bytes,
        url=f"/files/{record.id}",
        created_at=record.created_at,
    )


def delete_file(db: Session, file_id: int) -> dict:
    """Soft-delete a file."""
    record = db.query(StoredFile).filter(StoredFile.id == file_id).first()
    if not record:
        raise NotFoundException("File", file_id)
    record.is_deleted = True
    db.commit()
    return {"message": "File deleted successfully"}
