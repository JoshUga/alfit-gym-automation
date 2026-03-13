"""Storage Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    id: int
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
