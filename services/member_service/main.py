"""Member Service - Manages gym members and member groups."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.health import create_health_router
from shared.exceptions import AlfitException, alfit_exception_handler
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
