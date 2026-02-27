"""
Demo Mode Guards

Provides FastAPI dependencies to enforce read-only behavior in demo mode.
When ENV=demo, all write operations are blocked with 403 Forbidden.
"""

from fastapi import HTTPException, status
from app.core.config import settings, Environment

import logging

logger = logging.getLogger("airs.demo_guard")


class DemoModeError(HTTPException):
    """Exception raised when a write operation is attempted in demo mode."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo environment is read-only. Write operations are disabled."
        )


def require_writable():
    """
    FastAPI dependency that blocks write operations in demo mode.
    
    Usage:
        @router.post("/resource")
        async def create_resource(
            ...,
            _: None = Depends(require_writable)
        ):
            ...
    """
    if settings.ENV == Environment.DEMO:
        logger.warning("Blocked write operation in demo mode")
        raise DemoModeError()


def is_demo_mode() -> bool:
    """Check if the application is running in demo mode."""
    return settings.ENV == Environment.DEMO


def get_environment_info() -> dict:
    """
    Get environment information for frontend consumption.
    
    Returns:
        dict with environment name and read-only status
    """
    return {
        "environment": settings.ENV.value,
        "is_demo": is_demo_mode(),
        "is_read_only": is_demo_mode(),
        "app_name": settings.APP_NAME,
    }
