"""Email Service - Email sending and template management."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.database import Base, get_engine, get_session_factory
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from services.email_service import models  # noqa: F401
from services.email_service import service
from services.email_service.routes import router as email_router

app = FastAPI(title="Alfit Email Service", version="0.1.0")

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
def create_tables() -> None:
    """Create email service tables if they do not exist."""
    Base.metadata.create_all(bind=get_engine())


@app.on_event("startup")
def auto_init_emailengine() -> None:
    """Bootstrap EmailEngine account mapping from environment variables."""
    session = get_session_factory()()
    try:
        service.auto_initialize_emailengine(session)
    finally:
        session.close()
