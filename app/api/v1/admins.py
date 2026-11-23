"""
Admin Management API Routes.

Endpoints for admin registration, profile management, and administration.
Note: Authentication (login/logout) is handled by the auth module (partner's responsibility).
"""

from fastapi import Path as ApiPath
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from app.config import get_settings
from app.core.database import get_db
from app.core.request_status import AdminStatus, AdminRole, BloodRequestStatus

from app.repositories.admin import AdminRepository
from app.repositories.blood_request import BloodRequestRepository
from app.repositories.donor import DonorRepository
from app.models.admin import AdminDetails
from app.schemas.admin import (
    AdminCreate,
    AdminInviteRequest,
    AdminUpdate,
    AdminResponse,
    AdminSummaryResponse,
    AdminStatsResponse,
)
from app.schemas.common import SuccessResponse, PaginatedResponse
from app.utils.emails import normalize_email
from app.utils.id_generator import generate_prefixed_id
from app.api.auth.deps import get_current_admin, require_super_admin
from app.services.audit_service import record_admin_action
from app.services.otp_service import (
    PURPOSE_ADMIN_INVITE, generate_otp, store_otp, verify_otp,
    failed_confirmation_count, record_failed_confirmation, clear_failed_confirmations,
)
from app.core.rate_limiter import check_account_limit, limiter
from app.services.refresh_session_service import revoke_all_for_user

router = APIRouter(prefix="/admins", tags=["Admins"])


def _admin_view(admin: AdminDetails, viewer: AdminDetails) -> Union[AdminResponse, AdminSummaryResponse]:
    """The full record for the viewer's own row; everyone else's without date of birth and phone number."""
    model = AdminResponse if admin.id == viewer.id else AdminSummaryResponse
    return model.model_validate(admin)


async def _management_target(repo: AdminRepository, actor: AdminDetails, target_id: str, *, super_only: bool = False) -> AdminDetails | None:
    authenticated_version = actor.token_version
    accounts = await repo.lock_management_accounts(actor.id, target_id)
    current = accounts.get(actor.id)
    if current is None or current.active_status != AdminStatus.ACTIVE:
        raise HTTPException(status_code=401, detail="Account is inactive or no longer exists")
    if current.token_version != authenticated_version:
        raise HTTPException(status_code=401, detail="Session has been revoked")
    if super_only and current.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    return accounts.get(target_id)


async def _guard_deactivation(repo: AdminRepository, target: AdminDetails, actor: AdminDetails) -> None:
    """Refuse the two ways an admin can lock the team out: switching themselves off, or the last admin off."""
    if target.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account; ask another admin to do it",
        )
    if target.active_status == AdminStatus.ACTIVE and target.role == AdminRole.SUPER_ADMIN:
        if await repo.count_active_super_admins(exclude_id=target.id) == 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot deactivate the last active super admin",
            )


async def _guard_role_change(repo: AdminRepository, target: AdminDetails, new_role: AdminRole) -> None:
    if (
        target.active_status == AdminStatus.ACTIVE
        and target.role == AdminRole.SUPER_ADMIN
        and new_role != AdminRole.SUPER_ADMIN
        and await repo.count_active_super_admins(exclude_id=target.id) == 0
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot demote the last active super admin",
        )


# =======================
# Admin Invite (OTP gate)
# =======================

@router.post(
    "/invite",
    summary="Send admin invite OTP",
    status_code=status.HTTP_200_OK,
)
@limiter.limit(get_settings().PASSWORD_RESET_RATE_LIMIT)
async def invite_admin(
    request: Request,
    data: AdminInviteRequest,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(require_super_admin),
):
    """
    Generate and email a 6-digit invite OTP to the given address.

    Only existing admins can send invites. The OTP is valid for 10 minutes
    and must be supplied in the subsequent `POST /admins/register` call.
    """
    check_account_limit(request, data.email, get_settings().ACCOUNT_CODE_SEND_RATE_LIMIT)
    from app.services.email_service import get_email_service
    otp = generate_otp()
    await store_otp(session, data.email, otp, PURPOSE_ADMIN_INVITE)

    email_svc = get_email_service()
    sent = await email_svc.send_otp_email(
        email=data.email,
        otp=otp,
        name="New Admin",
        purpose="admin_invite",
    )
    if not sent:
        # Do not report success when the invite never left the server: the invitee would wait for a
        # code that is not coming. A retry issues a new code.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not send the invite email; please try again later",
        )
    record_admin_action(session, current_admin.id, "admin.invite", "admin_invite")
    return {"message": f"Invite OTP sent to {data.email}."}


# =======================
# Admin Registration
# =======================

