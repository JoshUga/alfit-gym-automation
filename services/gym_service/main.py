"""Gym Service - Manages gym profiles, phone numbers, and Evolution credentials."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.gym_service import models  # noqa: F401
from services.gym_service.routes import router as gym_router

app = FastAPI(title="Alfit Gym Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("gym-service"))
app.include_router(gym_router, prefix="/api/v1", tags=["Gyms"])


@app.on_event("startup")
def create_tables() -> None:
    """Create gym service tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Backward-compatible migration for existing deployments.
    with engine.begin() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("gyms")}
        if "onboarding_welcome_sent_at" not in columns:
            conn.execute(text("ALTER TABLE gyms ADD COLUMN onboarding_welcome_sent_at DATETIME NULL"))
        if "preferred_currency" not in columns:
            conn.execute(text("ALTER TABLE gyms ADD COLUMN preferred_currency VARCHAR(8) NOT NULL DEFAULT 'UGX'"))
