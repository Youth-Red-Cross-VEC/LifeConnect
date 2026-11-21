# Models package - All SQLAlchemy models

from app.models.base import Base, TimestampMixin
from app.models.donor import (
    DonorDetail,
    PersonalDetails,
    AddressDetails,
    DiseaseDetails,
    TermsAndConditions,
    AuthenticationDetailsDonor,
)
from app.models.admin import AdminDetails, AuthenticationDetailsAdmin
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.models.hospital import HospitalDetails
from app.models.query import QueryTable
from app.models.otp import OtpCode
from app.models.refresh_session import RefreshSession
from app.models.audit import AdminAuditLog
from app.models.privacy import ErasureFile, ErasureRequest

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Donor related
    "DonorDetail",
    "PersonalDetails",
    "AddressDetails",
    "DiseaseDetails",
    "TermsAndConditions",
    "AuthenticationDetailsDonor",
    # Admin related
    "AdminDetails",
    "AuthenticationDetailsAdmin",
    # Blood request related
    "BloodRequestDetails",
    "ResponseDetails",
    # Hospital
    "HospitalDetails",
    # Query/Support
    "QueryTable",
    # Auth support
    "OtpCode",
    "RefreshSession",
    "AdminAuditLog",
    "ErasureRequest",
    "ErasureFile",
]
