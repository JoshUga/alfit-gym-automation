"""Analytics Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.analytics_service.schemas import (
    KPIResponse,
    MessageLogResponse,
    MessageVolumeData,
)
from services.analytics_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.get("/analytics/kpis", response_model=APIResponse[KPIResponse])
def get_kpis(
    gym_id: int = Query(..., description="Gym ID"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get KPIs for a gym."""
    result = service.get_kpis(db, gym_id)
    return APIResponse(data=result)


@router.get("/analytics/message-volume", response_model=APIResponse[list[MessageVolumeData]])
def get_message_volume(
    gym_id: int = Query(..., description="Gym ID"),
    days: int = Query(30, description="Number of days to look back"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get message volume trends."""
    result = service.get_message_volume(db, gym_id, days)
    return APIResponse(data=result)


@router.get("/analytics/notification-delivery", response_model=APIResponse[dict])
def get_notification_delivery(
    gym_id: int = Query(..., description="Gym ID"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get notification delivery report."""
    result = service.get_notification_delivery_report(db, gym_id)
    return APIResponse(data=result)


@router.get("/logs/messages", response_model=APIResponse[list[MessageLogResponse]])
def get_message_logs(
    gym_id: int = Query(..., description="Gym ID"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get message logs."""
    result = service.get_message_logs(db, gym_id)
    return APIResponse(data=result)
