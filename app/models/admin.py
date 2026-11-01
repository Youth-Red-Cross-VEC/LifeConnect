from sqlalchemy import String, Integer, DateTime, Date, Time, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
from datetime import datetime, date, time
from typing import Optional
from app.core.request_status import AdminStatus, AdminRole


class AdminDetails(Base, TimestampMixin):
    """
    Admin user entity for blood donation management.
    
    Admins can:
    - Approve/decline blood requests
    - Close ongoing requests
    - Manage donors and hospitals
    """

    __tablename__ = "admin_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default="0")
    role: Mapped[AdminRole] = mapped_column(
        SAEnum(AdminRole, native_enum=False, length=20, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=AdminRole.ADMIN,
        server_default=AdminRole.ADMIN.value,
    )
    username: Mapped[str] = mapped_column(String(45), nullable=False)
    authentication_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False
    )
    vec_registration_number: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(36), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    active_status: Mapped[AdminStatus] = mapped_column(
        SAEnum(AdminStatus, native_enum=False, length=36, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        index=True,
    )
    last_login_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_donation_count: Mapped[int] = mapped_column(Integer, default=0)
    closed_requests_count: Mapped[int] = mapped_column(Integer, default=0)


class AuthenticationDetailsAdmin(Base):
    """Admin authentication/login history."""

    __tablename__ = "authentication_details_admin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auth_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    login_date: Mapped[date] = mapped_column(Date, nullable=False)
    login_time: Mapped[time] = mapped_column(Time, nullable=False)
