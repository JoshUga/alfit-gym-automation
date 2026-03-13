"""Notification Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.notification_service.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplatePreviewRequest,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
)
from services.notification_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/templates", response_model=APIResponse[TemplateResponse])
def create_template(
    data: TemplateCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a notification template."""
    result = service.create_template(db, data)
    return APIResponse(data=result, message="Template created successfully")


@router.get("/templates/{template_id}", response_model=APIResponse[TemplateResponse])
def get_template(
    template_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get a template by ID."""
    result = service.get_template(db, template_id)
    return APIResponse(data=result)


@router.get("/gyms/{gym_id}/templates", response_model=APIResponse[list[TemplateResponse]])
def list_templates(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List templates for a gym."""
    result = service.list_templates(db, gym_id)
    return APIResponse(data=result)


@router.put("/templates/{template_id}", response_model=APIResponse[TemplateResponse])
def update_template(
    template_id: int,
    data: TemplateUpdate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update a template."""
    result = service.update_template(db, template_id, data)
    return APIResponse(data=result, message="Template updated successfully")


@router.delete("/templates/{template_id}", response_model=APIResponse)
def delete_template(
    template_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete a template."""
    result = service.delete_template(db, template_id)
    return APIResponse(message=result["message"])


@router.post("/templates/preview", response_model=APIResponse[dict])
def preview_template(
    data: TemplatePreviewRequest,
    current_user: UserClaims = Depends(get_current_user),
):
    """Preview a template with variable substitution."""
    result = service.preview_template(data.content, data.variables)
    return APIResponse(data=result)


@router.post("/notifications/schedule", response_model=APIResponse[ScheduleResponse])
def schedule_notification(
    data: ScheduleCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Schedule a notification."""
    result = service.schedule_notification(db, data)
    return APIResponse(data=result, message="Notification scheduled successfully")


@router.get("/notifications/scheduled", response_model=APIResponse[list[ScheduleResponse]])
def list_scheduled_notifications(
    gym_id: int = Query(..., description="Gym ID to filter by"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List scheduled notifications."""
    result = service.list_scheduled_notifications(db, gym_id)
    return APIResponse(data=result)


@router.put("/notifications/scheduled/{schedule_id}", response_model=APIResponse[ScheduleResponse])
def update_scheduled_notification(
    schedule_id: int,
    data: ScheduleUpdate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update a scheduled notification."""
    result = service.update_scheduled_notification(db, schedule_id, data)
    return APIResponse(data=result, message="Schedule updated successfully")


@router.delete("/notifications/scheduled/{schedule_id}", response_model=APIResponse)
def cancel_notification(
    schedule_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Cancel a scheduled notification."""
    result = service.cancel_notification(db, schedule_id)
    return APIResponse(message=result["message"])
