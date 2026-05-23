"""
API v1 versioned routes.

Exposes:
  GET  /api/v1/methodology     — transparent scoring methodology
  POST /api/v1/pilot-leads     — enterprise pilot programme intake form
  POST /api/v1/telemetry/events — SIEM webhook ingestion endpoint
"""

from fastapi import APIRouter
from app.api.v1 import methodology, pilot_leads, integrations, telemetry

router = APIRouter()
router.include_router(methodology.router, tags=["methodology"])
router.include_router(pilot_leads.router, tags=["pilot"])
router.include_router(integrations.router, tags=["integrations"])
router.include_router(telemetry.router, tags=["telemetry"])
