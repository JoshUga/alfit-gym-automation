"""Member Service API routes."""

import os
import logging
import httpx
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.exceptions import ForbiddenException, NotFoundException
from shared.models import APIResponse
from services.member_service.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    GroupCreate,
    GroupResponse,
    MemberPaymentCreate,
    MemberPaymentResponse,
    TrainerAssignmentCreate,
    TrainerAssignmentResponse,
)
from services.member_service import service

logger = logging.getLogger(__name__)
router = APIRouter()

GYM_SERVICE_URL = os.getenv("GYM_SERVICE_URL", "http://gym-service:8000")
WORKOUT_SERVICE_URL = os.getenv("WORKOUT_SERVICE_URL", "http://workout-service:8000")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL", "http://email-service:8000")


def get_session():
    """Get database session dependency."""
    yield from get_db()


def _validate_staff_member_assignment(current_user: UserClaims, member_id: int, db: Session) -> None:
    if "gym_staff" not in current_user.roles:
        return
    member = service.get_member(db, member_id)
    if current_user.user_id not in member.trainer_user_ids:
        raise NotFoundException("Member", member_id)


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


def _fire_generate_workout_plan(
    member_id: int,
    gym_id: int,
    member_name: str,
    target: str | None,
    training_days: list[str] | None,
    auth_header: str | None,
) -> dict:
    """Best-effort call to workout_service to auto-generate initial member workout plan."""
    if not auth_header:
        return {"status": "skipped", "reason": "missing_auth_header"}

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"{WORKOUT_SERVICE_URL}/api/v1/members/{member_id}/workout-plan/generate",
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json={
                    "gym_id": gym_id,
                    "member_name": member_name,
                    "target": target,
                    "training_days": training_days,
                },
            )
        if response.status_code >= 400:
            return {
                "status": "failed",
                "reason": f"workout_service_http_{response.status_code}",
            }
        return {"status": "generated"}
    except Exception as exc:
        logger.warning("Could not auto-generate workout plan for member %s: %s", member_id, exc)
        return {"status": "error", "reason": str(exc)}


def _fire_welcome_email(
    gym_id: int,
    member_name: str,
    member_email: str | None,
    training_days: list[str] | None,
    target: str | None,
    monthly_payment_amount: int | None,
) -> dict:
    """Best-effort call to email_service to send a welcome email to new members."""
    if not member_email:
        return {"status": "skipped", "reason": "member_email_missing"}

    try:
        with httpx.Client(timeout=12.0) as client:
            response = client.post(
                f"{EMAIL_SERVICE_URL}/api/v1/email/send/internal",
                headers={"Content-Type": "application/json"},
                json={
                    "gym_id": gym_id,
                    "recipient": member_email,
                    "subject": f"Welcome to your gym journey, {member_name}",
                    "template_name": "member_welcome",
                    "template_data": {
                        "member_name": member_name,
                        "training_days": ", ".join(training_days or []) or "not specified",
                        "target": target or "not specified",
                        "monthly_payment_amount": monthly_payment_amount,
                    },
                },
            )

        if response.status_code >= 400:
            return {"status": "failed", "reason": f"email_service_http_{response.status_code}"}

        payload = response.json() if response.content else {}
        response_data = payload.get("data") if isinstance(payload, dict) else None
        email_delivery_status = str((response_data or {}).get("status") or "").lower()
        if email_delivery_status and email_delivery_status != "sent":
            return {"status": "failed", "reason": f"email_service_{email_delivery_status}"}
        return {"status": "sent"}
    except Exception as exc:
        logger.warning("Could not send welcome email for member %s in gym %s: %s", member_name, gym_id, exc)
        return {"status": "error", "reason": str(exc)}


