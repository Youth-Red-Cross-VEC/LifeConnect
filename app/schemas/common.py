from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class MessageResponse(BaseModel):
    """Standard message response."""

    message: str
    success: bool = True


# Alias for semantic clarity
SuccessResponse = MessageResponse


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_code: Optional[str] = None


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls, items: list, total: int, page: int, page_size: int
    ) -> "PaginatedResponse":
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(
        default=20, ge=1, le=100, description="Items per page (max 100)"
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    database: str
    version: str
    timestamp: datetime
