"""Gym Service business logic."""

from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ConflictException
from services.gym_service.models import Gym, GymPhoneNumber, EvolutionCredential
from services.gym_service.schemas import (
    GymCreate,
    GymUpdate,
    GymResponse,
    PhoneNumberCreate,
    PhoneNumberResponse,
    EvolutionCredentialCreate,
    EvolutionCredentialResponse,
)


def register_gym(db: Session, gym_data: GymCreate, owner_id: int) -> GymResponse:
    """Register a new gym."""
    gym = Gym(
        name=gym_data.name,
        address=gym_data.address,
        phone=gym_data.phone,
        email=gym_data.email,
        owner_id=owner_id,
    )
    db.add(gym)
    db.commit()
    db.refresh(gym)
    return GymResponse.model_validate(gym)


def get_gym(db: Session, gym_id: int) -> GymResponse:
    """Get gym by ID."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)
    return GymResponse.model_validate(gym)


def update_gym(db: Session, gym_id: int, gym_data: GymUpdate) -> GymResponse:
    """Update gym details."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    update_data = gym_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(gym, field, value)

    db.commit()
    db.refresh(gym)
    return GymResponse.model_validate(gym)


def delete_gym(db: Session, gym_id: int) -> dict:
    """Soft-delete a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)
    gym.is_active = False
    db.commit()
    return {"message": "Gym deleted successfully"}


def add_phone_number(db: Session, gym_id: int, data: PhoneNumberCreate) -> PhoneNumberResponse:
    """Add a phone number to a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    phone = GymPhoneNumber(
        gym_id=gym_id,
        phone_number=data.phone_number,
        label=data.label,
    )
    db.add(phone)
    db.commit()
    db.refresh(phone)
    return PhoneNumberResponse.model_validate(phone)


def list_phone_numbers(db: Session, gym_id: int) -> list[PhoneNumberResponse]:
    """List all phone numbers for a gym."""
    phones = db.query(GymPhoneNumber).filter(GymPhoneNumber.gym_id == gym_id).all()
    return [PhoneNumberResponse.model_validate(p) for p in phones]


def remove_phone_number(db: Session, gym_id: int, phone_id: int) -> dict:
    """Remove a phone number from a gym."""
    phone = (
        db.query(GymPhoneNumber)
        .filter(GymPhoneNumber.id == phone_id, GymPhoneNumber.gym_id == gym_id)
        .first()
    )
    if not phone:
        raise NotFoundException("PhoneNumber", phone_id)
    db.delete(phone)
    db.commit()
    return {"message": "Phone number removed successfully"}


def set_evolution_credentials(
    db: Session, gym_id: int, data: EvolutionCredentialCreate
) -> EvolutionCredentialResponse:
    """Set Evolution API credentials for a gym."""
    gym = db.query(Gym).filter(Gym.id == gym_id).first()
    if not gym:
        raise NotFoundException("Gym", gym_id)

    cred = EvolutionCredential(
        gym_id=gym_id,
        api_key=data.api_key,
        instance_name=data.instance_name,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    return EvolutionCredentialResponse.model_validate(cred)


def get_evolution_credentials(db: Session, gym_id: int) -> list[EvolutionCredentialResponse]:
    """Get Evolution API credentials for a gym."""
    creds = db.query(EvolutionCredential).filter(EvolutionCredential.gym_id == gym_id).all()
    return [EvolutionCredentialResponse.model_validate(c) for c in creds]
