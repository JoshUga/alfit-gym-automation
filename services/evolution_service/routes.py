"""Evolution Service API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.evolution_service.schemas import (
    InstanceCreate,
    InstanceResponse,
    SendMessageRequest,
    SendMessageResponse,
    WebhookRegisterRequest,
    WebhookRegistrationResponse,
    WebhookPayload,
)
from services.evolution_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/evolution/instances", response_model=APIResponse[InstanceResponse])
def create_instance(
    data: InstanceCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create a new Evolution API instance."""
    result = service.create_instance(db, data)
    return APIResponse(data=result, message="Instance created successfully")


@router.get(
    "/evolution/instances/{instance_id}/status",
    response_model=APIResponse[InstanceResponse],
)
def get_instance_status(
    instance_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get the status of an Evolution instance."""
    result = service.get_instance_status(db, instance_id)
    return APIResponse(data=result)


@router.post("/evolution/send-message", response_model=APIResponse[SendMessageResponse])
def send_message(
    data: SendMessageRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Send a message through an Evolution instance."""
    result = service.send_message(db, data)
    return APIResponse(data=result, message="Message sent")


@router.post(
    "/evolution/webhooks/register",
    response_model=APIResponse[WebhookRegistrationResponse],
)
def register_webhook(
    data: WebhookRegisterRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Register a webhook for an Evolution instance."""
    result = service.register_webhook(db, data)
    return APIResponse(data=result, message="Webhook registered successfully")


@router.post("/evolution/webhooks/incoming", response_model=APIResponse[dict])
def receive_webhook(payload: WebhookPayload):
    """Receive an incoming webhook from Evolution API."""
    result = service.handle_incoming_webhook(payload)
    return APIResponse(data=result)
