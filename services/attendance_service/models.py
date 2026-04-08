"""Attendance Service database models."""

from sqlalchemy import Column, Integer, String, Date, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from shared.database import Base
import enum


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    gym_id = Column(Integer, nullable=False, index=True)
    member_id = Column(Integer, nullable=False, index=True)
    attendance_date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(AttendanceStatus), nullable=False, default=AttendanceStatus.PRESENT)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
