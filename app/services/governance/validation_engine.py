"""
Internal Governance Validation Framework (IGVF) — Validation Engine.

Comprehensive governance validation for an organization:
  - Compliance framework applicability (re-uses compliance_engine)
  - Audit readiness score: 100 − (Critical×15) − (High×8) − (Medium×3), floor 0
  - SLA tier gap detection (re-uses uptime analysis logic)
  - Tech stack lifecycle risk aggregation
  - Governance Health Index (GHI): composite weighted score

Formula:
  GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1)

All outputs are deterministic — no LLM usage.
This module is intended for staging-only internal assurance.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.finding import Finding, Severity
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.compliance_engine import get_applicable_frameworks
from app.services.governance.lifecycle_engine import get_version_status

logger = logging.getLogger("airs.igvf")

# ── Audit readiness severity weights ────────────────────────────────
SEVERITY_WEIGHTS: Dict[str, int] = {
    "critical": 15,
    "high": 8,
    "medium": 3,
    "low": 0,
}

# ── SLA tier targets ────────────────────────────────────────────────
TIER_SLAS: Dict[str, float] = {
    "Tier 1": 99.99,
    "Tier 2": 99.9,
    "Tier 3": 99.5,
    "Tier 4": 99.0,
}

TIER_NORMALIZE: Dict[str, str] = {
    "tier_1": "Tier 1",
    "tier_2": "Tier 2",
    "tier_3": "Tier 3",
    "tier_4": "Tier 4",
}

# ── GHI dimension weights ──────────────────────────────────────────
GHI_WEIGHTS = {
    "audit": 0.4,
    "lifecycle": 0.3,
    "sla": 0.2,
    "compliance": 0.1,
}


# ── Result data classes ─────────────────────────────────────────────

@dataclass
class ComplianceResult:
    """Compliance framework applicability result."""
    total_frameworks: int = 0
    mandatory_count: int = 0
    recommended_count: int = 0
    frameworks: List[Dict] = field(default_factory=list)
    score: float = 0.0  # 0–100 normalized

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AuditReadinessResult:
    """Audit readiness score based on open findings."""
    score: float = 100.0  # 0–100, starts at 100
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    total_open: int = 0
    deductions: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SLAResult:
    """SLA tier gap analysis result."""
    application_tier: str = "Not configured"
    tier_sla: Optional[float] = None
    sla_target: Optional[float] = None
    gap_pct: Optional[float] = None
    status: str = "not_configured"
    score: float = 0.0  # 0–100 normalized

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LifecycleResult:
    """Tech stack lifecycle risk result."""
    total_components: int = 0
    eol_count: int = 0
    deprecated_count: int = 0
    outdated_count: int = 0  # 2+ major versions behind
    healthy_count: int = 0
    risk_breakdown: Dict[str, int] = field(default_factory=dict)
    score: float = 100.0  # 0–100 normalized

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GovernanceHealthIndex:
    """Composite Governance Health Index."""
    ghi: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
    weights: Dict[str, float] = field(default_factory=lambda: dict(GHI_WEIGHTS))
    grade: str = "F"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationResult:
    """Complete IGVF validation result for an organization."""
    organization_id: str = ""
    organization_name: str = ""
    compliance: ComplianceResult = field(default_factory=ComplianceResult)
    audit_readiness: AuditReadinessResult = field(default_factory=AuditReadinessResult)
    sla: SLAResult = field(default_factory=SLAResult)
    lifecycle: LifecycleResult = field(default_factory=LifecycleResult)
    governance_health_index: GovernanceHealthIndex = field(
        default_factory=GovernanceHealthIndex
    )
    passed: bool = False
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


# ── Engine functions ────────────────────────────────────────────────

def compute_audit_readiness(findings: List[Finding]) -> AuditReadinessResult:
    """
    Compute audit readiness score from open findings.

    Formula: score = max(0, 100 − (Critical×15) − (High×8) − (Medium×3))
    Only open/in_progress findings count.
    """
    result = AuditReadinessResult()

    for f in findings:
        if f.status in ("resolved", "accepted"):
            continue
        result.total_open += 1
        severity = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
        if severity == "critical":
            result.critical_count += 1
        elif severity == "high":
            result.high_count += 1
        elif severity == "medium":
            result.medium_count += 1
        elif severity == "low":
            result.low_count += 1

    crit_deduction = result.critical_count * SEVERITY_WEIGHTS["critical"]
    high_deduction = result.high_count * SEVERITY_WEIGHTS["high"]
    med_deduction = result.medium_count * SEVERITY_WEIGHTS["medium"]

    result.deductions = {
        "critical": crit_deduction,
        "high": high_deduction,
        "medium": med_deduction,
    }

    result.score = max(0.0, 100.0 - crit_deduction - high_deduction - med_deduction)
    return result


def compute_compliance(org: Organization) -> ComplianceResult:
    """
    Compute compliance applicability and derive a normalized score.

    Score logic:
      - If no frameworks apply → 100 (nothing required)
      - If frameworks exist → ratio of mandatory coverage
        100 × (1 - mandatory_uncovered / total_mandatory) → for now,
        having any mandatory framework = aware, score = 100.
        In future, compare against registered frameworks.
    """
    frameworks = get_applicable_frameworks(org)
    result = ComplianceResult()
    result.total_frameworks = len(frameworks)
    result.mandatory_count = sum(1 for f in frameworks if f.mandatory)
    result.recommended_count = sum(1 for f in frameworks if not f.mandatory)
    result.frameworks = [
        {
            "framework": f.framework,
            "reason": f.reason,
            "mandatory": f.mandatory,
        }
        for f in frameworks
    ]

    # Score: compliance awareness. Having identified frameworks = awareness.
    # Deduction only if profile is empty (no attributes set → score is lower).
    if result.total_frameworks > 0:
        result.score = 100.0
    else:
        # No frameworks triggered — check if profile is configured at all
        has_profile = any([
            org.processes_pii, org.processes_phi,
            org.processes_cardholder_data, org.handles_dod_data,
            org.uses_ai_in_production, org.government_contractor,
            org.financial_services,
        ])
        result.score = 50.0 if has_profile else 0.0

    return result


def compute_sla_gap(org: Organization) -> SLAResult:
    """
    Compute SLA tier gap analysis.

    Score:
      - on_track/over_provisioned → 100
      - at_risk (gap ≤ 0.5%) → 60
      - unrealistic (gap > 0.5%) → 20
      - not_configured → 0
    """
    result = SLAResult()

    raw_tier = org.application_tier or "Not configured"
    tier = TIER_NORMALIZE.get(raw_tier, raw_tier)
    result.application_tier = tier
    result.sla_target = org.sla_target

    tier_sla = TIER_SLAS.get(tier)
    result.tier_sla = tier_sla

    if not tier_sla or result.sla_target is None:
        result.status = "not_configured"
        result.score = 0.0
        return result

    gap = tier_sla - result.sla_target
    result.gap_pct = round(gap, 4)

    if gap <= 0:
        result.status = "on_track"
        result.score = 100.0
    elif gap <= 0.5:
        result.status = "at_risk"
        result.score = 60.0
    else:
        result.status = "unrealistic"
        result.score = 20.0

    return result


def compute_lifecycle(tech_items: List[TechStackItem]) -> LifecycleResult:
    """
    Compute lifecycle risk from tech stack items.

    Score: 100 − (eol_count × 25) − (deprecated × 15) − (outdated × 5), floor 0.
    Outdated = 2+ major versions behind.
    """
    result = LifecycleResult()
    result.total_components = len(tech_items)

    risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for item in tech_items:
        status = item.lts_status
        status_val = status.value if hasattr(status, "value") else str(status)
        versions_behind = item.major_versions_behind or 0

        if status_val == "eol":
            result.eol_count += 1
            risk_counts["critical"] += 1
        elif status_val == "deprecated":
            result.deprecated_count += 1
            risk_counts["high"] += 1
        elif versions_behind >= 2:
            result.outdated_count += 1
            risk_counts["medium"] += 1
        else:
            result.healthy_count += 1
            risk_counts["low"] += 1

    result.risk_breakdown = risk_counts

    deduction = (
        result.eol_count * 25
        + result.deprecated_count * 15
        + result.outdated_count * 5
    )
    result.score = max(0.0, 100.0 - deduction)

    return result


def compute_ghi(
    audit_score: float,
    lifecycle_score: float,
    sla_score: float,
    compliance_score: float,
) -> GovernanceHealthIndex:
    """
    Compute the Governance Health Index.

    GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1)

    Grade:
      90+ → A
      80+ → B
      60+ → C
      40+ → D
      <40 → F
    """
    ghi_value = (
        audit_score * GHI_WEIGHTS["audit"]
        + lifecycle_score * GHI_WEIGHTS["lifecycle"]
        + sla_score * GHI_WEIGHTS["sla"]
        + compliance_score * GHI_WEIGHTS["compliance"]
    )
    ghi_value = round(ghi_value, 2)

    if ghi_value >= 90:
        grade = "A"
    elif ghi_value >= 80:
        grade = "B"
    elif ghi_value >= 60:
        grade = "C"
    elif ghi_value >= 40:
        grade = "D"
    else:
        grade = "F"

    return GovernanceHealthIndex(
        ghi=ghi_value,
        dimensions={
            "audit": round(audit_score, 2),
            "lifecycle": round(lifecycle_score, 2),
            "sla": round(sla_score, 2),
            "compliance": round(compliance_score, 2),
        },
        weights=dict(GHI_WEIGHTS),
        grade=grade,
    )


def validate_organization(
    db: Session,
    org: Organization,
) -> ValidationResult:
    """
    Run the full IGVF validation for an organization.

    Aggregates:
      1. Compliance framework applicability
      2. Audit readiness score (from open findings)
      3. SLA tier gap analysis
      4. Tech stack lifecycle risk
      5. Governance Health Index (GHI)

    Returns a ValidationResult with all dimensions and pass/fail status.
    """
    result = ValidationResult()
    result.organization_id = org.id
    result.organization_name = org.name

    # 1. Compliance
    result.compliance = compute_compliance(org)

    # 2. Audit readiness — gather all open findings across assessments
    all_findings: List[Finding] = []
    for assessment in org.assessments:
        all_findings.extend(assessment.findings)
    result.audit_readiness = compute_audit_readiness(all_findings)

    # 3. SLA gap
    result.sla = compute_sla_gap(org)

    # 4. Lifecycle risk
    result.lifecycle = compute_lifecycle(list(org.tech_stack_items))

    # 5. GHI
    result.governance_health_index = compute_ghi(
        audit_score=result.audit_readiness.score,
        lifecycle_score=result.lifecycle.score,
        sla_score=result.sla.score,
        compliance_score=result.compliance.score,
    )

    # Determine pass/fail and collect issues
    issues: List[str] = []

    if result.audit_readiness.score < 50:
        issues.append(
            f"Audit readiness critically low ({result.audit_readiness.score:.0f}/100): "
            f"{result.audit_readiness.critical_count} critical, "
            f"{result.audit_readiness.high_count} high findings open"
        )

    if result.lifecycle.eol_count > 0:
        issues.append(
            f"{result.lifecycle.eol_count} component(s) at end-of-life — "
            "immediate upgrade required"
        )

    if result.sla.status == "unrealistic":
        issues.append(
            f"SLA gap of {result.sla.gap_pct:.2f}% — "
            f"target ({result.sla.sla_target}%) far below "
            f"{result.sla.application_tier} requirement ({result.sla.tier_sla}%)"
        )

    if result.compliance.total_frameworks == 0 and result.compliance.score == 0:
        issues.append("No governance profile configured — compliance unknown")

    result.issues = issues
    result.passed = len(issues) == 0 and result.governance_health_index.ghi >= 60

    # Structured log for audit trail
    logger.info(
        "igvf_validation org_id=%s ghi=%.2f grade=%s passed=%s issues=%d "
        "audit=%.0f lifecycle=%.0f sla=%.0f compliance=%.0f",
        org.id,
        result.governance_health_index.ghi,
        result.governance_health_index.grade,
        result.passed,
        len(issues),
        result.audit_readiness.score,
        result.lifecycle.score,
        result.sla.score,
        result.compliance.score,
    )

    return result
