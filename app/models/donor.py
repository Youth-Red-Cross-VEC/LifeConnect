from sqlalchemy import String, Boolean, Integer, DateTime, Date, Time, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from datetime import datetime, date, time
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.donor import DonorDetail


class PersonalDetails(Base, TimestampMixin):
    """Personal details of a donor."""

    __tablename__ = "personal_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(45), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    contact_number: Mapped[str] = mapped_column(String(15), nullable=False)
    secondary_contact_number: Mapped[Optional[str]] = mapped_column(
        String(15), nullable=True
    )
    marital_status: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aadhar_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Relationship
    donor: Mapped["DonorDetail"] = relationship(back_populates="personal_details")


class AddressDetails(Base, TimestampMixin):
    """Address details of a donor."""

    __tablename__ = "address_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(45), nullable=False)
    state: Mapped[str] = mapped_column(String(45), nullable=False)
    city: Mapped[str] = mapped_column(String(45), nullable=False, index=True)

    # Relationship
    donor: Mapped["DonorDetail"] = relationship(back_populates="address")


class DiseaseDetails(Base):
    """Disease/health condition details of a donor."""

    __tablename__ = "disease_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationship
    donor: Mapped["DonorDetail"] = relationship(back_populates="disease")


class TermsAndConditions(Base):
    """Terms and conditions version tracking."""

    __tablename__ = "terms_and_conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)


class DonorDetail(Base, TimestampMixin):
    """
    Main donor entity containing blood donation details.
    
    Indexes on email and blood_group for efficient queries.
    """

    __tablename__ = "donor_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    active_status: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
    authentication_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False
    )
    last_donated_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    number_of_times_donated: Mapped[int] = mapped_column(Integer, default=0)
    last_login_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Foreign keys
    personal_details_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("personal_details.id"), nullable=False
    )
    address_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("address_details.id"), nullable=False
    )
    disease_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("disease_details.id"), nullable=False
    )
    terms_and_conditions_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("terms_and_conditions.id"), nullable=False
    )

    # Relationships
    personal_details: Mapped["PersonalDetails"] = relationship(
        back_populates="donor", lazy="joined"
    )
    address: Mapped["AddressDetails"] = relationship(
        back_populates="donor", lazy="joined"
    )
    disease: Mapped["DiseaseDetails"] = relationship(
        back_populates="donor", lazy="joined"
    )


class AuthenticationDetailsDonor(Base):
    """Donor authentication/login history."""

    __tablename__ = "authentication_details_donor"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    auth_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    login_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    login_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
