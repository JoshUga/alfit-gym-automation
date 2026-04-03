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
)
from services.member_service import service

logger = logging.getLogger(__name__)
router = APIRouter()

GYM_SERVICE_URL = os.getenv("GYM_SERVICE_URL", "http://gym-service:8000")


def get_session():
    """Get database session dependency."""
    yield from get_db()


def _fire_welcome_message(
    gym_id: int, member_name: str, member_phone: str, schedule: str | None, auth_header: str | None
) -> None:
    """Best-effort call to gym_service to send a WhatsApp welcome message."""
    if not auth_header:
        return
    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(
                f"{GYM_SERVICE_URL}/api/v1/gyms/{gym_id}/whatsapp/send-welcome",
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                json={"member_name": member_name, "member_phone": member_phone, "schedule": schedule},
            )
    except Exception as exc:
        logger.warning("Could not send welcome WhatsApp for member in gym %s: %s", gym_id, exc)


@router.post("/members", response_model=APIResponse[MemberResponse])
def add_member(
    request: Request,
    data: MemberCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Add a new member."""
    result = service.add_member(db, data)
    _fire_welcome_message(
        gym_id=data.gym_id,
        member_name=result.name,
        member_phone=result.phone_number,
        schedule=result.schedule,
        auth_header=request.headers.get("Authorization"),
    )
    return APIResponse(data=result, message="Member added successfully")


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
