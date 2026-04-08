"""Message Service business logic."""

import logging
import os
import httpx
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from shared.exceptions import ConflictException
from services.message_service.models import ProcessedMessage
from services.message_service.schemas import (
    IncomingMessageEvent,
    ProcessedMessageResponse,
    EvolutionUpsertWebhook,
)

logger = logging.getLogger(__name__)
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000").rstrip("/")
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution-api:8080").rstrip("/")
EVOLUTION_API_GLOBAL_KEY = os.getenv("EVOLUTION_API_GLOBAL_KEY", "")


def _extract_gym_id_from_instance(instance_name: str | None) -> int:
    """Infer gym id from instance names like gym-12."""
    if not instance_name:
        return 0
    parts = instance_name.strip().split("-")
    if len(parts) < 2:
        return 0
    try:
        return int(parts[-1])
    except (TypeError, ValueError):
        return 0


def _extract_message_data(data: object) -> dict:
    """Support common Evolution webhook shapes for MESSAGES_UPSERT events."""
    if not isinstance(data, dict):
        return {}

    if isinstance(data.get("key"), dict) or "message" in data:
        return data

    for key in ("messages", "message", "data"):
        value = data.get(key)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            return value[0]
        if isinstance(value, dict):
            if isinstance(value.get("messages"), list) and value["messages"]:
                first = value["messages"][0]
                if isinstance(first, dict):
                    return first
            if isinstance(value.get("key"), dict) or "message" in value:
                return value
    return {}


def _extract_text_content(message_obj: dict) -> str:
    """Extract message text from commonly used Evolution/Baileys payload fields."""
    content = message_obj.get("message")
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return ""

    conversation = content.get("conversation")
    if isinstance(conversation, str):
        return conversation

    ext_text = content.get("extendedTextMessage")
    if isinstance(ext_text, dict) and isinstance(ext_text.get("text"), str):
        return ext_text["text"]

    image_caption = content.get("imageMessage")
    if isinstance(image_caption, dict) and isinstance(image_caption.get("caption"), str):
        return image_caption["caption"]

    return ""


def _extract_sender_number(sender: str) -> str:
    """Normalize sender ids like 5511999999999@s.whatsapp.net to plain number."""
    raw = str(sender or "").strip()
    if not raw:
        return ""
    return raw.split("@")[0]


def _is_from_me(message_obj: dict) -> bool:
    key = message_obj.get("key") if isinstance(message_obj.get("key"), dict) else {}
    return bool(key.get("fromMe"))


def _generate_ai_reply(gym_id: int, incoming_message: str) -> dict:
    """Call AI service to generate a reply for an incoming message."""
    with httpx.Client(timeout=25.0) as client:
        response = client.post(
            f"{AI_SERVICE_URL}/api/v1/ai/generate-response/internal",
            headers={"Content-Type": "application/json"},
            json={
                "gym_id": gym_id,
                "phone_number_id": 0,
                "incoming_message": incoming_message,
            },
        )

    if response.status_code >= 400:
        raise RuntimeError(f"ai_generate_failed_{response.status_code}")

    payload = response.json() if response.content else {}
    data = payload.get("data") if isinstance(payload, dict) else None
    text = str((data or {}).get("response_text") or "").strip()
    if not text:
        raise RuntimeError("ai_response_empty")
    return {"response_text": text}


def _send_whatsapp_reply(instance_name: str, to_number: str, text: str) -> None:
    """Send a text reply through Evolution API."""
    if not EVOLUTION_API_GLOBAL_KEY:
        raise RuntimeError("evolution_api_key_missing")

    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            f"{EVOLUTION_API_URL}/message/sendText/{instance_name}",
            headers={"apikey": EVOLUTION_API_GLOBAL_KEY, "Content-Type": "application/json"},
            json={"number": to_number, "text": text},
        )

    if response.status_code >= 400:
        raise RuntimeError(f"evolution_send_failed_{response.status_code}")


