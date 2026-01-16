"""
Query/Support Ticket API Routes.

Endpoints for users to submit support queries and admins to respond.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.repositories.query import QueryRepository
from app.models.query import QueryTable
from app.schemas.query import (
    QueryCreate,
    QueryResponse,
    QueryReply,
    QueryListResponse,
)
from app.schemas.common import SuccessResponse, PaginatedResponse

router = APIRouter(prefix="/queries", tags=["Support Queries"])


# =======================
# User Endpoints
# =======================

@router.post(
    "/",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a support query",
)
async def submit_query(
    data: QueryCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit a new support query.
    
    Users can submit queries without authentication.
    Queries are marked as 'PENDING' until an admin responds.
    """
    repo = QueryRepository(session)
    
    query = QueryTable(
        user_name=data.user_name,
        user_email=data.user_email,
        user_query=data.user_query,
        user_query_date=date.today(),
        admin_id="PENDING",
        admin_name="PENDING",
        admin_response=None,
        admin_response_date=None,
    )
    
    await repo.create(query)
    await session.commit()
    
    return query


@router.get(
    "/my-queries",
    response_model=list[QueryResponse],
    summary="Get queries by user email",
)
async def get_my_queries(
    email: str = Query(..., description="User's email address"),
    session: AsyncSession = Depends(get_db),
):
    """
    Get all queries submitted by a specific email address.
    
    Users can check their query status using their email.
    """
    repo = QueryRepository(session)
    queries = await repo.get_by_user_email(email)
    
    return queries


# =======================
# Admin Endpoints
# =======================

@router.get(
    "/",
    response_model=QueryListResponse,
    summary="List all queries (Admin)",
)
async def list_queries(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(
        None, 
        description="Filter by status: 'pending' or 'resolved'"
    ),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """
    Get paginated list of all support queries.
    
    Admin-only endpoint to view and manage user queries.
    """
    repo = QueryRepository(session)
    offset = (page - 1) * page_size
    
    pending_only = status_filter == "pending"
    resolved_only = status_filter == "resolved"
    
    queries, total = await repo.get_all(
        offset=offset,
        limit=page_size,
        pending_only=pending_only,
        resolved_only=resolved_only,
    )
    
    pending_count = await repo.get_pending_count()
    resolved_count = await repo.get_resolved_count()
    
    return QueryListResponse(
        items=[QueryResponse.model_validate(q) for q in queries],
        total=total,
        pending_count=pending_count,
        resolved_count=resolved_count,
    )


@router.get(
    "/pending",
    response_model=list[QueryResponse],
    summary="Get pending queries (Admin)",
)
async def get_pending_queries(
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Get all queries awaiting admin response."""
    repo = QueryRepository(session)
    queries, _ = await repo.get_all(pending_only=True, limit=100)
    
    return queries


@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    summary="Get query by ID",
)
async def get_query(
    query_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Get a specific query by ID."""
    repo = QueryRepository(session)
    query = await repo.get_by_id(query_id)
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found",
        )
    
    return query


@router.post(
    "/{query_id}/reply",
    response_model=QueryResponse,
    summary="Reply to a query (Admin)",
)
async def reply_to_query(
    query_id: int,
    data: QueryReply,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """
    Add admin response to a user query.
    
    Once responded, the query is marked as resolved.
    """
    repo = QueryRepository(session)
    
    query = await repo.add_admin_response(
        query_id=query_id,
        admin_response=data.admin_response,
        admin_id=data.admin_id,
        admin_name=data.admin_name,
    )
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found",
        )
    
    await session.commit()
    
    return query


@router.delete(
    "/{query_id}",
    response_model=SuccessResponse,
    summary="Delete a query (Admin)",
)
async def delete_query(
    query_id: int,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Delete a support query."""
    repo = QueryRepository(session)
    
    deleted = await repo.delete(query_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found",
        )
    
    await session.commit()
    
    return SuccessResponse(message=f"Query {query_id} has been deleted")
