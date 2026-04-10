"""Notification Service business logic."""

import json
import os
from datetime import datetime, timedelta, date, UTC
import httpx
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ValidationException
from services.notification_service.models import (
    NotificationTemplate,
    ScheduledNotification,
    NotificationStatus,
    NotificationDispatchLog,
)
from services.notification_service.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    SessionReminderDispatchResponse,
)
from services.member_service.models import Member, MemberStatus
from services.attendance_service.models import AttendanceRecord, AttendanceStatus

MESSAGE_SERVICE_URL = os.getenv("MESSAGE_SERVICE_URL", "http://message-service:8000").rstrip("/")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://email-service:8000").rstrip("/")


def create_template(db: Session, data: TemplateCreate) -> TemplateResponse:
    """Create a notification template."""
    template = NotificationTemplate(
        gym_id=data.gym_id,
        name=data.name,
        content=data.content,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


def get_template(db: Session, template_id: int) -> TemplateResponse:
    """Get a template by ID."""
    template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    if not template:
        raise NotFoundException("NotificationTemplate", template_id)
    return TemplateResponse.model_validate(template)


def list_templates(db: Session, gym_id: int) -> list[TemplateResponse]:
    """List all templates for a gym."""
    templates = db.query(NotificationTemplate).filter(NotificationTemplate.gym_id == gym_id).all()
    return [TemplateResponse.model_validate(t) for t in templates]


def update_template(db: Session, template_id: int, data: TemplateUpdate) -> TemplateResponse:
    """Update a template."""
    template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    if not template:
        raise NotFoundException("NotificationTemplate", template_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return TemplateResponse.model_validate(template)


def delete_template(db: Session, template_id: int) -> dict:
    """Delete a template."""
    template = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    if not template:
        raise NotFoundException("NotificationTemplate", template_id)
    db.delete(template)
    db.commit()
    return {"message": "Template deleted successfully"}


def preview_template(content: str, variables: dict | None = None) -> dict:
    """Preview a template with variable substitution using {{key}} syntax."""
    rendered = content
    if variables:
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            rendered = rendered.replace(placeholder, str(value))
    return {"rendered_content": rendered}


def schedule_notification(db: Session, data: ScheduleCreate) -> ScheduleResponse:
    """Schedule a notification."""
    template = db.query(NotificationTemplate).filter(NotificationTemplate.id == data.template_id).first()
    if not template:
        raise NotFoundException("NotificationTemplate", data.template_id)

    if data.schedule_type == "one_time" and not data.send_time:
        raise ValidationException("send_time is required for one-time notifications")
    if data.schedule_type == "recurring" and not data.cron_expression:
        raise ValidationException("cron_expression is required for recurring notifications")

    notification = ScheduledNotification(
        gym_id=data.gym_id,
        template_id=data.template_id,
        target_type=data.target_type,
        target_id=data.target_id,
        schedule_type=data.schedule_type,
        send_time=data.send_time,
        cron_expression=data.cron_expression,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return ScheduleResponse.model_validate(notification)


def list_scheduled_notifications(db: Session, gym_id: int | None = None) -> list[ScheduleResponse]:
    """List scheduled notifications for a gym."""
    query = db.query(ScheduledNotification)
    if gym_id is not None:
        query = query.filter(ScheduledNotification.gym_id == gym_id)
    notifications = query.all()
    return [ScheduleResponse.model_validate(n) for n in notifications]


def update_scheduled_notification(
    db: Session, schedule_id: int, data: ScheduleUpdate
) -> ScheduleResponse:
    """Update a scheduled notification."""
    notification = (
        db.query(ScheduledNotification).filter(ScheduledNotification.id == schedule_id).first()
    )
    if not notification:
        raise NotFoundException("ScheduledNotification", schedule_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(notification, field, value)

    db.commit()
    db.refresh(notification)
    return ScheduleResponse.model_validate(notification)


def cancel_notification(db: Session, schedule_id: int) -> dict:
    """Cancel a scheduled notification."""
    notification = (
        db.query(ScheduledNotification).filter(ScheduledNotification.id == schedule_id).first()
    )
    if not notification:
        raise NotFoundException("ScheduledNotification", schedule_id)
    notification.status = NotificationStatus.CANCELLED
    db.commit()
    return {"message": "Notification cancelled successfully"}


def _normalize_day_name(day: str | None) -> str:
    value = str(day or "").strip().lower()
    aliases = {
        "mon": "monday",
        "tue": "tuesday",
        "tues": "tuesday",
        "wed": "wednesday",
        "thu": "thursday",
        "thur": "thursday",
        "thurs": "thursday",
        "fri": "friday",
        "sat": "saturday",
        "sun": "sunday",
    }
    return aliases.get(value, value)


def _parse_training_days(raw_value: str | None) -> set[str]:
    if not raw_value:
        return set()
    try:
        payload = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return set()
    if not isinstance(payload, list):
        return set()
    return {_normalize_day_name(str(day)) for day in payload if str(day).strip()}


def _already_dispatched(
    db: Session, gym_id: int, member_id: int, channel: str, kind: str, dispatch_date: date
) -> bool:
    existing = (
        db.query(NotificationDispatchLog)
        .filter(
            NotificationDispatchLog.gym_id == gym_id,
            NotificationDispatchLog.member_id == member_id,
            NotificationDispatchLog.channel == channel,
            NotificationDispatchLog.notification_kind == kind,
            NotificationDispatchLog.dispatch_date == dispatch_date,
        )
        .first()
    )
    return existing is not None


def _mark_dispatched(
    db: Session, gym_id: int, member_id: int, channel: str, kind: str, dispatch_date: date
) -> None:
    db.add(
        NotificationDispatchLog(
            gym_id=gym_id,
            member_id=member_id,
            channel=channel,
            notification_kind=kind,
            dispatch_date=dispatch_date,
        )
    )


def _send_whatsapp(gym_id: int, phone_number: str, content: str) -> bool:
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{MESSAGE_SERVICE_URL}/api/v1/messages/send/internal",
                headers={"Content-Type": "application/json"},
                json={
                    "gym_id": gym_id,
                    "phone_number": phone_number,
                    "content": content,
                },
            )
        return response.status_code < 400
    except Exception:
        return False


def _send_email(gym_id: int, recipient: str, subject: str, template_name: str, content: str) -> bool:
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(
                f"{EMAIL_SERVICE_URL}/api/v1/email/send/internal",
                headers={"Content-Type": "application/json"},
                json={
                    "gym_id": gym_id,
                    "recipient": recipient,
                    "subject": subject,
                    "template_name": template_name,
                    "template_data": {"content": content},
                },
            )
        return response.status_code < 400
    except Exception:
        return False


def dispatch_session_reminders(
    db: Session,
    gym_id: int,
    run_at: datetime | None = None,
) -> SessionReminderDispatchResponse:
    now = run_at or datetime.now(UTC)
    today = now.date()
    tomorrow = today + timedelta(days=1)
    today_name = _normalize_day_name(today.strftime("%A"))
    tomorrow_name = _normalize_day_name(tomorrow.strftime("%A"))
    send_missed = now.hour >= 22

    members = (
        db.query(Member)
        .filter(Member.gym_id == gym_id)
        .filter(Member.status == MemberStatus.ACTIVE)
        .all()
    )

    whatsapp_sent = 0
    email_sent = 0
    whatsapp_failed = 0
    email_failed = 0
    skipped_no_email = 0

    for member in members:
        member_days = _parse_training_days(member.training_days)
        if not member_days:
            continue

        has_today_attendance = (
            db.query(AttendanceRecord.id)
            .filter(
                AttendanceRecord.gym_id == gym_id,
                AttendanceRecord.member_id == member.id,
                AttendanceRecord.attendance_date == today,
                AttendanceRecord.status == AttendanceStatus.PRESENT,
            )
            .first()
            is not None
        )

        reminders: list[tuple[str, str, str]] = []
        if tomorrow_name in member_days:
            reminders.append(
                (
                    "session_tomorrow_reminder",
                    "Session Reminder for Tomorrow",
                    f"Hi {member.name}, reminder: your gym session is scheduled for tomorrow.",
                )
            )
        if today_name in member_days and not has_today_attendance:
            reminders.append(
                (
                    "session_today_reminder",
                    "Session Reminder for Today",
                    f"Hi {member.name}, reminder: your gym session is scheduled for today.",
                )
            )
            if send_missed:
                reminders.append(
                    (
                        "session_missed_10pm",
                        "Missed Session Alert",
                        f"Hi {member.name}, it's 10pm and you are not marked attended for today's session.",
                    )
                )

        for reminder_kind, subject, content in reminders:
            if not _already_dispatched(db, gym_id, member.id, "whatsapp", reminder_kind, today):
                if _send_whatsapp(gym_id, member.phone_number, content):
                    _mark_dispatched(db, gym_id, member.id, "whatsapp", reminder_kind, today)
                    whatsapp_sent += 1
                else:
                    whatsapp_failed += 1

            if not member.email:
                skipped_no_email += 1
                continue

            if _already_dispatched(db, gym_id, member.id, "email", reminder_kind, today):
                continue
            if _send_email(gym_id, member.email, subject, reminder_kind, content):
                _mark_dispatched(db, gym_id, member.id, "email", reminder_kind, today)
                email_sent += 1
            else:
                email_failed += 1

    db.commit()
    return SessionReminderDispatchResponse(
        gym_id=gym_id,
        run_at=now,
        whatsapp_sent=whatsapp_sent,
        email_sent=email_sent,
        whatsapp_failed=whatsapp_failed,
        email_failed=email_failed,
        skipped_no_email=skipped_no_email,
    )
