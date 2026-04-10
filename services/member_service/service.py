"""Member Service business logic."""

import json
from datetime import datetime, UTC
from sqlalchemy import func
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ConflictException
from services.member_service.models import (
    Member,
    MemberGroup,
    MemberGroupAssignment,
    MemberTrainerAssignment,
    MemberStatus,
    MemberPayment,
    MemberPaymentStatus,
)
from services.member_service.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    ScheduleEntry,
    GroupCreate,
    GroupResponse,
    MemberPaymentCreate,
    MemberPaymentResponse,
    TrainerAssignmentResponse,
)


def _parse_weekly_schedule(schedule_value: str | None) -> list[ScheduleEntry] | None:
    if not schedule_value:
        return None
    try:
        payload = json.loads(schedule_value)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(payload, list):
        return None

    parsed: list[ScheduleEntry] = []
    for entry in payload:
        if not isinstance(entry, dict):
            continue
        try:
            parsed.append(ScheduleEntry.model_validate(entry))
        except Exception:
            continue
    return parsed or None


def _format_weekly_schedule(entries: list[ScheduleEntry]) -> str:
    return "\n".join(
        f"{entry.day}: {entry.activity} ({entry.start_time} - {entry.end_time})"
        for entry in entries
    )


def _parse_training_days(training_days_value: str | None) -> list[str] | None:
    if not training_days_value:
        return None
    try:
        payload = json.loads(training_days_value)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, list):
        return None
    parsed = [str(day).strip() for day in payload if str(day).strip()]
    return parsed or None


def _resolve_schedule_storage(
    schedule: str | None,
    weekly_schedule: list[ScheduleEntry] | None,
) -> str | None:
    if weekly_schedule is not None:
        if not weekly_schedule:
            return None
        return json.dumps([entry.model_dump() for entry in weekly_schedule])
    return schedule


def _member_to_response(member: Member) -> MemberResponse:
    weekly_schedule = _parse_weekly_schedule(member.schedule)
    schedule_text = _format_weekly_schedule(weekly_schedule) if weekly_schedule else member.schedule
    training_days = _parse_training_days(member.training_days)
    if training_days is None and member.schedule and member.schedule.lower().startswith("training days:"):
        raw_days = member.schedule.split(":", 1)[1] if ":" in member.schedule else ""
        inferred_days = [day.strip() for day in raw_days.split(",") if day.strip()]
        training_days = inferred_days or None
    return MemberResponse(
        id=member.id,
        gym_id=member.gym_id,
        name=member.name,
        email=member.email,
        phone_number=member.phone_number,
        status=member.status.value if hasattr(member.status, "value") else str(member.status),
        schedule=schedule_text,
        training_days=training_days,
        target=member.target,
        monthly_payment_amount=member.monthly_payment_amount,
        trainer_user_ids=[assignment.trainer_user_id for assignment in (member.trainer_assignments or [])],
        weekly_schedule=weekly_schedule,
        created_at=member.created_at,
    )


def add_member(db: Session, data: MemberCreate) -> MemberResponse:
    """Add a new member to a gym."""
    member = Member(
        gym_id=data.gym_id,
        name=data.name,
        email=data.email,
        phone_number=data.phone_number,
        schedule=_resolve_schedule_storage(data.schedule, data.weekly_schedule),
        training_days=json.dumps(data.training_days),
        target=data.target,
        monthly_payment_amount=data.monthly_payment_amount,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _member_to_response(member)


def get_member(db: Session, member_id: int) -> MemberResponse:
    """Get a member by ID."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)
    return _member_to_response(member)


def list_gym_members(db: Session, gym_id: int) -> list[MemberResponse]:
    """List all members for a gym."""
    members = db.query(Member).filter(Member.gym_id == gym_id).all()
    return [_member_to_response(m) for m in members]


def list_trainer_members(db: Session, gym_id: int, trainer_user_id: int) -> list[MemberResponse]:
    members = (
        db.query(Member)
        .join(
            MemberTrainerAssignment,
            MemberTrainerAssignment.member_id == Member.id,
        )
        .filter(
            Member.gym_id == gym_id,
            MemberTrainerAssignment.trainer_user_id == trainer_user_id,
        )
        .all()
    )
    return [_member_to_response(member) for member in members]


def update_member(db: Session, member_id: int, data: MemberUpdate) -> MemberResponse:
    """Update a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    update_data = data.model_dump(exclude_unset=True)
    if "weekly_schedule" in update_data or "schedule" in update_data:
        member.schedule = _resolve_schedule_storage(
            update_data.get("schedule"),
            update_data.get("weekly_schedule"),
        )
        update_data.pop("schedule", None)
        update_data.pop("weekly_schedule", None)

    if "training_days" in update_data:
        training_days = update_data.pop("training_days")
        member.training_days = json.dumps(training_days) if training_days else None

    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return _member_to_response(member)


def delete_member(db: Session, member_id: int) -> dict:
    """Soft-delete a member by setting status to suspended."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)
    member.status = MemberStatus.SUSPENDED
    db.commit()
    return {"message": "Member deleted successfully"}


def create_group(db: Session, gym_id: int, data: GroupCreate) -> GroupResponse:
    """Create a member group."""
    group = MemberGroup(
        gym_id=gym_id,
        name=data.name,
        description=data.description,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return GroupResponse.model_validate(group)


def list_groups(db: Session, gym_id: int) -> list[GroupResponse]:
    """List all groups for a gym."""
    groups = db.query(MemberGroup).filter(MemberGroup.gym_id == gym_id).all()
    return [GroupResponse.model_validate(g) for g in groups]


def assign_member_to_group(db: Session, group_id: int, member_id: int) -> dict:
    """Assign a member to a group."""
    group = db.query(MemberGroup).filter(MemberGroup.id == group_id).first()
    if not group:
        raise NotFoundException("Group", group_id)
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    existing = (
        db.query(MemberGroupAssignment)
        .filter(
            MemberGroupAssignment.group_id == group_id,
            MemberGroupAssignment.member_id == member_id,
        )
        .first()
    )
    if existing:
        raise ConflictException("Member is already in this group")

    assignment = MemberGroupAssignment(member_id=member_id, group_id=group_id)
    db.add(assignment)
    db.commit()
    return {"message": "Member assigned to group successfully"}


def remove_member_from_group(db: Session, group_id: int, member_id: int) -> dict:
    """Remove a member from a group."""
    assignment = (
        db.query(MemberGroupAssignment)
        .filter(
            MemberGroupAssignment.group_id == group_id,
            MemberGroupAssignment.member_id == member_id,
        )
        .first()
    )
    if not assignment:
        raise NotFoundException("MemberGroupAssignment", f"{group_id}/{member_id}")
    db.delete(assignment)
    db.commit()
    return {"message": "Member removed from group successfully"}


def list_member_payments(db: Session, member_id: int) -> list[MemberPaymentResponse]:
    """List payments for a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    payments = (
        db.query(MemberPayment)
        .filter(MemberPayment.member_id == member_id)
        .order_by(MemberPayment.paid_at.desc(), MemberPayment.created_at.desc())
        .all()
    )
    return [MemberPaymentResponse.model_validate(payment) for payment in payments]


def create_member_payment(
    db: Session,
    member_id: int,
    data: MemberPaymentCreate,
) -> MemberPaymentResponse:
    """Register a payment for a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    normalized_status = (data.status or "completed").strip().lower()
    allowed_statuses = {status.value for status in MemberPaymentStatus}
    if normalized_status not in allowed_statuses:
        normalized_status = MemberPaymentStatus.COMPLETED.value

    billing_month = (data.billing_month or "").strip()
    if not billing_month:
        reference_date = data.paid_at or datetime.now(UTC)
        billing_month = reference_date.strftime("%Y-%m")
    else:
        try:
            datetime.strptime(billing_month, "%Y-%m")
        except ValueError:
            billing_month = datetime.now(UTC).strftime("%Y-%m")

    completed_paid_so_far = (
        db.query(func.coalesce(func.sum(MemberPayment.amount), 0))
        .filter(
            MemberPayment.member_id == member.id,
            MemberPayment.billing_month == billing_month,
            MemberPayment.status == MemberPaymentStatus.COMPLETED,
        )
        .scalar()
    )
    already_paid = int(completed_paid_so_far or 0)
    paid_after_this = already_paid + (data.amount if normalized_status == MemberPaymentStatus.COMPLETED.value else 0)
    balance_left = None
    if member.monthly_payment_amount is not None and member.monthly_payment_amount > 0:
        balance_left = max(member.monthly_payment_amount - paid_after_this, 0)

    payment = MemberPayment(
        member_id=member.id,
        gym_id=member.gym_id,
        amount=data.amount,
        currency=(data.currency or "UGX").upper(),
        payment_method=data.payment_method,
        status=MemberPaymentStatus(normalized_status),
        billing_month=billing_month,
        balance_left=balance_left,
        paid_at=data.paid_at,
        note=data.note,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return MemberPaymentResponse.model_validate(payment)


def list_trainer_assignments(
    db: Session,
    gym_id: int,
    trainer_user_id: int | None = None,
) -> list[TrainerAssignmentResponse]:
    query = (
        db.query(MemberTrainerAssignment)
        .join(Member, MemberTrainerAssignment.member_id == Member.id)
        .filter(Member.gym_id == gym_id)
    )
    if trainer_user_id is not None:
        query = query.filter(MemberTrainerAssignment.trainer_user_id == trainer_user_id)
    assignments = query.order_by(MemberTrainerAssignment.id.desc()).all()
    return [TrainerAssignmentResponse.model_validate(assignment) for assignment in assignments]


def assign_trainer_to_member(
    db: Session,
    member_id: int,
    trainer_user_id: int,
) -> TrainerAssignmentResponse:
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    existing = (
        db.query(MemberTrainerAssignment)
        .filter(
            MemberTrainerAssignment.member_id == member_id,
            MemberTrainerAssignment.trainer_user_id == trainer_user_id,
        )
        .first()
    )
    if existing:
        return TrainerAssignmentResponse.model_validate(existing)

    assignment = MemberTrainerAssignment(
        member_id=member_id,
        trainer_user_id=trainer_user_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return TrainerAssignmentResponse.model_validate(assignment)


def remove_trainer_from_member(db: Session, member_id: int, trainer_user_id: int) -> dict:
    assignment = (
        db.query(MemberTrainerAssignment)
        .filter(
            MemberTrainerAssignment.member_id == member_id,
            MemberTrainerAssignment.trainer_user_id == trainer_user_id,
        )
        .first()
    )
    if not assignment:
        raise NotFoundException("MemberTrainerAssignment", f"{member_id}/{trainer_user_id}")
    db.delete(assignment)
    db.commit()
    return {"message": "Trainer removed from member successfully"}
