"""
API v1 versioned routes.

Currently exposes:
  GET /api/v1/methodology — transparent scoring methodology
"""

from fastapi import APIRouter
from app.api.v1 import methodology

router = APIRouter()
router.include_router(methodology.router, tags=["methodology"])
