"""
Admin Management API Routes.

Endpoints for admin registration, profile management, and administration.
Note: Authentication (login/logout) is handled by the auth module (partner's responsibility).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import hashlib
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import DuplicateEntityError, EntityNotFoundError
from app.repositories.admin import AdminRepository
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.models.admin import AdminDetails
from app.schemas.admin import (
    AdminCreate,
    AdminUpdate,
    AdminResponse,
    AdminStatsResponse,
)
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.utils.id_generator import generate_prefixed_id

router = APIRouter(prefix="/admins", tags=["Admins"])


# =======================
# Admin Registration
# =======================

@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new admin",
)
async def register_admin(
    data: AdminCreate,
    session: AsyncSession = Depends(get_db),
):
    """
    Register a new admin account.
    
    Note: In production, this should require verification (OTP) 
    and approval from an existing admin. The auth module handles this.
    """
    repo = AdminRepository(session)
    
    # Check for duplicate email
    if await repo.exists_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin with this email already exists",
        )
    
    # Check for duplicate registration number
    if await repo.exists_by_registration_number(data.vec_registration_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin with this registration number already exists",
        )
    
    # Generate IDs
    admin_id = generate_prefixed_id("ADM")
    auth_id = generate_prefixed_id("AUTHADM")
    
    # Hash password using bcrypt (secure)
    from app.core.security import hash_password
    hashed_password = hash_password(data.password)
    
    # Create admin
    admin = AdminDetails(
        id=admin_id,
        email=data.email,
        password=hashed_password,
        username=data.username,
        authentication_id=auth_id,
        vec_registration_number=data.vec_registration_number,
        date_of_birth=data.date_of_birth,
        mobile_number=data.mobile_number,
        department=data.department,
        active_status="Active",
        last_login_date=None,
        approved_donation_count=0,
        closed_requests_count=0,
    )
    
    await repo.create(admin)
    await session.commit()
    
    return admin


# =======================
# Admin Profile & CRUD
# =======================

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List all admins",
)
async def list_admins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Get paginated list of all admins."""
    repo = AdminRepository(session)
    offset = (page - 1) * page_size
    
    admins, total = await repo.get_all(
        offset=offset,
        limit=page_size,
        active_only=active_only,
    )
    
    return PaginatedResponse(
        items=[AdminResponse.model_validate(a) for a in admins],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{admin_id}",
    response_model=AdminResponse,
    summary="Get admin by ID",
)
async def get_admin(
    admin_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Get admin details by ID."""
    repo = AdminRepository(session)
    admin = await repo.get_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    return admin


@router.get(
    "/me/profile",
    response_model=AdminResponse,
    summary="Get current admin profile",
)
async def get_my_profile(
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """
    Get the currently logged-in admin's profile.
    
    Note: This requires auth implementation to identify current user.
    For now, returns a placeholder error.
    """
    # TODO: Once auth is implemented, get admin_id from current_admin
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented. Use /admins/{admin_id} instead.",
    )


@router.put(
    "/{admin_id}",
    response_model=AdminResponse,
    summary="Update admin details",
)
async def update_admin(
    admin_id: str,
    data: AdminUpdate,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Update admin details."""
    repo = AdminRepository(session)
    admin = await repo.get_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    # Update fields if provided
    if data.username is not None:
        admin.username = data.username
    if data.mobile_number is not None:
        admin.mobile_number = data.mobile_number
    if data.department is not None:
        admin.department = data.department
    if data.active_status is not None:
        admin.active_status = data.active_status
    
    await repo.update(admin)
    await session.commit()
    
    return admin


@router.patch(
    "/{admin_id}/deactivate",
    response_model=SuccessResponse,
    summary="Deactivate an admin",
)
async def deactivate_admin(
    admin_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth - should be superadmin
):
    """Deactivate an admin account."""
    repo = AdminRepository(session)
    admin = await repo.get_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    admin.active_status = "Inactive"
    await repo.update(admin)
    await session.commit()
    
    return SuccessResponse(message=f"Admin {admin_id} has been deactivated")


@router.patch(
    "/{admin_id}/activate",
    response_model=SuccessResponse,
    summary="Activate an admin",
)
async def activate_admin(
    admin_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth - should be superadmin
):
    """Activate an admin account."""
    repo = AdminRepository(session)
    admin = await repo.get_by_id(admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    admin.active_status = "Active"
    await repo.update(admin)
    await session.commit()
    
    return SuccessResponse(message=f"Admin {admin_id} has been activated")


# =======================
# Admin Stats
# =======================

@router.get(
    "/{admin_id}/stats",
    response_model=AdminStatsResponse,
    summary="Get admin performance stats",
)
async def get_admin_stats(
    admin_id: str,
    session: AsyncSession = Depends(get_db),
    # current_admin = Depends(get_current_admin),  # TODO: Auth
):
    """Get performance statistics for a specific admin."""
    admin_repo = AdminRepository(session)
    request_repo = BloodRequestRepository(session)
    donor_repo = DonorRepository(session)
    
    admin = await admin_repo.get_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    # Get request stats
    status_stats = await request_repo.get_status_stats()
    
    # Get active donor count - get_all returns (donors, total)
    _, active_donor_count = await donor_repo.get_all(limit=1, active_only=True)
    
    return AdminStatsResponse(
        total_approved=admin.approved_donation_count,
        total_closed=admin.closed_requests_count,
        pending_requests=status_stats.get("Pending", 0),
        ongoing_requests=status_stats.get("Approved", 0),
        active_donors=active_donor_count,
    )
