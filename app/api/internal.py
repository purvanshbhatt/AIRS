"""
Internal Governance Validation Framework (IGVF) — Internal Assurance Endpoint.

Route: GET /internal/governance/validate/{organization_id}

Safety:
  - Returns 404 if ENV != staging  (invisible in non-staging environments)
  - Protected by admin_token header (not Firebase auth)
"""

import logging
import os
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.config import settings, Environment
from app.db.database import get_db
from app.models.organization import Organization
from app.services.governance.validation_engine import validate_organization

router = APIRouter()
logger = logging.getLogger("airs.igvf.api")

# Admin token — read from environment, default for local dev
ADMIN_TOKEN = os.environ.get("IGVF_ADMIN_TOKEN", "igvf-staging-token")


def _require_staging():
    """Gate: return 404 if not running in staging environment."""
    if settings.ENV != Environment.STAGING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )


def _verify_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")):
    """Verify the admin token header."""
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token",
        )


@router.get(
    "/governance/validate/{organization_id}",
    summary="Run IGVF validation for an organization",
    tags=["internal"],
    dependencies=[Depends(_require_staging), Depends(_verify_admin_token)],
)
def run_igvf_validation(
    organization_id: str,
    db: Session = Depends(get_db),
):
    """
    Execute the full Internal Governance Validation Framework check
    for a single organization.

    Returns compliance, audit readiness, SLA gap, lifecycle risk,
    and the composite Governance Health Index (GHI).

    Only available when ENV=staging.
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {organization_id} not found",
        )

    result = validate_organization(db, org)

    logger.info(
        "igvf_api org_id=%s ghi=%.2f passed=%s",
        organization_id,
        result.governance_health_index.ghi,
        result.passed,
    )

    return result.to_dict()


@router.get(
    "/governance/validate",
    summary="List all organizations with GHI scores",
    tags=["internal"],
    dependencies=[Depends(_require_staging), Depends(_verify_admin_token)],
)
def run_igvf_validation_all(
    db: Session = Depends(get_db),
):
    """
    Run IGVF validation for ALL organizations and return summary.
    Only available when ENV=staging.
    """
    orgs = db.query(Organization).all()
    results = []
    for org in orgs:
        result = validate_organization(db, org)
        results.append({
            "organization_id": org.id,
            "organization_name": org.name,
            "ghi": result.governance_health_index.ghi,
            "grade": result.governance_health_index.grade,
            "passed": result.passed,
            "issues_count": len(result.issues),
        })

    return {
        "total_organizations": len(results),
        "results": results,
    }
