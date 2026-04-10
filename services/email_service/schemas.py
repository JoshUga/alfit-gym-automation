"""Email Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional, Any
from datetime import datetime


class SendEmailRequest(BaseModel):
    gym_id: Optional[int] = None
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


class SMTPAccountCreate(BaseModel):
    gym_id: Optional[int] = None
    name: str
    emailengine_account_id: str
    is_active: bool = True


class SMTPAccountResponse(BaseModel):
    id: int
    gym_id: Optional[int] = None
    name: str
    emailengine_account_id: str
    is_active: bool
    health_status: str
    last_health_check_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SMTPHealthCheckRequest(BaseModel):
    gym_id: Optional[int] = None
    account_id: Optional[int] = None


class SMTPHealthCheckResult(BaseModel):
    account_id: int
    name: str
    health_status: str
    checked_at: datetime


class SMTPHealthCheckResponse(BaseModel):
    results: list[SMTPHealthCheckResult]
