"""AI Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIConfigCreate(BaseModel):
    gym_id: int
    provider: str
    api_key: str
    model_name: Optional[str] = None
    base_prompt: str


class AIConfigUpdate(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    base_prompt: Optional[str] = None
    is_active: Optional[bool] = None


class AIConfigResponse(BaseModel):
    id: int
    gym_id: int
    provider: str
    model_name: Optional[str] = None
    base_prompt: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GenerateResponseRequest(BaseModel):
    gym_id: int
    phone_number_id: int
    incoming_message: str


class GenerateResponseResult(BaseModel):
    response_text: str
    provider: str
    model: Optional[str] = None
    response_time_ms: float
