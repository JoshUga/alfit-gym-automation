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
    WhatsAppConnectRequest,
    WhatsAppConnectResponse,
    WhatsAppStatusResponse,
    WhatsAppSendWelcomeRequest,
    WhatsAppSendWelcomeResponse,
    WhatsAppOnboardingWelcomeRequest,
    WhatsAppOnboardingWelcomeResponse,
    GymSMTPSettingsUpdate,
    GymSMTPSettingsResponse,
    DomainCheckoutCreate,
    DomainCheckoutResponse,
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
    result = service.register_gym(db, gym_data, current_user.user_id, current_user.email)
    return APIResponse(data=result, message="Gym registered successfully")


@router.get("/gyms/me", response_model=APIResponse[GymResponse])
def get_my_gym(
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get the authenticated owner's active gym."""
    owner_id = current_user.owner_id or current_user.user_id
    result = service.get_owner_gym(db, owner_id)
    return APIResponse(data=result)


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


@router.post(
    "/gyms/{gym_id}/whatsapp/connect",
    response_model=APIResponse[WhatsAppConnectResponse],
)
def connect_whatsapp(
    gym_id: int,
    data: WhatsAppConnectRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create/connect a gym WhatsApp line using EvolutionAPI (QR or pairing code)."""
    result = service.connect_whatsapp_instance(db, gym_id, data)
    return APIResponse(data=result, message="WhatsApp connection started")


@router.get(
    "/gyms/{gym_id}/whatsapp/status",
    response_model=APIResponse[WhatsAppStatusResponse],
)
def get_whatsapp_status(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get WhatsApp connection status for a gym EvolutionAPI instance."""
    result = service.get_whatsapp_connection_status(db, gym_id)
    return APIResponse(data=result)


@router.post(
    "/gyms/{gym_id}/whatsapp/send-welcome",
    response_model=APIResponse[WhatsAppSendWelcomeResponse],
)
def send_welcome_message(
    gym_id: int,
    data: WhatsAppSendWelcomeRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Send a WhatsApp welcome message to a newly added member."""
    result = service.send_welcome_to_member(
        db,
        gym_id,
        data.member_name,
        data.member_phone,
        data.schedule,
        data.training_days,
        data.target,
        data.monthly_payment_amount,
    )
    status = str(result.get("status") or "unknown")
    if status == "sent":
        msg = "Welcome message sent"
    elif status == "skipped":
        msg = f"Welcome message skipped: {result.get('reason', 'unknown')}"
    else:
        msg = f"Welcome message not sent: {result.get('reason', status)}"
    return APIResponse(data=WhatsAppSendWelcomeResponse(**result), message=msg)


@router.post(
    "/gyms/{gym_id}/whatsapp/send-onboarding-welcome",
    response_model=APIResponse[WhatsAppOnboardingWelcomeResponse],
)
def send_onboarding_welcome_message(
    gym_id: int,
    data: WhatsAppOnboardingWelcomeRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Send an AI-crafted self-welcome message to the owner's own WhatsApp number after connect."""
    result = service.send_onboarding_self_message(
        db=db,
        gym_id=gym_id,
        phone_number=data.phone_number,
        owner_name=data.owner_name,
    )
    return APIResponse(
        data=WhatsAppOnboardingWelcomeResponse(**result),
        message="Onboarding welcome message processed",
    )


@router.get(
    "/gyms/{gym_id}/smtp-settings",
    response_model=APIResponse[GymSMTPSettingsResponse | None],
)
def get_gym_smtp_settings(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
):
    """Get gym SMTP settings."""
    result = service.get_gym_smtp_settings(gym_id)
    return APIResponse(data=result)


@router.put(
    "/gyms/{gym_id}/smtp-settings",
    response_model=APIResponse[GymSMTPSettingsResponse],
)
def upsert_gym_smtp_settings(
    gym_id: int,
    data: GymSMTPSettingsUpdate,
    current_user: UserClaims = Depends(get_current_user),
):
    """Create/update gym SMTP settings."""
    result = service.upsert_gym_smtp_settings(gym_id, data.model_dump())
    return APIResponse(data=result, message="SMTP settings saved")


@router.post(
    "/gyms/{gym_id}/smtp-settings/test",
    response_model=APIResponse[dict],
)
def test_gym_smtp_settings(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
):
    """Test gym SMTP settings."""
    result = service.test_gym_smtp_settings(gym_id)
    message = "SMTP test successful" if result.get("ok") else "SMTP test failed"
    return APIResponse(data=result, message=message)


@router.post(
    "/gyms/{gym_id}/domains/checkout",
    response_model=APIResponse[DomainCheckoutResponse],
)
def create_domain_checkout(
    gym_id: int,
    data: DomainCheckoutCreate,
    current_user: UserClaims = Depends(get_current_user),
):
    """Create a PayGate checkout link for domain purchase."""
    result = service.create_domain_checkout(gym_id, data.domain_name, data.years)
    return APIResponse(data=result, message="Domain checkout created")
