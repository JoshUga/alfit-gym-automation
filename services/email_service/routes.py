"""Email Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.email_service.schemas import (
    SendEmailRequest,
    EmailLogResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
)
from services.email_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/email/send", response_model=APIResponse[EmailLogResponse])
def send_email(
    data: SendEmailRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Send an email."""
    result = service.send_email(db, data)
    return APIResponse(data=result, message="Email sent successfully")


@router.get("/email/logs", response_model=APIResponse[list[EmailLogResponse]])
def list_email_logs(
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List sent email logs."""
    result = service.list_email_logs(db, limit)
    return APIResponse(data=result)


@router.post("/email/templates/preview", response_model=APIResponse[EmailPreviewResponse])
def preview_email_template(
    data: EmailPreviewRequest,
    current_user: UserClaims = Depends(get_current_user),
):
    """Preview an email template."""
    result = service.preview_email_template(data.template_name, data.template_data)
    return APIResponse(data=EmailPreviewResponse(**result))
