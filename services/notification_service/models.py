"""Notification Service database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from shared.database import Base
import enum


class TargetType(str, enum.Enum):
    MEMBER = "member"
    GROUP = "group"


class ScheduleType(str, enum.Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScheduledNotification(Base):
    __tablename__ = "scheduled_notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    template_id = Column(Integer, ForeignKey("notification_templates.id", ondelete="CASCADE"), nullable=False)
    target_type = Column(SQLEnum(TargetType), nullable=False)
    target_id = Column(Integer, nullable=False)
    schedule_type = Column(SQLEnum(ScheduleType), nullable=False)
    send_time = Column(DateTime(timezone=True), nullable=True)
    cron_expression = Column(String(100), nullable=True)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
