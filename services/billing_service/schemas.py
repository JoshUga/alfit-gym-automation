"""Billing Service Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class PlanCreate(BaseModel):
    name: str
    price: float
    features: Optional[dict] = None
    max_phone_numbers: int = 1
    max_ai_messages: int = 100


class PlanResponse(BaseModel):
    id: int
    name: str
    price: float
    features: Optional[Any] = None
    max_phone_numbers: int
    max_ai_messages: int
    is_active: bool

    model_config = {"from_attributes": True}


class SubscriptionCreate(BaseModel):
    gym_id: int
    plan_id: int


class SubscriptionResponse(BaseModel):
    id: int
    gym_id: int
    plan_id: int
    status: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    amount: float
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DomainCheckoutCreate(BaseModel):
    gym_id: int
    domain_name: str
    years: int = 1


class DomainCheckoutResponse(BaseModel):
    domain_name: str
    years: int
    amount: float
    currency: str
    checkout_url: str
    reference: str
    ipn_token: Optional[str] = None


class DomainPaymentStatusResponse(BaseModel):
    reference: str
    status: str
    domain_name: str
    checkout_url: str
    txid_out: Optional[str] = None
    value_coin: Optional[str] = None
    coin: Optional[str] = None
