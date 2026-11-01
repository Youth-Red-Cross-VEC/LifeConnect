from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.dates import utcnow


class OtpCode(Base):
    """One outstanding one-time code per (purpose, email). The code itself is stored hashed."""

    __tablename__ = "otp_codes"
    __table_args__ = (UniqueConstraint("purpose", "email", name="uq_otp_codes_purpose_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    code_hmac: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)


class OtpFailureWindow(Base):
    """Hourly failed-confirmation budget, retained independently of individual OTP codes."""

    __tablename__ = "otp_failure_windows"
    __table_args__ = (UniqueConstraint("purpose", "email", name="uq_otp_failure_windows_purpose_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purpose: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    window_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)
