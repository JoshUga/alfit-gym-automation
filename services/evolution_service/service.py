"""Evolution Service business logic."""

import logging
import json
import os
import re
import httpx
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
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution-api:8080").rstrip("/")
EVOLUTION_API_GLOBAL_KEY = os.getenv("EVOLUTION_API_GLOBAL_KEY", "")


def _find_first(obj, keys: list[str]):
    if isinstance(obj, dict):
        for key in keys:
            if key in obj and obj[key] is not None:
                return obj[key]
        for value in obj.values():
            found = _find_first(value, keys)
            if found is not None:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = _find_first(item, keys)
            if found is not None:
                return found
    return None


def _extract_sender_number(payload: dict) -> str | None:
    raw = _find_first(payload, ["remoteJid", "from", "sender", "fromNumber"])
    if not raw:
        return None
    digits = re.sub(r"\D", "", str(raw))
    return digits or None


def _extract_instance_name(payload: dict) -> str | None:
    value = _find_first(payload, ["instance", "instanceName", "instance_name"])
    return str(value).strip() if value else None


def _is_from_me(payload: dict) -> bool:
    from_me = _find_first(payload, ["fromMe", "from_me"])
    return bool(from_me)


def _extract_message_text(payload: dict) -> str:
    value = _find_first(payload, ["conversation", "text", "message", "body", "content"])
    return str(value).strip() if value else ""


def _send_auto_reply(instance_name: str, to_number: str, text: str) -> bool:
    if not EVOLUTION_API_GLOBAL_KEY:
        return False

    payload = {
        "number": to_number,
        "text": text,
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{instance_name}",
                headers={"apikey": EVOLUTION_API_GLOBAL_KEY, "Content-Type": "application/json"},
                json=payload,
            )
        return resp.status_code < 400
    except Exception:
        return False


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
    raw_payload = payload.model_dump()
    event_type = str(payload.event_type or "").strip()
    logger.info("Received Evolution webhook event: %s", event_type)

    if _is_from_me(raw_payload):
        return {"status": "ignored", "reason": "outbound_message", "event_type": event_type}

    sender = _extract_sender_number(raw_payload)
    instance_name = _extract_instance_name(raw_payload)
    incoming_text = _extract_message_text(raw_payload)

    if not sender or not instance_name:
        return {"status": "ignored", "reason": "missing_sender_or_instance", "event_type": event_type}

    auto_reply = (
        "Thanks for your message. We received it and will get back to you shortly. "
        "You can also send your name to get started quickly."
    )

    sent = _send_auto_reply(instance_name, sender, auto_reply)
    return {
        "status": "auto_replied" if sent else "received",
        "event_type": event_type,
        "instance_name": instance_name,
        "to": sender,
        "incoming_preview": incoming_text[:120],
    }
