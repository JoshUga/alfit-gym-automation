"""Evolution Service database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base
import enum


class InstanceStatus(str, enum.Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"


class EvolutionInstance(Base):
    __tablename__ = "evolution_instances"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    instance_name = Column(String(255), nullable=False)
    status = Column(SQLEnum(InstanceStatus), default=InstanceStatus.PENDING, nullable=False)
    api_url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    webhooks = relationship("WebhookRegistration", back_populates="instance", cascade="all, delete-orphan")


class WebhookRegistration(Base):
    __tablename__ = "webhook_registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("evolution_instances.id", ondelete="CASCADE"), nullable=False, index=True)
    webhook_url = Column(String(500), nullable=False)
    events = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    instance = relationship("EvolutionInstance", back_populates="webhooks")
