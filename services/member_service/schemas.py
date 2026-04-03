"""Member Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ScheduleEntry(BaseModel):
    day: str
    start_time: str
    end_time: str
    activity: str


class MemberCreate(BaseModel):
    gym_id: int
    name: str
    email: Optional[EmailStr] = None
    phone_number: str
    schedule: Optional[str] = None
    weekly_schedule: Optional[list[ScheduleEntry]] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
    schedule: Optional[str] = None
    weekly_schedule: Optional[list[ScheduleEntry]] = None


class MemberResponse(BaseModel):
    id: int
    gym_id: int
    name: str
    email: Optional[str] = None
    phone_number: str
    status: str
    schedule: Optional[str] = None
    weekly_schedule: Optional[list[ScheduleEntry]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupResponse(BaseModel):
    id: int
    gym_id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
