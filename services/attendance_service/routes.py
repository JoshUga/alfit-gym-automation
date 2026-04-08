"""Attendance Service API routes."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.attendance_service.schemas import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
)
from services.attendance_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/attendance/records", response_model=APIResponse[AttendanceRecordResponse])
def create_record(
    data: AttendanceRecordCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create or update a member attendance record for a specific date."""
    result = service.create_attendance_record(db, data)
    return APIResponse(data=result, message="Attendance saved successfully")


@router.get("/gyms/{gym_id}/attendance/records", response_model=APIResponse[list[AttendanceRecordResponse]])
def list_records(
    gym_id: int,
    member_id: int | None = Query(None),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List attendance records for a gym (optionally filtered by member/date range)."""
    result = service.list_attendance_records(db, gym_id, member_id, start_date, end_date)
    return APIResponse(data=result)


@router.get(
    "/gyms/{gym_id}/members/{member_id}/attendance/summary",
    response_model=APIResponse[AttendanceSummaryResponse],
)
def member_summary(
    gym_id: int,
    member_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get attendance summary for a member."""
    result = service.get_member_attendance_summary(db, gym_id, member_id)
    return APIResponse(data=result)
