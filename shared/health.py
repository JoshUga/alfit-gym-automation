"""Health check endpoint factory."""

from fastapi import APIRouter


def create_health_router(service_name: str) -> APIRouter:
    """Create a health check router for a service."""
    router = APIRouter(tags=["Health"])
    
    @router.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": service_name,
        }
    
    return router
