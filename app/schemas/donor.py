from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from app.schemas.validation import OtpCode, BirthDate, BloodGroup, Paragraph, Phone, PostalCode, SingleLine
from app.schemas.common import BaseSchema
from app.schemas.passwords import check_new_password, check_password_length


# ============ Personal Details Schemas ============


class PersonalDetailsCreate(BaseModel, extra="forbid"):
    """Schema for creating personal details."""

    first_name: SingleLine = Field(..., min_length=1, max_length=45)
    last_name: Optional[SingleLine] = Field(None, max_length=45)
    # Accepted for backwards compatibility but ignored: the server derives age from date_of_birth.
    age: Optional[int] = Field(None, description="Ignored; computed from date_of_birth")
    date_of_birth: BirthDate
    contact_number: Phone = Field(..., min_length=10, max_length=15)
    secondary_contact_number: Optional[Phone] = Field(None, max_length=15)
    marital_status: Optional[SingleLine] = Field(None, max_length=10)


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


class AddressDetailsCreate(BaseModel, extra="forbid"):
    """Schema for creating address details."""

    address: Paragraph = Field(..., min_length=5, max_length=200)
    pincode: PostalCode = Field(..., min_length=5, max_length=10)
    country: SingleLine = Field(..., min_length=1, max_length=45)
    state: SingleLine = Field(..., min_length=1, max_length=45)
    city: SingleLine = Field(..., min_length=1, max_length=45)


class AddressDetailsResponse(BaseSchema):
    """Schema for address details response."""

    id: str
    address: str
    pincode: str
    country: str
    state: str
    city: str


# ============ Disease Details Schemas ============


class DiseaseDetailsCreate(BaseModel, extra="forbid"):
    """Schema for disease details."""

    name: SingleLine = Field(..., min_length=1, max_length=100)
    description: Optional[Paragraph] = Field(None, max_length=200)


class DiseaseDetailsResponse(BaseSchema):
    """Schema for disease details response."""

    id: str
    name: str
    description: Optional[str]


# ============ Donor Schemas ============



class DonorCreate(BaseModel, extra="forbid"):
    """Schema for donor registration."""

    name: SingleLine = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    blood_group: BloodGroup = Field(..., description="Blood group (A+, A-, B+, B-, AB+, AB-, O+, O-)")

    # Nested details
    personal_details: PersonalDetailsCreate
    address_details: AddressDetailsCreate
    disease_details: DiseaseDetailsCreate


    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_new_password(v)


class DonorEnrollment(DonorCreate):
    enrollment_code: OtpCode


class EnrollmentCodeRequest(BaseModel, extra="forbid"):
    email: EmailStr = Field(max_length=100)


class DonorUpdate(BaseModel, extra="forbid"):
    """Schema for updating donor details."""
    name: Optional[SingleLine] = Field(None, min_length=2, max_length=100)
    # Accepted and validated, but never applied: blood group is immutable for self-service.
    blood_group: Optional[BloodGroup] = None
    # Donors control their own availability; only an admin can enable/disable the account.
    is_available: Optional[bool] = None
    contact_number: Optional[Phone] = Field(None, max_length=15)
    address: Optional[Paragraph] = Field(None, min_length=5, max_length=200)
    city: Optional[SingleLine] = Field(None, min_length=1, max_length=45)
    state: Optional[SingleLine] = Field(None, min_length=1, max_length=45)
    pincode: Optional[PostalCode] = Field(None, min_length=5, max_length=10)



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


class DonorLoginRequest(BaseModel, extra="forbid"):
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


class PasswordResetRequest(BaseModel, extra="forbid"):
    """Schema for password reset request."""

    email: EmailStr = Field(..., max_length=100)


class PasswordResetConfirm(BaseModel, extra="forbid"):
    """Schema for password reset confirmation."""

    email: EmailStr = Field(..., max_length=100)
    otp: OtpCode
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return check_new_password(v)
