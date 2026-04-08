"""Message Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class IncomingMessageEvent(BaseModel):
    message_id: str
    gym_id: int
    phone_number_id: int
    sender: str
    content: str
    timestamp: Optional[datetime] = None


class ProcessedMessageResponse(BaseModel):
    id: int
    message_id: str
    sender: str
    content: Optional[str] = None
    is_processed: bool
    ai_response_triggered: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvolutionUpsertWebhook(BaseModel):
    event: Optional[str] = None
    event_type: Optional[str] = None
    instance: Optional[str] = None
    instance_name: Optional[str] = None
    data: Any = None
