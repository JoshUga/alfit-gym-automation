"""AI Service business logic."""

import os
import time
import logging
import httpx
from sqlalchemy.orm import Session
from shared.exceptions import ValidationException
from services.ai_service.models import AIConfig, AIResponseLog, AIProvider
from services.ai_service.schemas import (
    AIRuntimeConfigResponse,
    GenerateResponseRequest,
    GenerateResponseResult,
)

logger = logging.getLogger(__name__)

# Default model names per provider
DEFAULT_MODELS = {
    AIProvider.OPENAI: "gpt-3.5-turbo",
    AIProvider.GEMINI: "gemini-pro",
    AIProvider.OPENROUTER: "openai/gpt-3.5-turbo",
    AIProvider.OLLAMA: "SmolLM-135M",
}


def _normalize_provider(value: str | None) -> AIProvider:
    raw = (value or "ollama").strip().lower()
    if raw == AIProvider.OPENAI.value:
        return AIProvider.OPENAI
    if raw == AIProvider.GEMINI.value:
        return AIProvider.GEMINI
    if raw == AIProvider.OPENROUTER.value:
        return AIProvider.OPENROUTER
    if raw == AIProvider.OLLAMA.value:
        return AIProvider.OLLAMA
    raise ValidationException(
        "Invalid AI_PROVIDER. Allowed values: openai, gemini, openrouter, ollama"
    )


def _provider_api_key(provider: AIProvider) -> str:
    if provider == AIProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY", "")
    if provider == AIProvider.GEMINI:
        return os.getenv("GEMINI_API_KEY", "")
    if provider == AIProvider.OPENROUTER:
        return os.getenv("OPENROUTER_API_KEY", "")
    if provider == AIProvider.OLLAMA:
        return "local-runtime"
    return ""


def _generate_with_ollama(model_name: str, base_prompt: str, incoming_message: str) -> str:
    """Generate a response using a local Ollama instance."""
    ollama_base = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    prompt = f"{base_prompt}\n\nUser message:\n{incoming_message}\n\nRespond as the gym assistant."

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            f"{ollama_base}/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
            },
        )

    if resp.status_code >= 400:
        raise ValidationException(f"Ollama request failed: {resp.text}")

    payload = resp.json() if resp.content else {}
    text = str(payload.get("response") or "").strip()
    if not text:
        raise ValidationException("Ollama returned an empty response")
    return text


def _ollama_fallback_model(primary_model: str) -> str | None:
    fallback = os.getenv("AI_FALLBACK_MODEL", "smollm:135m").strip()
    if not fallback or fallback == primary_model:
        return None
    return fallback


def get_runtime_config() -> AIRuntimeConfigResponse:
    """Expose effective AI runtime settings coming from environment variables."""
    provider = _normalize_provider(os.getenv("AI_PROVIDER", AIProvider.OLLAMA.value))
    model_name = os.getenv("AI_MODEL", DEFAULT_MODELS[provider])
    base_prompt = os.getenv(
        "AI_BASE_PROMPT",
        "You are a helpful gym assistant. Keep responses concise and practical.",
    )
    key = _provider_api_key(provider)

    return AIRuntimeConfigResponse(
        provider=provider.value,
        model_name=model_name,
        configured=bool(key.strip()),
        base_prompt=base_prompt,
    )


def create_ai_config(db: Session, data: dict) -> None:
    """Deprecated: AI config is environment managed."""
    raise ValidationException(
        "AI settings are environment-managed. Configure AI_PROVIDER and provider API key env vars on ai-service."
    )


def get_ai_config(db: Session, config_id: int) -> None:
    """Deprecated: AI config is environment managed."""
    raise ValidationException(
        "AI settings are environment-managed. Per-gym AI configs are disabled."
    )


def list_ai_configs(db: Session, gym_id: int) -> list:
    """Deprecated: AI config is environment managed."""
    return []


def update_ai_config(db: Session, config_id: int, data: dict) -> None:
    """Deprecated: AI config is environment managed."""
    raise ValidationException(
        "AI settings are environment-managed. Per-gym AI configs are disabled."
    )


def generate_response(db: Session, data: GenerateResponseRequest) -> GenerateResponseResult:
    """Generate an AI response for an incoming message."""
    runtime = get_runtime_config()
    provider = _normalize_provider(runtime.provider)
    key = _provider_api_key(provider)
    if not key.strip():
        raise ValidationException(
            f"{provider.value} API key is not configured in environment"
        )

    start_time = time.time()

    model_used = runtime.model_name
    if provider == AIProvider.OLLAMA:
        try:
            response_text = _generate_with_ollama(
                model_name=model_used,
                base_prompt=runtime.base_prompt,
                incoming_message=data.incoming_message,
            )
        except ValidationException:
            fallback = _ollama_fallback_model(model_used)
            if not fallback:
                raise
            logger.warning(
                "Ollama model '%s' unavailable; falling back to '%s'",
                model_used,
                fallback,
            )
            response_text = _generate_with_ollama(
                model_name=fallback,
                base_prompt=runtime.base_prompt,
                incoming_message=data.incoming_message,
            )
            model_used = fallback
    else:
        # Placeholder for managed providers; keep explicit provider labeling.
        response_text = f"[AI Response from {provider.value}] Thank you for your message."
    elapsed_ms = (time.time() - start_time) * 1000

    log = AIResponseLog(
        gym_id=data.gym_id,
        phone_number_id=data.phone_number_id,
        incoming_message=data.incoming_message,
        prompt_used=runtime.base_prompt,
        ai_provider=provider.value,
        ai_response=response_text,
        response_time_ms=elapsed_ms,
    )
    db.add(log)
    db.commit()

    return GenerateResponseResult(
        response_text=response_text,
        provider=provider.value,
        model=model_used,
        response_time_ms=elapsed_ms,
    )
