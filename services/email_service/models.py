"""Email Service database models."""

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
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
