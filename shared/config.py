"""Centralized configuration management using pydantic-settings."""

import logging
from pydantic_settings import BaseSettings
from functools import lru_cache

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "alfit"
    MYSQL_PASSWORD: str = "alfit_password"
    MYSQL_DATABASE: str = "alfit"
    
    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration."""
    
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    
    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        )
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class JWTSettings(BaseSettings):
    """JWT configuration."""
    
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    model_config = {"env_prefix": "", "extra": "ignore"}


class BaseAppSettings(BaseSettings):
    """Base application settings."""
    
    APP_NAME: str = "Alfit Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    model_config = {"env_prefix": "", "extra": "ignore"}


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@lru_cache()
def get_redis_settings() -> RedisSettings:
    return RedisSettings()


@lru_cache()
def get_rabbitmq_settings() -> RabbitMQSettings:
    return RabbitMQSettings()


@lru_cache()
def get_jwt_settings() -> JWTSettings:
    settings = JWTSettings()
    if settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
        logger.warning(
            "Using default JWT secret key. Set JWT_SECRET_KEY env var in production."
        )
    return settings
