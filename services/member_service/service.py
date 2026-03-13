"""Member Service business logic."""

from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ConflictException
from services.member_service.models import Member, MemberGroup, MemberGroupAssignment, MemberStatus
from services.member_service.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    GroupCreate,
    GroupResponse,
)


def add_member(db: Session, data: MemberCreate) -> MemberResponse:
    """Add a new member to a gym."""
    member = Member(
        gym_id=data.gym_id,
        name=data.name,
        email=data.email,
        phone_number=data.phone_number,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return MemberResponse.model_validate(member)


def get_member(db: Session, member_id: int) -> MemberResponse:
    """Get a member by ID."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)
    return MemberResponse.model_validate(member)


def list_gym_members(db: Session, gym_id: int) -> list[MemberResponse]:
    """List all members for a gym."""
    members = db.query(Member).filter(Member.gym_id == gym_id).all()
    return [MemberResponse.model_validate(m) for m in members]


def update_member(db: Session, member_id: int, data: MemberUpdate) -> MemberResponse:
    """Update a member."""
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        raise NotFoundException("Member", member_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)
    return MemberResponse.model_validate(member)


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
