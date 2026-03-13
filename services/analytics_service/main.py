"""Analytics Service - Provides KPIs, message volume trends, and reporting."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
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
