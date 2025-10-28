"""
API routes package
"""
from fastapi import APIRouter
from .provinces import router as province_router
from .districts import router as district_router
from .constituencies import router as constituency_router
from .wards import router as ward_router
from .members import router as member_router
from .roles import router as role_router
from .permissions import router as permission_router
from .user_roles import router as user_role_router
from .events import router as event_router
from .referrals import router as referral_router

# Create main API router
api_router = APIRouter()

# Include location routers
api_router.include_router(province_router, prefix="/provinces", tags=["provinces"])
api_router.include_router(district_router, prefix="/districts", tags=["districts"])
api_router.include_router(constituency_router, prefix="/constituencies", tags=["constituencies"])
api_router.include_router(ward_router, prefix="/wards", tags=["wards"])

# Include member router
api_router.include_router(member_router, prefix="/members", tags=["members"])

# Include RBAC routers
api_router.include_router(role_router, tags=["roles"])
api_router.include_router(permission_router, tags=["permissions"])
api_router.include_router(user_role_router, tags=["user-roles"])

# Include event router
api_router.include_router(event_router, tags=["events"])

# Include referral router
api_router.include_router(referral_router, tags=["referrals"])

__all__ = ["api_router"]
