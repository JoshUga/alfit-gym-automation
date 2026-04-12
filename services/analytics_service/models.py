"""Analytics Service database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, Boolean
from sqlalchemy.sql import func
from shared.database import Base
import enum


class MessageType(str, enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)


class GymPhoneNumber(Base):
    __tablename__ = "gym_phone_numbers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)


class MessageLog(Base):
    __tablename__ = "message_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    phone_number_id = Column(Integer, nullable=True)
    sender = Column(String(100), nullable=False)
    recipient = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)
    message_type = Column(SQLEnum(MessageType), nullable=False)
    status = Column(String(50), default="delivered")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
