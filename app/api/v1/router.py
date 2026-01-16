"""
API v1 Router - Aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.donors import router as donors_router
from app.api.v1.blood_requests import router as blood_requests_router
from app.api.v1.hospitals import router as hospitals_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.admins import router as admins_router
from app.api.v1.queries import router as queries_router
from app.api.v1.certificates import router as certificates_router

# Import auth router when partner implements it
# from app.api.auth.router import router as auth_router

router = APIRouter(prefix="/api/v1")

# Include all routers
router.include_router(health_router)
router.include_router(donors_router)
router.include_router(blood_requests_router)
router.include_router(hospitals_router)
router.include_router(analytics_router)
router.include_router(admins_router)
router.include_router(queries_router)
router.include_router(certificates_router)

# Auth router (partner's domain)
# router.include_router(auth_router)

