"""Message Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.message_service.schemas import (
    IncomingMessageEvent,
    ProcessedMessageResponse,
    EvolutionUpsertWebhook,
    OutboundWhatsAppRequest,
)
from services.message_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/messages/process", response_model=APIResponse[ProcessedMessageResponse])
def process_message(
    data: IncomingMessageEvent,
    db: Session = Depends(get_session),
):
    """Process an incoming message."""
    result = service.process_message(db, data)
    return APIResponse(data=result, message="Message processed successfully")


@router.get("/messages/processed", response_model=APIResponse[list[ProcessedMessageResponse]])
def list_processed_messages(
    gym_id: int = Query(..., description="Gym ID"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List processed messages."""
    result = service.list_processed_messages(db, gym_id)
    return APIResponse(data=result)


@router.post("/messages/evolution-upsert", response_model=APIResponse[dict])
def receive_evolution_upsert(
    data: EvolutionUpsertWebhook,
    db: Session = Depends(get_session),
):
    """Receive MESSAGES_UPSERT webhook payloads from Evolution API."""
    result = service.handle_evolution_upsert(db, data)
    return APIResponse(data=result)


@router.post("/messages/evolution-upsert/{event_slug:path}", response_model=APIResponse[dict])
def receive_evolution_upsert_with_event_path(
    event_slug: str,
    data: EvolutionUpsertWebhook,
    db: Session = Depends(get_session),
):
    """Receive Evolution webhooks that append event names to the callback path."""
    normalized_event = event_slug.replace("-", ".").strip().lower()
    patched = data.model_copy(
        update={
            "event": data.event or normalized_event,
            "event_type": data.event_type or normalized_event,
        }
    )
    result = service.handle_evolution_upsert(db, patched)
    return APIResponse(data=result)


@router.post("/messages/send", response_model=APIResponse[dict])
def send_whatsapp_message(
    data: OutboundWhatsAppRequest,
    current_user: UserClaims = Depends(get_current_user),
):
    """Send an outbound WhatsApp message."""
    result = service.send_outbound_whatsapp(data)
    return APIResponse(data=result, message="WhatsApp message sent")


@router.post("/messages/send/internal", response_model=APIResponse[dict])
def send_whatsapp_message_internal(
    data: OutboundWhatsAppRequest,
):
    """Internal service endpoint for outbound WhatsApp messages."""
    result = service.send_outbound_whatsapp(data)
    return APIResponse(data=result, message="WhatsApp message sent")
