"""Analytics Service business logic."""

from datetime import datetime, timedelta, timezone, date
from sqlalchemy import func as sql_func, cast, Date
from sqlalchemy.orm import Session
from services.gym_service.models import GymPhoneNumber
from services.member_service.models import Member
from services.analytics_service.models import MessageLog, MessageType
from services.analytics_service.schemas import (
    KPIResponse,
    MessageLogResponse,
    MessageVolumeData,
)


def get_kpis(db: Session, gym_id: int) -> KPIResponse:
    """Get KPIs for a gym."""
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    total_members = (
        db.query(sql_func.count(Member.id))
        .filter(Member.gym_id == gym_id)
        .scalar()
        or 0
    )

    active_phone_numbers = (
        db.query(sql_func.count(GymPhoneNumber.id))
        .filter(GymPhoneNumber.gym_id == gym_id, GymPhoneNumber.is_active.is_(True))
        .scalar()
        or 0
    )

    messages_7d = (
        db.query(sql_func.count(MessageLog.id))
        .filter(
            MessageLog.gym_id == gym_id,
            MessageLog.message_type == MessageType.OUTGOING,
            MessageLog.created_at >= seven_days_ago,
        )
        .scalar()
        or 0
    )

    messages_30d = (
        db.query(sql_func.count(MessageLog.id))
        .filter(
            MessageLog.gym_id == gym_id,
            MessageLog.message_type == MessageType.OUTGOING,
            MessageLog.created_at >= thirty_days_ago,
        )
        .scalar()
        or 0
    )

    total_messages = (
        db.query(sql_func.count(MessageLog.id))
        .filter(MessageLog.gym_id == gym_id)
        .scalar()
        or 0
    )
    delivered = (
        db.query(sql_func.count(MessageLog.id))
        .filter(MessageLog.gym_id == gym_id, MessageLog.status == "delivered")
        .scalar()
        or 0
    )
    delivery_rate = (delivered / total_messages * 100) if total_messages > 0 else 0.0

    return KPIResponse(
        total_members=total_members,
        active_phone_numbers=active_phone_numbers,
        messages_sent_7d=messages_7d,
        messages_sent_30d=messages_30d,
        notification_delivery_rate=round(delivery_rate, 2),
    )


def get_message_volume(db: Session, gym_id: int, days: int = 30) -> list[MessageVolumeData]:
    """Get message volume trends for a gym."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = (
        db.query(
            cast(MessageLog.created_at, Date).label("log_date"),
            MessageLog.message_type,
            sql_func.count(MessageLog.id).label("count"),
        )
        .filter(MessageLog.gym_id == gym_id, MessageLog.created_at >= since)
        .group_by("log_date", MessageLog.message_type)
        .order_by("log_date")
        .all()
    )

    volume_map: dict[date, dict[str, int]] = {}
    for row in rows:
        d = row.log_date
        if d not in volume_map:
            volume_map[d] = {"incoming": 0, "outgoing": 0}
        volume_map[d][row.message_type.value] = row.count

    return [
        MessageVolumeData(date=d, incoming_count=v["incoming"], outgoing_count=v["outgoing"])
        for d, v in sorted(volume_map.items())
    ]


def get_notification_delivery_report(db: Session, gym_id: int) -> dict:
    """Get notification delivery report for a gym."""
    total = (
        db.query(sql_func.count(MessageLog.id))
        .filter(
            MessageLog.gym_id == gym_id,
            MessageLog.message_type == MessageType.OUTGOING,
        )
        .scalar()
        or 0
    )
    delivered = (
        db.query(sql_func.count(MessageLog.id))
        .filter(
            MessageLog.gym_id == gym_id,
            MessageLog.message_type == MessageType.OUTGOING,
            MessageLog.status == "delivered",
        )
        .scalar()
        or 0
    )
    failed = total - delivered
    rate = (delivered / total * 100) if total > 0 else 0.0

    return {
        "total_sent": total,
        "delivered": delivered,
        "failed": failed,
        "delivery_rate": round(rate, 2),
    }


def get_message_logs(db: Session, gym_id: int) -> list[MessageLogResponse]:
    """Get message logs for a gym."""
    logs = (
        db.query(MessageLog)
        .filter(MessageLog.gym_id == gym_id)
        .order_by(MessageLog.created_at.desc())
        .all()
    )
    return [MessageLogResponse.model_validate(log) for log in logs]
