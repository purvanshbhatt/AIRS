"""
API v1 versioned routes.

Exposes:
  GET  /api/v1/config              — environment configuration (public)
  GET  /api/v1/methodology         — transparent scoring methodology
  POST /api/v1/pilot-leads         — enterprise pilot programme intake form
  POST /api/v1/integrations/siem/event    — legacy SIEM webhook ingestion
  POST /api/v1/telemetry/webhook/event    — canonical governance webhook (Module 2)
"""

from fastapi import APIRouter
from app.api.v1 import methodology, pilot_leads, integrations, telemetry, frameworks, config, governance_webhook

router = APIRouter()
router.include_router(config.router, tags=["config"])
router.include_router(methodology.router, tags=["methodology"])
router.include_router(pilot_leads.router, tags=["pilot"])
router.include_router(integrations.router, tags=["integrations"])
router.include_router(telemetry.router, tags=["telemetry"])
router.include_router(frameworks.router, tags=["frameworks"])
router.include_router(governance_webhook.router, tags=["governance"])
