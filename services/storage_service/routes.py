"""Storage Service API routes."""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.storage_service.schemas import FileUploadResponse
from services.storage_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/upload", response_model=APIResponse[FileUploadResponse])
async def upload_file(
    file: UploadFile = File(...),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Upload a file. Reads content to determine size; for large files consider streaming."""
    size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    while chunk := await file.read(chunk_size):
        size += len(chunk)
    result = service.upload_file(
        db,
        original_name=file.filename or "unknown",
        mime_type=file.content_type,
        size_bytes=size,
        uploader_id=current_user.user_id,
    )
    return APIResponse(data=result, message="File uploaded successfully")


@router.get("/files/{file_id}", response_model=APIResponse[FileUploadResponse])
def get_file_info(
    file_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get file info."""
    result = service.get_file_info(db, file_id)
    return APIResponse(data=result)


@router.delete("/files/{file_id}", response_model=APIResponse)
def delete_file(
    file_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete a file."""
    result = service.delete_file(db, file_id)
    return APIResponse(message=result["message"])
