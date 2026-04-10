"""Admin Service business logic."""

import logging
import os
from datetime import datetime, timezone
from fastapi import Header
from sqlalchemy import text
from sqlalchemy.orm import Session
from shared.exceptions import ValidationException
from services.admin_service.models import AuditLog, SystemBackup
from services.admin_service.schemas import (
    AuditLogResponse,
    SystemHealthResponse,
    ServiceStatus,
    ServiceAdminOverviewResponse,
    ServiceAdminGymItem,
    ServiceBackupResponse,
    ServiceBackupRestoreResponse,
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

SERVICE_ADMIN_USERNAME = os.getenv("SERVICE_ADMIN_USERNAME", "service-admin")
SERVICE_ADMIN_PASSWORD = os.getenv("SERVICE_ADMIN_PASSWORD", "service-admin-2026")

BACKUP_TABLES = [
    "alfit_gym.gyms",
    "alfit_member.members",
    "alfit_member.member_groups",
    "alfit_member.member_group_assignments",
    "alfit_member.member_payments",
    "alfit_attendance.attendance_records",
    "alfit_notification.notification_templates",
    "alfit_notification.scheduled_notifications",
    "alfit_message.processed_messages",
    "alfit_email.email_logs",
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


def require_service_admin(
    x_admin_username: str | None = Header(default=None, alias="X-Admin-Username"),
    x_admin_password: str | None = Header(default=None, alias="X-Admin-Password"),
) -> bool:
    if x_admin_username != SERVICE_ADMIN_USERNAME or x_admin_password != SERVICE_ADMIN_PASSWORD:
        raise ValidationException("Invalid service admin credentials")
    return True


def service_admin_login(username: str, password: str) -> bool:
    return username == SERVICE_ADMIN_USERNAME and password == SERVICE_ADMIN_PASSWORD


def _safe_count(db: Session, sql_query: str) -> int:
    try:
        result = db.execute(text(sql_query)).scalar()
        return int(result or 0)
    except Exception:
        return 0


def get_service_admin_overview(db: Session) -> ServiceAdminOverviewResponse:
    return ServiceAdminOverviewResponse(
        total_gyms=_safe_count(db, "SELECT COUNT(*) FROM alfit_gym.gyms"),
        active_gyms=_safe_count(db, "SELECT COUNT(*) FROM alfit_gym.gyms WHERE is_active = 1"),
        total_members=_safe_count(db, "SELECT COUNT(*) FROM alfit_member.members"),
        active_members=_safe_count(db, "SELECT COUNT(*) FROM alfit_member.members WHERE status = 'active'"),
        total_attendance_records=_safe_count(db, "SELECT COUNT(*) FROM alfit_attendance.attendance_records"),
        total_scheduled_notifications=_safe_count(db, "SELECT COUNT(*) FROM alfit_notification.scheduled_notifications"),
        total_processed_messages=_safe_count(db, "SELECT COUNT(*) FROM alfit_message.processed_messages"),
        total_email_logs=_safe_count(db, "SELECT COUNT(*) FROM alfit_email.email_logs"),
    )


def list_service_admin_gyms(db: Session) -> list[ServiceAdminGymItem]:
    try:
        rows = db.execute(
            text(
                """
                SELECT
                    g.id,
                    g.name,
                    g.email,
                    g.phone,
                    g.is_active,
                    COALESCE(m.member_count, 0) AS member_count
                FROM alfit_gym.gyms g
                LEFT JOIN (
                    SELECT gym_id, COUNT(*) AS member_count
                    FROM alfit_member.members
                    GROUP BY gym_id
                ) m ON m.gym_id = g.id
                ORDER BY g.id DESC
                """
            )
        ).mappings().all()
    except Exception:
        return []

    return [
        ServiceAdminGymItem(
            id=int(row.get("id") or 0),
            name=str(row.get("name") or ""),
            email=str(row.get("email") or "") or None,
            phone=str(row.get("phone") or "") or None,
            is_active=bool(row.get("is_active")),
            member_count=int(row.get("member_count") or 0),
        )
        for row in rows
        if row.get("id") is not None
    ]


def create_system_backup(db: Session, label: str | None = None) -> ServiceBackupResponse:
    payload: dict[str, list[dict]] = {}
    for table in BACKUP_TABLES:
        try:
            rows = db.execute(text(f"SELECT * FROM {table}")).mappings().all()
            payload[table] = [dict(row) for row in rows]
        except Exception:
            payload[table] = []

    backup = SystemBackup(label=label, status="completed", payload=payload)
    db.add(backup)
    db.commit()
    db.refresh(backup)
    return ServiceBackupResponse.model_validate(backup)


def list_system_backups(db: Session, limit: int = 100) -> list[ServiceBackupResponse]:
    backups = db.query(SystemBackup).order_by(SystemBackup.created_at.desc()).limit(limit).all()
    return [ServiceBackupResponse.model_validate(item) for item in backups]


def _restore_table(db: Session, table_name: str, rows: list[dict], clear_existing: bool) -> bool:
    try:
        if clear_existing:
            db.execute(text(f"DELETE FROM {table_name}"))
    except Exception:
        return False

    if not rows:
        return True

    for row in rows:
        if not row:
            continue
        columns = list(row.keys())
        placeholders = ", ".join([f":{column}" for column in columns])
        sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        try:
            db.execute(text(sql), row)
        except Exception:
            continue
    return True


def restore_system_backup(
    db: Session, backup_id: int, clear_existing: bool = False
) -> ServiceBackupRestoreResponse:
    backup = db.query(SystemBackup).filter(SystemBackup.id == backup_id).first()
    if not backup:
        raise ValidationException("Backup not found")
    payload = backup.payload if isinstance(backup.payload, dict) else {}

    restored_tables = 0
    for table_name, rows in payload.items():
        table_rows = rows if isinstance(rows, list) else []
        ok = _restore_table(db, table_name, table_rows, clear_existing)
        if ok:
            restored_tables += 1
    db.commit()
    return ServiceBackupRestoreResponse(backup_id=backup_id, restored_tables=restored_tables)
