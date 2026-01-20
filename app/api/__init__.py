from fastapi import APIRouter
from app.api import scoring, organizations, assessments, narratives

router = APIRouter()

# Include routes
router.include_router(scoring.router, prefix="/scoring", tags=["scoring"])
router.include_router(organizations.router, prefix="/orgs", tags=["organizations"])
router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
router.include_router(narratives.router, prefix="/narratives", tags=["narratives"])
