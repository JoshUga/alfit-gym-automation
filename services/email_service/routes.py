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
    SMTPAccountCreate,
    SMTPAccountResponse,
    SMTPHealthCheckRequest,
    SMTPHealthCheckResponse,
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


@router.post("/email/send/internal", response_model=APIResponse[EmailLogResponse])
def send_email_internal(
    data: SendEmailRequest,
    db: Session = Depends(get_session),
):
    """Internal service endpoint for sending emails without user JWT."""
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


@router.post("/email/smtp/accounts", response_model=APIResponse[SMTPAccountResponse])
def create_smtp_account(
    data: SMTPAccountCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create an SMTP account mapping in EmailEngine."""
    result = service.create_smtp_account(db, data)
    return APIResponse(data=result, message="SMTP account created successfully")


@router.get("/email/smtp/accounts", response_model=APIResponse[list[SMTPAccountResponse]])
def list_smtp_accounts(
    gym_id: int | None = Query(None),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List SMTP accounts."""
    result = service.list_smtp_accounts(db, gym_id)
    return APIResponse(data=result)


@router.post("/email/smtp/health-check", response_model=APIResponse[SMTPHealthCheckResponse])
def smtp_health_check(
    data: SMTPHealthCheckRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Run SMTP health checks via EmailEngine."""
    result = service.run_smtp_health_checks(db, data.gym_id, data.account_id)
    return APIResponse(data=result)
