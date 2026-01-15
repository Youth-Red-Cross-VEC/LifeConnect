from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from app.models.admin import AdminDetails, AuthenticationDetailsAdmin
from typing import Optional, List
from datetime import datetime, date


class AdminRepository:
    """
    Repository for admin data access.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, admin_id: str) -> Optional[AdminDetails]:
        """Get admin by ID."""
        query = select(AdminDetails).where(AdminDetails.id == admin_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[AdminDetails]:
        """Get admin by email."""
        query = select(AdminDetails).where(AdminDetails.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        """Check if admin with email exists."""
        query = select(func.count()).where(AdminDetails.email == email)
        result = await self.session.execute(query)
        return result.scalar() > 0

    async def exists_by_registration_number(self, reg_number: str) -> bool:
        """Check if admin with registration number exists."""
        query = select(func.count()).where(
            AdminDetails.vec_registration_number == reg_number
        )
        result = await self.session.execute(query)
        return result.scalar() > 0

    async def get_all_active(self) -> List[AdminDetails]:
        """Get all active admins."""
        query = select(AdminDetails).where(AdminDetails.active_status == "Active")
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        active_only: bool = False,
    ) -> tuple[List[AdminDetails], int]:
        """Get all admins with pagination."""
        query = select(AdminDetails)

        if active_only:
            query = query.where(AdminDetails.active_status == "Active")

        # Count
        count_query = select(func.count()).select_from(AdminDetails)
        if active_only:
            count_query = count_query.where(AdminDetails.active_status == "Active")
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()

        # Paginated
        query = query.offset(offset).limit(limit).order_by(AdminDetails.created_at.desc())
        result = await self.session.execute(query)
        admins = list(result.scalars().all())

        return admins, total

    async def create(self, admin: AdminDetails) -> AdminDetails:
        """Create a new admin."""
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def update(self, admin: AdminDetails) -> AdminDetails:
        """Update admin details."""
        await self.session.merge(admin)
        await self.session.flush()
        return admin

    async def update_last_login(self, admin_id: str) -> None:
        """Update admin's last login time."""
        stmt = (
            update(AdminDetails)
            .where(AdminDetails.id == admin_id)
            .values(last_login_date=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def increment_approved_count(self, admin_id: str) -> None:
        """Increment admin's approved donation count."""
        stmt = (
            update(AdminDetails)
            .where(AdminDetails.id == admin_id)
            .values(approved_donation_count=AdminDetails.approved_donation_count + 1)
        )
        await self.session.execute(stmt)

    async def increment_closed_count(self, admin_id: str) -> None:
        """Increment admin's closed requests count."""
        stmt = (
            update(AdminDetails)
            .where(AdminDetails.id == admin_id)
            .values(closed_requests_count=AdminDetails.closed_requests_count + 1)
        )
        await self.session.execute(stmt)

    async def log_authentication(
        self, auth_id: str, name: str, login_date: date, login_time
    ) -> None:
        """Log admin authentication event."""
        auth_log = AuthenticationDetailsAdmin(
            auth_id=auth_id,
            name=name,
            login_date=login_date,
            login_time=login_time,
        )
        self.session.add(auth_log)

    async def update_password(self, admin_id: str, hashed_password: str) -> None:
        """Update admin password."""
        stmt = (
            update(AdminDetails)
            .where(AdminDetails.id == admin_id)
            .values(password=hashed_password)
        )
        await self.session.execute(stmt)
