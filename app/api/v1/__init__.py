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
from app.api.v1 import methodology, pilot_leads, integrations, telemetry, frameworks, config, governance_webhook, connectors, telemetry_events, mobile, inventory, continuous_scoring, simulations, policies, metrics, telemetry_roi, intelligence, control_verification, readiness, technology, decisions, reports, evidence

router = APIRouter()
router.include_router(config.router, tags=["config"])
router.include_router(methodology.router, tags=["methodology"])
router.include_router(pilot_leads.router, tags=["pilot"])
router.include_router(integrations.router, tags=["integrations"])
router.include_router(telemetry.router, tags=["telemetry"])
router.include_router(frameworks.router, tags=["frameworks"])
router.include_router(governance_webhook.router, tags=["governance"])
router.include_router(connectors.router, tags=["connectors"])
router.include_router(telemetry_events.router, tags=["telemetry-events"])
router.include_router(mobile.router, tags=["mobile"])
router.include_router(inventory.router, tags=["inventory"])
router.include_router(continuous_scoring.router, tags=["continuous-scoring"])
router.include_router(simulations.router, tags=["simulations"])
router.include_router(policies.router, tags=["policies"])
router.include_router(metrics.router, tags=["observability"])
router.include_router(telemetry_roi.router, tags=["telemetry-roi"])
router.include_router(reports.router, tags=["reports"])
router.include_router(intelligence.router, tags=["intelligence"])
router.include_router(control_verification.router, prefix="/verification", tags=["control-verification"])
router.include_router(readiness.router, tags=["readiness"])
router.include_router(technology.router, tags=["technology"])
router.include_router(decisions.router, tags=["decisions"])
router.include_router(evidence.router, tags=["evidence"])
