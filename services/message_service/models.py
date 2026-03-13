"""Message Service database models."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from shared.database import Base


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String(255), nullable=False, unique=True, index=True)
    gym_id = Column(Integer, nullable=False, index=True)
    phone_number_id = Column(Integer, nullable=False)
    sender = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)
    is_processed = Column(Boolean, default=False)
    ai_response_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
