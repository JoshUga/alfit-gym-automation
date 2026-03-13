"""Evolution Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class InstanceCreate(BaseModel):
    gym_id: int
    instance_name: str
    api_url: str


class InstanceResponse(BaseModel):
    id: int
    gym_id: int
    instance_name: str
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    instance_id: int
    to_number: str
    message_content: str
    message_type: Optional[str] = "text"


class SendMessageResponse(BaseModel):
    message_id: Optional[str] = None
    status: str


class WebhookRegisterRequest(BaseModel):
    instance_id: int
    webhook_url: str
    events: Optional[list[str]] = None


class WebhookRegistrationResponse(BaseModel):
    id: int
    instance_id: int
    webhook_url: str
    events: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WebhookPayload(BaseModel):
    event_type: str
    data: Any
