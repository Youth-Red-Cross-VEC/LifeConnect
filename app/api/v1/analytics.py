"""
Analytics API Routes.

Dashboard statistics and reporting endpoints for admins.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.auth.deps import get_current_admin
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.repositories.hospital import HospitalRepository
from app.models.donor import DonorDetail
from app.models.blood_request import BloodRequestDetails
from app.models.hospital import HospitalDetails

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """
    Get dashboard statistics for admin panel.
    
    Returns counts for donors, requests, and hospitals.
    """
    request_repo = BloodRequestRepository(session)

    # Get request stats
    status_stats = await request_repo.get_status_stats()
    blood_group_stats = await request_repo.get_blood_group_stats()

    # Get donor counts
    total_donors = await session.execute(
        select(func.count()).select_from(DonorDetail)
    )
    active_donors = await session.execute(
        select(func.count())
        .select_from(DonorDetail)
        .where(DonorDetail.active_status == True)
    )

    # Get hospital count
    total_hospitals = await session.execute(
        select(func.count()).select_from(HospitalDetails)
    )

    return {
        "requests": {
            "pending": status_stats.get("Pending", 0),
            "ongoing": status_stats.get("Approved", 0),
            "closed": status_stats.get("Closed", 0),
            "expired": status_stats.get("Expired", 0),
            "declined": status_stats.get("Declined", 0),
            "total": sum(status_stats.values()),
        },
        "donors": {
            "total": total_donors.scalar(),
            "active": active_donors.scalar(),
        },
        "hospitals": {
            "total": total_hospitals.scalar(),
        },
        "requests_by_blood_group": blood_group_stats,
    }


@router.get("/donors/by-blood-group")
async def get_donors_by_blood_group(
    session: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Get donor count by blood group."""
    from sqlalchemy import case
    
    query = (
        select(
            DonorDetail.blood_group,
            func.count().label("total"),
            func.sum(case((DonorDetail.active_status == True, 1), else_=0)).label("active"),
        )
        .group_by(DonorDetail.blood_group)
    )

    result = await session.execute(query)

    return {
        row.blood_group: {"total": row.total, "active": int(row.active or 0)}
        for row in result.all()
    }


@router.get("/donors/by-city")
async def get_donors_by_city(
    session: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Get donor count by city."""
    from app.models.donor import AddressDetails

    query = (
        select(
            AddressDetails.city,
            func.count().label("count"),
        )
        .join(DonorDetail)
        .group_by(AddressDetails.city)
        .order_by(func.count().desc())
        .limit(20)
    )

    result = await session.execute(query)
    return {row.city: row.count for row in result.all()}


@router.get("/requests/monthly")
async def get_monthly_request_stats(
    session: AsyncSession = Depends(get_db),
    current_admin = Depends(get_current_admin),
):
    """Get request counts by month for the last 12 months."""
    from sqlalchemy import extract
    from datetime import datetime, timedelta, timezone

    # Get requests from last 12 months
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)

    query = (
        select(
            extract("year", BloodRequestDetails.created_at).label("year"),
            extract("month", BloodRequestDetails.created_at).label("month"),
            func.count().label("count"),
        )
        .where(BloodRequestDetails.created_at >= twelve_months_ago)
        .group_by(
            extract("year", BloodRequestDetails.created_at),
            extract("month", BloodRequestDetails.created_at),
        )
        .order_by(
            extract("year", BloodRequestDetails.created_at),
            extract("month", BloodRequestDetails.created_at),
        )
    )

    result = await session.execute(query)

    return [
        {
            "year": int(row.year),
            "month": int(row.month),
            "count": row.count,
        }
        for row in result.all()
    ]
