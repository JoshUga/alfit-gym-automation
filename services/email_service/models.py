"""Email Service database models."""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from shared.database import Base
import enum


class EmailStatus(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    template_name = Column(String(255), nullable=True)
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.SENT, nullable=False)
    provider = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SMTPAccount(Base):
    __tablename__ = "smtp_accounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    emailengine_account_id = Column(String(255), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    health_status = Column(String(50), nullable=False, default="unknown")
    last_health_check_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GymSMTPSettings(Base):
    __tablename__ = "gym_smtp_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, unique=True, index=True)
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False, default=587)
    username = Column(String(255), nullable=False)
    password = Column(String(512), nullable=False)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    secure = Column(Boolean, default=False, nullable=False)
    starttls = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
