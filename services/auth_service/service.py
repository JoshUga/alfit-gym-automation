"""Auth Service business logic."""

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from shared.auth import create_access_token, create_refresh_token, decode_token
from shared.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from services.auth_service.models import User, UserRole
from services.auth_service.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    TrainerCreate,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _token_payload_for_user(user: User) -> dict:
    return {
        "sub": str(user.id),
        "email": user.email,
        "roles": [user.role.value],
        "owner_id": user.parent_owner_id or user.id,
    }


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        owner_id=user.parent_owner_id or user.id,
        is_active=user.is_active,
        created_at=user.created_at,
    )


def register_user(db: Session, user_data: UserRegister) -> TokenResponse:
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ConflictException(f"User with email {user_data.email} already exists")
    
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=UserRole.GYM_OWNER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token_data = _token_payload_for_user(user)
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


def login_user(db: Session, login_data: UserLogin) -> TokenResponse:
    """Authenticate a user and return tokens."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not user.hashed_password:
        raise UnauthorizedException("Invalid credentials")
    
    if not verify_password(login_data.password, user.hashed_password):
        raise UnauthorizedException("Invalid credentials")
    
    if not user.is_active:
        raise UnauthorizedException("Account is disabled")
    
    token_data = _token_payload_for_user(user)
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


def refresh_token(token: str) -> TokenResponse:
    """Refresh access token using refresh token."""
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise ValidationException("Invalid token type")
    
    token_data = {
        "sub": payload["sub"],
        "email": payload["email"],
        "roles": payload.get("roles", []),
        "owner_id": payload.get("owner_id"),
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


def get_user_by_id(db: Session, user_id: int) -> UserResponse:
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    return _to_user_response(user)


def create_trainer_user(
    db: Session,
    owner_user_id: int,
    trainer_data: TrainerCreate,
) -> UserResponse:
    existing = db.query(User).filter(User.email == trainer_data.email).first()
    if existing:
        raise ConflictException(f"User with email {trainer_data.email} already exists")

    owner = db.query(User).filter(User.id == owner_user_id).first()
    if not owner:
        raise NotFoundException("User", owner_user_id)
    if owner.role != UserRole.GYM_OWNER:
        raise UnauthorizedException("Only gym owners can create trainer accounts")

    user = User(
        email=trainer_data.email,
        hashed_password=hash_password(trainer_data.password),
        full_name=trainer_data.full_name,
        role=UserRole.GYM_STAFF,
        parent_owner_id=owner_user_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


def list_trainers_by_owner(db: Session, owner_user_id: int) -> list[UserResponse]:
    users = (
        db.query(User)
        .filter(
            User.parent_owner_id == owner_user_id,
            User.role == UserRole.GYM_STAFF,
            User.is_active.is_(True),
        )
        .order_by(User.id.desc())
        .all()
    )
    return [_to_user_response(user) for user in users]


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> dict:
    """Change user password."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException("User", user_id)
    
    if not verify_password(old_password, user.hashed_password):
        raise UnauthorizedException("Current password is incorrect")
    
    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "Password changed successfully"}
