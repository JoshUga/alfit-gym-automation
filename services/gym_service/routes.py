"""Gym Service API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.gym_service.schemas import (
    GymCreate,
    GymUpdate,
    GymResponse,
    PhoneNumberCreate,
    PhoneNumberResponse,
    EvolutionCredentialCreate,
    EvolutionCredentialResponse,
)
from services.gym_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/gyms/register", response_model=APIResponse[GymResponse])
def register_gym(
    gym_data: GymCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Register a new gym."""
    result = service.register_gym(db, gym_data, current_user.user_id)
    return APIResponse(data=result, message="Gym registered successfully")


@router.get("/gyms/{gym_id}", response_model=APIResponse[GymResponse])
def get_gym(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get gym details."""
    result = service.get_gym(db, gym_id)
    return APIResponse(data=result)


@router.put("/gyms/{gym_id}", response_model=APIResponse[GymResponse])
def update_gym(
    gym_id: int,
    gym_data: GymUpdate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update gym details."""
    result = service.update_gym(db, gym_id, gym_data)
    return APIResponse(data=result, message="Gym updated successfully")


@router.delete("/gyms/{gym_id}", response_model=APIResponse)
def delete_gym(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Delete a gym."""
    result = service.delete_gym(db, gym_id)
    return APIResponse(message=result["message"])


@router.post("/gyms/{gym_id}/phone-numbers", response_model=APIResponse[PhoneNumberResponse])
def add_phone_number(
    gym_id: int,
    data: PhoneNumberCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Add a phone number to a gym."""
    result = service.add_phone_number(db, gym_id, data)
    return APIResponse(data=result, message="Phone number added successfully")


@router.get("/gyms/{gym_id}/phone-numbers", response_model=APIResponse[list[PhoneNumberResponse]])
def list_phone_numbers(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List phone numbers for a gym."""
    result = service.list_phone_numbers(db, gym_id)
    return APIResponse(data=result)


@router.delete("/gyms/{gym_id}/phone-numbers/{phone_id}", response_model=APIResponse)
def remove_phone_number(
    gym_id: int,
    phone_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Remove a phone number from a gym."""
    result = service.remove_phone_number(db, gym_id, phone_id)
    return APIResponse(message=result["message"])


@router.post(
    "/gyms/{gym_id}/evolution-credentials",
    response_model=APIResponse[EvolutionCredentialResponse],
)
def set_evolution_credentials(
    gym_id: int,
    data: EvolutionCredentialCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Set Evolution API credentials for a gym."""
    result = service.set_evolution_credentials(db, gym_id, data)
    return APIResponse(data=result, message="Credentials saved successfully")


@router.get(
    "/gyms/{gym_id}/evolution-credentials",
    response_model=APIResponse[list[EvolutionCredentialResponse]],
)
def get_evolution_credentials(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get Evolution API credentials for a gym."""
    result = service.get_evolution_credentials(db, gym_id)
    return APIResponse(data=result)
