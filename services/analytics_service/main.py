"""Analytics Service - Provides KPIs, message volume trends, and reporting."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from shared.database import Base, get_engine
from services.analytics_service import models  # noqa: F401
from services.analytics_service.routes import router as analytics_router

app = FastAPI(title="Alfit Analytics Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("analytics-service"))
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])


@app.on_event("startup")
def create_tables() -> None:
    """Create analytics service tables if they do not exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
