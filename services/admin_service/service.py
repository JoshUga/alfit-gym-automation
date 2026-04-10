"""Admin Service business logic."""

import logging
import os
import secrets
import re
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
SERVICE_ADMIN_PASSWORD = os.getenv("SERVICE_ADMIN_PASSWORD", "change-this-service-admin-password-now")

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

BACKUP_TABLE_SET = set(BACKUP_TABLES)


def _is_safe_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value or ""))


def _table_candidates(table_name: str) -> list[str]:
    if "." not in table_name:
        return [table_name]
    _, plain_name = table_name.split(".", 1)
    return [table_name, plain_name]


def _safe_execute_count(db: Session, queries: list[str]) -> int:
    for sql_query in queries:
        try:
            result = db.execute(text(sql_query)).scalar()
            return int(result or 0)
        except Exception:
            continue
    return 0


def _fetch_rows_with_fallback(db: Session, queries: list[str]) -> list[dict]:
    for sql_query in queries:
        try:
            return [dict(row) for row in db.execute(text(sql_query)).mappings().all()]
        except Exception:
            continue
    return []


def _clear_table_with_fallback(db: Session, table_name: str) -> bool:
    for candidate in _table_candidates(table_name):
        try:
            db.execute(text(f"DELETE FROM {candidate}"))
            return True
        except Exception:
            continue
    return False


def _insert_row_with_fallback(db: Session, table_name: str, row: dict) -> bool:
    columns = [
        str(column)
        for column in row.keys()
        if _is_safe_identifier(str(column))
    ]
    if not columns:
        return False

    safe_row = {column: row.get(column) for column in columns}
    placeholders = ", ".join([f":{column}" for column in columns])
    for candidate in _table_candidates(table_name):
        sql = f"INSERT INTO {candidate} ({', '.join(columns)}) VALUES ({placeholders})"
        try:
            db.execute(text(sql), safe_row)
            return True
        except Exception:
            continue
    return False


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
    username_ok = secrets.compare_digest(str(x_admin_username or ""), SERVICE_ADMIN_USERNAME)
    password_ok = secrets.compare_digest(str(x_admin_password or ""), SERVICE_ADMIN_PASSWORD)
    if not username_ok or not password_ok:
        raise ValidationException("Invalid service admin credentials")
    return True


def service_admin_login(username: str, password: str) -> bool:
    return secrets.compare_digest(username, SERVICE_ADMIN_USERNAME) and secrets.compare_digest(password, SERVICE_ADMIN_PASSWORD)


def _safe_count(db: Session, sql_query: str) -> int:
    try:
        result = db.execute(text(sql_query)).scalar()
        return int(result or 0)
    except Exception:
        return 0


def get_service_admin_overview(db: Session) -> ServiceAdminOverviewResponse:
    return ServiceAdminOverviewResponse(
        total_gyms=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_gym.gyms",
            "SELECT COUNT(*) FROM gyms",
        ]),
        active_gyms=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_gym.gyms WHERE is_active = 1",
            "SELECT COUNT(*) FROM gyms WHERE is_active = 1",
        ]),
        total_members=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_member.members",
            "SELECT COUNT(*) FROM members",
        ]),
        active_members=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_member.members WHERE status = 'active'",
            "SELECT COUNT(*) FROM members WHERE status = 'active'",
        ]),
        total_attendance_records=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_attendance.attendance_records",
            "SELECT COUNT(*) FROM attendance_records",
        ]),
        total_scheduled_notifications=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_notification.scheduled_notifications",
            "SELECT COUNT(*) FROM scheduled_notifications",
        ]),
        total_processed_messages=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_message.processed_messages",
            "SELECT COUNT(*) FROM processed_messages",
        ]),
        total_email_logs=_safe_execute_count(db, [
            "SELECT COUNT(*) FROM alfit_email.email_logs",
            "SELECT COUNT(*) FROM email_logs",
        ]),
    )


def list_service_admin_gyms(db: Session) -> list[ServiceAdminGymItem]:
    rows = _fetch_rows_with_fallback(db, [
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
        """,
        """
        SELECT
            g.id,
            g.name,
            g.email,
            g.phone,
            g.is_active,
            COALESCE(m.member_count, 0) AS member_count
        FROM gyms g
        LEFT JOIN (
            SELECT gym_id, COUNT(*) AS member_count
            FROM members
            GROUP BY gym_id
        ) m ON m.gym_id = g.id
        ORDER BY g.id DESC
        """,
    ])

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
        if table not in BACKUP_TABLE_SET:
            continue
        rows = _fetch_rows_with_fallback(
            db,
            [f"SELECT * FROM {candidate}" for candidate in _table_candidates(table)],
        )
        payload[table] = rows

    backup = SystemBackup(label=label, status="completed", payload=payload)
    db.add(backup)
    db.commit()
    db.refresh(backup)
    return ServiceBackupResponse.model_validate(backup)


def list_system_backups(db: Session, limit: int = 100) -> list[ServiceBackupResponse]:
    backups = db.query(SystemBackup).order_by(SystemBackup.created_at.desc()).limit(limit).all()
    return [ServiceBackupResponse.model_validate(item) for item in backups]


def _restore_table(db: Session, table_name: str, rows: list[dict], clear_existing: bool) -> bool:
    if table_name not in BACKUP_TABLE_SET:
        return False
    if clear_existing and not _clear_table_with_fallback(db, table_name):
        return False

    if not rows:
        return True

    for row in rows:
        if not row:
            continue
        _insert_row_with_fallback(db, table_name, row)
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


def purge_system_data(db: Session, include_backups: bool = False) -> dict:
    cleared_tables = 0
    for table_name in BACKUP_TABLES:
        if _clear_table_with_fallback(db, table_name):
            cleared_tables += 1

    if include_backups:
        try:
            cleared_tables += db.query(SystemBackup).delete()
        except Exception:
            pass
    db.commit()
    return {"cleared_tables": cleared_tables, "include_backups": include_backups}
