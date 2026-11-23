from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date, timezone
from app.schemas.validation import CalendarDate, CalendarDateTime, Quantity, BloodGroup, Paragraph, Phone, PostalCode, RecordId, SingleLine
from app.schemas.common import BaseSchema
from app.core.request_status import BloodRequestStatus  # noqa: F401  (re-exported)
from app.utils.dates import utcnow




# ============ Hospital Schemas ============


class HospitalCreate(BaseModel, extra="forbid"):
    """Schema for creating a hospital."""

    hospital_name: SingleLine = Field(..., min_length=2, max_length=100)
    hospital_address: Paragraph = Field(..., min_length=5, max_length=200)
    pincode: PostalCode = Field(..., min_length=5, max_length=10)
    city: SingleLine = Field(..., min_length=1, max_length=45)
    state: SingleLine = Field(..., min_length=1, max_length=45)
    country: SingleLine = Field(default="India", min_length=1, max_length=45)
    branch: Optional[SingleLine] = Field(None, max_length=45)
    landmark: Optional[SingleLine] = Field(None, max_length=100)


class HospitalUpdate(BaseModel, extra="forbid"):
    """Schema for updating hospital details."""

    hospital_name: Optional[SingleLine] = Field(None, min_length=2, max_length=100)
    hospital_address: Optional[Paragraph] = Field(None, min_length=5, max_length=200)
    pincode: Optional[PostalCode] = Field(None, max_length=10)
    city: Optional[SingleLine] = Field(None, min_length=1, max_length=45)
    state: Optional[SingleLine] = Field(None, min_length=1, max_length=45)
    branch: Optional[SingleLine] = Field(None, max_length=45)
    landmark: Optional[SingleLine] = Field(None, max_length=100)

    @field_validator("hospital_name", "hospital_address", "pincode", "city", "state")
    @classmethod
    def required_fields_cannot_be_cleared(cls, value: Optional[str], info) -> Optional[str]:
        # Omitting a field leaves it alone; sending an explicit null would blank a required column.
        # (branch and landmark are optional columns and may be cleared.)
        if value is None:
            raise ValueError(f"{info.field_name} cannot be null")
        return value


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


class BloodRequestCreate(BaseModel, extra="forbid"):
    """Schema for creating a blood request."""

    patient_name: SingleLine = Field(..., min_length=2, max_length=100)
    blood_group: BloodGroup = Field(..., description="Required blood group")
    hospital_id: RecordId = Field(..., min_length=1, max_length=36, description="Hospital ID")
    contact_number: Phone = Field(..., min_length=10, max_length=15)
    patient_age: Quantity = Field(..., ge=0, le=150)
    due_date: CalendarDateTime = Field(..., description="Required by date")
    request_reason: Optional[Paragraph] = Field(None, max_length=200)
    units_required: Quantity = Field(..., ge=1, le=20)
    attendant_name: Optional[SingleLine] = Field(None, max_length=100)
    # reCAPTCHA v3 token (action "blood_request"); required only when RECAPTCHA_ENFORCED=true
    recaptcha_token: Optional[str] = Field(None, max_length=4096)


    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, value: datetime) -> datetime:
        if value.tzinfo is not None:
            try:
                value = value.astimezone(timezone.utc).replace(tzinfo=None)
            except OverflowError as exc:
                raise ValueError("Due date is outside the supported range") from exc
        if value < utcnow():
            raise ValueError("due_date cannot be in the past")
        return value


class BloodRequestApprove(BaseModel):
    """Schema for approving a blood request."""

    request_id: str
    send_donor_emails: bool = True


class BloodRequestDecline(BaseModel):
    """Schema for declining a blood request."""

    request_id: str
    reason: Optional[str] = None


class BloodRequestClose(BaseModel, extra="forbid"):
    """Schema for closing a blood request."""

    # Optional: the path /{request_id}/close is authoritative; kept for older clients.
    request_id: Optional[RecordId] = Field(default=None, max_length=36)
    status: str = Field(default="Closed")
    report: Optional[Paragraph] = Field(None, max_length=255)
    units_donated: Quantity = Field(..., ge=0)
    donation_date: CalendarDate
    donor_ids: List[RecordId] = Field(default_factory=list, max_length=100)
    send_certificates: bool = True

    @field_validator("donation_date")
    @classmethod
    def validate_donation_date(cls, value: date) -> date:
        if value > utcnow().date():
            raise ValueError("donation_date cannot be in the future")
        return value


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


class ResponseDetailsCreate(BaseModel, extra="forbid"):
    """Schema for creating response details."""

    status: Optional[str] = None
    report: Optional[Paragraph] = Field(None, max_length=255)
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
