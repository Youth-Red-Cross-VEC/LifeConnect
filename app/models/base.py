from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime
from datetime import datetime
from typing import Optional

from app.utils.dates import utcnow


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides:
    - Common table configurations
    - Type annotations for SQLAlchemy 2.0
    """

    pass


class TimestampMixin:
    """
    Mixin class that adds created_at and updated_at timestamps.
    
    Usage:
        class MyModel(Base, TimestampMixin):
            ...
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=None,
        onupdate=utcnow,
        nullable=True,
    )
