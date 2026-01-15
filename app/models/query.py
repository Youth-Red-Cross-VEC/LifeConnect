from sqlalchemy import String, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
from datetime import date
from typing import Optional


class QueryTable(Base, TimestampMixin):
    """
    Support query/ticket system for user-admin communication.
    
    Tracks user queries and admin responses.
    """

    __tablename__ = "query_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(55), nullable=False)
    user_email: Mapped[str] = mapped_column(String(55), nullable=False, index=True)
    admin_id: Mapped[str] = mapped_column(String(55), nullable=False, index=True)
    admin_name: Mapped[str] = mapped_column(String(55), nullable=False)
    user_query: Mapped[Optional[str]] = mapped_column(String(555), nullable=True)
    admin_response: Mapped[Optional[str]] = mapped_column(String(555), nullable=True)
    user_query_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    admin_response_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
