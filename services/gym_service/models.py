"""Gym Service database models."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base


class Gym(Base):
    __tablename__ = "gyms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    owner_id = Column(Integer, nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    phone_numbers = relationship("GymPhoneNumber", back_populates="gym", cascade="all, delete-orphan")
    evolution_credentials = relationship("EvolutionCredential", back_populates="gym", cascade="all, delete-orphan")


class GymPhoneNumber(Base):
    __tablename__ = "gym_phone_numbers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False)
    label = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    evolution_instance_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gym = relationship("Gym", back_populates="phone_numbers")


class EvolutionCredential(Base):
    __tablename__ = "evolution_credentials"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key = Column(String(500), nullable=False)
    instance_name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    gym = relationship("Gym", back_populates="evolution_credentials")
