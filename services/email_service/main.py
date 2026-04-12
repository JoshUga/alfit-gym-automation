"""Email Service - Email sending and template management."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.database import Base, get_engine
from shared.database import get_session_factory
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
import services.email_service.models  # noqa: F401
from services.email_service import service
from services.email_service.routes import router as email_router

app = FastAPI(title="Alfit Email Service", version="0.1.0")
logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("email-service"))
app.include_router(email_router, prefix="/api/v1", tags=["Email"])


@app.on_event("startup")
def auto_init_emailengine() -> None:
    """Bootstrap EmailEngine account mapping from environment variables."""
    try:
        Base.metadata.create_all(bind=get_engine())
    except Exception as exc:
        logger.warning("Email-service DB schema init failed: %s", exc)

    try:
        session = get_session_factory()()
    except Exception as exc:
        logger.warning("Skipping EmailEngine auto-init because DB session could not be created: %s", exc)
        return
    try:
        service.auto_initialize_emailengine(session)
    except Exception as exc:
        logger.warning("EmailEngine auto-init failed: %s", exc)
    try:
        health_report = service.run_smtp_health_checks(session)
        unhealthy = [item for item in health_report.results if item.health_status != "healthy"]
        if unhealthy:
            logger.warning("SMTP startup health check found issues: %s", [item.model_dump() for item in unhealthy])
        else:
            logger.info("SMTP startup health check passed for %d account(s)", len(health_report.results))
    except Exception as exc:
        logger.warning("SMTP startup health check failed: %s", exc)
    finally:
        session.close()
