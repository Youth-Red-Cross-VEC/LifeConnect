"""
Password Hashing Utilities.

Uses bcrypt for secure password hashing.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash string (includes salt and cost factor)
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash (cost factor 12 = good security/performance balance)
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash from database
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        # Handle case where hash format is invalid
        return False


def needs_rehash(hashed_password: str) -> bool:
    """
    Check if a password hash needs to be upgraded.
    
    Returns True if the hash uses old parameters.
    Modern bcrypt hashes start with $2b$ and use rounds >= 12.
    """
    if not hashed_password.startswith('$2'):
        return True
    # Check if rounds are less than 12
    try:
        parts = hashed_password.split('$')
        if len(parts) >= 3:
            rounds = int(parts[2])
            return rounds < 12
    except (ValueError, IndexError):
        pass
    return False
