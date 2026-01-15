from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from sqlalchemy.orm import selectinload
from app.models.donor import (
    DonorDetail,
    PersonalDetails,
    AddressDetails,
    DiseaseDetails,
    TermsAndConditions,
    AuthenticationDetailsDonor,
)
from typing import Optional, List
from datetime import datetime, date


class DonorRepository:
    """
    Repository for donor data access.
    
    Provides async CRUD operations with proper relationship loading.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, donor_id: str) -> Optional[DonorDetail]:
        """Get donor by ID with all related details."""
        query = (
            select(DonorDetail)
            .options(
                selectinload(DonorDetail.personal_details),
                selectinload(DonorDetail.address),
                selectinload(DonorDetail.disease),
            )
            .where(DonorDetail.id == donor_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[DonorDetail]:
        """Get donor by email."""
        query = select(DonorDetail).where(DonorDetail.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if donor with email exists."""
        query = select(func.count()).where(DonorDetail.email == email)
        result = await self.session.execute(query)
        return result.scalar() > 0

    async def get_active_by_blood_group(
        self, blood_group: str
    ) -> List[DonorDetail]:
        """Get all active donors with matching blood group."""
        query = (
            select(DonorDetail)
            .options(
                selectinload(DonorDetail.personal_details),
                selectinload(DonorDetail.address),
            )
            .where(
                and_(
                    DonorDetail.blood_group == blood_group,
                    DonorDetail.active_status == True,
                )
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        blood_group: Optional[str] = None,
        active_only: bool = False,
        name_search: Optional[str] = None,
    ) -> tuple[List[DonorDetail], int]:
        """
        Get all donors with pagination and filters.
        Returns (donors, total_count).
        """
        # Base query
        query = select(DonorDetail).options(
            selectinload(DonorDetail.address),
        )

        # Apply filters
        conditions = []
        if blood_group:
            conditions.append(DonorDetail.blood_group == blood_group)
        if active_only:
            conditions.append(DonorDetail.active_status == True)
        if name_search:
            conditions.append(DonorDetail.name.ilike(f"%{name_search}%"))

        if conditions:
            query = query.where(and_(*conditions))

        # Count query
        count_query = select(func.count()).select_from(DonorDetail)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Paginated query
        query = query.offset(offset).limit(limit).order_by(DonorDetail.created_at.desc())
        result = await self.session.execute(query)
        donors = list(result.scalars().all())

        return donors, total

    async def create(
        self,
        donor: DonorDetail,
        personal_details: PersonalDetails,
        address_details: AddressDetails,
        disease_details: DiseaseDetails,
        terms: TermsAndConditions,
    ) -> DonorDetail:
        """Create a new donor with all related details."""
        self.session.add(personal_details)
        self.session.add(address_details)
        self.session.add(disease_details)
        self.session.add(terms)
        self.session.add(donor)
        await self.session.flush()
        return donor

    async def update(self, donor: DonorDetail) -> DonorDetail:
        """Update donor details."""
        await self.session.merge(donor)
        await self.session.flush()
        return donor

    async def update_last_login(self, donor_id: str) -> None:
        """Update donor's last login time."""
        stmt = (
            update(DonorDetail)
            .where(DonorDetail.id == donor_id)
            .values(last_login_date=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def update_last_donated(
        self, donor_id: str, donation_date: datetime
    ) -> None:
        """Update donor's last donated date and increment count."""
        stmt = (
            update(DonorDetail)
            .where(DonorDetail.id == donor_id)
            .values(
                last_donated_date=donation_date,
                number_of_times_donated=DonorDetail.number_of_times_donated + 1,
                active_status=False,  # Deactivate after donation
            )
        )
        await self.session.execute(stmt)

    async def set_active_status(self, donor_id: str, active: bool) -> None:
        """Set donor active status."""
        stmt = (
            update(DonorDetail)
            .where(DonorDetail.id == donor_id)
            .values(active_status=active)
        )
        await self.session.execute(stmt)

    async def reactivate_eligible_donors(self, cutoff_date: date) -> int:
        """Reactivate donors who haven't donated since cutoff date."""
        stmt = (
            update(DonorDetail)
            .where(
                and_(
                    DonorDetail.active_status == False,
                    DonorDetail.last_donated_date <= cutoff_date,
                )
            )
            .values(active_status=True)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def log_authentication(
        self, auth_id: str, name: str, login_date: date, login_time
    ) -> None:
        """Log donor authentication event."""
        auth_log = AuthenticationDetailsDonor(
            auth_id=auth_id,
            name=name,
            login_date=login_date,
            login_time=login_time,
        )
        self.session.add(auth_log)

    async def delete(self, donor_id: str) -> bool:
        """Delete a donor (soft delete recommended for production)."""
        stmt = delete(DonorDetail).where(DonorDetail.id == donor_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
