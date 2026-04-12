"""Billing Service database models."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base
import enum


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    features = Column(JSON, nullable=True)
    max_phone_numbers = Column(Integer, default=1)
    max_ai_messages = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subscription = relationship("Subscription", back_populates="payments")


class DomainOrder(Base):
    __tablename__ = "domain_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    domain_name = Column(String(255), nullable=False, index=True)
    years = Column(Integer, nullable=False, default=1)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="USD")
    provider = Column(String(50), nullable=False, default="paygate")
    payment_reference = Column(String(255), nullable=False, unique=True, index=True)
    checkout_url = Column(String(1000), nullable=False)
    callback_url = Column(String(1000), nullable=True)
    address_in = Column(String(255), nullable=True)
    polygon_address_in = Column(String(255), nullable=True)
    ipn_token = Column(String(1024), nullable=True)
    paid_value_coin = Column(String(100), nullable=True)
    paid_coin = Column(String(50), nullable=True)
    txid_in = Column(String(255), nullable=True)
    txid_out = Column(String(255), nullable=True)
    value_forwarded_coin = Column(String(100), nullable=True)
    status = Column(String(30), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
