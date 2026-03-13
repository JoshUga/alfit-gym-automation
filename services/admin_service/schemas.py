"""Admin Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    admin_id: int
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Any] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ServiceStatus(BaseModel):
    name: str
    status: str
    last_check: Optional[datetime] = None


class SystemHealthResponse(BaseModel):
    services: list[ServiceStatus] = []


class UserRoleUpdate(BaseModel):
    roles: list[str]


class GymStatusUpdate(BaseModel):
    is_active: bool
