"""
Authentication Router - Complete Implementation

Login, logout, and password reset endpoints for donors and admins.
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.database import get_db
from app.config import get_settings
from app.core.rate_limiter import enforce_account_limit, limiter
from app.core.recaptcha import verify_recaptcha
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails
from app.services.email_service import get_email_service
from app.services.erasure_service import lock_donor
from app.services.refresh_session_service import (
    claim_session,
    issue_refresh_token,
    revoke_all_for_user,
    revoke_chain,
)
from app.models.refresh_session import RefreshSession
from app.services.otp_service import (
    PURPOSE_ADMIN_RESET,
    PURPOSE_DONOR_RESET,
    generate_otp,
    store_otp,
    verify_otp,
    failed_confirmation_count,
    record_failed_confirmation,
    clear_failed_confirmations,
)
from app.api.auth.utils import (
    DUMMY_PASSWORD_HASH,
    hash_password_async,
    verify_password_async,
    needs_rehash,
    create_access_token,
    decode_token
)
from app.schemas.passwords import check_password_length
from app.schemas.donor import PasswordResetRequest, PasswordResetConfirm
from app.utils.emails import normalize_email
from app.utils.dates import utcnow
from app.api.auth.deps import get_current_user
from app.core.request_status import AdminStatus

logger = logging.getLogger(__name__)


async def _send_reset_email(email: str, otp: str, name: str) -> None:
    """Send a reset code after the generic response and warn if delivery fails."""
    sent = await get_email_service().send_otp_email(email, otp, name)
    if not sent:
        logger.warning("Password reset email delivery failed")
_settings = get_settings()

# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class LoginRequest(BaseModel, extra="forbid"):
    """Login request schema."""
    email: EmailStr = Field(..., max_length=100)
    password: str
    recaptcha_token: Optional[str] = Field(None, max_length=4096)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return check_password_length(v)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "donor@example.com",
                "password": "password123"
            }
        }


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str
    username: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "<access-token>",
                "token_type": "bearer",
                "user_id": "DON-123456",
                "user_type": "donor",
                "username": "John Doe"
            }
        }


def _refresh_cookie_name() -> str:
    if get_settings().APP_ENV.lower() == "development":
        return "lc_refresh_token"
    return "__Host-lc_refresh_token"


def _cookie_path() -> str:
    return "/" if _refresh_cookie_name().startswith("__Host-") else "/api/v1/auth"


def check_session_origin(request: Request) -> None:
    """CORS controls response reads. Reject untrusted browser session writes before side effects."""
    origins = request.headers.getlist("origin")
    if origins:
        own_origin = f"{request.url.scheme}://{request.url.netloc}"
        trusted = get_settings().ALLOWED_ORIGINS or []
        if len(origins) != 1 or (origins[0] != own_origin and origins[0] not in trusted):
            raise HTTPException(403, "Untrusted request origin")
    elif (request.url.path.endswith(("/refresh", "/logout"))
          and _refresh_cookie_name() in request.cookies
          and request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json"):
        # JSON is not a CORS-safelisted content type. Browser cross-origin use requires preflight.
        raise HTTPException(403, "Session requests require a trusted Origin or application/json")



def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        _refresh_cookie_name(),
        token,
        httponly=True,
        secure=settings.APP_ENV.lower() != "development",
        samesite="strict",
        path=_cookie_path(),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        _refresh_cookie_name(),
        path=_cookie_path(),
        httponly=True,
        secure=get_settings().APP_ENV.lower() != "development",
        samesite="strict",
    )


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


async def enforce_recaptcha(token: Optional[str], action: str) -> None:
    """Reject the request (400, fail closed) when RECAPTCHA_ENFORCED and the token is missing/invalid."""
    if not get_settings().RECAPTCHA_ENFORCED:
        return
    if not token or not await verify_recaptcha(token, action):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reCAPTCHA verification failed",
        )


def _invalid_refresh(response: Response) -> HTTPException:
    _clear_refresh_cookie(response)
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"Set-Cookie": response.headers["set-cookie"]},
    )


async def _reject_reused_refresh_token(
    session: AsyncSession, old_session: RefreshSession, response: Response
) -> None:
    """A spent refresh token is being replayed: assume theft, kill the whole chain, answer 401."""
    await revoke_all_for_user(session, old_session.user_id, old_session.role)
    # Commit now: raising below rolls the request transaction back and would undo the revocation.
    await session.commit()
    logger.warning("Refresh token reuse detected")
    raise _invalid_refresh(response)


# ============================================================
# ROUTER SETUP
# ============================================================

router = APIRouter(
    prefix="/auth",
    dependencies=[Depends(check_session_origin)],
    tags=["Authentication"]
)

# ============================================================
# DONOR AUTHENTICATION ENDPOINTS
# ============================================================

@router.post("/donor/login", response_model=TokenResponse)
@limiter.limit(_settings.AUTH_RATE_LIMIT)
async def donor_login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Donor login endpoint.
    
    Authenticates a donor with email and password.
    Returns JWT access and refresh tokens.
    
    Args:
        credentials: Email and password
        session: Database session
        
    Returns:
        TokenResponse: Access token, refresh token, and user info
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    await enforce_account_limit(request, credentials.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    await enforce_recaptcha(credentials.recaptcha_token, "donor_login")
    try:
        # Get donor by email
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(credentials.email))
            .with_for_update(of=DonorDetail)
        )
        donor = result.scalar_one_or_none()
        
        # Check if donor exists
        if not donor:
            # Same bcrypt cost as a wrong password, so response time does not reveal which emails exist.
            await verify_password_async(credentials.password, DUMMY_PASSWORD_HASH)
            logger.warning("Login attempt with unknown email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not await verify_password_async(credentials.password, donor.password):
            logger.warning("Failed login attempt for donor")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if not donor.active_status:
            logger.warning("Login blocked for inactive donor")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if needs_rehash(donor.password):
            donor.password = await hash_password_async(credentials.password)

        # Update last login â€” store full datetime
        donor.last_login_date = utcnow()
        
        logger.info("Donor logged in successfully")
        
        # Create tokens
        token_data = {
            "sub": donor.id,
            "user_type": "donor",
            "email": donor.email,
            "tv": donor.token_version,
        }
        
        access_token = create_access_token(token_data)
        refresh_token, _ = await issue_refresh_token(session, token_data)
        _set_refresh_cookie(response, refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=donor.id,
            user_type="donor",
            username=donor.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during donor login: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit(_settings.AUTH_RATE_LIMIT)
async def admin_login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Admin login endpoint.
    
    Authenticates an admin with email and password.
    Returns JWT access and refresh tokens.
    
    Args:
        credentials: Email and password
        session: Database session
        
    Returns:
        TokenResponse: Access token, refresh token, and user info
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    await enforce_account_limit(request, credentials.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    await enforce_recaptcha(credentials.recaptcha_token, "admin_login")
    try:
        # Get admin by email
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(credentials.email))
            .with_for_update(of=AdminDetails)
        )
        admin = result.scalar_one_or_none()
        
        # Check if admin exists
        if not admin:
            await verify_password_async(credentials.password, DUMMY_PASSWORD_HASH)
            logger.warning("Admin login attempt with unknown email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not await verify_password_async(credentials.password, admin.password):
            logger.warning("Failed admin login attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if admin.active_status != AdminStatus.ACTIVE:
            logger.warning("Login blocked for inactive admin")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if needs_rehash(admin.password):
            admin.password = await hash_password_async(credentials.password)

        # Update last login â€” store full datetime
        admin.last_login_date = utcnow()
        
        logger.info("Admin logged in successfully")
        
        # Create tokens
        token_data = {
            "sub": admin.id,
            "user_type": "admin",
            "email": admin.email,
            "tv": admin.token_version,
            "role": admin.role,
        }
        
        access_token = create_access_token(token_data)
        refresh_token, _ = await issue_refresh_token(session, token_data)
        _set_refresh_cookie(response, refresh_token)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=admin.id,
            user_type="admin",
            username=admin.username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during admin login: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


# ============================================================
# TOKEN REFRESH ENDPOINT
# ============================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Refresh access token using refresh token.
    
    Takes an expired access token's refresh token and issues new tokens.
    
    Args:
        data: Refresh token
        session: Database session
        
    Returns:
        TokenResponse: New access and refresh tokens
        
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    try:
        # Decode refresh token
        presented_token = request.cookies.get(_refresh_cookie_name())
        if not presented_token:
            raise HTTPException(401, "Invalid or expired refresh token")
        payload = decode_token(presented_token)
        if payload is None:
            raise _invalid_refresh(response)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # The token must match a live server-side session (rotation + reuse detection)
        old_session = await session.get(RefreshSession, payload.get("jti") or "")
        if old_session is None:
            await revoke_all_for_user(session, payload.get("sub"), payload.get("user_type"))
            await session.commit()
            raise _invalid_refresh(response)
        if (
            old_session.user_id != payload.get("sub")
            or old_session.role != payload.get("user_type")
        ):
            raise _invalid_refresh(response)
        if old_session.revoked_at is not None:
            await _reject_reused_refresh_token(session, old_session, response)
        if old_session.expires_at < utcnow():
            raise _invalid_refresh(response)

        # Extract user info
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        # Fetch updated user from database
        if user_type == "donor":
            user = await lock_donor(session, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Donor not found",
                )
        elif user_type == "admin":
            user = await session.get(AdminDetails, user_id, with_for_update=True)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user type",
            )
        
        is_active = (
            bool(user.active_status) if user_type == "donor"
            else user.active_status == AdminStatus.ACTIVE
        )
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        if payload.get("tv") != user.token_version:
            raise _invalid_refresh(response)

        # Create new tokens
        token_data = {
            "sub": user.id,
            "user_type": user_type,
            "email": user.email,
            "tv": user.token_version,
        }
        if user_type == "admin":
            token_data["role"] = user.role
        
        # Spend the old token atomically. If a concurrent request already did, this one is a replay.
        if not await claim_session(session, old_session.jti):
            await _reject_reused_refresh_token(session, old_session, response)

        access_token = create_access_token(token_data)
        refresh_token, new_jti = await issue_refresh_token(session, token_data)
        _set_refresh_cookie(response, refresh_token)
        old_session.replaced_by = new_jti
        
        logger.info("Token refreshed for account")
        
        username = user.name if user_type == "donor" else user.username  # type: ignore[union-attr]
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user_id=user.id,
            user_type=user_type,
            username=username
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Log out: revoke the given refresh token and any token rotated from it.

    Always answers 200 so the client can clear its session even if the token
    was already invalid.
    """
    payload = decode_token(request.cookies.get(_refresh_cookie_name(), ""))
    if payload and payload.get("type") == "refresh":
        await revoke_chain(session, payload.get("jti"))
    if _refresh_cookie_name() in request.cookies:
        _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db, scope="function"),
):
    """Revoke all sessions and invalidate every access token issued before this request."""
    user_type = current_user["user_type"]
    if user_type == "donor":
        account = await lock_donor(session, current_user["user_id"])
    else:
        account = await session.get(
            AdminDetails, current_user["user_id"], with_for_update=True, populate_existing=True,
        )
    if account is None:
        raise HTTPException(status_code=401, detail="Account no longer exists")
    account.token_version += 1
    await revoke_all_for_user(session, account.id, user_type)
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out everywhere")


