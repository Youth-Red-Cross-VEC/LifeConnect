from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.request_status import AdminStatus, AdminRole
from typing import Optional
from datetime import datetime, date
from app.schemas.common import BaseSchema
from app.schemas.passwords import check_new_password, check_password_length


class AdminCreate(BaseModel):
    """Schema for admin registration."""

    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    username: str = Field(..., min_length=2, max_length=45)
    vec_registration_number: str = Field(..., max_length=36)
    date_of_birth: date
    mobile_number: str = Field(..., min_length=10, max_length=36)
    department: Optional[str] = Field(None, max_length=50)
    invite_otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP sent to this email by an existing admin via POST /admins/invite")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_new_password(v)


class AdminInviteRequest(BaseModel):
    """Schema for requesting an admin invite OTP."""
    email: EmailStr = Field(..., max_length=100, description="Email address of the person to invite as admin")


class AdminUpdate(BaseModel):
    """Schema for updating admin details."""

    username: Optional[str] = Field(None, min_length=2, max_length=45)
    mobile_number: Optional[str] = Field(None, max_length=36)
    department: Optional[str] = Field(None, max_length=50)
    active_status: Optional[AdminStatus] = None
    role: Optional[AdminRole] = None


class AdminSummaryResponse(BaseSchema):
    """What one admin may see of another: no date of birth, no phone number."""

    id: str
    email: str
    username: str
    vec_registration_number: str
    department: Optional[str]
    active_status: str
    role: AdminRole
    last_login_date: Optional[datetime]
    approved_donation_count: int
    closed_requests_count: int
    created_at: datetime


class AdminResponse(AdminSummaryResponse):
    """An admin's own full record (/admins/me/profile, registration, and their own row elsewhere)."""

    date_of_birth: date
    mobile_number: str


class AdminLoginRequest(BaseModel):
    """Schema for admin login."""

    email: EmailStr = Field(..., max_length=100)
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_password_length(v)


class AdminLoginResponse(BaseModel):
    """Schema for admin login response."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str = "admin"
    username: str


class AdminStatsResponse(BaseModel):
    """Schema for admin dashboard stats."""

    total_approved: int
    total_closed: int
    pending_requests: int
    ongoing_requests: int
    active_donors: int
