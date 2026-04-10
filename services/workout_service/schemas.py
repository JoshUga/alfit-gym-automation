"""Workout Service Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class WorkoutPlanGenerateRequest(BaseModel):
    gym_id: int
    member_name: str
    target: Optional[str] = None
    training_days: Optional[list[str]] = None


class WorkoutPlanUpdateRequest(BaseModel):
    member_name: Optional[str] = None
    target: Optional[str] = None
    training_days: Optional[list[str]] = None
    plan_text: str


class WorkoutPlanResponse(BaseModel):
    id: int
    gym_id: int
    member_id: int
    member_name: Optional[str] = None
    target: Optional[str] = None
    training_days: Optional[list[str]] = None
    plan_text: str
    provider: Optional[str] = None
    model: Optional[str] = None
    generated_by_ai: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
