"""Admin Service API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import require_roles, UserClaims
from shared.models import APIResponse
from services.admin_service.schemas import (
    AuditLogResponse,
    SystemHealthResponse,
    UserRoleUpdate,
    GymStatusUpdate,
)
from services.admin_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.get("/admin/users", response_model=APIResponse[list[dict]])
def list_users(
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """List all platform users (placeholder - delegates to auth service)."""
    service.create_audit_log(db, current_user.user_id, "list_users", "user")
    return APIResponse(data=[], message="Use auth service for user listing")


@router.put("/admin/users/{user_id}/roles", response_model=APIResponse)
def update_user_roles(
    user_id: int,
    data: UserRoleUpdate,
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """Update user roles (placeholder - delegates to auth service)."""
    service.create_audit_log(
        db, current_user.user_id, "update_roles", "user", str(user_id), {"roles": data.roles}
    )
    return APIResponse(message="Role update delegated to auth service")


@router.get("/admin/gyms", response_model=APIResponse[list[dict]])
def list_gyms(
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """List all gyms (placeholder - delegates to gym service)."""
    service.create_audit_log(db, current_user.user_id, "list_gyms", "gym")
    return APIResponse(data=[], message="Use gym service for gym listing")


@router.put("/admin/gyms/{gym_id}/status", response_model=APIResponse)
def update_gym_status(
    gym_id: int,
    data: GymStatusUpdate,
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """Update gym status (placeholder - delegates to gym service)."""
    service.create_audit_log(
        db, current_user.user_id, "update_gym_status", "gym", str(gym_id),
        {"is_active": data.is_active},
    )
    return APIResponse(message="Gym status update delegated to gym service")


@router.get("/admin/subscriptions", response_model=APIResponse[list[dict]])
def list_subscriptions(
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """List all subscriptions (placeholder - delegates to billing service)."""
    service.create_audit_log(db, current_user.user_id, "list_subscriptions", "subscription")
    return APIResponse(data=[], message="Use billing service for subscription listing")


@router.get("/admin/health-status", response_model=APIResponse[SystemHealthResponse])
def get_health_status(
    current_user: UserClaims = Depends(require_roles("super_admin")),
):
    """Get system health overview."""
    result = service.get_system_health()
    return APIResponse(data=result)


@router.get("/admin/audit-logs", response_model=APIResponse[list[AuditLogResponse]])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    current_user: UserClaims = Depends(require_roles("super_admin")),
    db: Session = Depends(get_session),
):
    """Get audit logs."""
    result = service.list_audit_logs(db, limit)
    return APIResponse(data=result)