# ============================================================
# PASSWORD RESET ENDPOINTS
# ============================================================

@router.post("/donor/password-reset/request", response_model=MessageResponse)
@limiter.limit(_settings.PASSWORD_RESET_RATE_LIMIT)
async def request_donor_password_reset(
    request: Request,
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """Request a donor reset without disclosing whether the account exists."""
    await enforce_account_limit(request, data.email, get_settings().ACCOUNT_CODE_SEND_RATE_LIMIT)
    try:
        # Check if donor exists
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(data.email))
            .with_for_update(of=DonorDetail)
        )
        donor = result.scalar_one_or_none()
        
        if not donor:
            logger.info("Password reset requested for unknown email")
            # Don't reveal if email exists (security best practice)
            return MessageResponse(
                message="If this email exists, you will receive a reset link"
            )
         
        otp = generate_otp()
        await store_otp(session, donor.email, otp, PURPOSE_DONOR_RESET)
        # Send after the response: awaiting SMTP here would make known emails answer slower than unknown ones.
        background_tasks.add_task(_send_reset_email, donor.email, otp, donor.name)
        
        logger.info("Password reset requested for donor")
        
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error requesting password reset: {type(e).__name__}")
        # Return generic message for security
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/donor/password-reset/confirm", response_model=MessageResponse)
@limiter.limit(get_settings().AUTH_RATE_LIMIT)
async def confirm_donor_password_reset(
    request: Request,
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Confirm password reset with OTP.
    
    Args:
        data: Email, OTP, and new password
        session: Database session
        
    Returns:
        MessageResponse: Confirmation message
        
    Raises:
        HTTPException: 400 if OTP is invalid
    """
    await enforce_account_limit(request, data.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    try:
        # Find donor
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(data.email))
            .with_for_update(of=DonorDetail)
        )
        donor = result.scalar_one_or_none()

        if await failed_confirmation_count(session, data.email, PURPOSE_DONOR_RESET) >= 10:
            raise HTTPException(status_code=429, detail="Too many failed code attempts; try again later")

        # Use the same public error for unknown accounts and unusable codes.
        otp_ok = await verify_otp(
            session, data.email, data.otp, PURPOSE_DONOR_RESET, commit_success=False,
        )
        if donor is None or not otp_ok:
            if otp_ok:
                # An orphaned code must not authorize an update or be committed by the failure counter.
                await session.rollback()
            await record_failed_confirmation(session, data.email, PURPOSE_DONOR_RESET)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
        await clear_failed_confirmations(session, data.email, PURPOSE_DONOR_RESET)
        # Hash new password
        donor.password = await hash_password_async(data.new_password)
        donor.token_version += 1
        await revoke_all_for_user(session, donor.id, "donor")
        
        logger.info("Password reset for donor")
        
        return MessageResponse(message="Password reset successful. Please login")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming password reset: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )


@router.post("/admin/password-reset/request", response_model=MessageResponse)
@limiter.limit(_settings.PASSWORD_RESET_RATE_LIMIT)
async def request_admin_password_reset(
    request: Request,
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """Request password reset for an admin."""
    await enforce_account_limit(request, data.email, get_settings().ACCOUNT_CODE_SEND_RATE_LIMIT)
    try:
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(data.email))
            .with_for_update(of=AdminDetails)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            logger.info("Admin password reset requested for unknown email")
        else:
            otp = generate_otp()
            await store_otp(session, admin.email, otp, PURPOSE_ADMIN_RESET)
            background_tasks.add_task(_send_reset_email, admin.email, otp, admin.username)
            logger.info("Admin password reset requested for")

        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error requesting admin password reset: {type(e).__name__}")
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/admin/password-reset/confirm", response_model=MessageResponse)
@limiter.limit(get_settings().AUTH_RATE_LIMIT)
async def confirm_admin_password_reset(
    request: Request,
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """Confirm password reset for admin."""
    await enforce_account_limit(request, data.email, get_settings().ACCOUNT_AUTH_RATE_LIMIT)
    try:
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(data.email))
            .with_for_update(of=AdminDetails)
        )
        admin = result.scalar_one_or_none()

        if await failed_confirmation_count(session, data.email, PURPOSE_ADMIN_RESET) >= 10:
            raise HTTPException(status_code=429, detail="Too many failed code attempts; try again later")

        # Consume the code in the same transaction as the credential and session changes.
        otp_ok = await verify_otp(
            session, data.email, data.otp, PURPOSE_ADMIN_RESET, commit_success=False,
        )
        if admin is None or not otp_ok:
            if otp_ok:
                await session.rollback()
            await record_failed_confirmation(session, data.email, PURPOSE_ADMIN_RESET)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")
        await clear_failed_confirmations(session, data.email, PURPOSE_ADMIN_RESET)
        # Hash new password
        admin.password = await hash_password_async(data.new_password)
        admin.token_version += 1
        await revoke_all_for_user(session, admin.id, "admin")
        
        logger.info("Password reset for admin")
        
        return MessageResponse(message="Password reset successful. Please login")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming admin password reset: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )
