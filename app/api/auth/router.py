"""
Authentication Router - Complete Implementation

Login, logout, and password reset endpoints for donors and admins.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.config import get_settings
from app.core.rate_limiter import limiter
from app.core.recaptcha import verify_recaptcha
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails
from app.services.email_service import get_email_service
from app.services.refresh_session_service import issue_refresh_token, revoke_chain
from app.models.refresh_session import RefreshSession
from app.services.otp_service import (
    PURPOSE_ADMIN_RESET,
    PURPOSE_DONOR_RESET,
    generate_otp,
    store_otp,
    verify_otp,
)
from app.api.auth.utils import (
    hash_password,
    verify_password,
    needs_rehash,
    create_access_token,
    decode_token
)
from app.api.auth.deps import get_current_donor, get_current_admin

logger = logging.getLogger(__name__)

# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    recaptcha_token: Optional[str] = None
    
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
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""
    email: EmailStr
    otp: str
    new_password: str


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
@limiter.limit("5/minute")
async def donor_login(
    request: Request,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_db)
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
            select(DonorDetail).where(DonorDetail.email == credentials.email)
        )
        donor = result.scalar_one_or_none()
        
        # Check if donor exists
        if not donor:
            logger.warning("Login attempt with unknown email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not verify_password(credentials.password, donor.password):
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
            donor.password = hash_password(credentials.password)

        # Update last login — store full datetime
        donor.last_login_date = datetime.now()
        await session.commit()
        
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
        logger.error(f"Error during donor login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        )


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def admin_login(
    request: Request,
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_db)
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
            select(AdminDetails).where(AdminDetails.email == credentials.email)
        )
        admin = result.scalar_one_or_none()
        
        # Check if admin exists
        if not admin:
            logger.warning("Admin login attempt with unknown email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        
        # Verify password
        if not verify_password(credentials.password, admin.password):
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
            admin.password = hash_password(credentials.password)

        # Update last login — store full datetime
        admin.last_login_date = datetime.now()
        await session.commit()
        
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
        logger.error(f"Error during admin login: {str(e)}")
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
    session: AsyncSession = Depends(get_db)
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
            # A rotated-out token is being replayed: assume theft and kill the whole chain.
            await revoke_chain(session, old_session.jti)
            # Commit now: raising below rolls the request transaction back and would undo the revocation.
            await session.commit()
            logger.warning(f"Refresh token reuse detected for {old_session.role} {old_session.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )
        if old_session.expires_at < datetime.utcnow():
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
        
        access_token = create_access_token(token_data)
        refresh_token, new_jti = await issue_refresh_token(session, token_data)
        old_session.revoked_at = datetime.utcnow()
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
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh",
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    session: AsyncSession = Depends(get_db)
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
@limiter.limit("3/minute")
async def request_donor_password_reset(
    request: Request,
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_db)
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
            select(DonorDetail).where(DonorDetail.email == data.email)
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
        email_service = get_email_service()
        await email_service.send_otp_email(donor.email, otp, donor.name)
        
        logger.info(f"Password reset requested for donor: {donor.id}")
        
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {str(e)}")
        # Return generic message for security
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/donor/password-reset/confirm", response_model=MessageResponse)
async def confirm_donor_password_reset(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db)
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
            select(DonorDetail).where(DonorDetail.email == data.email)
        )
        donor = result.scalar_one_or_none()
        
        if not donor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Donor not found",
            )

        if not await verify_otp(session, data.email, data.otp, PURPOSE_DONOR_RESET):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired OTP",)
        # Hash new password
        donor.password = hash_password(data.new_password)
        await session.commit()
        
        logger.info(f"Password reset for donor: {donor.id}")
        
        return MessageResponse(message="Password reset successful. Please login")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )


@router.post("/admin/password-reset/request", response_model=MessageResponse)
@limiter.limit("3/minute")
async def request_admin_password_reset(
    request: Request,
    data: PasswordResetRequest,
    session: AsyncSession = Depends(get_db)
):
    """Request password reset for an admin."""
    try:
        result = await session.execute(
            select(AdminDetails).where(AdminDetails.email == data.email)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            logger.info("Admin password reset requested for unknown email")
        else:
            otp = generate_otp()
            await store_otp(session, admin.email, otp, PURPOSE_ADMIN_RESET)
            email_service = get_email_service()
            await email_service.send_otp_email(admin.email, otp, admin.username)
            logger.info(f"Admin password reset requested for: {admin.id}")

        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )
        
    except Exception as e:
        logger.error(f"Error requesting admin password reset: {str(e)}")
        return MessageResponse(
            message="If this email exists, you will receive a reset link"
        )


@router.post("/admin/password-reset/confirm", response_model=MessageResponse)
async def confirm_admin_password_reset(
    data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db)
):
    """Confirm password reset for admin."""
    try:
        result = await session.execute(
            select(AdminDetails).where(AdminDetails.email == data.email)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found",
            )
        
        # Verify OTP (simplified)
        if not await verify_otp(session, data.email, data.otp, PURPOSE_ADMIN_RESET):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired OTP",)
        # Hash new password
        admin.password = hash_password(data.new_password)
        await session.commit()
        
        logger.info(f"Password reset for admin: {admin.id}")
        
        return MessageResponse(message="Password reset successful. Please login")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming admin password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during password reset",
        )