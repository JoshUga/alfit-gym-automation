"""Notification Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TemplateCreate(BaseModel):
    gym_id: int
    name: str
    content: str


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


class TemplateResponse(BaseModel):
    id: int
    gym_id: int
    name: str
    content: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    content: str
    variables: Optional[dict] = None


class ScheduleCreate(BaseModel):
    gym_id: int
    template_id: int
    target_type: str
    target_id: int
    schedule_type: str
    send_time: Optional[datetime] = None
    cron_expression: Optional[str] = None


class ScheduleUpdate(BaseModel):
    send_time: Optional[datetime] = None
    cron_expression: Optional[str] = None
    status: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    gym_id: int
    template_id: int
    target_type: str
    target_id: int
    schedule_type: str
    send_time: Optional[datetime] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
