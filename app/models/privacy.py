from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.dates import utcnow


class ErasureRequest(Base):
    __tablename__ = "erasure_requests"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'completed', 'rejected')", name="ck_erasure_request_status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    donor_id: Mapped[str | None] = mapped_column(
        ForeignKey("donor_details.id", ondelete="SET NULL"), unique=True,
    )
    status: Mapped[str] = mapped_column(String(12), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ErasureFile(Base):
    """Durable pending removal of an identified certificate."""

    __tablename__ = "erasure_files"

    filename: Mapped[str] = mapped_column(String(255), primary_key=True)
