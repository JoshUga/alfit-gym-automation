"""Evolution Service business logic."""

import logging
import json
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException
from services.evolution_service.models import EvolutionInstance, WebhookRegistration, InstanceStatus
from services.evolution_service.schemas import (
    InstanceCreate,
    InstanceResponse,
    SendMessageRequest,
    SendMessageResponse,
    WebhookRegisterRequest,
    WebhookRegistrationResponse,
    WebhookPayload,
)

logger = logging.getLogger(__name__)


def create_instance(db: Session, data: InstanceCreate) -> InstanceResponse:
    """Create a new Evolution API instance."""
    instance = EvolutionInstance(
        gym_id=data.gym_id,
        instance_name=data.instance_name,
        api_url=data.api_url,
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return InstanceResponse.model_validate(instance)


def get_instance_status(db: Session, instance_id: int) -> InstanceResponse:
    """Get the status of an Evolution instance."""
    instance = db.query(EvolutionInstance).filter(EvolutionInstance.id == instance_id).first()
    if not instance:
        raise NotFoundException("EvolutionInstance", instance_id)
    return InstanceResponse.model_validate(instance)


def send_message(db: Session, data: SendMessageRequest) -> SendMessageResponse:
    """Send a message through an Evolution instance."""
    instance = db.query(EvolutionInstance).filter(EvolutionInstance.id == data.instance_id).first()
    if not instance:
        raise NotFoundException("EvolutionInstance", data.instance_id)

    # Placeholder: actual Evolution API call would go here
    logger.info(
        f"Sending message via instance {instance.instance_name} to {data.to_number}"
    )
    return SendMessageResponse(
        message_id=f"msg_{instance.id}_{data.to_number}",
        status="queued",
    )


def register_webhook(db: Session, data: WebhookRegisterRequest) -> WebhookRegistrationResponse:
    """Register a webhook for an Evolution instance."""
    instance = db.query(EvolutionInstance).filter(EvolutionInstance.id == data.instance_id).first()
    if not instance:
        raise NotFoundException("EvolutionInstance", data.instance_id)

    events_str = json.dumps(data.events) if data.events else None
    webhook = WebhookRegistration(
        instance_id=data.instance_id,
        webhook_url=data.webhook_url,
        events=events_str,
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    return WebhookRegistrationResponse.model_validate(webhook)


def handle_incoming_webhook(payload: WebhookPayload) -> dict:
    """Process an incoming webhook from Evolution API."""
    logger.info(f"Received webhook event: {payload.event_type}")
    return {"status": "received", "event_type": payload.event_type}