@router.post("/members", response_model=APIResponse[MemberResponse])
def add_member(
    request: Request,
    data: MemberCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Add a new member."""
    if "gym_staff" in current_user.roles:
        raise ForbiddenException("Trainer accounts cannot add members")
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
    workout_result = _fire_generate_workout_plan(
        member_id=result.id,
        gym_id=data.gym_id,
        member_name=result.name,
        target=result.target,
        training_days=result.training_days,
        auth_header=request.headers.get("Authorization"),
    )
    email_result = _fire_welcome_email(
        gym_id=data.gym_id,
        member_name=result.name,
        member_email=result.email,
        training_days=result.training_days,
        target=result.target,
        monthly_payment_amount=result.monthly_payment_amount,
    )
    welcome_status = str(welcome_result.get("status") or "unknown")
    workout_status = str(workout_result.get("status") or "unknown")
    email_status = str(email_result.get("status") or "unknown")

    workout_message = "workout plan generated"
    if workout_status == "skipped":
        workout_message = f"workout generation skipped ({workout_result.get('reason', 'unknown')})"
    elif workout_status != "generated":
        workout_message = f"workout generation not completed ({workout_result.get('reason', workout_status)})"

    email_message = "welcome email sent"
    if email_status == "skipped":
        email_message = f"welcome email skipped ({email_result.get('reason', 'unknown')})"
    elif email_status != "sent":
        email_message = f"welcome email not sent ({email_result.get('reason', email_status)})"

    if welcome_status == "sent":
        message = f"Member added, WhatsApp welcome sent, {email_message}, and {workout_message}"
    elif welcome_status == "skipped":
        message = (
            "Member added, WhatsApp welcome skipped "
            f"({welcome_result.get('reason', 'unknown')}), {email_message}, and {workout_message}"
        )
    else:
        message = (
            "Member added, WhatsApp welcome not sent "
            f"({welcome_result.get('reason', welcome_status)}), {email_message}, and {workout_message}"
        )
    return APIResponse(data=result, message=message)


@router.get("/members/{member_id}", response_model=APIResponse[MemberResponse])
def get_member(
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get a member by ID."""
    result = service.get_member(db, member_id)
    if "gym_staff" in current_user.roles and current_user.user_id not in result.trainer_user_ids:
        raise NotFoundException("Member", member_id)
    return APIResponse(data=result)


@router.get("/gyms/{gym_id}/members", response_model=APIResponse[list[MemberResponse]])
def list_gym_members(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List all members for a gym."""
    if "gym_staff" in current_user.roles:
        result = service.list_trainer_members(db, gym_id, current_user.user_id)
    else:
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
    _validate_staff_member_assignment(current_user, member_id, db)
    result = service.update_member(db, member_id, data)
    return APIResponse(data=result, message="Member updated successfully")


@router.delete("/members/{member_id}", response_model=APIResponse)
def delete_member(
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Soft-delete a member."""
    if "gym_staff" in current_user.roles:
        raise ForbiddenException("Trainer accounts cannot delete members")
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
    _validate_staff_member_assignment(current_user, member_id, db)
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
    _validate_staff_member_assignment(current_user, member_id, db)
    result = service.create_member_payment(db, member_id, data)
    return APIResponse(data=result, message="Payment recorded successfully")


@router.get(
    "/gyms/{gym_id}/trainer-assignments",
    response_model=APIResponse[list[TrainerAssignmentResponse]],
)
def list_trainer_assignments(
    gym_id: int,
    trainer_user_id: int | None = None,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List trainer assignments for a gym."""
    if "gym_staff" in current_user.roles:
        trainer_user_id = current_user.user_id
    result = service.list_trainer_assignments(db, gym_id, trainer_user_id)
    return APIResponse(data=result)


@router.post(
    "/members/{member_id}/trainer-assignments",
    response_model=APIResponse[TrainerAssignmentResponse],
)
def assign_trainer_to_member(
    member_id: int,
    data: TrainerAssignmentCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Assign a trainer to a member."""
    if "gym_owner" not in current_user.roles:
        raise ForbiddenException("Only gym owners can assign trainers")
    result = service.assign_trainer_to_member(db, member_id, data.trainer_user_id)
    return APIResponse(data=result, message="Trainer assigned successfully")


@router.delete(
    "/members/{member_id}/trainer-assignments/{trainer_user_id}",
    response_model=APIResponse,
)
def remove_trainer_from_member(
    member_id: int,
    trainer_user_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Remove trainer assignment from a member."""
    if "gym_owner" not in current_user.roles:
        raise ForbiddenException("Only gym owners can remove trainer assignments")
    result = service.remove_trainer_from_member(db, member_id, trainer_user_id)
    return APIResponse(message=result["message"])
