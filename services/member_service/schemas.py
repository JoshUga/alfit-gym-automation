"""Member Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class MemberCreate(BaseModel):
    gym_id: int
    name: str
    email: Optional[EmailStr] = None
    phone_number: str


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    status: Optional[str] = None


class MemberResponse(BaseModel):
    id: int
    gym_id: int
    name: str
    email: Optional[str] = None
    phone_number: str
    status: str
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
