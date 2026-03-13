"""Message Service business logic."""

import logging
from sqlalchemy.orm import Session
from shared.exceptions import ConflictException
from services.message_service.models import ProcessedMessage
from services.message_service.schemas import (
    IncomingMessageEvent,
    ProcessedMessageResponse,
)

logger = logging.getLogger(__name__)


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
