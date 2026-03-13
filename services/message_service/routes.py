"""Message Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.message_service.schemas import (
    IncomingMessageEvent,
    ProcessedMessageResponse,
)
from services.message_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/messages/process", response_model=APIResponse[ProcessedMessageResponse])
def process_message(
    data: IncomingMessageEvent,
    db: Session = Depends(get_session),
):
    """Process an incoming message."""
    result = service.process_message(db, data)
    return APIResponse(data=result, message="Message processed successfully")


@router.get("/messages/processed", response_model=APIResponse[list[ProcessedMessageResponse]])
def list_processed_messages(
    gym_id: int = Query(..., description="Gym ID"),
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List processed messages."""
    result = service.list_processed_messages(db, gym_id)
    return APIResponse(data=result)
