"""Workout Service database models."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from shared.database import Base


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    member_name = Column(String(255), nullable=True)
    target = Column(String(255), nullable=True)
    training_days = Column(Text, nullable=True)
    plan_text = Column(Text, nullable=False)
    provider = Column(String(50), nullable=True)
    model = Column(String(120), nullable=True)
    generated_by_ai = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
