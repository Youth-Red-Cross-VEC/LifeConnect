from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.blood_request import BloodRequestDetails


class HospitalDetails(Base, TimestampMixin):
    """
    Hospital entity for blood request locations.
    
    Indexed on city and pincode for location-based queries.
    """

    __tablename__ = "hospital_details"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    hospital_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    hospital_address: Mapped[str] = mapped_column(String(200), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(45), nullable=False)
    country: Mapped[str] = mapped_column(String(45), nullable=False)
    branch: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    landmark: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationship
    blood_requests: Mapped[List["BloodRequestDetails"]] = relationship(
        back_populates="hospital"
    )
