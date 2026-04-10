"""Member Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field
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
    training_days: list[str]
    target: str
    monthly_payment_amount: int
    weekly_schedule: Optional[list[ScheduleEntry]] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None
    schedule: Optional[str] = None
    training_days: Optional[list[str]] = None
    target: Optional[str] = None
    monthly_payment_amount: Optional[int] = None
    weekly_schedule: Optional[list[ScheduleEntry]] = None


class MemberResponse(BaseModel):
    id: int
    gym_id: int
    name: str
    email: Optional[str] = None
    phone_number: str
    status: str
    schedule: Optional[str] = None
    training_days: Optional[list[str]] = None
    target: Optional[str] = None
    monthly_payment_amount: Optional[int] = None
    trainer_user_ids: list[int] = Field(default_factory=list)
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


class MemberPaymentCreate(BaseModel):
    amount: int
    currency: str = "UGX"
    payment_method: Optional[str] = None
    status: str = "completed"
    billing_month: Optional[str] = None
    paid_at: Optional[datetime] = None
    note: Optional[str] = None


class MemberPaymentResponse(BaseModel):
    id: int
    member_id: int
    gym_id: int
    amount: int
    currency: str
    payment_method: Optional[str] = None
    status: str
    billing_month: Optional[str] = None
    balance_left: Optional[int] = None
    paid_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TrainerAssignmentCreate(BaseModel):
    trainer_user_id: int


class TrainerAssignmentResponse(BaseModel):
    id: int
    member_id: int
    trainer_user_id: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
