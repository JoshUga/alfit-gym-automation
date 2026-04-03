"""AI Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


class AIRuntimeConfigResponse(BaseModel):
    provider: str
    model_name: str
    configured: bool
    base_prompt: str
    source: str = "environment"


class GenerateResponseRequest(BaseModel):
    gym_id: int
    phone_number_id: int
    incoming_message: str


class GenerateResponseResult(BaseModel):
    response_text: str
    provider: str
    model: Optional[str] = None
    response_time_ms: float
