"""Admin Service business logic."""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException
from services.admin_service.models import AuditLog
from services.admin_service.schemas import (
    AuditLogResponse,
    SystemHealthResponse,
    ServiceStatus,
)

logger = logging.getLogger(__name__)

SERVICE_NAMES = [
    "auth-service",
    "gym-service",
    "member-service",
    "notification-service",
    "ai-service",
    "billing-service",
    "analytics-service",
    "admin-service",
    "storage-service",
    "email-service",
    "message-service",
]


def list_audit_logs(db: Session, limit: int = 100) -> list[AuditLogResponse]:
    """List recent audit logs."""
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [AuditLogResponse.model_validate(log) for log in logs]


def create_audit_log(
    db: Session,
    admin_id: int,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> AuditLogResponse:
    """Create an audit log entry."""
    log = AuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return AuditLogResponse.model_validate(log)


def get_system_health() -> SystemHealthResponse:
    """Get system health overview (placeholder)."""
    now = datetime.now(timezone.utc)
    statuses = [
        ServiceStatus(name=name, status="healthy", last_check=now)
        for name in SERVICE_NAMES
    ]
    return SystemHealthResponse(services=statuses)
