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
)

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
