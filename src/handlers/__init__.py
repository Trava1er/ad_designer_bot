"""
Handlers package for AdDesigner Hub Bot.
Modular structure for better organization.
"""

from aiogram import Router
from .common import router as common_router
from .user import router as user_router
from .admin import router as admin_router
from .payment import router as payment_router
from .navigation import router as navigation_router
from .webapp import router as webapp_router

# Create main router and include all sub-routers
# IMPORTANT: navigation_router should be last because it has catch-all handler
router = Router()
router.include_router(common_router)
router.include_router(user_router)
router.include_router(webapp_router)
router.include_router(payment_router)
router.include_router(admin_router)
router.include_router(navigation_router)  # LAST - has @router.message() catch-all

__all__ = ['router']
