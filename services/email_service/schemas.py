"""Email Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime


class SendEmailRequest(BaseModel):
    recipient: EmailStr
    subject: str
    template_name: str
    template_data: Optional[dict] = None


class EmailLogResponse(BaseModel):
    id: int
    recipient: str
    subject: str
    template_name: Optional[str] = None
    status: str
    provider: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EmailPreviewRequest(BaseModel):
    template_name: str
    template_data: Optional[dict] = None


class EmailPreviewResponse(BaseModel):
    subject: Optional[str] = None
    html_content: str
