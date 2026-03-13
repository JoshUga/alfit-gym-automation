"""AI Service database models."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from shared.database import Base
import enum


class AIProvider(str, enum.Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    OPENROUTER = "openrouter"


class AIConfig(Base):
    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    provider = Column(SQLEnum(AIProvider), nullable=False)
    api_key_encrypted = Column(String(1000), nullable=False)
    model_name = Column(String(255), nullable=True)
    base_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AIResponseLog(Base):
    __tablename__ = "ai_response_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    phone_number_id = Column(Integer, nullable=False)
    incoming_message = Column(Text, nullable=False)
    prompt_used = Column(Text, nullable=True)
    ai_provider = Column(String(50), nullable=False)
    ai_response = Column(Text, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
