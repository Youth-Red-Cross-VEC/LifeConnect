from app.core.request_status import BloodRequestStatus
from sqlalchemy import CheckConstraint, String, Text, Integer, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.hospital import HospitalDetails


class ResponseDetails(Base, TimestampMixin):
    """
    Response/outcome details for a blood request.
    
    Tracks donation results including units donated,
    certificate status, and participating donors.
    """

    __tablename__ = "response_details"
    # The upper bound (units_donated <= the request's units_required) spans two tables, so a
    # CHECK cannot express it; the close endpoint enforces it.
    __table_args__ = (
        CheckConstraint(
            "units_donated IS NULL OR units_donated >= 0",
            name="ck_response_details_units_donated_nonneg",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    report: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    units_donated: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    certificate_status: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    donation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    donor_ids: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Comma-separated donor IDs (Text: a request can list many donors)

    # Relationship
    blood_request: Mapped["BloodRequestDetails"] = relationship(
        back_populates="response"
    )


class BloodRequestDetails(Base, TimestampMixin):
    """
    Blood donation request entity.
    
    Tracks the full lifecycle:
    see app/core/request_status.py:TRANSITIONS
    
    Indexes on status and blood_group for efficient queries.
    """

    __tablename__ = "blood_request_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    hospital_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(15), nullable=False)
    patient_age: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    request_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(
        String(45), nullable=False, index=True, default=BloodRequestStatus.PENDING.value
    )
    units_required: Mapped[int] = mapped_column(Integer, nullable=False)
    attendant_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Foreign keys
    hospital_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("hospital_details.id"), nullable=False
    )
    response_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("response_details.id"), nullable=False
    )

    # Admin tracking
    approved_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    closed_admin_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    # Relationships
    hospital: Mapped["HospitalDetails"] = relationship(back_populates="blood_requests")
    response: Mapped["ResponseDetails"] = relationship(back_populates="blood_request")
