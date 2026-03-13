"""Gym Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GymCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class GymUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class GymResponse(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    owner_id: int
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PhoneNumberCreate(BaseModel):
    phone_number: str
    label: Optional[str] = None


class PhoneNumberResponse(BaseModel):
    id: int
    phone_number: str
    label: Optional[str] = None
    is_active: bool
    evolution_instance_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class EvolutionCredentialCreate(BaseModel):
    api_key: str
    instance_name: str


class EvolutionCredentialResponse(BaseModel):
    id: int
    instance_name: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
