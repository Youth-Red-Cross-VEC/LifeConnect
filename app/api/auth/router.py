"""
Authentication Router - Complete Implementation

Login, logout, and password reset endpoints for donors and admins.
"""
import random
import time
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.rate_limiter import limiter
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails
from app.services.email_service import get_email_service
from app.api.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.api.auth.deps import get_current_donor, get_current_admin

logger = logging.getLogger(__name__)

# OTP store with expiry: {email: {"otp": "123456", "expires_at": timestamp}}
otp_store: dict[str, dict[str, object]] = {}


def store_otp(email: str, otp: str):
    """Store OTP with 10 minute expiry."""
    otp_store[email] = {
        "otp": otp,
        "expires_at": time.time() + 600  # 10 minutes
    }


def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP and check expiry."""
    record = otp_store.get(email)
    if not record:
        return False
    if time.time() > float(record["expires_at"]):  # type: ignore[arg-type]
        del otp_store[email]  # Clean up expired OTP
        return False
    if record["otp"] != otp:
        return False
    del otp_store[email]  # Clean up after successful verify
    return True

# ============================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================

class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    
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
    try:
        # Get donor by email
        result = await session.execute(
            select(DonorDetail).where(DonorDetail.email == credentials.email)
        )
        donor = result.scalar_one_or_none()
        
        # Check if donor exists
        if not donor:
            logger.warning(f"Login attempt with non-existent email: {credentials.email}")
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
        refresh_token = create_refresh_token(token_data)
        
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
    try:
        # Get admin by email
        result = await session.execute(
            select(AdminDetails).where(AdminDetails.email == credentials.email)
        )
        admin = result.scalar_one_or_none()
        
        # Check if admin exists
        if not admin:
            logger.warning(f"Admin login attempt with non-existent email: {credentials.email}")
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
        refresh_token = create_refresh_token(token_data)
        
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
        
        # Create new tokens
        token_data = {
            "sub": user.id,
            "user_type": user_type,
            "email": user.email,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
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
            logger.info(f"Password reset for non-existent email: {data.email}")
            # Don't reveal if email exists (security best practice)
            return MessageResponse(
                message="If this email exists, you will receive a reset link"
            )
         
        # TODO: Generate OTP and send email
        # otp = generate_otp()
        # await send_password_reset_email(donor.email, otp)
        # Store OTP in database with expiry
        otp = str(random.randint(100000, 999999))
        store_otp(donor.email, otp)
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

        if not verify_otp(data.email, data.otp):
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
            logger.info(f"Admin password reset for non-existent email: {data.email}")
        else:
            otp = str(random.randint(100000, 999999))
            store_otp(admin.email, otp)
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
        if not verify_otp(data.email, data.otp):
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