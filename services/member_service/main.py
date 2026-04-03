"""Member Service - Manages gym members and member groups."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.member_service import models  # noqa: F401
from services.member_service.routes import router as member_router

app = FastAPI(title="Alfit Member Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("member-service"))
app.include_router(member_router, prefix="/api/v1", tags=["Members"])


@app.on_event("startup")
def create_tables() -> None:
    """Create member service tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Backward-compatible migration for existing deployments.
    with engine.begin() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("members")}
        if "schedule" not in columns:
            conn.execute(text("ALTER TABLE members ADD COLUMN schedule TEXT NULL"))
