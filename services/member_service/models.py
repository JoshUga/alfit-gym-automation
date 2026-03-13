"""Member Service database models."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from shared.database import Base
import enum


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TRIAL = "trial"


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=False)
    status = Column(SQLEnum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    group_assignments = relationship("MemberGroupAssignment", back_populates="member", cascade="all, delete-orphan")


class MemberGroup(Base):
    __tablename__ = "member_groups"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assignments = relationship("MemberGroupAssignment", back_populates="group", cascade="all, delete-orphan")


class MemberGroupAssignment(Base):
    __tablename__ = "member_group_assignments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    member_id = Column(Integer, ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("member_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    member = relationship("Member", back_populates="group_assignments")
    group = relationship("MemberGroup", back_populates="assignments")
