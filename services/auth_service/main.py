"""Auth Service - Manages authentication, authorization, and user sessions."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.auth_service import models  # noqa: F401
from services.auth_service.routes import router as auth_router

app = FastAPI(title="Alfit Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("auth-service"))
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])


@app.on_event("startup")
def create_tables() -> None:
    """Create auth service tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        inspector = inspect(conn)
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "parent_owner_id" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN parent_owner_id INTEGER NULL"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_users_parent_owner_id ON users(parent_owner_id)"
            )
        )
