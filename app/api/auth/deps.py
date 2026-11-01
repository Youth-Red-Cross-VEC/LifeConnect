"""
Authentication Dependencies for Protected Routes

FastAPI dependencies that validate JWT tokens and provide current user/donor/admin
to protected endpoints. These are used as Depends() in route definitions.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging

from app.core.database import get_db
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails
from app.api.auth.utils import decode_token

logger = logging.getLogger(__name__)

# ============================================================
# OAuth2 CONFIGURATION
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

# ============================================================
# MAIN AUTHENTICATION DEPENDENCIES
# ============================================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db, scope="function")
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    
    This dependency validates the JWT token and extracts user information.
    
    Args:
        token: JWT token from Authorization header
        session: Database session
        
    Returns:
        dict: {
            "user_id": str (e.g., "DON-abc12345"),
            "user_type": "donor" | "admin",
            "email": str
        }
        
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
        
    Example in route:
        @router.get("/me")
        async def get_profile(current_user: dict = Depends(get_current_user)):
            return {"user_id": current_user["user_id"]}
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if payload is None:
        logger.warning("Invalid or expired token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type is "access"
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    user_id = payload.get("sub")
    user_type = payload.get("user_type")
    email = payload.get("email")
    
    if not all([user_id, user_type, email]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Re-check account state on every request so deactivated/deleted accounts
    # lose access immediately instead of when the token expires.
    if user_type == "donor":
        account = await session.get(DonorDetail, user_id)
        is_active = bool(account and account.active_status)
    elif user_type == "admin":
        account = await session.get(AdminDetails, user_id)
        is_active = bool(account and str(account.active_status).lower() == "active")
    else:
        is_active = False

    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": user_id,
        "user_type": user_type,
        "email": account.email,
    }


async def get_current_donor(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db, scope="function")
) -> DonorDetail:
    """
    Get current authenticated donor.
    
    Validates token, verifies user is a donor, and fetches full donor object.
    Use this on endpoints that should only be accessible by donors.
    
    Args:
        token: JWT token from Authorization header
        session: Database session
        
    Returns:
        DonorDetail: Full donor object from database
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not a donor
        HTTPException: 404 if donor not found in database
        
    Example in route:
        @router.get("/donations")
        async def get_my_donations(
            current_donor: DonorDetail = Depends(get_current_donor)
        ):
            return {"donor_id": current_donor.id}
    """
    user = await get_current_user(token, session)
    
    if user.get("user_type") != "donor":
        logger.warning(f"Non-donor {user['user_id']} tried donor endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only donors can access this resource",
        )
    
    donor = await session.get(DonorDetail, user["user_id"])
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donor not found",
        )
    
    return donor


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db, scope="function")
) -> AdminDetails:
    """
    Get current authenticated admin.
    
    Validates token, verifies user is an admin, and fetches full admin object.
    Use this on endpoints that should only be accessible by admins.
    
    Args:
        token: JWT token from Authorization header
        session: Database session
        
    Returns:
        AdminDetails: Full admin object from database
        
    Raises:
        HTTPException: 401 if not authenticated
        HTTPException: 403 if user is not an admin
        HTTPException: 404 if admin not found in database
        
    Example in route:
        @router.get("/statistics")
        async def get_stats(
            current_admin: AdminDetails = Depends(get_current_admin)
        ):
            return {"admin": current_admin.name}
    """
    user = await get_current_user(token, session)
    
    if user.get("user_type") != "admin":
        logger.warning(f"Non-admin {user['user_id']} tried admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this resource",
        )
    
    admin = await session.get(AdminDetails, user["user_id"])
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found",
        )
    
    return admin


async def get_current_donor_or_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db, scope="function"),
) -> Dict[str, Any]:
    """
    Get current authenticated user — either a donor OR an admin.

    Use on endpoints that should be accessible by:
    - Admins (any donor's record)
    - Donors (only their own record — caller must additionally verify donor_id matches)

    Returns:
        dict: {"user_id": str, "user_type": "donor"|"admin", "email": str}

    Raises:
        HTTPException: 401 if not authenticated
    """
    return await get_current_user(token, session)


async def get_optional_donor_id(
    request: Request,
    session: AsyncSession = Depends(get_db, scope="function"),
) -> Optional[str]:
    """The signed-in donor's id, or None for anonymous callers.

    For public endpoints that behave differently when a donor is signed in. A missing, expired or
    otherwise unusable token is treated as anonymous instead of rejected, so a stale token in the
    browser can never block a public form.

    Reads the Authorization header directly rather than using the OAuth2 scheme dependency: that would
    mark the route as secured in the OpenAPI document, but the route stays public.
    """
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    token = token.strip()
    try:
        user = await get_current_user(token, session)
    except HTTPException:
        return None
    return user["user_id"] if user["user_type"] == "donor" else None
