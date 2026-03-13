"""Notification Service business logic."""

import re
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ValidationException
from services.notification_service.models import (
    NotificationTemplate,
    ScheduledNotification,
    NotificationStatus,
)
from services.notification_service.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
)


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


def list_scheduled_notifications(db: Session, gym_id: int) -> list[ScheduleResponse]:
    """List scheduled notifications for a gym."""
    notifications = (
        db.query(ScheduledNotification)
        .filter(ScheduledNotification.gym_id == gym_id)
        .all()
    )
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
