"""Attendance Service business logic."""

from datetime import date
from sqlalchemy import func
from sqlalchemy.orm import Session
from shared.exceptions import ValidationException
from services.attendance_service.models import AttendanceRecord, AttendanceStatus
from services.attendance_service.schemas import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
)


def _normalize_status(status: str) -> AttendanceStatus:
    normalized = (status or "present").strip().lower()
    if normalized not in {AttendanceStatus.PRESENT.value, AttendanceStatus.ABSENT.value}:
        raise ValidationException("Attendance status must be either 'present' or 'absent'")
    return AttendanceStatus(normalized)


def create_attendance_record(db: Session, data: AttendanceRecordCreate) -> AttendanceRecordResponse:
    status = _normalize_status(data.status)

    existing = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.gym_id == data.gym_id,
            AttendanceRecord.member_id == data.member_id,
            AttendanceRecord.attendance_date == data.attendance_date,
        )
        .first()
    )

    if existing:
        existing.status = status
        existing.note = data.note
        db.commit()
        db.refresh(existing)
        return AttendanceRecordResponse.model_validate(existing)

    record = AttendanceRecord(
        gym_id=data.gym_id,
        member_id=data.member_id,
        attendance_date=data.attendance_date,
        status=status,
        note=data.note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return AttendanceRecordResponse.model_validate(record)


def list_attendance_records(
    db: Session,
    gym_id: int,
    member_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[AttendanceRecordResponse]:
    query = db.query(AttendanceRecord).filter(AttendanceRecord.gym_id == gym_id)

    if member_id is not None:
        query = query.filter(AttendanceRecord.member_id == member_id)
    if start_date is not None:
        query = query.filter(AttendanceRecord.attendance_date >= start_date)
    if end_date is not None:
        query = query.filter(AttendanceRecord.attendance_date <= end_date)

    records = query.order_by(AttendanceRecord.attendance_date.desc(), AttendanceRecord.created_at.desc()).all()
    return [AttendanceRecordResponse.model_validate(record) for record in records]


def get_member_attendance_summary(db: Session, gym_id: int, member_id: int) -> AttendanceSummaryResponse:
    grouped = (
        db.query(AttendanceRecord.status, func.count(AttendanceRecord.id))
        .filter(
            AttendanceRecord.gym_id == gym_id,
            AttendanceRecord.member_id == member_id,
        )
        .group_by(AttendanceRecord.status)
        .all()
    )

    present_sessions = 0
    absent_sessions = 0
    for status, count in grouped:
        normalized = status.value if hasattr(status, "value") else str(status)
        if normalized == AttendanceStatus.PRESENT.value:
            present_sessions = int(count)
        elif normalized == AttendanceStatus.ABSENT.value:
            absent_sessions = int(count)

    total_sessions = present_sessions + absent_sessions
    attendance_rate = int(round((present_sessions / total_sessions) * 100)) if total_sessions else 0

    return AttendanceSummaryResponse(
        member_id=member_id,
        gym_id=gym_id,
        total_sessions=total_sessions,
        present_sessions=present_sessions,
        absent_sessions=absent_sessions,
        attendance_rate=attendance_rate,
    )
