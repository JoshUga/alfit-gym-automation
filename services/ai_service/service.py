"""AI Service business logic."""

import time
import logging
from sqlalchemy.orm import Session
from shared.exceptions import NotFoundException, ValidationException
from services.ai_service.models import AIConfig, AIResponseLog, AIProvider
from services.ai_service.schemas import (
    AIConfigCreate,
    AIConfigUpdate,
    AIConfigResponse,
    GenerateResponseRequest,
    GenerateResponseResult,
)

logger = logging.getLogger(__name__)

# Default model names per provider
DEFAULT_MODELS = {
    AIProvider.OPENAI: "gpt-3.5-turbo",
    AIProvider.GEMINI: "gemini-pro",
    AIProvider.OPENROUTER: "openai/gpt-3.5-turbo",
}


def create_ai_config(db: Session, data: AIConfigCreate) -> AIConfigResponse:
    """Create an AI configuration for a gym."""
    config = AIConfig(
        gym_id=data.gym_id,
        provider=data.provider,
        api_key_encrypted=data.api_key,
        model_name=data.model_name or DEFAULT_MODELS.get(data.provider),
        base_prompt=data.base_prompt,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return AIConfigResponse.model_validate(config)


def get_ai_config(db: Session, config_id: int) -> AIConfigResponse:
    """Get an AI config by ID."""
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise NotFoundException("AIConfig", config_id)
    return AIConfigResponse.model_validate(config)


def list_ai_configs(db: Session, gym_id: int) -> list[AIConfigResponse]:
    """List AI configs for a gym."""
    configs = db.query(AIConfig).filter(AIConfig.gym_id == gym_id).all()
    return [AIConfigResponse.model_validate(c) for c in configs]


def update_ai_config(db: Session, config_id: int, data: AIConfigUpdate) -> AIConfigResponse:
    """Update an AI config."""
    config = db.query(AIConfig).filter(AIConfig.id == config_id).first()
    if not config:
        raise NotFoundException("AIConfig", config_id)

    update_data = data.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        update_data["api_key_encrypted"] = update_data.pop("api_key")

    for field, value in update_data.items():
        setattr(config, field, value)

    db.commit()
    db.refresh(config)
    return AIConfigResponse.model_validate(config)


def generate_response(db: Session, data: GenerateResponseRequest) -> GenerateResponseResult:
    """Generate an AI response for an incoming message."""
    config = (
        db.query(AIConfig)
        .filter(AIConfig.gym_id == data.gym_id, AIConfig.is_active.is_(True))
        .first()
    )
    if not config:
        raise NotFoundException("Active AIConfig for gym", data.gym_id)

    start_time = time.time()

    # Placeholder: actual AI provider call would go here
    response_text = f"[AI Response from {config.provider.value}] Thank you for your message."
    elapsed_ms = (time.time() - start_time) * 1000

    log = AIResponseLog(
        gym_id=data.gym_id,
        phone_number_id=data.phone_number_id,
        incoming_message=data.incoming_message,
        prompt_used=config.base_prompt,
        ai_provider=config.provider.value,
        ai_response=response_text,
        response_time_ms=elapsed_ms,
    )
    db.add(log)
    db.commit()

    return GenerateResponseResult(
        response_text=response_text,
        provider=config.provider.value,
        model=config.model_name,
        response_time_ms=elapsed_ms,
    )
