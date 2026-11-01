import re

from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


MIN_SECRET_KEY_LENGTH = 32
# Anything that looks like the value shipped in .env.example or a doc, never a generated key.
_PLACEHOLDER_SECRET = re.compile(
    r"your[-_ ]?secret|change[-_ ]?me|replace[-_ ]?me|placeholder|secret[-_ ]?key[-_ ]?here|example", re.I
)
_GENERATE_HINT = 'python -c "import secrets; print(secrets.token_hex(32))"'


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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # External APIs
    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_BASE_URL: str = "https://maps.googleapis.com/maps/api/distancematrix/json"
    RECAPTCHA_SECRET_KEY: Optional[str] = None  # Add when reCAPTCHA API keys are available
    # When true, login endpoints reject requests without a valid reCAPTCHA token. Set true in production.
    RECAPTCHA_ENFORCED: bool = False

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
    # memory:// counts per process. With more than one web worker/replica use a shared
    # store (e.g. redis://host:6379/0) or the effective limit is multiplied by the worker count.
    RATE_LIMIT_STORAGE_URI: str = "memory://"

    # Per-IP limits on credential endpoints (brute force / email flooding)
    AUTH_RATE_LIMIT: str = "5/minute"
    PASSWORD_RESET_RATE_LIMIT: str = "3/minute"

    # The public blood-request form emails the admins on every submission, so it gets its own, stricter
    # limit (several limits can be joined with ';').
    BLOOD_REQUEST_RATE_LIMIT: str = "5/minute;30/hour"
    # One notification email is sent per new request, BCC'd to at most this many active admins.
    ADMIN_NOTIFY_MAX_RECIPIENTS: int = 20

    # One-time codes (admin invite, password reset)
    OTP_TTL_SECONDS: int = 600
    OTP_MAX_ATTEMPTS: int = 5

    # Donation eligibility: days a donor stays unavailable after donating (90 is the common deferral).
    DONATION_COOLDOWN_DAYS: int = 90

    # Scheduler (enable on exactly ONE dedicated process, never on web workers)
    SCHEDULER_ENABLED: bool = False
    SCHEDULER_TIMEZONE: str = "Asia/Kolkata"
    # Start the in-process scheduler at app startup when SCHEDULER_ENABLED is true.
    RUN_SCHEDULER: bool = True

    # Optional TrueType/OpenType font used to draw certificate text. Unset: DejaVuSans from matplotlib.
    CERT_FONT_PATH: Optional[str] = None

    # Serve /docs, /redoc and /openapi.json. Unset: on in development, off when APP_ENV=production.
    DOCS_ENABLED: Optional[bool] = None

    @property
    def docs_enabled(self) -> bool:
        if self.DOCS_ENABLED is not None:
            return self.DOCS_ENABLED
        return self.APP_ENV.lower() != "production"

    @model_validator(mode="after")
    def _validate_security_settings(self) -> "Settings":
        # Every environment: the JWT signing key must be a real secret. A short or copied-from-the-docs
        # key lets anyone who guesses it mint admin tokens.
        if _PLACEHOLDER_SECRET.search(self.SECRET_KEY):
            raise ValueError(
                f"SECRET_KEY is still a placeholder from the docs or .env.example. Generate one with: {_GENERATE_HINT}"
            )
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters. Generate one with: {_GENERATE_HINT}"
            )
        if self.APP_ENV.lower() == "production":
            if not self.RECAPTCHA_SECRET_KEY:
                raise ValueError("RECAPTCHA_SECRET_KEY must be set when APP_ENV=production")
            if not self.RECAPTCHA_ENFORCED:
                raise ValueError("RECAPTCHA_ENFORCED must be true when APP_ENV=production")
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Allow extra env vars like POSTGRES_*
        # A failed check must not echo every setting (database URL, SMTP password, SECRET_KEY) into logs.
        hide_input_in_errors = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance for dependency injection.
    Uses lru_cache to ensure settings are only loaded once.
    """
    return Settings()
