from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses Pydantic for validation and type safety.
    """

    # Database Configuration
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800

    # Security - JWT Configuration (Partner will implement auth using these)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # External APIs
    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_BASE_URL: str = "https://maps.googleapis.com/maps/api/distancematrix/json"

    # Email Configuration
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_USE_TLS: bool = True

    # Application Settings
    APP_NAME: str = "LifeConnect API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = False

    # CORS Settings
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # Scheduler
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance for dependency injection.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
