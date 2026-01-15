from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import selectinload
from app.models.blood_request import BloodRequestDetails, ResponseDetails
from app.models.hospital import HospitalDetails
from typing import Optional, List
from datetime import date


class BloodRequestRepository:
    """
    Repository for blood request data access.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self, request_id: str, include_hospital: bool = True
    ) -> Optional[BloodRequestDetails]:
        """Get blood request by ID."""
        query = select(BloodRequestDetails).where(BloodRequestDetails.id == request_id)

        if include_hospital:
            query = query.options(
                selectinload(BloodRequestDetails.hospital),
                selectinload(BloodRequestDetails.response),
            )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self, status: str, offset: int = 0, limit: int = 50
    ) -> List[BloodRequestDetails]:
        """Get all requests with given status."""
        query = (
            select(BloodRequestDetails)
            .options(selectinload(BloodRequestDetails.hospital))
            .where(BloodRequestDetails.status == status)
            .order_by(BloodRequestDetails.due_date.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_requests(self) -> List[BloodRequestDetails]:
        """Get all pending requests."""
        return await self.get_by_status("Pending")

    async def get_ongoing_requests(self) -> List[BloodRequestDetails]:
        """Get all ongoing (approved) requests."""
        return await self.get_by_status("Approved")

    async def get_closed_requests(self, limit: int = 100) -> List[BloodRequestDetails]:
        """Get closed requests."""
        return await self.get_by_status("Closed", limit=limit)

    async def get_expired_requests(self, limit: int = 100) -> List[BloodRequestDetails]:
        """Get expired requests."""
        return await self.get_by_status("Expired", limit=limit)

    async def get_declined_requests(self, limit: int = 100) -> List[BloodRequestDetails]:
        """Get declined requests."""
        return await self.get_by_status("Declined", limit=limit)

    async def count_by_status(self, status: str) -> int:
        """Count requests by status."""
        query = select(func.count()).where(BloodRequestDetails.status == status)
        result = await self.session.execute(query)
        return result.scalar()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        blood_group: Optional[str] = None,
    ) -> tuple[List[BloodRequestDetails], int]:
        """Get all requests with pagination and filters."""
        query = select(BloodRequestDetails).options(
            selectinload(BloodRequestDetails.hospital)
        )

        conditions = []
        if status:
            conditions.append(BloodRequestDetails.status == status)
        if blood_group:
            conditions.append(BloodRequestDetails.blood_group == blood_group)

        if conditions:
            query = query.where(and_(*conditions))

        # Count
        count_query = select(func.count()).select_from(BloodRequestDetails)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Paginated
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(BloodRequestDetails.created_at.desc())
        )
        result = await self.session.execute(query)
        requests = list(result.scalars().all())

        return requests, total

    async def create(
        self, request: BloodRequestDetails, response: ResponseDetails
    ) -> BloodRequestDetails:
        """Create a new blood request with response details."""
        self.session.add(response)
        self.session.add(request)
        await self.session.flush()
        return request

    async def update_status(
        self,
        request_id: str,
        status: str,
        admin_id: Optional[str] = None,
        is_approval: bool = False,
        is_close: bool = False,
    ) -> None:
        """Update request status."""
        values = {"status": status}

        if is_approval and admin_id:
            values["approved_admin_id"] = admin_id
        if is_close and admin_id:
            values["closed_admin_id"] = admin_id

        stmt = (
            update(BloodRequestDetails)
            .where(BloodRequestDetails.id == request_id)
            .values(**values)
        )
        await self.session.execute(stmt)

    async def expire_overdue_requests(self, current_date: date) -> int:
        """Mark overdue pending requests as expired."""
        stmt = (
            update(BloodRequestDetails)
            .where(
                and_(
                    BloodRequestDetails.status.in_(["Pending", "Not_Approved"]),
                    BloodRequestDetails.due_date < current_date,
                )
            )
            .values(status="Expired")
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def update_response(
        self,
        response_id: str,
        status: Optional[str] = None,
        report: Optional[str] = None,
        units_donated: Optional[int] = None,
        certificate_status: Optional[str] = None,
        donation_date: Optional[date] = None,
        donor_ids: Optional[str] = None,
    ) -> None:
        """Update response details."""
        values = {}
        if status is not None:
            values["status"] = status
        if report is not None:
            values["report"] = report
        if units_donated is not None:
            values["units_donated"] = units_donated
        if certificate_status is not None:
            values["certificate_status"] = certificate_status
        if donation_date is not None:
            values["donation_date"] = donation_date
        if donor_ids is not None:
            values["donor_ids"] = donor_ids

        if values:
            stmt = (
                update(ResponseDetails)
                .where(ResponseDetails.id == response_id)
                .values(**values)
            )
            await self.session.execute(stmt)

    # ============ Analytics ============

    async def get_blood_group_stats(self) -> dict:
        """Get request counts by blood group."""
        query = (
            select(
                BloodRequestDetails.blood_group,
                func.count().label("count"),
            )
            .group_by(BloodRequestDetails.blood_group)
        )
        result = await self.session.execute(query)
        return {row.blood_group: row.count for row in result.all()}

    async def get_status_stats(self) -> dict:
        """Get request counts by status."""
        query = (
            select(
                BloodRequestDetails.status,
                func.count().label("count"),
            )
            .group_by(BloodRequestDetails.status)
        )
        result = await self.session.execute(query)
        return {row.status: row.count for row in result.all()}