@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new admin",
)
@limiter.limit(get_settings().AUTH_RATE_LIMIT)
async def register_admin(
    request: Request,
    data: AdminCreate,
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """
    Register a new admin account.

    Requires a valid `invite_otp` issued by an existing admin via `POST /admins/invite`.
    The OTP is sent to the registrant's email and is valid for 10 minutes.
    This prevents self-registration without an existing admin's approval.
    """
    check_account_limit(request, data.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    if await failed_confirmation_count(session, data.email, PURPOSE_ADMIN_INVITE) >= 10:
        raise HTTPException(status_code=429, detail="Too many failed code attempts; try again later")

    # Verify invite OTP
    if not await verify_otp(session, data.email, data.invite_otp, PURPOSE_ADMIN_INVITE, commit_success=False):
        await record_failed_confirmation(session, data.email, PURPOSE_ADMIN_INVITE)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite code",
        )
    await clear_failed_confirmations(session, data.email, PURPOSE_ADMIN_INVITE)

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
    
    # Hash password with the shared direct-bcrypt utility off the event loop.
    from app.api.auth.utils import hash_password_async
    hashed_password = await hash_password_async(data.password)
    
    # Create admin
    admin = AdminDetails(
        id=admin_id,
        email=normalize_email(data.email),
        password=hashed_password,
        username=data.username,
        authentication_id=auth_id,
        vec_registration_number=data.vec_registration_number,
        date_of_birth=data.date_of_birth,
        mobile_number=data.mobile_number,
        department=data.department,
        active_status=AdminStatus.ACTIVE.value,
        last_login_date=None,
        approved_donation_count=0,
        closed_requests_count=0,
    )
    
    try:
        await repo.create(admin)
    except IntegrityError:
        # Two registrations raced past the existence checks; the unique constraint is authoritative.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin with this email or registration number already exists",
        ) from None
    record_admin_action(session, admin_id, "admin.register", "admin", admin_id)
    
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
    page: int = Query(1, ge=1, le=100000),
    page_size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False),
    session: AsyncSession = Depends(get_db, scope="function"),
        current_admin: AdminDetails = Depends(get_current_admin),
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
        items=[_admin_view(a, current_admin) for a in admins],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get(
    "/{admin_id}",
    response_model=Union[AdminResponse, AdminSummaryResponse],
    summary="Get admin by ID",
)
async def get_admin(
    admin_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(get_current_admin),
):
    """Get admin details by ID (date of birth and phone number only for your own record)."""
    repo = AdminRepository(session)
    admin = await repo.get_by_id(admin_id)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )

    return _admin_view(admin, current_admin)


@router.get(
    "/me/profile",
    response_model=AdminResponse,
    summary="Get current admin profile",
)
async def get_my_profile(
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(get_current_admin),
):
    """
    Get the currently logged-in admin's profile.
    """
    admin = await AdminRepository(session).get_by_id(current_admin.id)
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return admin


@router.put(
    "/{admin_id}",
    response_model=Union[AdminResponse, AdminSummaryResponse],
    summary="Update admin details",
)
async def update_admin(
    admin_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    data: AdminUpdate,
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(get_current_admin),
):
    """Update admin details."""
    repo = AdminRepository(session)
    admin = await _management_target(repo, current_admin, admin_id)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    fields = data.model_fields_set
    if current_admin.role != AdminRole.SUPER_ADMIN:
        if admin.id != current_admin.id:
            raise HTTPException(status_code=403, detail="Only a super admin may edit another admin")
        if fields - {"username", "mobile_number"}:
            raise HTTPException(status_code=403, detail="You may only edit your own name and mobile number")

    if data.role is not None and data.role != admin.role:
        await _guard_role_change(repo, admin, data.role)
        admin.role = data.role
        admin.token_version += 1
        await revoke_all_for_user(session, admin.id, "admin")

    # Update fields if provided
    if data.username is not None:
        admin.username = data.username
    if data.mobile_number is not None:
        admin.mobile_number = data.mobile_number
    if data.department is not None:
        admin.department = data.department
    if data.active_status is not None:
        if data.active_status == AdminStatus.INACTIVE:
            await _guard_deactivation(repo, admin, current_admin)
            await revoke_all_for_user(session, admin.id, "admin")
        admin.active_status = data.active_status.value
        admin.token_version += 1
    
    try:
        await repo.update(admin)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That value is already used by another admin",
        ) from None
    record_admin_action(
        session, current_admin.id, "admin.update", "admin", admin_id,
        detail="fields=" + ",".join(sorted(data.model_dump(exclude_unset=True))),
    )

    return _admin_view(admin, current_admin)


@router.patch(
    "/{admin_id}/deactivate",
    response_model=SuccessResponse,
    summary="Deactivate an admin",
)
async def deactivate_admin(
    admin_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(require_super_admin),
):
    """Deactivate an admin account."""
    repo = AdminRepository(session)
    admin = await _management_target(repo, current_admin, admin_id, super_only=True)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    await _guard_deactivation(repo, admin, current_admin)
    admin.active_status = AdminStatus.INACTIVE
    admin.token_version += 1
    await revoke_all_for_user(session, admin.id, "admin")
    await repo.update(admin)
    record_admin_action(session, current_admin.id, "admin.deactivate", "admin", admin_id)

    return SuccessResponse(message=f"Admin {admin_id} has been deactivated")


@router.patch(
    "/{admin_id}/activate",
    response_model=SuccessResponse,
    summary="Activate an admin",
)
async def activate_admin(
    admin_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(require_super_admin),
):
    """Activate an admin account."""
    repo = AdminRepository(session)
    admin = await _management_target(repo, current_admin, admin_id, super_only=True)
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with ID {admin_id} not found",
        )
    
    admin.active_status = AdminStatus.ACTIVE
    admin.token_version += 1
    await repo.update(admin)
    record_admin_action(session, current_admin.id, "admin.activate", "admin", admin_id)

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
    admin_id: Annotated[str, ApiPath(min_length=1, max_length=36)],
    session: AsyncSession = Depends(get_db, scope="function"),
    current_admin: AdminDetails = Depends(get_current_admin),
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
        pending_requests=status_stats.get(BloodRequestStatus.PENDING, 0),
        ongoing_requests=status_stats.get(BloodRequestStatus.APPROVED, 0),
        active_donors=active_donor_count,
    )
