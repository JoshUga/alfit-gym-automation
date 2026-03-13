"""Auth Service API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.auth import get_current_user, UserClaims
from shared.models import APIResponse
from services.auth_service.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefreshRequest,
    UserResponse,
    ChangePasswordRequest,
)
from services.auth_service import service

router = APIRouter()


def get_session():
    """Get database session dependency."""
    yield from get_db()


@router.post("/register", response_model=APIResponse[TokenResponse])
def register(user_data: UserRegister, db: Session = Depends(get_session)):
    """Register a new user."""
    result = service.register_user(db, user_data)
    return APIResponse(data=result, message="User registered successfully")


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(login_data: UserLogin, db: Session = Depends(get_session)):
    """Login with email and password."""
    result = service.login_user(db, login_data)
    return APIResponse(data=result, message="Login successful")


@router.post("/token/refresh", response_model=APIResponse[TokenResponse])
def refresh_token(request: TokenRefreshRequest):
    """Refresh access token."""
    result = service.refresh_token(request.refresh_token)
    return APIResponse(data=result, message="Token refreshed")


@router.get("/me", response_model=APIResponse[UserResponse])
def get_current_user_info(
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Get current user information."""
    result = service.get_user_by_id(db, current_user.user_id)
    return APIResponse(data=result)


@router.post("/change-password", response_model=APIResponse)
def change_password(
    request: ChangePasswordRequest,
    current_user: UserClaims = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """Change user password."""
    result = service.change_password(
        db, current_user.user_id, request.old_password, request.new_password
    )
    return APIResponse(message=result["message"])
