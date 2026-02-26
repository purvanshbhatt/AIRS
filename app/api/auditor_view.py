"""
Auditor View API – read-only access endpoints for external auditors.

Authenticated users generate shareable links; auditors access read-only
GHI, compliance, and evidence data via token — no login required.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.models.organization import Organization
from app.services.auditor_view import (
    create_auditor_link,
    validate_token,
    revoke_token,
    list_active_tokens,
)
from app.services.governance.validation_engine import validate_organization

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Authenticated endpoints (link management) ───────────────────────

@router.post(
    "/orgs/{org_id}/auditor-link",
    summary="Generate Auditor Link",
    description=(
        "Generate a time-limited read-only link for external auditors "
        "(e.g., Big-4 firms) to view GHI and compliance posture."
    ),
)
async def generate_auditor_link(
    org_id: str,
    ttl_hours: int = Query(72, ge=1, le=720, description="Link validity in hours (max 30 days)"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """POST /api/governance/orgs/{org_id}/auditor-link"""
    from app.services.organization import OrganizationService

    service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    result = create_auditor_link(
        org_id=org.id,
        org_name=org.name,
        created_by=user.uid,
        ttl_hours=ttl_hours,
    )
    return result


@router.get(
    "/orgs/{org_id}/auditor-links",
    summary="List Active Auditor Links",
    description="List all active (non-expired, non-revoked) auditor links for an organization.",
)
async def get_auditor_links(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/orgs/{org_id}/auditor-links"""
    from app.services.organization import OrganizationService

    service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = service.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    links = list_active_tokens(org_id)
    return {"org_id": org_id, "active_links": links, "count": len(links)}


@router.delete(
    "/orgs/{org_id}/auditor-link",
    summary="Revoke Auditor Link",
    description="Revoke an auditor access token.",
)
async def revoke_auditor_link(
    org_id: str,
    token: str = Query(..., description="The auditor token to revoke"),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """DELETE /api/governance/orgs/{org_id}/auditor-link"""
    revoked = revoke_token(token)
    if not revoked:
        raise HTTPException(status_code=404, detail="Token not found or already revoked")
    return {"status": "revoked"}


# ── Public auditor endpoint (token-validated, no auth) ───────────────

@router.get(
    "/auditor-view",
    summary="Auditor Read-Only View",
    description=(
        "Public endpoint — validates the auditor token and returns a "
        "read-only snapshot of the organization's governance posture, "
        "GHI score, compliance frameworks, and evidence status."
    ),
)
async def auditor_view(
    token: str = Query(..., description="Auditor access token"),
    db: Session = Depends(get_db),
):
    """GET /api/governance/auditor-view?token=..."""
    meta = validate_token(token)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid, expired, or revoked auditor token.",
        )

    org_id = meta["org_id"]

    # Fetch org without tenant isolation (auditor doesn't have UID)
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization no longer exists")

    # GHI & validation
    validation = validate_organization(db, org)

    # Compliance frameworks
    from app.services.governance.compliance_engine import get_applicable_frameworks
    frameworks = get_applicable_frameworks(org)

    # Parse geo regions
    geo_regions = []
    if org.geo_regions:
        try:
            geo_regions = json.loads(org.geo_regions)
        except (json.JSONDecodeError, TypeError):
            geo_regions = []

    return {
        "org_name": meta["org_name"],
        "org_id": org_id,
        "access_expires": meta["expires_at"],
        "access_count": meta["access_count"],
        "governance_profile": {
            "revenue_band": org.revenue_band,
            "employee_count": org.employee_count,
            "geo_regions": geo_regions,
            "processes_pii": bool(org.processes_pii),
            "processes_phi": bool(org.processes_phi),
            "processes_cardholder_data": bool(org.processes_cardholder_data),
            "handles_dod_data": bool(org.handles_dod_data),
            "uses_ai_in_production": bool(org.uses_ai_in_production),
            "application_tier": org.application_tier,
            "sla_target": org.sla_target,
        },
        "health_index": {
            "ghi": validation.governance_health_index.ghi,
            "grade": validation.governance_health_index.grade,
            "dimensions": validation.governance_health_index.dimensions,
            "weights": validation.governance_health_index.weights,
        },
        "audit_readiness": validation.audit_readiness.to_dict(),
        "lifecycle": validation.lifecycle.to_dict(),
        "sla": validation.sla.to_dict(),
        "compliance": validation.compliance.to_dict(),
        "applicable_frameworks": [
            {"framework": f.framework, "reason": f.reason, "priority": f.priority}
            for f in frameworks
        ],
        "passed": validation.passed,
        "issues": validation.issues,
        "read_only": True,
    }
