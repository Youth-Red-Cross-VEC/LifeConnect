"""Password rules shared by every schema that accepts a password.

bcrypt only looks at the first 72 BYTES of its input. Older releases silently ignore the rest, newer ones
raise, so a limit counted in characters is wrong: 25 four-byte emoji are 100 bytes. Every password field
therefore checks the UTF-8 byte length.
"""

PASSWORD_MAX_BYTES = 72


def check_password_length(value: str) -> str:
    """Reject anything bcrypt cannot hash faithfully (used on login, where only the length matters)."""
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError(
            f"Password must be at most {PASSWORD_MAX_BYTES} bytes (UTF-8); "
            "characters outside plain ASCII count as several bytes"
        )
    return value


def check_new_password(value: str) -> str:
    """The policy for choosing a password: registration and password reset."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isupper() for c in value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit")
    return check_password_length(value)
