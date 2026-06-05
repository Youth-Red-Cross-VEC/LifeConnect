# Authentication & Authorization Module - PARTNER'S DOMAIN
#
# This module is the responsibility of the partner handling JWT authentication.
# See AUTH_README.md for detailed instructions.

from app.api.auth.deps import (
    get_current_user,
    get_current_donor,
    get_current_admin
)
from app.api.auth.router import router

__all__ = [
    "router",
    "get_current_user",
    "get_current_donor",
    "get_current_admin"
]
