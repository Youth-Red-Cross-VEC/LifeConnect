"""
Hospital API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.repositories.hospital import HospitalRepository
from app.schemas.blood_request import (
    HospitalCreate,
    HospitalUpdate,
    HospitalResponse,
    HospitalAutofillResponse,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.models.hospital import HospitalDetails
from app.utils import generate_hospital_id
from app.core.exceptions import not_found_exception, duplicate_exception

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


@router.post("/", response_model=HospitalResponse, status_code=status.HTTP_201_CREATED)
async def create_hospital(
    data: HospitalCreate,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Create a new hospital (admin only)."""
    repo = HospitalRepository(session)

    # Check for duplicate
    existing = await repo.get_by_name(data.hospital_name)
    if existing:
        raise duplicate_exception("Hospital", "name", data.hospital_name)

    hospital = HospitalDetails(
        id=generate_hospital_id(),
        hospital_name=data.hospital_name,
        hospital_address=data.hospital_address,
        pincode=data.pincode,
        city=data.city,
        state=data.state,
        country=data.country,
        branch=data.branch,
        landmark=data.landmark,
    )

    await repo.create(hospital)
    return HospitalResponse.model_validate(hospital)


@router.get("/", response_model=PaginatedResponse)
async def list_hospitals(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    """List all hospitals with pagination."""
    repo = HospitalRepository(session)
    offset = (page - 1) * page_size

    hospitals, total = await repo.get_all(
        offset=offset,
        limit=page_size,
        city=city,
        search=search,
    )

    return PaginatedResponse.create(
        items=[HospitalResponse.model_validate(h) for h in hospitals],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/autofill", response_model=List[HospitalAutofillResponse])
async def hospital_autofill(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=10, le=20),
    session: AsyncSession = Depends(get_db),
):
    """Get hospital suggestions for autofill."""
    repo = HospitalRepository(session)
    hospitals = await repo.get_autofill_suggestions(q, limit)

    return [
        HospitalAutofillResponse(
            id=h.id,
            hospital_name=h.hospital_name,
            city=h.city,
            address=h.hospital_address,
        )
        for h in hospitals
    ]


@router.get("/cities", response_model=List[str])
async def get_cities(session: AsyncSession = Depends(get_db)):
    """Get list of cities with hospitals."""
    repo = HospitalRepository(session)
    return await repo.get_cities()


@router.get("/{hospital_id}", response_model=HospitalResponse)
async def get_hospital(
    hospital_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get hospital details by ID."""
    repo = HospitalRepository(session)
    hospital = await repo.get_by_id(hospital_id)

    if not hospital:
        raise not_found_exception("Hospital", hospital_id)

    return HospitalResponse.model_validate(hospital)


@router.patch("/{hospital_id}", response_model=HospitalResponse)
async def update_hospital(
    hospital_id: str,
    data: HospitalUpdate,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Update hospital details (admin only)."""
    repo = HospitalRepository(session)
    hospital = await repo.get_by_id(hospital_id)

    if not hospital:
        raise not_found_exception("Hospital", hospital_id)

    # Update fields if provided
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(hospital, field, value)

    await repo.update(hospital)
    return HospitalResponse.model_validate(hospital)


@router.delete("/{hospital_id}", response_model=MessageResponse)
async def delete_hospital(
    hospital_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),
):
    """Delete a hospital (admin only)."""
    repo = HospitalRepository(session)

    deleted = await repo.delete(hospital_id)
    if not deleted:
        raise not_found_exception("Hospital", hospital_id)

    return MessageResponse(message=f"Hospital {hospital_id} deleted successfully")
