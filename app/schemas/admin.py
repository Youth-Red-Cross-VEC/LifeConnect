from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.schemas.common import BaseSchema


class AdminCreate(BaseModel):
    """Schema for admin registration."""

    email: EmailStr
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
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class AdminInviteRequest(BaseModel):
    """Schema for requesting an admin invite OTP."""
    email: EmailStr = Field(..., description="Email address of the person to invite as admin")


class AdminUpdate(BaseModel):
    """Schema for updating admin details."""

    username: Optional[str] = Field(None, min_length=2, max_length=45)
    mobile_number: Optional[str] = Field(None, max_length=36)
    department: Optional[str] = Field(None, max_length=50)
    active_status: Optional[str] = None


class AdminResponse(BaseSchema):
    """Schema for admin response."""

    id: str
    email: str
    username: str
    vec_registration_number: str
    date_of_birth: date
    mobile_number: str
    department: Optional[str]
    active_status: str
    last_login_date: Optional[datetime]
    approved_donation_count: int
    closed_requests_count: int
    created_at: datetime


class AdminLoginRequest(BaseModel):
    """Schema for admin login."""

    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    """Schema for admin login response."""

    access_token: str
    refresh_token: str
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
