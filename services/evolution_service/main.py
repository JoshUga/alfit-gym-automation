"""Evolution Service - EvolutionAPI proxy for WhatsApp integration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
from services.evolution_service.routes import router as evolution_router

app = FastAPI(title="Alfit Evolution Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AlfitException, alfit_exception_handler)
app.include_router(create_health_router("evolution-service"))
app.include_router(evolution_router, prefix="/api/v1", tags=["Evolution"])
