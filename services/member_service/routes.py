"""Member Service API routes."""

import os
import logging
import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.member_service.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    GroupCreate,
    GroupResponse,
    MemberPaymentCreate,
    MemberPaymentResponse,
)
from services.member_service import service

logger = logging.getLogger(__name__)
router = APIRouter()

GYM_SERVICE_URL = os.getenv("GYM_SERVICE_URL", "http://gym-service:8000")


def get_session():
    """Get database session dependency."""
    yield from get_db()


def _fire_welcome_message(
    gym_id: int,
    member_name: str,
    member_phone: str,
    schedule: str | None,
    training_days: list[str] | None,
    target: str | None,
    monthly_payment_amount: int | None,
    auth_header: str | None,
) -> dict:
    """Best-effort call to gym_service to send a WhatsApp welcome message."""
    if not auth_header:
        return {"status": "skipped", "reason": "missing_auth_header"}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{GYM_SERVICE_URL}/api/v1/gyms/{gym_id}/whatsapp/send-welcome",
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json={
                    "member_name": member_name,
                    "member_phone": member_phone,
                    "schedule": schedule,
                    "training_days": training_days,
                    "target": target,
                    "monthly_payment_amount": monthly_payment_amount,
                },
            )
        if response.status_code >= 400:
            return {
                "status": "failed",
                "reason": f"gym_service_http_{response.status_code}",
            }
        payload = response.json() if response.content else {}
        return (payload.get("data") or {"status": "unknown"}) if isinstance(payload, dict) else {"status": "unknown"}
    except Exception as exc:
        logger.warning("Could not send welcome WhatsApp for member in gym %s: %s", gym_id, exc)
        return {"status": "error", "reason": str(exc)}


@router.post("/members", response_model=APIResponse[MemberResponse])
def add_member(
    request: Request,
    data: MemberCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Add a new member."""
    result = service.add_member(db, data)
    welcome_result = _fire_welcome_message(
        gym_id=data.gym_id,
        member_name=result.name,
        member_phone=result.phone_number,
        schedule=result.schedule,
        training_days=result.training_days,
        target=result.target,
        monthly_payment_amount=result.monthly_payment_amount,
        auth_header=request.headers.get("Authorization"),
    )
    welcome_status = str(welcome_result.get("status") or "unknown")
    if welcome_status == "sent":
        message = "Member added and WhatsApp welcome sent"
    elif welcome_status == "skipped":
        message = f"Member added, WhatsApp welcome skipped ({welcome_result.get('reason', 'unknown')})"
    else:
        message = f"Member added, WhatsApp welcome not sent ({welcome_result.get('reason', welcome_status)})"
    return APIResponse(data=result, message=message)


@router.get("/members/{member_id}", response_model=APIResponse[MemberResponse])
def get_member(
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get a member by ID."""
    result = service.get_member(db, member_id)
    return APIResponse(data=result)


@router.get("/gyms/{gym_id}/members", response_model=APIResponse[list[MemberResponse]])
def list_gym_members(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List all members for a gym."""
    result = service.list_gym_members(db, gym_id)
    return APIResponse(data=result)


@router.put("/members/{member_id}", response_model=APIResponse[MemberResponse])
def update_member(
    member_id: int,
    data: MemberUpdate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update a member."""
    result = service.update_member(db, member_id, data)
    return APIResponse(data=result, message="Member updated successfully")


@router.delete("/members/{member_id}", response_model=APIResponse)
def delete_member(
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Soft-delete a member."""
    result = service.delete_member(db, member_id)
    return APIResponse(message=result["message"])


@router.post("/gyms/{gym_id}/groups", response_model=APIResponse[GroupResponse])
def create_group(
    gym_id: int,
    data: GroupCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a member group."""
    result = service.create_group(db, gym_id, data)
    return APIResponse(data=result, message="Group created successfully")


@router.get("/gyms/{gym_id}/groups", response_model=APIResponse[list[GroupResponse]])
def list_groups(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List all groups for a gym."""
    result = service.list_groups(db, gym_id)
    return APIResponse(data=result)


@router.post("/groups/{group_id}/members/{member_id}", response_model=APIResponse)
def assign_member_to_group(
    group_id: int,
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Assign a member to a group."""
    result = service.assign_member_to_group(db, group_id, member_id)
    return APIResponse(message=result["message"])


@router.delete("/groups/{group_id}/members/{member_id}", response_model=APIResponse)
def remove_member_from_group(
    group_id: int,
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Remove a member from a group."""
    result = service.remove_member_from_group(db, group_id, member_id)
    return APIResponse(message=result["message"])


@router.get("/members/{member_id}/payments", response_model=APIResponse[list[MemberPaymentResponse]])
def list_member_payments(
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List all payments for a member."""
    result = service.list_member_payments(db, member_id)
    return APIResponse(data=result)


@router.post("/members/{member_id}/payments", response_model=APIResponse[MemberPaymentResponse])
def create_member_payment(
    member_id: int,
    data: MemberPaymentCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a payment for a member."""
    result = service.create_member_payment(db, member_id, data)
    return APIResponse(data=result, message="Payment recorded successfully")
