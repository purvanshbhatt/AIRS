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
from app.db.firestore import firestore_save_org
from app.core.auth import require_auth, User
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationProfileUpdate,
    OrganizationProfileResponse,
    UptimeTierAnalysis,
)
from app.schemas.compliance import ComplianceApplicabilityResponse
from app.services.governance.compliance_engine import get_applicable_frameworks
from app.services.governance.validation_engine import validate_organization
from app.services.organization import OrganizationService
from app.services.governance_forecast import generate_governance_forecast

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Uptime tier SLA targets ──────────────────────────────────────────
TIER_SLAS = {
    "Tier 1": 99.99,
    "Tier 2": 99.9,
    "Tier 3": 99.5,
    "Tier 4": 99.0,
}

# Map normalized tier values (from schema validation) to display names
TIER_NORMALIZE = {
    "tier_1": "Tier 1",
    "tier_2": "Tier 2",
    "tier_3": "Tier 3",
    "tier_4": "Tier 4",
}

# Tiers requiring SOC 2 CC7 (System Operations) audit attention
SOC2_CC7_TIERS = {"Tier 1", "Tier 2"}


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

    # Dual-write to Firestore for persistence
    firestore_save_org(org)

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

    raw_tier = org.application_tier or "Not configured"
    sla_target = org.sla_target

    # Normalize tier format: "tier_1" → "Tier 1"
    tier = TIER_NORMALIZE.get(raw_tier, raw_tier)
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

    # SOC 2 CC7 applicability for Tier 1/2
    soc2_cc7_applicable = tier in SOC2_CC7_TIERS
    soc2_cc7_note = None
    if soc2_cc7_applicable:
        soc2_cc7_note = (
            f"{tier} classification triggers SOC 2 CC7 (System Operations) audit requirements. "
            f"Ensure incident response, monitoring, and recovery controls are documented."
        )

    # Over-provision detection: SLA target significantly exceeds tier requirement
    over_provisioned = False
    cost_warning = None
    if gap < -0.5:
        # Target exceeds tier SLA by more than 0.5% — likely over-provisioned
        over_provisioned = True
        cost_warning = (
            f"SLA target ({sla_target}%) exceeds {tier} requirement ({tier_sla}%) by "
            f"{abs(gap):.2f}%. Consider whether the additional infrastructure cost is justified, "
            f"or reclassify to a higher tier."
        )

    if gap <= 0:
        status_val = "over_provisioned" if over_provisioned else "on_track"
        if over_provisioned:
            message = (
                f"SLA target ({sla_target}%) exceeds {tier} requirement ({tier_sla}%). "
                f"Review tier classification or reduce over-provisioned infrastructure."
            )
        else:
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
        over_provisioned=over_provisioned,
        cost_warning=cost_warning,
        soc2_cc7_applicable=soc2_cc7_applicable,
        soc2_cc7_note=soc2_cc7_note,
    )


# ── Governance Health Index ──────────────────────────────────────────

@router.get(
    "/{org_id}/health-index",
    summary="Get Governance Health Index (GHI)",
    description=(
        "Returns the composite Governance Health Index for an organization. "
        "GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1). "
        "All calculations are deterministic — no LLM usage."
    ),
    tags=["governance"],
)
async def get_governance_health_index(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/health-index"""
    org = _get_org(db, user, org_id)
    result = validate_organization(db, org)

    return {
        "org_id": org.id,
        "ghi": result.governance_health_index.ghi,
        "grade": result.governance_health_index.grade,
        "dimensions": result.governance_health_index.dimensions,
        "weights": result.governance_health_index.weights,
        "audit_readiness": result.audit_readiness.to_dict(),
        "lifecycle": result.lifecycle.to_dict(),
        "sla": result.sla.to_dict(),
        "compliance": result.compliance.to_dict(),
        "passed": result.passed,
        "issues": result.issues,
    }


# ── Governance Forecast (Gemini) ─────────────────────────────────────

@router.get(
    "/{org_id}/forecast",
    summary="Get Governance Forecast",
    description=(
        "AI-powered forward-looking governance prediction. Uses Gemini to "
        "analyze the org's tech stack and profile, predicting SOC 2 CC7.1 "
        "readiness gaps. Falls back to deterministic analysis if LLM is unavailable."
    ),
    tags=["governance"],
)
async def get_governance_forecast(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """GET /api/governance/{org_id}/forecast"""
    org = _get_org(db, user, org_id)

    # Gather org data for the forecast
    geo_regions = []
    if org.geo_regions:
        try:
            geo_regions = json.loads(org.geo_regions)
        except (json.JSONDecodeError, TypeError):
            geo_regions = []

    # Gather tech stack items if available
    tech_stack = []
    try:
        from app.models.tech_stack import TechStackItem
        items = db.query(TechStackItem).filter(
            TechStackItem.org_id == org_id
        ).all()
        tech_stack = [
            {"name": item.name, "category": item.category, "version": item.version}
            for item in items
        ]
    except Exception:
        pass

    org_data = {
        "name": org.name,
        "revenue_band": org.revenue_band,
        "employee_count": org.employee_count,
        "application_tier": org.application_tier,
        "sla_target": org.sla_target,
        "processes_pii": bool(org.processes_pii),
        "processes_phi": bool(org.processes_phi),
        "processes_cardholder_data": bool(org.processes_cardholder_data),
        "uses_ai_in_production": bool(org.uses_ai_in_production),
        "government_contractor": bool(org.government_contractor),
        "geo_regions": geo_regions,
        "tech_stack": tech_stack,
    }

    result = await generate_governance_forecast(org_data)
    return {"org_id": org.id, **result}
