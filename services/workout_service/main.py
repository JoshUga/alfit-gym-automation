"""Workout Service - Generates and stores member workout plans."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.workout_service import models  # noqa: F401
from services.workout_service.routes import router as workout_router

app = FastAPI(title="Alfit Workout Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("workout-service"))
app.include_router(workout_router, prefix="/api/v1", tags=["Workout"])


@app.on_event("startup")
def create_tables() -> None:
    """Create workout service tables if they do not exist."""
    Base.metadata.create_all(bind=get_engine())
