"""
Authentication Dependencies - PARTNER'S DOMAIN

This file contains placeholder implementations that need to be replaced
with actual JWT authentication logic.

See AUTH_README.md for detailed implementation instructions.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from app.models.donor import DonorDetail
from app.models.admin import AdminDetails

# OAuth2 scheme for extracting token from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ============================================================
# TODO: PARTNER - Implement these authentication dependencies
# ============================================================


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Get current authenticated user from JWT token.
    
    TODO: Implement JWT token validation and return user info.
    
    Returns:
        dict: {"user_id": str, "user_type": "donor" | "admin", "email": str}
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    # PLACEHOLDER - Replace with actual JWT validation
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Decode JWT token and extract user info
    # from jose import JWTError, jwt
    # payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # user_id = payload.get("sub")
    # user_type = payload.get("type")

    # Placeholder return - REMOVE THIS
    return {
        "user_id": "placeholder",
        "user_type": "admin",
        "email": "placeholder@example.com",
    }


async def get_current_donor(token: str = Depends(oauth2_scheme)) -> DonorDetail:
    """
    Get current authenticated donor.
    
    TODO: Validate token and verify user is a donor.
    
    Returns:
        DonorDetail: The authenticated donor object
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not a donor
    """
    user = await get_current_user(token)

    if user.get("user_type") != "donor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only donors can access this resource",
        )

    # TODO: Fetch donor from database using user_id
    # from app.core.database import get_db
    # async for session in get_db():
    #     donor = await session.get(DonorDetail, user["user_id"])
    #     if not donor:
    #         raise HTTPException(status_code=404, detail="Donor not found")
    #     return donor

    # Placeholder - REMOVE THIS
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented",
    )


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> AdminDetails:
    """
    Get current authenticated admin.
    
    TODO: Validate token and verify user is an admin.
    
    Returns:
        AdminDetails: The authenticated admin object
        
    Raises:
        HTTPException: 401 if not authenticated, 403 if not an admin
    """
    user = await get_current_user(token)

    if user.get("user_type") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this resource",
        )

    # TODO: Fetch admin from database using user_id
    # from app.core.database import get_db
    # async for session in get_db():
    #     admin = await session.get(AdminDetails, user["user_id"])
    #     if not admin:
    #         raise HTTPException(status_code=404, detail="Admin not found")
    #     return admin

    # Placeholder - REMOVE THIS
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented",
    )


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.
    
    Use this for endpoints that work for both authenticated and anonymous users.
    """
    if token is None:
        return None

    try:
        return await get_current_user(token)
    except HTTPException:
        return None
