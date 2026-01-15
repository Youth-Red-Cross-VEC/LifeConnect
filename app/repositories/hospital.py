from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.models.hospital import HospitalDetails
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

    async def get_by_name(self, name: str) -> Optional[HospitalDetails]:
        """Get hospital by name (case-insensitive)."""
        query = select(HospitalDetails).where(
            func.lower(HospitalDetails.hospital_name) == func.lower(name)
        )
        result = await self.session.execute(query)
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
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    HospitalDetails.hospital_name.ilike(search_pattern),
                    HospitalDetails.city.ilike(search_pattern),
                    HospitalDetails.hospital_address.ilike(search_pattern),
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
            .where(HospitalDetails.hospital_name.ilike(f"%{search}%"))
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
