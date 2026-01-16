"""
Query/Support Ticket Repository.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.query import QueryTable
from typing import Optional, List
from datetime import date


class QueryRepository:
    """Repository for query/support ticket data access."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, query_id: int) -> Optional[QueryTable]:
        """Get query by ID."""
        query = select(QueryTable).where(QueryTable.id == query_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        pending_only: bool = False,
        resolved_only: bool = False,
    ) -> tuple[List[QueryTable], int]:
        """
        Get all queries with pagination.
        Returns (queries, total_count).
        """
        query = select(QueryTable)
        
        # Apply filters
        if pending_only:
            query = query.where(QueryTable.admin_response == None)
        elif resolved_only:
            query = query.where(QueryTable.admin_response != None)
        
        # Count query
        count_query = select(func.count()).select_from(QueryTable)
        if pending_only:
            count_query = count_query.where(QueryTable.admin_response == None)
        elif resolved_only:
            count_query = count_query.where(QueryTable.admin_response != None)
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        # Paginated query
        query = query.offset(offset).limit(limit).order_by(QueryTable.id.desc())
        result = await self.session.execute(query)
        queries = list(result.scalars().all())
        
        return queries, total

    async def get_pending_count(self) -> int:
        """Get count of queries without admin response."""
        query = select(func.count()).select_from(QueryTable).where(
            QueryTable.admin_response == None
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def get_resolved_count(self) -> int:
        """Get count of queries with admin response."""
        query = select(func.count()).select_from(QueryTable).where(
            QueryTable.admin_response != None
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, query: QueryTable) -> QueryTable:
        """Create a new query."""
        self.session.add(query)
        await self.session.flush()
        return query

    async def add_admin_response(
        self,
        query_id: int,
        admin_response: str,
        admin_id: str,
        admin_name: str,
    ) -> Optional[QueryTable]:
        """Add admin response to a query."""
        query = await self.get_by_id(query_id)
        if not query:
            return None
        
        query.admin_response = admin_response
        query.admin_response_date = date.today()
        query.admin_id = admin_id
        query.admin_name = admin_name
        
        await self.session.flush()
        return query

    async def get_by_user_email(self, email: str) -> List[QueryTable]:
        """Get all queries from a specific user."""
        query = (
            select(QueryTable)
            .where(QueryTable.user_email == email)
            .order_by(QueryTable.id.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, query_id: int) -> bool:
        """Delete a query."""
        from sqlalchemy import delete
        stmt = delete(QueryTable).where(QueryTable.id == query_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
