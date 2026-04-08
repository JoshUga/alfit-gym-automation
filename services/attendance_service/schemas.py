"""Attendance Service Pydantic schemas."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class AttendanceRecordCreate(BaseModel):
    gym_id: int
    member_id: int
    attendance_date: date
    status: str = "present"
    note: Optional[str] = None


class AttendanceRecordResponse(BaseModel):
    id: int
    gym_id: int
    member_id: int
    attendance_date: date
    status: str
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AttendanceSummaryResponse(BaseModel):
    member_id: int
    gym_id: int
    total_sessions: int
    present_sessions: int
    absent_sessions: int
    attendance_rate: int
