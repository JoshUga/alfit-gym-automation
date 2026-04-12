"""AI Service - Manages AI auto-responder configurations and response generation."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from services.ai_service.routes import router as ai_router
from services.ai_service import service

app = FastAPI(title="Alfit AI Service", version="0.1.0")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("ai-service"))
app.include_router(ai_router, prefix="/api/v1", tags=["AI"])


@app.on_event("startup")
def verify_ai_runtime() -> None:
    """Run AI/Ollama startup checks and log readiness state."""
    result = service.run_startup_runtime_checks()
    if result.get("status") == "healthy":
        logger.info("AI startup check passed: %s", result)
    else:
        logger.warning("AI startup check reported issues: %s", result)
