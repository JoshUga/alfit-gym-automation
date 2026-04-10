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


class ServiceAdminLoginRequest(BaseModel):
    username: str
    password: str


class ServiceAdminLoginResponse(BaseModel):
    authenticated: bool


class ServiceAdminOverviewResponse(BaseModel):
    total_gyms: int
    active_gyms: int
    total_members: int
    active_members: int
    total_attendance_records: int
    total_scheduled_notifications: int
    total_processed_messages: int
    total_email_logs: int


class ServiceAdminGymItem(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    member_count: int = 0


class ServiceBackupCreateRequest(BaseModel):
    label: Optional[str] = None


class ServiceBackupResponse(BaseModel):
    id: int
    label: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ServiceBackupRestoreRequest(BaseModel):
    clear_existing: bool = False


class ServiceBackupRestoreResponse(BaseModel):
    backup_id: int
    restored_tables: int
