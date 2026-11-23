"""
Query/Support Ticket API Routes.

Endpoints for users to submit support queries and admins to respond.
"""

from fastapi import Path as ApiPath
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config import get_settings
from app.core.rate_limiter import limiter
from app.core.database import get_db
from app.utils.dates import utcnow
from app.utils.emails import normalize_email
from app.repositories.query import QueryRepository
from app.models.query import QueryTable
from app.schemas.query import (
    QueryCreate,
    QueryPublicResponse,
    QueryResponse,
    QueryReply,
    QueryListResponse,
)
from app.schemas.common import SuccessResponse
from app.services.audit_service import record_admin_action
from app.api.auth.deps import get_current_admin, get_current_user, get_optional_donor_id

router = APIRouter(prefix="/queries", tags=["Support Queries"])


# =======================
# User Endpoints
# =======================

@router.post(
    "/",
    response_model=QueryPublicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a support query",
)
@limiter.limit(get_settings().SUPPORT_QUERY_RATE_LIMIT)
async def submit_query(
    request: Request,
    data: QueryCreate,
    session: AsyncSession = Depends(get_db, scope="function"),
    donor_id: Optional[str] = Depends(get_optional_donor_id),
):
    """
    Submit a new support query.
    
    Users can submit queries without authentication.
    Queries are marked as 'PENDING' until an admin responds.
    A signed-in donor owns the queries they file (and can read them back via /my-queries);
    anonymous queries are visible to admins only.
    """
    repo = QueryRepository(session)
    
    query = QueryTable(
        user_name=data.user_name,
        user_email=normalize_email(data.user_email),
        donor_id=donor_id,
        user_query=data.user_query,
        user_query_date=utcnow().date(),
        admin_id="PENDING",
        admin_name="PENDING",
        admin_response=None,
        admin_response_date=None,
    )
    
    await repo.create(query)
    
    return query


@router.get(
    "/my-queries",
    response_model=list[QueryPublicResponse],
    summary="Get the signed-in donor's own queries",
)
async def get_my_queries(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=1000000),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get the queries the authenticated donor filed while signed in.

    Ownership follows the donor ID recorded at submission. A later verified registration
    does not establish ownership of an earlier anonymous query.
    Anonymous and legacy queries have no owner and are visible to admins only. Admin accounts
    have no donor queries.
    """
    if current_user["user_type"] != "donor":
        return []
    repo = QueryRepository(session)
    return await repo.get_by_donor_id(current_user["user_id"], limit=limit, offset=offset)


# =======================
# Admin Endpoints
# =======================

@router.get(
    "/",
    response_model=QueryListResponse,
    summary="List all queries (Admin)",
)
async def list_queries(
    page: int = Query(1, ge=1, le=100000),
    page_size: int = Query(20, ge=1, le=100),
    status_value: Optional[str] = Query(
        None, pattern="^(pending|resolved)$", alias="status", description="Filter by status: 'pending' or 'resolved'"
    ),
    status_filter: Optional[str] = Query(
        None, pattern="^(pending|resolved)$", description="Deprecated alias of `status`", deprecated=True
    ),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Get paginated list of all support queries.
    
    Admin-only endpoint to view and manage user queries.
    """
    repo = QueryRepository(session)
    offset = (page - 1) * page_size
    
    wanted = status_value or status_filter
    pending_only = wanted == "pending"
    resolved_only = wanted == "resolved"
    
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
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0, le=1000000),
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get all queries awaiting admin response."""
    repo = QueryRepository(session)
    queries, _ = await repo.get_all(pending_only=True, limit=limit, offset=offset)
    
    return queries


@router.get(
    "/{query_id}",
    response_model=QueryResponse,
    summary="Get query by ID (Admin)",
)
async def get_query(
    query_id: Annotated[int, ApiPath(ge=1, le=2147483647)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Get a specific query by ID (admin only)."""
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
    query_id: Annotated[int, ApiPath(ge=1, le=2147483647)],
    data: QueryReply,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """
    Add admin response to a user query.

    Once responded, the query is marked as resolved.
    Admin identity is taken from the JWT token, not the request body.
    """
    repo = QueryRepository(session)
    
    query = await repo.add_admin_response(
        query_id=query_id,
        admin_response=data.admin_response,
        admin_id=current_admin.id,
        admin_name=current_admin.username,
    )
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found",
        )

    record_admin_action(session, current_admin.id, "query.reply", "query", str(query_id))
    return query


@router.delete(
    "/{query_id}",
    response_model=SuccessResponse,
    summary="Delete a query (Admin)",
)
async def delete_query(
    query_id: Annotated[int, ApiPath(ge=1, le=2147483647)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin = Depends(get_current_admin),
):
    """Delete a support query."""
    repo = QueryRepository(session)
    
    deleted = await repo.delete(query_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found",
        )

    record_admin_action(session, current_admin.id, "query.delete", "query", str(query_id))
    return SuccessResponse(message=f"Query {query_id} has been deleted")
