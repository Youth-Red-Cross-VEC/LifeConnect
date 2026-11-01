from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.schemas.common import BaseSchema
from app.schemas.passwords import check_new_password, check_password_length
import re


# ============ Personal Details Schemas ============


class PersonalDetailsCreate(BaseModel):
    """Schema for creating personal details."""

    first_name: str = Field(..., min_length=1, max_length=45)
    last_name: Optional[str] = Field(None, max_length=45)
    # Accepted for backwards compatibility but ignored: the server derives age from date_of_birth.
    age: Optional[int] = Field(None, description="Ignored; computed from date_of_birth")
    date_of_birth: date
    contact_number: str = Field(..., min_length=10, max_length=15)
    secondary_contact_number: Optional[str] = Field(None, max_length=15)
    marital_status: Optional[str] = Field(None, max_length=10)

    @field_validator("contact_number", "secondary_contact_number")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Remove spaces and validate
        v = v.replace(" ", "").replace("-", "")
        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class PersonalDetailsResponse(BaseSchema):
    """Schema for personal details response."""

    id: str
    first_name: str
    last_name: Optional[str]
    age: int
    date_of_birth: date
    contact_number: str
    secondary_contact_number: Optional[str]
    marital_status: Optional[str]


# ============ Address Details Schemas ============


class AddressDetailsCreate(BaseModel):
    """Schema for creating address details."""

    address: str = Field(..., min_length=5, max_length=200)
    pincode: str = Field(..., min_length=5, max_length=10)
    country: str = Field(..., max_length=45)
    state: str = Field(..., max_length=45)
    city: str = Field(..., max_length=45)


class AddressDetailsResponse(BaseSchema):
    """Schema for address details response."""

    id: str
    address: str
    pincode: str
    country: str
    state: str
    city: str


# ============ Disease Details Schemas ============


class DiseaseDetailsCreate(BaseModel):
    """Schema for disease details."""

    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=200)


class DiseaseDetailsResponse(BaseSchema):
    """Schema for disease details response."""

    id: str
    name: str
    description: Optional[str]


# ============ Donor Schemas ============

VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class DonorCreate(BaseModel):
    """Schema for donor registration."""

    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    blood_group: str = Field(..., description="Blood group (A+, A-, B+, B-, AB+, AB-, O+, O-)")

    # Nested details
    personal_details: PersonalDetailsCreate
    address_details: AddressDetailsCreate
    disease_details: DiseaseDetailsCreate

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid blood group. Must be one of: {VALID_BLOOD_GROUPS}")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_new_password(v)


class DonorUpdate(BaseModel):
    """Schema for updating donor details."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    # Accepted and validated, but never applied: blood group is immutable for self-service.
    blood_group: Optional[str] = None
    # Donors control their own availability; only an admin can enable/disable the account.
    is_available: Optional[bool] = None
    contact_number: Optional[str] = Field(None, max_length=15)
    address: Optional[str] = Field(None, min_length=5, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=45)
    state: Optional[str] = Field(None, min_length=1, max_length=45)
    pincode: Optional[str] = Field(None, min_length=5, max_length=10)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.upper()
        if v not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid blood group. Must be one of: {VALID_BLOOD_GROUPS}")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.replace(" ", "").replace("-", "")
        if not re.match(r"^\+?[0-9]{10,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class DonorResponse(BaseSchema):
    """Schema for donor response."""

    id: str
    name: str
    email: str
    blood_group: str
    active_status: bool
    is_available: bool
    last_donated_date: Optional[datetime]
    number_of_times_donated: int
    last_login_date: Optional[datetime]
    created_at: datetime

    # Nested details (optional, for detailed views)
    personal_details: Optional[PersonalDetailsResponse] = None
    address: Optional[AddressDetailsResponse] = None


class DonorListResponse(BaseSchema):
    """Schema for donor list item (lighter response)."""

    id: str
    name: str
    email: str
    blood_group: str
    active_status: bool
    is_available: bool
    city: Optional[str] = None
    last_donated_date: Optional[datetime]


class DonorLoginRequest(BaseModel):
    """Schema for donor login."""

    email: EmailStr = Field(..., max_length=100)
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_password_length(v)


class DonorLoginResponse(BaseModel):
    """Schema for donor login response."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str = "donor"
    name: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., max_length=100)


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    email: EmailStr = Field(..., max_length=100)
    otp: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return check_new_password(v)
