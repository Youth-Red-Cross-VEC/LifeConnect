from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date
from app.schemas.common import BaseSchema
from enum import Enum


class BloodRequestStatus(str, Enum):
    """Valid blood request statuses."""

    PENDING = "Pending"
    APPROVED = "Approved"
    NOT_APPROVED = "Not_Approved"
    DECLINED = "Declined"
    ONGOING = "Ongoing"
    CLOSED = "Closed"
    EXPIRED = "Expired"


VALID_BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


# ============ Hospital Schemas ============


class HospitalCreate(BaseModel):
    """Schema for creating a hospital."""

    hospital_name: str = Field(..., min_length=2, max_length=100)
    hospital_address: str = Field(..., min_length=5, max_length=200)
    pincode: str = Field(..., min_length=5, max_length=10)
    city: str = Field(..., max_length=45)
    state: str = Field(..., max_length=45)
    country: str = Field(default="India", max_length=45)
    branch: Optional[str] = Field(None, max_length=45)
    landmark: Optional[str] = Field(None, max_length=100)


class HospitalUpdate(BaseModel):
    """Schema for updating hospital details."""

    hospital_name: Optional[str] = Field(None, max_length=100)
    hospital_address: Optional[str] = Field(None, max_length=200)
    pincode: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=45)
    state: Optional[str] = Field(None, max_length=45)
    branch: Optional[str] = Field(None, max_length=45)
    landmark: Optional[str] = Field(None, max_length=100)


class HospitalResponse(BaseSchema):
    """Schema for hospital response."""

    id: str
    hospital_name: str
    hospital_address: str
    pincode: str
    city: str
    state: str
    country: str
    branch: Optional[str]
    landmark: Optional[str]


class HospitalAutofillResponse(BaseModel):
    """Schema for hospital autofill suggestions."""

    id: str
    hospital_name: str
    city: str
    address: str


# ============ Blood Request Schemas ============


class BloodRequestCreate(BaseModel):
    """Schema for creating a blood request."""

    patient_name: str = Field(..., min_length=2, max_length=100)
    blood_group: str = Field(..., description="Required blood group")
    hospital_id: str = Field(..., description="Hospital ID")
    contact_number: str = Field(..., min_length=10, max_length=15)
    patient_age: int = Field(..., ge=0, le=150)
    due_date: datetime = Field(..., description="Required by date")
    request_reason: Optional[str] = Field(None, max_length=200)
    units_required: int = Field(..., ge=1, le=20)
    attendant_name: Optional[str] = Field(None, max_length=100)

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        v = v.upper()
        if v not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid blood group. Must be one of: {VALID_BLOOD_GROUPS}")
        return v


class BloodRequestApprove(BaseModel):
    """Schema for approving a blood request."""

    request_id: str
    send_donor_emails: bool = True


class BloodRequestDecline(BaseModel):
    """Schema for declining a blood request."""

    request_id: str
    reason: Optional[str] = None


class BloodRequestClose(BaseModel):
    """Schema for closing a blood request."""

    request_id: str
    status: str = Field(default="Closed")
    report: Optional[str] = Field(None, max_length=255)
    units_donated: int = Field(..., ge=0)
    donation_date: date
    donor_ids: List[str] = Field(default_factory=list)
    send_certificates: bool = True


class BloodRequestResponse(BaseSchema):
    """Schema for blood request response."""

    id: str
    patient_name: str
    blood_group: str
    hospital_name: str
    contact_number: str
    patient_age: int
    due_date: datetime
    request_reason: Optional[str]
    status: str
    units_required: int
    attendant_name: Optional[str]
    approved_admin_id: Optional[str]
    closed_admin_id: Optional[str]
    created_at: datetime

    # Nested hospital details (optional)
    hospital: Optional[HospitalResponse] = None


class BloodRequestListResponse(BaseSchema):
    """Schema for blood request list item."""

    id: str
    patient_name: str
    blood_group: str
    hospital_name: str
    due_date: datetime
    status: str
    units_required: int
    created_at: datetime


# ============ Response Details Schemas ============


class ResponseDetailsCreate(BaseModel):
    """Schema for creating response details."""

    status: Optional[str] = None
    report: Optional[str] = Field(None, max_length=255)
    units_donated: Optional[int] = None
    certificate_status: Optional[str] = None
    donation_date: Optional[date] = None
    donor_ids: Optional[str] = None


class ResponseDetailsResponse(BaseSchema):
    """Schema for response details."""

    id: str
    status: Optional[str]
    report: Optional[str]
    units_donated: Optional[int]
    certificate_status: Optional[str]
    donation_date: Optional[date]
    donor_ids: Optional[str]
