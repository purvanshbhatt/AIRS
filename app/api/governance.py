"""
Governance Profile & Compliance Applicability API routes.

Endpoints for managing organization governance profiles and
determining applicable compliance frameworks.
"""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.auth import require_auth, User
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationProfileUpdate,
    OrganizationProfileResponse,
    UptimeTierAnalysis,
)
from app.schemas.compliance import ComplianceApplicabilityResponse
from app.services.compliance_engine import get_applicable_frameworks
from app.services.organization import OrganizationService

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Uptime tier SLA targets ──────────────────────────────────────────
TIER_SLAS = {
    "Tier 1": 99.99,
    "Tier 2": 99.9,
    "Tier 3": 99.5,
    "Tier 4": 99.0,
}


def _get_org(db: Session, user: User, org_id: str) -> Organization:
    """Helper: resolve org with tenant isolation or 404."""
    service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization not found: {org_id}",
        )
    return org


# ── Governance Profile ───────────────────────────────────────────────

@router.get(
    "/{org_id}/profile",
    response_model=OrganizationProfileResponse,
    summary="Get Governance Profile",
    description="Returns the organization's governance/compliance profile attributes.",
)
async def get_profile(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/profile"""
    org = _get_org(db, user, org_id)

    geo_regions = []
    if org.geo_regions:
        try:
            geo_regions = json.loads(org.geo_regions)
        except (json.JSONDecodeError, TypeError):
            geo_regions = []

    return OrganizationProfileResponse(
        org_id=org.id,
        revenue_band=org.revenue_band,
        employee_count=org.employee_count,
        geo_regions=geo_regions,
        processes_pii=bool(org.processes_pii),
        processes_phi=bool(org.processes_phi),
        processes_cardholder_data=bool(org.processes_cardholder_data),
        handles_dod_data=bool(org.handles_dod_data),
        uses_ai_in_production=bool(org.uses_ai_in_production),
        government_contractor=bool(org.government_contractor),
        financial_services=bool(org.financial_services),
        application_tier=org.application_tier,
        sla_target=org.sla_target,
    )


@router.put(
    "/{org_id}/profile",
    response_model=OrganizationProfileResponse,
    summary="Update Governance Profile",
    description="Update the organization's governance/compliance profile attributes.",
)
async def update_profile(
    org_id: str,
    data: OrganizationProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """PUT /api/governance/{org_id}/profile"""
    org = _get_org(db, user, org_id)

    update_data = data.model_dump(exclude_unset=True)

    # Serialize geo_regions to JSON string
    if "geo_regions" in update_data and update_data["geo_regions"] is not None:
        update_data["geo_regions"] = json.dumps(update_data["geo_regions"])

    for key, value in update_data.items():
        setattr(org, key, value)

    db.commit()
    db.refresh(org)

    geo_regions = []
    if org.geo_regions:
        try:
            geo_regions = json.loads(org.geo_regions)
        except (json.JSONDecodeError, TypeError):
            geo_regions = []

    return OrganizationProfileResponse(
        org_id=org.id,
        revenue_band=org.revenue_band,
        employee_count=org.employee_count,
        geo_regions=geo_regions,
        processes_pii=bool(org.processes_pii),
        processes_phi=bool(org.processes_phi),
        processes_cardholder_data=bool(org.processes_cardholder_data),
        handles_dod_data=bool(org.handles_dod_data),
        uses_ai_in_production=bool(org.uses_ai_in_production),
        government_contractor=bool(org.government_contractor),
        financial_services=bool(org.financial_services),
        application_tier=org.application_tier,
        sla_target=org.sla_target,
    )


# ── Compliance Applicability ─────────────────────────────────────────

@router.get(
    "/{org_id}/applicable-frameworks",
    response_model=ComplianceApplicabilityResponse,
    summary="Get Applicable Frameworks",
    description=(
        "Deterministic rules engine that maps organization profile attributes "
        "to applicable compliance frameworks (HIPAA, SOC 2, PCI-DSS, etc.)."
    ),
)
async def applicable_frameworks(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/applicable-frameworks"""
    org = _get_org(db, user, org_id)
    frameworks = get_applicable_frameworks(org)
    return ComplianceApplicabilityResponse(
        org_id=org.id,
        frameworks=frameworks,
        total=len(frameworks),
    )


# ── Uptime Tier Analysis ────────────────────────────────────────────

@router.get(
    "/{org_id}/uptime-analysis",
    response_model=UptimeTierAnalysis,
    summary="Uptime Tier Gap Analysis",
    description=(
        "Compare the organization's stated SLA target against standard "
        "uptime tiers and identify gaps."
    ),
)
async def uptime_analysis(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/uptime-analysis"""
    org = _get_org(db, user, org_id)

    tier = org.application_tier or "Not configured"
    sla_target = org.sla_target
    tier_sla = TIER_SLAS.get(tier)

    if not tier_sla or sla_target is None:
        return UptimeTierAnalysis(
            application_tier=tier,
            tier_sla=tier_sla,
            sla_target=sla_target,
            gap_pct=None,
            status="not_configured",
            message="Application tier or SLA target not configured. Update your governance profile.",
        )

    gap = tier_sla - sla_target

    if gap <= 0:
        status_val = "on_track"
        message = f"SLA target ({sla_target}%) meets or exceeds {tier} requirement ({tier_sla}%)."
    elif gap <= 0.5:
        status_val = "at_risk"
        message = (
            f"SLA target ({sla_target}%) is {gap:.2f}% below {tier} requirement ({tier_sla}%). "
            f"Minor improvements needed."
        )
    else:
        status_val = "unrealistic"
        message = (
            f"SLA target ({sla_target}%) is {gap:.2f}% below {tier} requirement ({tier_sla}%). "
            f"Significant infrastructure changes required."
        )

    return UptimeTierAnalysis(
        application_tier=tier,
        tier_sla=tier_sla,
        sla_target=sla_target,
        gap_pct=round(gap, 4),
        status=status_val,
        message=message,
    )
