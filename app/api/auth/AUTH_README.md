# Authentication & Authorization Implementation Guide

## Overview

This document provides complete instructions for implementing JWT-based authentication
for the LifeConnect API. The authentication module is located in `app/api/auth/`.

## Files to Implement

| File | Purpose |
|------|---------|
| `app/api/auth/deps.py` | Authentication dependencies for protected routes |
| `app/api/auth/router.py` | Login, logout, and password reset endpoints |
| `app/api/auth/utils.py` | JWT token utilities (create this file) |

---

## Required Dependencies

Add these to `requirements.txt`:

```
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

Install:
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

---

## Implementation Steps

### Step 1: Create JWT Utilities (`app/api/auth/utils.py`)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

---

### Step 2: Update Auth Dependencies (`app/api/auth/deps.py`)

Replace the placeholder implementations:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models.donor import DonorDetail  
from app.models.admin import AdminDetails
from app.api.auth.utils import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login", 
    auto_error=False
)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> dict:
    """Get current authenticated user from JWT token."""
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    
    return {
        "user_id": payload.get("sub"),
        "user_type": payload.get("user_type"),
        "email": payload.get("email"),
    }

async def get_current_donor(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> DonorDetail:
    """Get current authenticated donor."""
    user = await get_current_user(token, session)
    
    if user.get("user_type") != "donor":
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
    session: AsyncSession = Depends(get_db)
) -> AdminDetails:
    """Get current authenticated admin."""
    user = await get_current_user(token, session)
    
    if user.get("user_type") != "admin":
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
```

---

### Step 3: Implement Login Routes (`app/api/auth/router.py`)

Replace donor_login:

```python
@router.post("/donor/login", response_model=TokenResponse)
async def donor_login(
    credentials: LoginRequest,
    session: AsyncSession = Depends(get_db),
):
    """Donor login endpoint."""
    from app.repositories.donor import DonorRepository
    from app.api.auth.utils import verify_password, create_access_token, create_refresh_token
    from datetime import datetime, timedelta
    from app.config import get_settings
    
    settings = get_settings()
    repo = DonorRepository(session)
    
    # Get donor by email
    donor = await repo.get_by_email(credentials.email)
    if not donor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Verify password
    if not verify_password(credentials.password, donor.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Update last login
    await repo.update_last_login(donor.id)
    
    # Log authentication
    await repo.log_authentication(
        auth_id=donor.authentication_id,
        name=donor.name,
        login_date=datetime.now().date(),
        login_time=datetime.now().time(),
    )
    
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
        username=donor.name,
    )
```

---

### Step 4: Enable Auth in Routes

After implementing auth, uncomment the auth dependencies in route files:

```python
# In app/api/v1/blood_requests.py, change:
# current_admin = Depends(get_current_admin),  # TODO: Auth

# To:
from app.api.auth.deps import get_current_admin
current_admin: AdminDetails = Depends(get_current_admin),
```

---

### Step 5: Update Router Include

In `app/api/v1/router.py`, uncomment:

```python
from app.api.auth.router import router as auth_router
router.include_router(auth_router)
```

---

## Token Structure

### Access Token Payload
```json
{
  "sub": "DON-abc12345",
  "user_type": "donor",
  "email": "donor@example.com",
  "exp": 1705123456,
  "type": "access"
}
```

### Refresh Token Payload
```json
{
  "sub": "DON-abc12345",
  "user_type": "donor", 
  "email": "donor@example.com",
  "exp": 1707715456,
  "type": "refresh"
}
```

---

## Environment Variables

Ensure these are set in `.env`:

```
SECRET_KEY=your-super-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30
```

---

## Testing Authentication

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/donor/login \
  -H "Content-Type: application/json" \
  -d '{"email": "donor@example.com", "password": "password123"}'
```

### Access Protected Route
```bash
curl http://localhost:8000/api/v1/donors/me \
  -H "Authorization: Bearer <access_token>"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

---

## Security Considerations

1. **Password Hashing**: Always use bcrypt, never store plain passwords
2. **Token Expiry**: Keep access tokens short-lived (24h), refresh tokens longer (30d)
3. **HTTPS**: Always use HTTPS in production
4. **Rate Limiting**: Add rate limiting to login endpoints
5. **Token Blacklist**: Consider implementing token blacklist for logout

---

## Questions?

Contact the main backend developer for any clarifications about:
- Database models and repositories
- Service layer integrations
- API response formats
