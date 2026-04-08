"""AI Service API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.ai_service.schemas import (
    AIRuntimeConfigResponse,
    GenerateResponseRequest,
    GenerateResponseResult,
)
from services.ai_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/ai/configs", response_model=APIResponse)
def create_ai_config(
    data: dict,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Create an AI configuration."""
    service.create_ai_config(db, data)
    return APIResponse(message="AI config created successfully")


@router.get("/ai/configs/{config_id}", response_model=APIResponse)
def get_ai_config(
    config_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get an AI configuration."""
    service.get_ai_config(db, config_id)
    return APIResponse()


@router.get("/gyms/{gym_id}/ai/configs", response_model=APIResponse[list])
def list_ai_configs(
    gym_id: int,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """List AI configurations for a gym."""
    result = service.list_ai_configs(db, gym_id)
    return APIResponse(data=result)


@router.put("/ai/configs/{config_id}", response_model=APIResponse)
def update_ai_config(
    config_id: int,
    data: dict,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Update an AI configuration."""
    service.update_ai_config(db, config_id, data)
    return APIResponse(message="AI config updated successfully")


@router.get("/ai/runtime-config", response_model=APIResponse[AIRuntimeConfigResponse])
def get_runtime_config(
    current_user: UserClaims = Depends(get_current_user),
):
    """Get effective AI configuration loaded from environment variables."""
    result = service.get_runtime_config()
    return APIResponse(data=result)


@router.post("/ai/generate-response", response_model=APIResponse[GenerateResponseResult])
def generate_response(
    data: GenerateResponseRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Generate an AI response for an incoming message."""
    result = service.generate_response(db, data)
    return APIResponse(data=result)


@router.post("/ai/generate-response/internal", response_model=APIResponse[GenerateResponseResult])
def generate_response_internal(
    data: GenerateResponseRequest,
    db: Session = Depends(get_session),
):
    """Internal service endpoint for generating AI responses without user JWT."""
    result = service.generate_response(db, data)
    return APIResponse(data=result)
