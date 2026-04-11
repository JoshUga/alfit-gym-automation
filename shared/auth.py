"""JWT utilities and authentication middleware."""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from shared.config import get_jwt_settings

security = HTTPBearer()


class UserClaims:
    """Represents authenticated user claims from JWT."""
    
    def __init__(self, user_id: int, email: str, roles: list[str], owner_id: int | None = None):
        self.user_id = user_id
        self.email = email
        self.roles = roles
        self.owner_id = owner_id


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    settings = get_jwt_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    settings = get_jwt_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    settings = get_jwt_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> UserClaims:
    """FastAPI dependency to get current authenticated user."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    email = payload.get("email")
    roles = payload.get("roles", [])
    owner_id = payload.get("owner_id")
    
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
    
    return UserClaims(
        user_id=int(user_id),
        email=email,
        roles=roles,
        owner_id=int(owner_id) if owner_id is not None else None,
    )


def require_roles(*required_roles: str):
    """Decorator factory to require specific roles."""
    def role_checker(current_user: UserClaims = Depends(get_current_user)) -> UserClaims:
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {required_roles}",
            )
        return current_user
    return role_checker
