"""Email Service business logic."""

import logging
from sqlalchemy.orm import Session
from services.email_service.models import EmailLog, EmailStatus
from services.email_service.schemas import (
    SendEmailRequest,
    EmailLogResponse,
)

logger = logging.getLogger(__name__)


def send_email(db: Session, data: SendEmailRequest) -> EmailLogResponse:
    """Send an email and log it."""
    # Placeholder: actual email provider call would go here
    logger.info(f"Sending email to {data.recipient} with template {data.template_name}")

    log = EmailLog(
        recipient=data.recipient,
        subject=data.subject,
        template_name=data.template_name,
        status=EmailStatus.SENT,
        provider="smtp",
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return EmailLogResponse.model_validate(log)


def list_email_logs(db: Session, limit: int = 100) -> list[EmailLogResponse]:
    """List sent email logs."""
    logs = (
        db.query(EmailLog)
        .order_by(EmailLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [EmailLogResponse.model_validate(log) for log in logs]


def preview_email_template(template_name: str, template_data: dict | None = None) -> dict:
    """Preview an email template with variable substitution."""
    # Placeholder rendering
    content = f"<h1>Template: {template_name}</h1>"
    if template_data:
        for key, value in template_data.items():
            content += f"<p>{key}: {value}</p>"
    return {"subject": f"Preview: {template_name}", "html_content": content}
