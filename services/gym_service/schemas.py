"""Gym Service Pydantic schemas."""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GymCreate(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: EmailStr


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


class WhatsAppConnectRequest(BaseModel):
    instance_name: Optional[str] = None
    phone_number: str


class WhatsAppConnectResponse(BaseModel):
    instance_name: str
    status: str
    qr_code: Optional[str] = None
    pairing_code: Optional[str] = None


class WhatsAppStatusResponse(BaseModel):
    instance_name: str
    status: str


class WhatsAppSendWelcomeRequest(BaseModel):
    member_name: str
    member_phone: str
    schedule: Optional[str] = None
    training_days: Optional[list[str]] = None
    target: Optional[str] = None
    monthly_payment_amount: Optional[int] = None


class WhatsAppSendWelcomeResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    code: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None


class WhatsAppOnboardingWelcomeRequest(BaseModel):
    phone_number: str
    owner_name: Optional[str] = None


class WhatsAppOnboardingWelcomeResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    email_status: Optional[str] = None
    email_reason: Optional[str] = None
