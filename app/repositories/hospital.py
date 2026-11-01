from app.utils.search import LIKE_ESCAPE, escape_like
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.hospital import HospitalDetails
from app.models.blood_request import BloodRequestDetails
from typing import Optional, List


class HospitalRepository:
    """
    Repository for hospital data access.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, hospital_id: str) -> Optional[HospitalDetails]:
        """Get hospital by ID."""
        query = select(HospitalDetails).where(HospitalDetails.id == hospital_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def find_duplicate(
        self,
        name: str,
        branch: Optional[str],
        pincode: str,
        exclude_id: Optional[str] = None,
    ) -> Optional[HospitalDetails]:
        """
        Find another hospital with the same identity: name + branch + pincode
        (case-insensitive; a missing branch equals an empty one).
        """
        query = select(HospitalDetails).where(
            func.lower(HospitalDetails.hospital_name) == name.strip().lower(),
            func.lower(func.coalesce(HospitalDetails.branch, "")) == (branch or "").strip().lower(),
            HospitalDetails.pincode == pincode.strip(),
        )
        if exclude_id:
            query = query.where(HospitalDetails.id != exclude_id)
        result = await self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        city: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[List[HospitalDetails], int]:
        """Get all hospitals with pagination and filters."""
        query = select(HospitalDetails)

        conditions = []
        if city:
            conditions.append(func.lower(HospitalDetails.city) == func.lower(city))
        if search:
            search_pattern = f"%{escape_like(search)}%"
            conditions.append(
                or_(
                    HospitalDetails.hospital_name.ilike(search_pattern, escape=LIKE_ESCAPE),
                    HospitalDetails.city.ilike(search_pattern, escape=LIKE_ESCAPE),
                    HospitalDetails.hospital_address.ilike(search_pattern, escape=LIKE_ESCAPE),
                )
            )

        if conditions:
            from sqlalchemy import and_
            query = query.where(and_(*conditions))

        # Count
        count_query = select(func.count()).select_from(HospitalDetails)
        if conditions:
            from sqlalchemy import and_
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Paginated
        query = (
            query.offset(offset)
            .limit(limit)
            .order_by(HospitalDetails.hospital_name.asc())
        )
        result = await self.session.execute(query)
        hospitals = list(result.scalars().all())

        return hospitals, total

    async def get_autofill_suggestions(
        self, search: str, limit: int = 10
    ) -> List[HospitalDetails]:
        """Get hospital suggestions for autofill."""
        query = (
            select(HospitalDetails)
            .where(
                HospitalDetails.hospital_name.ilike(f"%{escape_like(search)}%", escape=LIKE_ESCAPE)
            )
            .order_by(HospitalDetails.hospital_name.asc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, hospital: HospitalDetails) -> HospitalDetails:
        """Create a new hospital."""
        self.session.add(hospital)
        await self.session.flush()
        return hospital

    async def update(self, hospital: HospitalDetails) -> HospitalDetails:
        """Update hospital details."""
        await self.session.merge(hospital)
        await self.session.flush()
        return hospital

    async def count_requests(self, hospital_id: str) -> int:
        """How many blood requests reference this hospital (0 means it is safe to delete)."""
        query = select(func.count()).select_from(BloodRequestDetails).where(
            BloodRequestDetails.hospital_id == hospital_id
        )
        return (await self.session.execute(query)).scalar() or 0

    async def delete(self, hospital_id: str) -> bool:
        """Delete a hospital."""
        from sqlalchemy import delete
        stmt = delete(HospitalDetails).where(HospitalDetails.id == hospital_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_cities(self) -> List[str]:
        """Get list of unique cities."""
        query = select(HospitalDetails.city).distinct().order_by(HospitalDetails.city)
        result = await self.session.execute(query)
        return [row[0] for row in result.all()]
