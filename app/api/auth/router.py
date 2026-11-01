"""
Authentication Router - Complete Implementation

Login, logout, and password reset endpoints for donors and admins.
"""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.database import get_db
from app.config import get_settings
from app.core.rate_limiter import limiter
from app.core.recaptcha import verify_recaptcha
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails
from app.services.email_service import get_email_service
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
)
from app.api.auth.utils import (
    DUMMY_PASSWORD_HASH,
    hash_password_async,
    verify_password_async,
    needs_rehash,
    create_access_token,
    decode_token
)
from app.schemas.passwords import check_new_password, check_password_length
from app.utils.emails import normalize_email
from app.utils.dates import utcnow

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

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr = Field(..., max_length=100)
    password: str
    recaptcha_token: Optional[str] = None

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
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: str
    username: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "DON-123456",
                "user_type": "donor",
                "username": "John Doe"
            }
        }


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request."""
    email: EmailStr = Field(..., max_length=100)


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    email: EmailStr = Field(..., max_length=100)
    otp: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return check_new_password(v)


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


async def _reject_reused_refresh_token(session: AsyncSession, old_session: RefreshSession) -> None:
    """A spent refresh token is being replayed: assume theft, kill the whole chain, answer 401."""
    await revoke_chain(session, old_session.jti)
    # Commit now: raising below rolls the request transaction back and would undo the revocation.
    await session.commit()
    logger.warning(f"Refresh token reuse detected for {old_session.role} {old_session.user_id}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )


# ============================================================
# ROUTER SETUP
# ============================================================

router = APIRouter(
    prefix="/auth",
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
    await enforce_recaptcha(credentials.recaptcha_token, "donor_login")
    try:
        # Get donor by email
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(credentials.email))
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
            logger.warning(f"Failed login attempt for donor: {donor.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if not donor.active_status:
            logger.warning(f"Login blocked for inactive donor: {donor.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if needs_rehash(donor.password):
            donor.password = await hash_password_async(credentials.password)

        # Update last login — store full datetime
        donor.last_login_date = utcnow()
        
        logger.info(f"Donor {donor.id} logged in successfully")
        
        # Create tokens
        token_data = {
            "sub": donor.id,
            "user_type": "donor",
            "email": donor.email,
        }
        
        access_token = create_access_token(token_data)
        refresh_token, _ = await issue_refresh_token(session, token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    await enforce_recaptcha(credentials.recaptcha_token, "admin_login")
    try:
        # Get admin by email
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(credentials.email))
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
            logger.warning(f"Failed admin login attempt: {admin.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if str(admin.active_status).lower() != "active":
            logger.warning(f"Login blocked for inactive admin: {admin.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        if needs_rehash(admin.password):
            admin.password = await hash_password_async(credentials.password)

        # Update last login — store full datetime
        admin.last_login_date = utcnow()
        
        logger.info(f"Admin {admin.id} logged in successfully")
        
        # Create tokens
        token_data = {
            "sub": admin.id,
            "user_type": "admin",
            "email": admin.email,
        }
        
        access_token = create_access_token(token_data)
        refresh_token, _ = await issue_refresh_token(session, token_data)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    data: RefreshRequest,
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
        payload = decode_token(data.refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        # The token must match a live server-side session (rotation + reuse detection)
        old_session = await session.get(RefreshSession, payload.get("jti") or "")
        if (
            old_session is None
            or old_session.user_id != payload.get("sub")
            or old_session.role != payload.get("user_type")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        if old_session.revoked_at is not None:
            await _reject_reused_refresh_token(session, old_session)
        if old_session.expires_at < utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        # Extract user info
        user_id = payload.get("sub")
        user_type = payload.get("user_type")
        
        # Fetch updated user from database
        if user_type == "donor":
            user = await session.get(DonorDetail, user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Donor not found",
                )
        elif user_type == "admin":
            user = await session.get(AdminDetails, user_id)
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
            else str(user.active_status).lower() == "active"
        )
        if not is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        # Create new tokens
        token_data = {
            "sub": user.id,
            "user_type": user_type,
            "email": user.email,
        }
        
        # Spend the old token atomically. If a concurrent request already did, this one is a replay.
        if not await claim_session(session, old_session.jti):
            await _reject_reused_refresh_token(session, old_session)

        access_token = create_access_token(token_data)
        refresh_token, new_jti = await issue_refresh_token(session, token_data)
        old_session.replaced_by = new_jti
        
        logger.info(f"Token refreshed for {user_type} {user.id}")
        
        username = user.name if user_type == "donor" else user.username  # type: ignore[union-attr]
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
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
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """
    Log out: revoke the given refresh token and any token rotated from it.

    Always answers 200 so the client can clear its session even if the token
    was already invalid.
    """
    payload = decode_token(data.refresh_token)
    if payload and payload.get("type") == "refresh":
        await revoke_chain(session, payload.get("jti"))
    return MessageResponse(message="Logged out")


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
    """
    Request password reset for a donor.
    
    In production, integrate with email service to send OTP.
    
    Args:
        data: Donor email
        session: Database session
        
    Returns:
        MessageResponse: Confirmation message
    """
    try:
        # Check if donor exists
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(data.email))
        )
        donor = result.scalar_one_or_none()
        
        if not donor:
            logger.info("Password reset requested for unknown email")
            # Don't reveal if email exists (security best practice)
            return MessageResponse(
                message="If this email exists, you will receive a reset link"
            )
         
        # TODO: Generate OTP and send email
        # otp = generate_otp()
        # await send_password_reset_email(donor.email, otp)
        # Store OTP in database with expiry
        otp = generate_otp()
        await store_otp(session, donor.email, otp, PURPOSE_DONOR_RESET)
        # Send after the response: awaiting SMTP here would make known emails answer slower than unknown ones.
        background_tasks.add_task(_send_reset_email, donor.email, otp, donor.name)
        
        logger.info(f"Password reset requested for donor: {donor.id}")
        
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {type(e).__name__}")
        # Return generic message for security
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/donor/password-reset/confirm", response_model=MessageResponse)
async def confirm_donor_password_reset(
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
    try:
        # Find donor
        result = await session.execute(
            select(DonorDetail).where(func.lower(DonorDetail.email) == normalize_email(data.email))
        )
        donor = result.scalar_one_or_none()

        # One answer for "no such account" and "wrong or expired code", and the same work for both
        # (verify_otp runs either way), so this endpoint cannot be used to discover registered emails.
        otp_ok = await verify_otp(session, data.email, data.otp, PURPOSE_DONOR_RESET)
        if donor is None or not otp_ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
        # Hash new password
        donor.password = await hash_password_async(data.new_password)
        await revoke_all_for_user(session, donor.id, "donor")
        
        logger.info(f"Password reset for donor: {donor.id}")
        
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
    try:
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(data.email))
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            logger.info("Admin password reset requested for unknown email")
        else:
            otp = generate_otp()
            await store_otp(session, admin.email, otp, PURPOSE_ADMIN_RESET)
            background_tasks.add_task(_send_reset_email, admin.email, otp, admin.username)
            logger.info(f"Admin password reset requested for: {admin.id}")

        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        logger.error(f"Error requesting admin password reset: {type(e).__name__}")
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/admin/password-reset/confirm", response_model=MessageResponse)
async def confirm_admin_password_reset(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db, scope="function")
):
    """Confirm password reset for admin."""
    try:
        result = await session.execute(
            select(AdminDetails).where(func.lower(AdminDetails.email) == normalize_email(data.email))
        )
        admin = result.scalar_one_or_none()

        # Same single answer and same work as the donor flow (no account enumeration).
        otp_ok = await verify_otp(session, data.email, data.otp, PURPOSE_ADMIN_RESET)
        if admin is None or not otp_ok:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OTP")
        # Hash new password
        admin.password = await hash_password_async(data.new_password)
        await revoke_all_for_user(session, admin.id, "admin")
        
        logger.info(f"Password reset for admin: {admin.id}")
        
        return MessageResponse(message="Password reset successful. Please login")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming admin password reset: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )
