"""Member Service business logic."""

import json
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ConflictException
from services.member_service.models import Member, MemberGroup, MemberGroupAssignment, MemberStatus
from services.member_service.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    ScheduleEntry,
    GroupCreate,
    GroupResponse,
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
    return MemberResponse(
        id=member.id,
        gym_id=member.gym_id,
        name=member.name,
        email=member.email,
        phone_number=member.phone_number,
        status=member.status.value if hasattr(member.status, "value") else str(member.status),
        schedule=schedule_text,
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
