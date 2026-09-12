"""
Query/Support Ticket Pydantic Schemas.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from app.schemas.common import BaseSchema


class QueryCreate(BaseModel):
    """Schema for creating a new support query."""
    
    user_name: str = Field(..., min_length=1, max_length=55)
    user_email: EmailStr
    user_query: str = Field(..., min_length=10, max_length=555)


class QueryResponse(BaseSchema):
    """Schema for query response."""
    
    id: int
    user_name: str
    user_email: str
    user_query: Optional[str]
    user_query_date: Optional[date]
    admin_id: str
    admin_name: str
    admin_response: Optional[str]
    admin_response_date: Optional[date]
    created_at: datetime


class QueryReply(BaseModel):
    """Schema for admin replying to a query."""
    
    admin_response: str = Field(..., min_length=1, max_length=555)
    # admin_id and admin_name are taken from the JWT token, not user input


class QueryListResponse(BaseModel):
    """Schema for listing queries."""
    
    items: list[QueryResponse]
    total: int
    pending_count: int  # Queries without admin response
    resolved_count: int  # Queries with admin response
