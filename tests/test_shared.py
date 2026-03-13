"""Tests for shared library components."""

import pytest
from datetime import timedelta
from shared.config import (
    DatabaseSettings,
    RedisSettings,
    RabbitMQSettings,
    JWTSettings,
    BaseAppSettings,
    get_database_settings,
    get_redis_settings,
    get_rabbitmq_settings,
    get_jwt_settings,
)
from shared.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    UserClaims,
)
from shared.models import (
    APIResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    TimestampMixin,
)
from shared.exceptions import (
    AlfitException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ValidationException,
)
from shared.health import create_health_router
from shared.http_client import ServiceClient
from shared.logging_config import setup_logging, JSONFormatter


class TestDatabaseSettings:
    def test_default_settings(self):
        settings = DatabaseSettings()
        assert settings.MYSQL_HOST == "localhost"
        assert settings.MYSQL_PORT == 3306
        assert settings.MYSQL_USER == "alfit"

    def test_database_url(self):
        settings = DatabaseSettings()
        url = settings.database_url
        assert "mysql+pymysql://" in url
        assert "alfit" in url


class TestRedisSettings:
    def test_default_settings(self):
        settings = RedisSettings()
        assert settings.REDIS_HOST == "localhost"
        assert settings.REDIS_PORT == 6379

    def test_redis_url_without_password(self):
        settings = RedisSettings()
        url = settings.redis_url
        assert url == "redis://localhost:6379/0"

    def test_redis_url_with_password(self):
        settings = RedisSettings(REDIS_PASSWORD="secret")
        url = settings.redis_url
        assert ":secret@" in url


class TestRabbitMQSettings:
    def test_default_settings(self):
        settings = RabbitMQSettings()
        assert settings.RABBITMQ_HOST == "localhost"
        assert settings.RABBITMQ_PORT == 5672

    def test_rabbitmq_url(self):
        settings = RabbitMQSettings()
        url = settings.rabbitmq_url
        assert "amqp://" in url


class TestJWTSettings:
    def test_default_settings(self):
        settings = JWTSettings()
        assert settings.JWT_ALGORITHM == "HS256"
        assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES == 30


class TestBaseAppSettings:
    def test_default_settings(self):
        settings = BaseAppSettings()
        assert settings.APP_NAME == "Alfit Service"
        assert settings.DEBUG is False


class TestCachedSettings:
    def test_get_database_settings(self):
        settings = get_database_settings()
        assert isinstance(settings, DatabaseSettings)

    def test_get_redis_settings(self):
        settings = get_redis_settings()
        assert isinstance(settings, RedisSettings)

    def test_get_rabbitmq_settings(self):
        settings = get_rabbitmq_settings()
        assert isinstance(settings, RabbitMQSettings)

    def test_get_jwt_settings(self):
        settings = get_jwt_settings()
        assert isinstance(settings, JWTSettings)


class TestJWTAuth:
    def test_create_access_token(self):
        token = create_access_token({"sub": "1", "email": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "1", "email": "test@example.com"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_access_token(self):
        data = {"sub": "1", "email": "test@example.com", "roles": ["gym_owner"]}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_decode_refresh_token(self):
        data = {"sub": "1", "email": "test@example.com"}
        token = create_refresh_token(data)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token("invalid-token")
        assert exc_info.value.status_code == 401

    def test_custom_expiration(self):
        token = create_access_token(
            {"sub": "1", "email": "test@example.com"},
            expires_delta=timedelta(hours=1),
        )
        payload = decode_token(token)
        assert payload["sub"] == "1"


class TestUserClaims:
    def test_user_claims(self):
        claims = UserClaims(user_id=1, email="test@example.com", roles=["gym_owner"])
        assert claims.user_id == 1
        assert claims.email == "test@example.com"
        assert "gym_owner" in claims.roles


class TestAPIModels:
    def test_api_response(self):
        response = APIResponse(data={"key": "value"}, message="OK")
        assert response.success is True
        assert response.message == "OK"
        assert response.data == {"key": "value"}

    def test_error_response(self):
        response = ErrorResponse(message="Something went wrong")
        assert response.success is False
        assert response.message == "Something went wrong"

    def test_pagination_params(self):
        params = PaginationParams(page=2, page_size=10)
        assert params.offset == 10

    def test_pagination_params_defaults(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0

    def test_paginated_response(self):
        response = PaginatedResponse(data=[1, 2, 3], total=100, page=1, page_size=20, total_pages=5)
        assert len(response.data) == 3
        assert response.total == 100

    def test_timestamp_mixin(self):
        mixin = TimestampMixin()
        assert mixin.created_at is None
        assert mixin.updated_at is None


class TestExceptions:
    def test_alfit_exception(self):
        exc = AlfitException("Error", status_code=500)
        assert str(exc) == "Error"
        assert exc.status_code == 500

    def test_not_found_exception(self):
        exc = NotFoundException("User", 1)
        assert "User" in str(exc)
        assert exc.status_code == 404

    def test_unauthorized_exception(self):
        exc = UnauthorizedException()
        assert exc.status_code == 401

    def test_forbidden_exception(self):
        exc = ForbiddenException()
        assert exc.status_code == 403

    def test_conflict_exception(self):
        exc = ConflictException("Duplicate")
        assert exc.status_code == 409

    def test_validation_exception(self):
        exc = ValidationException("Invalid data")
        assert exc.status_code == 422


class TestHealthRouter:
    def test_create_health_router(self):
        router = create_health_router("test-service")
        assert len(router.routes) > 0


class TestServiceClient:
    def test_init(self):
        client = ServiceClient("http://localhost:8000")
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.max_retries == 3

    def test_trailing_slash_removed(self):
        client = ServiceClient("http://localhost:8000/")
        assert client.base_url == "http://localhost:8000"


class TestLogging:
    def test_setup_logging(self):
        logger = setup_logging("test-service", "DEBUG")
        assert logger.name == "test-service"

    def test_json_formatter(self):
        import logging
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py",
            lineno=1, msg="Test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert "Test message" in output
        assert "timestamp" in output
