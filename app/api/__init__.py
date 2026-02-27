from fastapi import APIRouter
from app.api import (
    scoring,
    organizations,
    assessments,
    narratives,
    reports,
    integrations,
    external,
    pilot,
    governance,
    audit_calendar,
    tech_stack,
    pilot_program,
    auditor_view,
    drift,
)
from app.api.v1 import router as v1_router

router = APIRouter()

# Include routes
router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
router.include_router(organizations.router, prefix="/orgs", tags=["organizations"])
router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
router.include_router(narratives.router, prefix="/narratives", tags=["narratives"])
router.include_router(reports.router, prefix="/reports", tags=["reports"])
router.include_router(integrations.router, tags=["integrations"])
router.include_router(external.router, tags=["external"])
router.include_router(pilot.router, tags=["pilot"])
# v1 versioned routes (e.g. /api/v1/methodology)
router.include_router(v1_router, prefix="/v1", tags=["v1"])

# Governance expansion modules
router.include_router(governance.router, prefix="/governance", tags=["governance"])
router.include_router(audit_calendar.router, prefix="/governance", tags=["audit-calendar"])
router.include_router(tech_stack.router, prefix="/governance", tags=["tech-stack"])
router.include_router(pilot_program.router, prefix="/governance", tags=["pilot-program"])
router.include_router(auditor_view.router, prefix="/governance", tags=["auditor-view"])

# Compliance Drift & Shadow AI — staging only
router.include_router(drift.router, prefix="/governance", tags=["drift"])
