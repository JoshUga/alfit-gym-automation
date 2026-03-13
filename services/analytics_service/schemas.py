"""Analytics Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class KPIResponse(BaseModel):
    total_members: int = 0
    active_phone_numbers: int = 0
    messages_sent_7d: int = 0
    messages_sent_30d: int = 0
    ai_responses: int = 0
    notification_delivery_rate: float = 0.0


class MessageLogResponse(BaseModel):
    id: int
    gym_id: int
    sender: str
    recipient: str
    content: Optional[str] = None
    message_type: str
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageVolumeData(BaseModel):
    date: date
    incoming_count: int = 0
    outgoing_count: int = 0