def process_message(db: Session, data: IncomingMessageEvent) -> ProcessedMessageResponse:
    """Process an incoming message."""
    existing = (
        db.query(ProcessedMessage)
        .filter(ProcessedMessage.message_id == data.message_id)
        .first()
    )
    if existing:
        raise ConflictException(f"Message {data.message_id} already processed")

    # Placeholder: would trigger AI response logic here
    ai_triggered = False

    record = ProcessedMessage(
        message_id=data.message_id,
        gym_id=data.gym_id,
        phone_number_id=data.phone_number_id,
        sender=data.sender,
        content=data.content,
        is_processed=True,
        ai_response_triggered=ai_triggered,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ProcessedMessageResponse.model_validate(record)


def list_processed_messages(db: Session, gym_id: int) -> list[ProcessedMessageResponse]:
    """List processed messages for a gym."""
    messages = (
        db.query(ProcessedMessage)
        .filter(ProcessedMessage.gym_id == gym_id)
        .order_by(ProcessedMessage.created_at.desc())
        .all()
    )
    return [ProcessedMessageResponse.model_validate(m) for m in messages]


def handle_evolution_upsert(db: Session, payload: EvolutionUpsertWebhook) -> dict:
    """Handle Evolution MESSAGES_UPSERT webhook and persist processed message."""
    event_name = str(payload.event or payload.event_type or "").lower()
    if event_name not in {"messages.upsert", "messages_upsert", "messages-upsert"}:
        return {"status": "ignored", "reason": "unsupported_event"}

    message_obj = _extract_message_data(payload.data)
    key = message_obj.get("key") if isinstance(message_obj.get("key"), dict) else {}

    message_id = str(
        message_obj.get("id")
        or key.get("id")
        or ""
    ).strip()
    if not message_id:
        return {"status": "ignored", "reason": "missing_message_id"}

    existing = (
        db.query(ProcessedMessage)
        .filter(ProcessedMessage.message_id == message_id)
        .first()
    )
    if existing:
        return {"status": "ignored", "reason": "already_processed", "message_id": message_id}

    sender = str(
        message_obj.get("sender")
        or key.get("remoteJid")
        or "unknown"
    )
    content = _extract_text_content(message_obj)
    instance_name = payload.instance_name or payload.instance or ""
    gym_id = _extract_gym_id_from_instance(instance_name)
    from_me = _is_from_me(message_obj)

    record = ProcessedMessage(
        message_id=message_id,
        gym_id=gym_id,
        phone_number_id=0,
        sender=sender,
        content=content,
        is_processed=True,
        ai_response_triggered=False,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"status": "ignored", "reason": "already_processed", "message_id": message_id}

    if from_me:
        return {
            "status": "processed",
            "message_id": message_id,
            "reply_status": "skipped_from_me",
        }

    if not content.strip():
        return {
            "status": "processed",
            "message_id": message_id,
            "reply_status": "skipped_empty_content",
        }

    if gym_id <= 0 or not instance_name:
        return {
            "status": "processed",
            "message_id": message_id,
            "reply_status": "skipped_missing_routing",
        }

    to_number = _extract_sender_number(sender)
    if not to_number:
        return {
            "status": "processed",
            "message_id": message_id,
            "reply_status": "skipped_missing_sender",
        }

    try:
        ai_result = _generate_ai_reply(gym_id=gym_id, incoming_message=content)
        _send_whatsapp_reply(instance_name=instance_name, to_number=to_number, text=ai_result["response_text"])
        db.query(ProcessedMessage).filter(ProcessedMessage.message_id == message_id).update(
            {ProcessedMessage.ai_response_triggered: True},
            synchronize_session=False,
        )
        db.commit()
        reply_status = "sent"
    except Exception as exc:
        logger.warning("Auto-reply failed for inbound message %s: %s", message_id, exc)
        reply_status = "failed"

    logger.info("Processed Evolution upsert message %s for instance %s", message_id, instance_name)
    return {
        "status": "processed",
        "message_id": message_id,
        "reply_status": reply_status,
    }
