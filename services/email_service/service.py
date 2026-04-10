"""Email Service business logic."""

import logging
import os
from datetime import datetime, UTC
import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session
from services.email_service.models import EmailLog, EmailStatus, SMTPAccount
from services.email_service.schemas import (
    SendEmailRequest,
    EmailLogResponse,
    SMTPAccountCreate,
    SMTPAccountResponse,
    SMTPHealthCheckResponse,
    SMTPHealthCheckResult,
)

logger = logging.getLogger(__name__)
EMAILENGINE_BASE_URL = os.getenv("EMAILENGINE_BASE_URL", "").rstrip("/")
EMAILENGINE_API_TOKEN = os.getenv("EMAILENGINE_API_TOKEN", "")


def _pick_next_smtp_account(db: Session, gym_id: int | None) -> SMTPAccount | None:
    query = db.query(SMTPAccount).filter(SMTPAccount.is_active.is_(True))
    if gym_id is not None:
        query = query.filter(or_(SMTPAccount.gym_id == gym_id, SMTPAccount.gym_id.is_(None)))
    candidates = query.order_by(SMTPAccount.last_used_at.asc().nullsfirst(), SMTPAccount.id.asc()).all()
    healthy = [a for a in candidates if (a.health_status or "").lower() in {"healthy", "unknown"}]
    return healthy[0] if healthy else (candidates[0] if candidates else None)


def _build_emailengine_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if EMAILENGINE_API_TOKEN:
        headers["Authorization"] = f"Bearer {EMAILENGINE_API_TOKEN}"
    return headers


def _send_via_emailengine(account: SMTPAccount | None, data: SendEmailRequest) -> str:
    if not EMAILENGINE_BASE_URL or not account:
        return "emailengine-default"
    html_content = preview_email_template(data.template_name, data.template_data).get("html_content", "")
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            f"{EMAILENGINE_BASE_URL}/v1/account/{account.emailengine_account_id}/submit",
            headers=_build_emailengine_headers(),
            json={
                "to": [str(data.recipient)],
                "subject": data.subject,
                "text": "",
                "html": html_content,
            },
        )
    if response.status_code >= 400:
        raise RuntimeError(f"emailengine_send_failed_{response.status_code}")
    return "emailengine"


def _check_smtp_account_health(account: SMTPAccount) -> str:
    if not EMAILENGINE_BASE_URL:
        return "healthy" if account.is_active else "inactive"
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(
                f"{EMAILENGINE_BASE_URL}/v1/account/{account.emailengine_account_id}",
                headers=_build_emailengine_headers(),
            )
        return "healthy" if response.status_code < 400 else "unhealthy"
    except Exception:
        return "unhealthy"


def send_email(db: Session, data: SendEmailRequest) -> EmailLogResponse:
    """Send an email and log it."""
    account = _pick_next_smtp_account(db, data.gym_id)
    logger.info("Sending email to %s with template %s", data.recipient, data.template_name)

    status = EmailStatus.SENT
    provider = "emailengine-default"
    try:
        provider = _send_via_emailengine(account, data)
    except Exception as exc:
        logger.warning("Email send failed for %s: %s", data.recipient, exc)
        status = EmailStatus.FAILED

    log = EmailLog(
        recipient=str(data.recipient),
        subject=data.subject,
        template_name=data.template_name,
        status=status,
        provider=provider,
    )
    db.add(log)

    if account:
        account.last_used_at = datetime.now(UTC)
        if status == EmailStatus.FAILED:
            account.health_status = "unhealthy"

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


def create_smtp_account(db: Session, data: SMTPAccountCreate) -> SMTPAccountResponse:
    account = SMTPAccount(
        gym_id=data.gym_id,
        name=data.name,
        emailengine_account_id=data.emailengine_account_id,
        is_active=data.is_active,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return SMTPAccountResponse.model_validate(account)


def list_smtp_accounts(db: Session, gym_id: int | None = None) -> list[SMTPAccountResponse]:
    query = db.query(SMTPAccount)
    if gym_id is not None:
        query = query.filter(or_(SMTPAccount.gym_id == gym_id, SMTPAccount.gym_id.is_(None)))
    accounts = query.order_by(SMTPAccount.created_at.desc()).all()
    return [SMTPAccountResponse.model_validate(account) for account in accounts]


def run_smtp_health_checks(
    db: Session, gym_id: int | None = None, account_id: int | None = None
) -> SMTPHealthCheckResponse:
    query = db.query(SMTPAccount)
    if account_id is not None:
        query = query.filter(SMTPAccount.id == account_id)
    if gym_id is not None:
        query = query.filter(or_(SMTPAccount.gym_id == gym_id, SMTPAccount.gym_id.is_(None)))
    accounts = query.order_by(SMTPAccount.id.asc()).all()

    checked_at = datetime.now(UTC)
    results: list[SMTPHealthCheckResult] = []
    for account in accounts:
        status = _check_smtp_account_health(account)
        account.health_status = status
        account.last_health_check_at = checked_at
        results.append(
            SMTPHealthCheckResult(
                account_id=account.id,
                name=account.name,
                health_status=status,
                checked_at=checked_at,
            )
        )
    db.commit()
    return SMTPHealthCheckResponse(results=results)


def preview_email_template(template_name: str, template_data: dict | None = None) -> dict:
    """Preview an email template with variable substitution."""
    # Placeholder rendering
    content = f"<h1>Template: {template_name}</h1>"
    if template_data:
        for key, value in template_data.items():
            content += f"<p>{key}: {value}</p>"
    return {"subject": f"Preview: {template_name}", "html_content": content}
