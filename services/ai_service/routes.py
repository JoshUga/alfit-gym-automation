"""AI Service API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.ai_service.schemas import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    GenerateResponseRequest,
    GenerateResponseResult,
)
from services.ai_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/ai/configs", response_model=APIResponse[AIConfigResponse])
def create_ai_config(
    data: AIConfigCreate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create an AI configuration."""
    result = service.create_ai_config(db, data)
    return APIResponse(data=result, message="AI config created successfully")


@router.get("/ai/configs/{config_id}", response_model=APIResponse[AIConfigResponse])
def get_ai_config(
    config_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get an AI configuration."""
    result = service.get_ai_config(db, config_id)
    return APIResponse(data=result)


@router.get("/gyms/{gym_id}/ai/configs", response_model=APIResponse[list[AIConfigResponse]])
def list_ai_configs(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List AI configurations for a gym."""
    result = service.list_ai_configs(db, gym_id)
    return APIResponse(data=result)


@router.put("/ai/configs/{config_id}", response_model=APIResponse[AIConfigResponse])
def update_ai_config(
    config_id: int,
    data: AIConfigUpdate,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update an AI configuration."""
    result = service.update_ai_config(db, config_id, data)
    return APIResponse(data=result, message="AI config updated successfully")


@router.post("/ai/generate-response", response_model=APIResponse[GenerateResponseResult])
def generate_response(
    data: GenerateResponseRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Generate an AI response for an incoming message."""
    result = service.generate_response(db, data)
    return APIResponse(data=result)
