"""
Reliability Risk Index (RRI) — Deterministic Scoring Engine.

Converts:
  - Application Tier
  - SLA Target
  - RTO / RPO (from assessment answers)
  - Backup & Failover Controls
  - Monitoring Maturity
  - Incident Response Readiness

into a Reliability Exposure Score (0–100).

Formula:
  RRI = (SLA Commitment Risk × 0.25)
      + (Recovery Capability   × 0.25)
      + (Redundancy & HA       × 0.20)
      + (Monitoring & Detection × 0.15)
      + (BCDR Validation       × 0.15)

  then × Tier Risk Multiplier:
    Tier 0: ×1.30   Tier 1: ×1.15   Tier 2: ×1.00   Tier 3: ×0.85

All outputs are deterministic — no LLM usage.
"""

import json
import logging
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from functools import lru_cache
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.tech_stack import TechStackItem
from app.models.finding import Finding, Severity

logger = logging.getLogger("airs.rri")


# ── Constants ────────────────────────────────────────────────────────

TIER_RISK_MULTIPLIERS: Dict[str, float] = {
    "tier_0": 1.30,
    "Tier 0": 1.30,
    "tier_1": 1.15,
    "Tier 1": 1.15,
    "tier_2": 1.00,
    "Tier 2": 1.00,
    "tier_3": 0.85,
    "Tier 3": 0.85,
    "tier_4": 0.85,
    "Tier 4": 0.85,
}

TIER_NORMALIZE: Dict[str, str] = {
    "tier_0": "Tier 0",
    "tier_1": "Tier 1",
    "tier_2": "Tier 2",
    "tier_3": "Tier 3",
    "tier_4": "Tier 4",
}

# Downtime budget: minutes per year for a given SLA %
MINUTES_PER_YEAR = 525_960  # 365.25 * 24 * 60

# Industry SLA recommendations based on industry + stage
INDUSTRY_SLA_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "fintech": {"tier": "Tier 1", "sla_range": [99.95, 99.99], "rationale": "Financial services require near-zero downtime for regulatory compliance and customer trust."},
    "finance": {"tier": "Tier 1", "sla_range": [99.95, 99.99], "rationale": "Financial services require near-zero downtime for regulatory compliance and customer trust."},
    "healthtech": {"tier": "Tier 0", "sla_range": [99.99, 99.999], "rationale": "Patient safety and HIPAA mandate highest availability for clinical systems."},
    "healthcare": {"tier": "Tier 0", "sla_range": [99.99, 99.999], "rationale": "Patient safety and HIPAA mandate highest availability for clinical systems."},
    "technology": {"tier": "Tier 1", "sla_range": [99.9, 99.99], "rationale": "SaaS platforms need high availability for customer retention and SLA commitments."},
    "saas": {"tier": "Tier 1", "sla_range": [99.9, 99.99], "rationale": "SaaS platforms need high availability for customer retention and SLA commitments."},
    "e-commerce": {"tier": "Tier 1", "sla_range": [99.9, 99.99], "rationale": "Downtime directly correlates with revenue loss; peak traffic demands resilience."},
    "manufacturing": {"tier": "Tier 2", "sla_range": [99.5, 99.9], "rationale": "Operational technology benefits from reliability but allows maintenance windows."},
    "education": {"tier": "Tier 3", "sla_range": [99.0, 99.5], "rationale": "Academic cycles allow planned maintenance; critical during exam periods."},
    "government": {"tier": "Tier 1", "sla_range": [99.9, 99.99], "rationale": "Public-facing services require high availability per FedRAMP/FISMA requirements."},
    "media": {"tier": "Tier 2", "sla_range": [99.5, 99.9], "rationale": "Streaming and content delivery need reliability but tolerate brief interruptions."},
    "default": {"tier": "Tier 2", "sla_range": [99.5, 99.9], "rationale": "Standard industry baseline for business-critical applications."},
}

# RRI dimension weights
RRI_WEIGHTS = {
    "sla_commitment": 0.25,
    "recovery_capability": 0.25,
    "redundancy_ha": 0.20,
    "monitoring_detection": 0.15,
    "bcdr_validation": 0.15,
}

# Reliability Confidence Score (RCS) weights — separate axis from RRI
RCS_WEIGHTS = {
    "dr_test_recency": 0.20,
    "backup_validation": 0.20,
    "ir_tabletop_recency": 0.20,
    "monitoring_coverage": 0.20,
    "architecture_redundancy": 0.20,
}

# Breach exposure badge mapping (SLA vs recovery capability)
BREACH_EXPOSURE_BADGES = {
    "within_budget": {"badge": "\U0001f7e2 Within Downtime Budget", "severity": "green"},
    "sla_strain": {"badge": "\U0001f7e1 SLA Strain Likely", "severity": "yellow"},
    "breach_high": {"badge": "\U0001f534 Breach Exposure High", "severity": "red"},
    "contractual_risk": {"badge": "\u26AB Contractual Risk Critical", "severity": "black"},
}


# ── Data Classes ─────────────────────────────────────────────────────

@dataclass
class DowntimeBudget:
    """Calculated downtime budget from SLA target."""
    sla_target: float
    annual_minutes: float
    monthly_minutes: float
    annual_display: str
    monthly_display: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RRIDimension:
    """Single RRI dimension score."""
    name: str
    key: str
    score: float  # 0–100
    weight: float
    weighted_score: float
    signals: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SLAAdvisorRecommendation:
    """Smart SLA Advisor output."""
    recommended_tier: str
    sla_range: List[float]
    rationale: str
    industry: str
    confidence: str  # "high", "medium", "low"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BreachExposureBadge:
    """4-level executive breach exposure classification."""
    level: str        # within_budget, sla_strain, breach_high, contractual_risk
    badge: str        # Emoji + label
    severity: str     # green, yellow, red, black
    explanation: str  # Why this level

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AdvisoryItem:
    """Deterministic architectural misalignment advisory."""
    severity: str       # critical, high, medium, info
    title: str
    detail: str
    remediation: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReliabilityConfidenceScore:
    """Reliability Confidence Score (RCS) — measures confidence in resilience posture.

    Separate from RRI: RRI = Exposure, RCS = Confidence.
    Together they form a two-axis resilience matrix.
    """
    total_score: float        # 0–100 (higher = more confident)
    dr_test_recency: float    # 0–20
    backup_validation: float  # 0–20
    ir_tabletop_recency: float  # 0–20
    monitoring_coverage: float  # 0–20
    architecture_redundancy: float  # 0–20
    confidence_band: str      # Verified, Moderate, Low, Unvalidated
    sub_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AutoRecommendation:
    """Auto-detected recommendation when SLA/Tier is missing."""
    recommended_tier: str
    recommended_sla: float
    source: str  # "industry", "profile", "default"
    rationale: str
    accept_action: str  # description of what Accept does

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RRISnapshot:
    """Point-in-time RRI snapshot for trend tracking."""
    org_id: str
    timestamp: str
    rri_score: float
    rcs_score: float
    risk_band: str
    confidence_band: str
    dimensions: Dict[str, float]  # key→score

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BreachSimulation:
    """Board Simulation Mode result."""
    current_sla: float
    simulated_sla: float
    current_budget: DowntimeBudget
    simulated_budget: DowntimeBudget
    required_improvements: List[str]
    control_gaps: List[str]
    readiness_delta: float  # Change in RRI score
    cost_impact: str  # textual proxy

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ReliabilityRiskResult:
    """Full RRI calculation result."""
    rri_score: float  # 0–100 (higher = more exposure / risk)
    risk_band: str  # "Low", "Moderate", "High", "Critical"
    breach_probability: str  # "Negligible", "Low", "Moderate", "High"
    application_tier: str
    tier_multiplier: float
    raw_score: float  # Before tier multiplier
    downtime_budget: Optional[DowntimeBudget]
    dimensions: List[RRIDimension]
    top_gaps: List[str]
    architecture_alignment: str  # "aligned", "partial", "high_risk"
    sla_advisor: Optional[SLAAdvisorRecommendation]
    # ── New fields (v2) ──────────────────────────────────────────────
    breach_exposure: Optional[BreachExposureBadge] = None
    advisories: List[AdvisoryItem] = field(default_factory=list)
    reliability_confidence: Optional[ReliabilityConfidenceScore] = None
    auto_recommendation: Optional[AutoRecommendation] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        return d


# ── Utility Functions ────────────────────────────────────────────────

def calculate_downtime_budget(sla_target: float) -> DowntimeBudget:
    """Calculate annual and monthly downtime budgets from SLA percentage."""
    if sla_target is None or sla_target <= 0 or sla_target >= 100:
        sla_target = 99.0  # safe default

    downtime_fraction = (100 - sla_target) / 100
    annual_minutes = MINUTES_PER_YEAR * downtime_fraction
    monthly_minutes = annual_minutes / 12

    return DowntimeBudget(
        sla_target=sla_target,
        annual_minutes=round(annual_minutes, 2),
        monthly_minutes=round(monthly_minutes, 2),
        annual_display=_format_minutes(annual_minutes),
        monthly_display=_format_minutes(monthly_minutes),
    )


def _format_minutes(minutes: float) -> str:
    """Format minutes into human-readable duration."""
    if minutes < 1:
        return f"{minutes * 60:.0f}s"
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    if hours < 24:
        remaining_min = minutes % 60
        return f"{int(hours)}h {int(remaining_min)}m"
    days = hours / 24
    remaining_hours = hours % 24
    return f"{int(days)}d {int(remaining_hours)}h"


@lru_cache(maxsize=64)
def _cached_sla_advisor(industry_key: str) -> Tuple[str, tuple, str, str]:
    """Cached industry SLA lookup (industry rarely changes)."""
    rec = INDUSTRY_SLA_RECOMMENDATIONS.get(industry_key, INDUSTRY_SLA_RECOMMENDATIONS["default"])
    confidence = "high" if industry_key in INDUSTRY_SLA_RECOMMENDATIONS else "medium"
    return rec["tier"], tuple(rec["sla_range"]), rec["rationale"], confidence


def get_sla_advisor(industry: Optional[str]) -> SLAAdvisorRecommendation:
    """Smart SLA Advisor: recommend tier and SLA range based on industry (cached)."""
    key = (industry or "").strip().lower()
    tier, sla_range, rationale, confidence = _cached_sla_advisor(key)

    return SLAAdvisorRecommendation(
        recommended_tier=tier,
        sla_range=list(sla_range),
        rationale=rationale,
        industry=industry or "Unknown",
        confidence=confidence,
    )


def _get_risk_band(score: float) -> str:
    """Map RRI score to risk band."""
    if score <= 25:
        return "Low"
    elif score <= 50:
        return "Moderate"
    elif score <= 75:
        return "High"
    else:
        return "Critical"


def _get_breach_probability(score: float) -> str:
    """Map RRI score to estimated breach probability."""
    if score <= 20:
        return "Negligible"
    elif score <= 40:
        return "Low"
    elif score <= 65:
        return "Moderate"
    else:
        return "High"


def _get_architecture_alignment(dimensions: List[RRIDimension]) -> str:
    """Determine architecture alignment from dimension scores."""
    avg = sum(d.score for d in dimensions) / max(len(dimensions), 1)
    # Lower score = better (less risk exposure)
    if avg <= 30:
        return "aligned"
    elif avg <= 60:
        return "partial"
    else:
        return "high_risk"


# ── Breach Exposure Heat Badge ───────────────────────────────────────

def _calculate_breach_exposure(
    sla_target: Optional[float],
    recovery_score: float,
    sla_commitment_score: float,
) -> BreachExposureBadge:
    """
    Calculate 4-level executive breach exposure badge.

    Derived from declared SLA vs current recovery capability:
      🟢 Within Downtime Budget — recovery matches SLA commitment
      🟡 SLA Strain Likely     — gaps but manageable
      🔴 Breach Exposure High  — significant mismatch
      ⚫ Contractual Risk Critical — SLA is contractually dangerous
    """
    if sla_target is None:
        return BreachExposureBadge(
            level="sla_strain",
            badge=BREACH_EXPOSURE_BADGES["sla_strain"]["badge"],
            severity="yellow",
            explanation="SLA target not configured — unable to quantify exposure",
        )

    # Combined exposure signal: average of SLA commitment risk + recovery gap
    exposure = (sla_commitment_score + recovery_score) / 2

    if exposure <= 25:
        return BreachExposureBadge(
            level="within_budget",
            badge=BREACH_EXPOSURE_BADGES["within_budget"]["badge"],
            severity="green",
            explanation=f"Recovery capability aligns with {sla_target}% SLA commitment",
        )
    elif exposure <= 50:
        return BreachExposureBadge(
            level="sla_strain",
            badge=BREACH_EXPOSURE_BADGES["sla_strain"]["badge"],
            severity="yellow",
            explanation=f"Recovery gaps may strain {sla_target}% SLA during incidents",
        )
    elif exposure <= 75:
        return BreachExposureBadge(
            level="breach_high",
            badge=BREACH_EXPOSURE_BADGES["breach_high"]["badge"],
            severity="red",
            explanation=f"Significant mismatch between {sla_target}% SLA and recovery readiness",
        )
    else:
        return BreachExposureBadge(
            level="contractual_risk",
            badge=BREACH_EXPOSURE_BADGES["contractual_risk"]["badge"],
            severity="black",
            explanation=f"Current architecture cannot sustain {sla_target}% SLA — contractual breach likely",
        )


# ── Autonomous Advisory Layer ────────────────────────────────────────

def _detect_advisories(
    org: Organization,
    answers: Dict[str, Any],
    dimensions: List[RRIDimension],
    tech_items: List[Any],
) -> List[AdvisoryItem]:
    """
    Deterministic architectural misalignment detection.

    Triggers recommendations without LLM:
      IF condition THEN advisory with remediation.
    """
    advisories: List[AdvisoryItem] = []
    sla = org.sla_target
    tier = org.application_tier

    # Rule 1: High SLA + no automated failover
    has_failover = any(
        hasattr(t, 'category') and t.category and 'load balancer' in t.category.lower()
        for t in tech_items
    )
    if sla and sla >= 99.99 and not has_failover:
        advisories.append(AdvisoryItem(
            severity="critical",
            title="Architectural Misalignment Detected",
            detail=f"SLA target of {sla}% requires automated failover, but no load balancer or failover infrastructure is registered.",
            remediation="Deploy automated failover (ALB/NLB, multi-AZ) and register in tech stack.",
        ))

    # Rule 2: High SLA + low tier classification
    if sla and sla >= 99.9 and tier and tier in ("tier_3", "Tier 3", "tier_4", "Tier 4"):
        advisories.append(AdvisoryItem(
            severity="critical",
            title="Tier-SLA Conflict",
            detail=f"SLA of {sla}% conflicts with {tier} classification. Tier 3/4 cannot sustain this SLA target.",
            remediation="Reclassify to Tier 1 or Tier 0 and provision corresponding infrastructure.",
        ))

    # Rule 3: No DR plan + production SLA
    if sla and sla >= 99.0 and not answers.get("rs_04"):
        advisories.append(AdvisoryItem(
            severity="high",
            title="No Disaster Recovery Plan",
            detail="Production SLA commitment exists but no DR plan is documented.",
            remediation="Create and test a disaster recovery plan covering RTO/RPO objectives.",
        ))

    # Rule 4: No monitoring + meaningful SLA
    monitoring_dim = next((d for d in dimensions if d.key == "monitoring_detection"), None)
    if monitoring_dim and monitoring_dim.score >= 70:
        advisories.append(AdvisoryItem(
            severity="high",
            title="Monitoring Blind Spot",
            detail="Monitoring & detection maturity is insufficient — incidents may go undetected beyond SLA thresholds.",
            remediation="Deploy APM, infrastructure monitoring, and alerting (PagerDuty/OpsGenie).",
        ))

    # Rule 5: No IR readiness + high SLA
    ir_answers = {k: v for k, v in answers.items() if k.startswith("ir_")}
    ir_positive = sum(1 for v in ir_answers.values() if v is True) if ir_answers else 0
    if sla and sla >= 99.5 and ir_positive == 0:
        advisories.append(AdvisoryItem(
            severity="high",
            title="Incident Response Gaps",
            detail="No incident response controls validated despite high SLA commitment.",
            remediation="Implement IR runbooks, conduct tabletop exercises, define escalation paths.",
        ))

    # Rule 6: No backup procedures documented
    if not answers.get("rs_02") and sla and sla >= 99.0:
        advisories.append(AdvisoryItem(
            severity="medium",
            title="Backup Procedures Not Documented",
            detail="Backup procedures are undocumented — recovery outcomes are unpredictable.",
            remediation="Document backup procedures, validate restoration, define backup SLAs.",
        ))

    # Rule 7: RTO undefined
    rto = answers.get("rs_05")
    if rto is None and sla and sla >= 99.5:
        advisories.append(AdvisoryItem(
            severity="medium",
            title="RTO Not Defined",
            detail="Recovery Time Objective is not measured — unclear how quickly services can be restored.",
            remediation="Define and test RTO targets aligned with SLA commitment.",
        ))

    return advisories


# ── Reliability Confidence Score (RCS) ───────────────────────────────

def calculate_rcs(
    answers: Dict[str, Any],
    tech_items: List[Any],
    audit_entries: List[Any],
) -> ReliabilityConfidenceScore:
    """
    Calculate the Reliability Confidence Score (RCS).

    Separate from RRI:
      RRI = Exposure (how much risk you carry)
      RCS = Confidence (how validated is your resilience posture)

    Five sub-dimensions, each 0–20 points:
      - DR test recency
      - Backup validation frequency
      - IR tabletop recency
      - Monitoring coverage
      - Architecture redundancy

    Total: 0–100 (higher = more confident).
    """
    sub = {}

    # 1. DR Test Recency (0–20)
    dr_test = answers.get("rs_03")
    if dr_test is True:
        sub["dr_test_recency"] = 18.0
    elif dr_test is False:
        sub["dr_test_recency"] = 3.0
    else:
        sub["dr_test_recency"] = 0.0

    # 2. Backup Validation (0–20)
    backup_doc = answers.get("rs_02")
    backup_restore = answers.get("rs_06")
    backup_score = 0.0
    if backup_doc is True:
        backup_score += 10.0
    if backup_restore is True:
        backup_score += 10.0
    elif isinstance(backup_restore, (int, float)) and backup_restore > 0:
        backup_score += min(10.0, backup_restore / 10)
    sub["backup_validation"] = backup_score

    # 3. IR Tabletop Recency (0–20)
    ir_answers = {k: v for k, v in answers.items() if k.startswith("ir_")}
    ir_positive = sum(1 for v in ir_answers.values() if v is True)
    ir_total = max(len(ir_answers), 1)
    sub["ir_tabletop_recency"] = round(20.0 * (ir_positive / ir_total), 1)

    # 4. Monitoring Coverage (0–20)
    tl_answers = {k: v for k, v in answers.items() if k.startswith("tl_")}
    dc_answers = {k: v for k, v in answers.items() if k.startswith("dc_")}
    all_mon = {**tl_answers, **dc_answers}
    if all_mon:
        mon_positive = sum(1 for v in all_mon.values() if v is True or (isinstance(v, (int, float)) and v > 50))
        sub["monitoring_coverage"] = round(20.0 * (mon_positive / max(len(all_mon), 1)), 1)
    else:
        sub["monitoring_coverage"] = 0.0

    # 5. Architecture Redundancy (0–20)
    ha_categories = {"load balancer", "cdn", "cache", "database", "queue", "storage"}
    ha_tech = [t for t in tech_items if hasattr(t, 'category') and t.category and t.category.lower() in ha_categories]
    has_dr_plan = answers.get("rs_04") is True
    arch_score = min(12.0, len(ha_tech) * 3.0)  # Up to 12 from tech stack
    if has_dr_plan:
        arch_score += 8.0
    sub["architecture_redundancy"] = min(20.0, arch_score)

    total = sum(sub.values())

    # Confidence band
    if total >= 75:
        band = "Verified"
    elif total >= 50:
        band = "Moderate"
    elif total >= 25:
        band = "Low"
    else:
        band = "Unvalidated"

    return ReliabilityConfidenceScore(
        total_score=round(total, 1),
        dr_test_recency=sub["dr_test_recency"],
        backup_validation=sub["backup_validation"],
        ir_tabletop_recency=sub["ir_tabletop_recency"],
        monitoring_coverage=sub["monitoring_coverage"],
        architecture_redundancy=sub["architecture_redundancy"],
        confidence_band=band,
        sub_scores=sub,
    )


# ── Auto-Detection: Tier/SLA Defaults ────────────────────────────────

def _auto_recommend(org: Organization) -> Optional[AutoRecommendation]:
    """
    When SLA or Tier is missing, auto-detect recommended values
    instead of showing 'Not configured' dead-end.
    """
    sla_missing = org.sla_target is None
    tier_missing = org.application_tier is None or org.application_tier == ""

    if not sla_missing and not tier_missing:
        return None  # Nothing to recommend

    advisor = get_sla_advisor(org.industry)

    recommended_tier = org.application_tier or advisor.recommended_tier.lower().replace(" ", "_")
    recommended_sla = org.sla_target or advisor.sla_range[0]

    parts = []
    if tier_missing:
        parts.append(f"Application Tier → {advisor.recommended_tier}")
    if sla_missing:
        parts.append(f"SLA Target → {recommended_sla}%")

    return AutoRecommendation(
        recommended_tier=advisor.recommended_tier,
        recommended_sla=recommended_sla,
        source="industry" if advisor.confidence == "high" else "default",
        rationale=f"Based on {org.industry or 'general'} industry profile: {advisor.rationale}",
        accept_action=f"Set {', '.join(parts)} for {org.name}",
    )


# ── Audit Trail Logging ─────────────────────────────────────────────

def _log_rri_audit_event(db: Session, org_id: str, actor: str, rri_score: float, rcs_score: float):
    """Log RRI recalculation as an audit event."""
    try:
        from app.models.audit_event import AuditEvent
        event = AuditEvent(
            org_id=org_id,
            action=f"rri_calculated|score={rri_score:.1f}|rcs={rcs_score:.1f}",
            actor=actor,
        )
        db.add(event)
        db.commit()
    except Exception as e:
        logger.warning("Failed to log RRI audit event: %s", e)



# Each returns 0–100 where 0 = no risk exposure, 100 = maximum risk exposure

def _score_sla_commitment(
    sla_target: Optional[float],
    application_tier: Optional[str],
) -> RRIDimension:
    """
    SLA Commitment Risk: higher SLA targets with lower tiers = more risk.
    """
    signals = []
    gaps = []
    score = 50.0  # default moderate risk

    if sla_target is None:
        gaps.append("SLA target not configured — unable to quantify commitment risk")
        score = 70.0
    else:
        signals.append(f"SLA target: {sla_target}%")
        # Higher SLA = higher risk if not adequately provisioned
        if sla_target >= 99.99:
            score = 80.0  # Extremely high commitment
            gaps.append("99.99% SLA requires automated failover and zero-downtime deployments")
        elif sla_target >= 99.9:
            score = 55.0
        elif sla_target >= 99.5:
            score = 35.0
        elif sla_target >= 99.0:
            score = 20.0
        else:
            score = 10.0

    if application_tier:
        tier = TIER_NORMALIZE.get(application_tier, application_tier)
        signals.append(f"Application tier: {tier}")
        # Mismatch: high SLA but low tier = very risky
        if sla_target and sla_target >= 99.9 and tier in ("Tier 3", "Tier 4"):
            score = min(100, score + 25)
            gaps.append(f"SLA {sla_target}% conflicts with {tier} classification — architecture underprovisioned")
    else:
        gaps.append("Application tier not assigned")

    weight = RRI_WEIGHTS["sla_commitment"]
    return RRIDimension(
        name="SLA Commitment Risk",
        key="sla_commitment",
        score=round(score, 1),
        weight=weight,
        weighted_score=round(score * weight, 2),
        signals=signals,
        gaps=gaps,
    )


def _score_recovery_capability(
    answers: Dict[str, Any],
    tech_stack_count: int,
) -> RRIDimension:
    """
    Recovery Capability: RTO, RPO, backup controls from assessment answers.
    Questions: rs_05 (RTO), rs_01–rs_06 (recovery & resilience domain).
    """
    signals = []
    gaps = []
    score = 50.0  # default

    # RS domain questions
    rs_answers = {k: v for k, v in answers.items() if k.startswith("rs_")}

    if not rs_answers:
        gaps.append("No recovery/resilience assessment data available")
        score = 75.0
    else:
        answered_true = sum(1 for v in rs_answers.values() if v is True or (isinstance(v, str) and "yes" in str(v).lower()))
        total_rs = len(rs_answers)
        coverage = answered_true / max(total_rs, 1)
        signals.append(f"Recovery controls coverage: {answered_true}/{total_rs}")

        score = max(0, 100 - (coverage * 100))

        # RTO specifically
        rto = answers.get("rs_05")
        if rto is not None:
            if isinstance(rto, (int, float)) and rto > 0:
                signals.append(f"RTO: {rto}h")
                if rto <= 1:
                    score = max(0, score - 15)
                elif rto <= 4:
                    score = max(0, score - 10)
                elif rto > 24:
                    score = min(100, score + 15)
                    gaps.append(f"RTO of {rto}h exceeds 24h — significant recovery risk")
            elif isinstance(rto, str):
                rto_lower = rto.strip().lower()
                if "not" in rto_lower or "undefined" in rto_lower:
                    gaps.append("RTO undefined — recovery time unknown")
                    score = min(100, score + 20)
                else:
                    signals.append(f"RTO: {rto}")
        else:
            gaps.append("RTO not measured")
            score = min(100, score + 10)

    # Backup/failover signals from tech stack
    if tech_stack_count == 0:
        gaps.append("No infrastructure components registered in tech stack")

    weight = RRI_WEIGHTS["recovery_capability"]
    return RRIDimension(
        name="Recovery Capability",
        key="recovery_capability",
        score=round(score, 1),
        weight=weight,
        weighted_score=round(score * weight, 2),
        signals=signals,
        gaps=gaps,
    )


def _score_redundancy_ha(
    answers: Dict[str, Any],
    tech_items: List[Any],
) -> RRIDimension:
    """
    Redundancy & HA: failover controls, infrastructure diversity.
    """
    signals = []
    gaps = []
    score = 50.0

    # Check for HA-related answers
    # rs_02: "Are backup procedures documented?"
    # rs_04: "Is there a disaster recovery plan?"
    backup_doc = answers.get("rs_02")
    dr_plan = answers.get("rs_04")

    ha_signals = 0
    if backup_doc is True:
        ha_signals += 1
        signals.append("Backup procedures documented")
    else:
        gaps.append("Backup procedures not documented")

    if dr_plan is True:
        ha_signals += 1
        signals.append("Disaster recovery plan exists")
    else:
        gaps.append("No disaster recovery plan")

    # Check tech stack for redundancy indicators
    ha_categories = {"load balancer", "cdn", "cache", "database"}
    ha_tech = [t for t in tech_items if hasattr(t, 'category') and t.category and t.category.lower() in ha_categories]
    if ha_tech:
        ha_signals += min(len(ha_tech), 3)
        signals.append(f"{len(ha_tech)} HA-relevant infrastructure components")
    else:
        gaps.append("No redundancy infrastructure registered (load balancer, CDN, cache)")

    # Score calculation
    # More HA signals = lower risk
    coverage = ha_signals / 5  # normalize to 5 max signals
    score = max(0, 100 - (coverage * 100))

    weight = RRI_WEIGHTS["redundancy_ha"]
    return RRIDimension(
        name="Redundancy & High Availability",
        key="redundancy_ha",
        score=round(score, 1),
        weight=weight,
        weighted_score=round(score * weight, 2),
        signals=signals,
        gaps=gaps,
    )


def _score_monitoring_detection(
    answers: Dict[str, Any],
) -> RRIDimension:
    """
    Monitoring & Detection: EDR, logging, telemetry maturity.
    Questions: tl_01–tl_06 (telemetry/logging), dc_01–dc_06 (detection).
    """
    signals = []
    gaps = []
    score = 50.0

    # Telemetry & Logging questions
    tl_answers = {k: v for k, v in answers.items() if k.startswith("tl_")}
    dc_answers = {k: v for k, v in answers.items() if k.startswith("dc_")}

    all_monitoring = {**tl_answers, **dc_answers}

    if not all_monitoring:
        gaps.append("No monitoring/detection assessment data available")
        score = 80.0
    else:
        positive = sum(1 for v in all_monitoring.values() if v is True or (isinstance(v, (int, float)) and v > 50))
        total = len(all_monitoring)
        coverage = positive / max(total, 1)
        signals.append(f"Monitoring coverage: {positive}/{total} controls active")

        score = max(0, 100 - (coverage * 100))

        # EDR coverage specifically (dc_01)
        edr = answers.get("dc_01")
        if edr is not None:
            if isinstance(edr, (int, float)) and edr >= 80:
                signals.append(f"EDR coverage: {edr}%")
                score = max(0, score - 10)
            elif isinstance(edr, bool) and edr:
                signals.append("EDR deployed")
            elif isinstance(edr, str) and ("not" in edr.lower() or "unknown" in edr.lower()):
                gaps.append("EDR coverage undefined — detection blind spot")
                score = min(100, score + 15)
        else:
            gaps.append("EDR coverage not measured")

    weight = RRI_WEIGHTS["monitoring_detection"]
    return RRIDimension(
        name="Monitoring & Detection",
        key="monitoring_detection",
        score=round(score, 1),
        weight=weight,
        weighted_score=round(score * weight, 2),
        signals=signals,
        gaps=gaps,
    )


def _score_bcdr_validation(
    answers: Dict[str, Any],
    audit_entries: List[Any],
) -> RRIDimension:
    """
    BCDR Validation: DR testing frequency, tabletop exercises, backup validation.
    Questions: rs_03 (regular testing), ir_01–ir_06 (incident response).
    """
    signals = []
    gaps = []
    score = 50.0

    # IR questions
    ir_answers = {k: v for k, v in answers.items() if k.startswith("ir_")}
    ir_positive = sum(1 for v in ir_answers.values() if v is True) if ir_answers else 0
    ir_total = len(ir_answers)

    if ir_answers:
        signals.append(f"IR readiness: {ir_positive}/{ir_total} controls active")
        score = max(0, 100 - ((ir_positive / max(ir_total, 1)) * 80))
    else:
        gaps.append("No incident response assessment data")
        score = 70.0

    # Regular DR testing
    dr_test = answers.get("rs_03")
    if dr_test is True:
        signals.append("Regular DR testing confirmed")
        score = max(0, score - 10)
    else:
        gaps.append("DR testing not confirmed — BCDR readiness unvalidated")
        score = min(100, score + 10)

    # Audit calendar entries (more audits = better BCDR culture)
    if audit_entries:
        signals.append(f"{len(audit_entries)} audit calendar entries scheduled")
        score = max(0, score - min(len(audit_entries) * 3, 15))
    else:
        gaps.append("No audits scheduled — BCDR validation cadence undefined")

    weight = RRI_WEIGHTS["bcdr_validation"]
    return RRIDimension(
        name="BCDR Validation",
        key="bcdr_validation",
        score=round(score, 1),
        weight=weight,
        weighted_score=round(score * weight, 2),
        signals=signals,
        gaps=gaps,
    )


# ── Main Calculator ──────────────────────────────────────────────────

def calculate_rri(
    db: Session,
    org: Organization,
    answers: Optional[Dict[str, Any]] = None,
) -> ReliabilityRiskResult:
    """
    Calculate the full Reliability Risk Index for an organization.

    Gathers assessment answers, tech stack, and audit calendar data
    from the database, then scores each dimension deterministically.
    """
    if answers is None:
        answers = _gather_latest_answers(db, org.id)

    # Gather supporting data
    tech_items = db.query(TechStackItem).filter(
        TechStackItem.org_id == org.id
    ).all() if org.id else []

    audit_entries = []
    try:
        from app.models.audit_calendar import AuditCalendarEntry
        audit_entries = db.query(AuditCalendarEntry).filter(
            AuditCalendarEntry.org_id == org.id
        ).all()
    except Exception:
        pass

    # Calculate each dimension
    sla_dim = _score_sla_commitment(org.sla_target, org.application_tier)
    recovery_dim = _score_recovery_capability(answers, len(tech_items))
    redundancy_dim = _score_redundancy_ha(answers, tech_items)
    monitoring_dim = _score_monitoring_detection(answers)
    bcdr_dim = _score_bcdr_validation(answers, audit_entries)

    dimensions = [sla_dim, recovery_dim, redundancy_dim, monitoring_dim, bcdr_dim]

    # Raw weighted score
    raw_score = sum(d.weighted_score for d in dimensions)

    # Tier risk multiplier
    tier_key = org.application_tier or "tier_2"
    tier_multiplier = TIER_RISK_MULTIPLIERS.get(tier_key, 1.0)
    rri_score = min(100, round(raw_score * tier_multiplier, 1))

    # Downtime budget
    downtime_budget = None
    if org.sla_target:
        downtime_budget = calculate_downtime_budget(org.sla_target)

    # Collect top gaps (max 5)
    all_gaps = []
    for d in dimensions:
        for g in d.gaps:
            all_gaps.append(g)
    top_gaps = all_gaps[:5]

    # SLA advisor
    sla_advisor = get_sla_advisor(org.industry)

    # Tier display
    tier_display = TIER_NORMALIZE.get(tier_key, tier_key or "Not configured")

    # ── New v2 Subsystems ────────────────────────────────────────

    # Breach Exposure Heat Badge
    sla_dim = next((d for d in dimensions if d.key == "sla_commitment"), None)
    recovery_dim = next((d for d in dimensions if d.key == "recovery_capability"), None)
    breach_exposure = None
    if org.sla_target and sla_dim and recovery_dim:
        breach_exposure = _calculate_breach_exposure(
            org.sla_target, recovery_dim.score, sla_dim.score
        )

    # Autonomous Advisory Layer
    advisories = _detect_advisories(org, answers, dimensions, tech_items)

    # Reliability Confidence Score (RCS) — 2nd axis
    rcs = calculate_rcs(answers, tech_items, audit_entries)

    # Auto-recommendation: fill configuration dead-ends
    auto_recommendation = _auto_recommend(org)

    # Audit trail
    rcs_score = rcs.total_score if rcs else 0.0
    _log_rri_audit_event(db, org.id, "system", rri_score, rcs_score)

    return ReliabilityRiskResult(
        rri_score=rri_score,
        risk_band=_get_risk_band(rri_score),
        breach_probability=_get_breach_probability(rri_score),
        application_tier=tier_display,
        tier_multiplier=tier_multiplier,
        raw_score=round(raw_score, 1),
        downtime_budget=downtime_budget,
        dimensions=dimensions,
        top_gaps=top_gaps,
        architecture_alignment=_get_architecture_alignment(dimensions),
        sla_advisor=sla_advisor,
        breach_exposure=breach_exposure,
        advisories=advisories,
        reliability_confidence=rcs,
        auto_recommendation=auto_recommendation,
    )


def simulate_breach(
    db: Session,
    org: Organization,
    simulated_sla: float,
) -> BreachSimulation:
    """
    Board Simulation Mode: What if we upgraded SLA from X to Y?

    Shows required improvements, control gaps, and readiness delta.
    """
    # Current state
    current_result = calculate_rri(db, org)
    current_sla = org.sla_target or 99.0

    # Simulated state: temporarily override SLA
    original_sla = org.sla_target
    original_tier = org.application_tier
    org.sla_target = simulated_sla

    # Auto-suggest tier for simulated SLA
    if simulated_sla >= 99.99:
        org.application_tier = "tier_0"
    elif simulated_sla >= 99.9:
        org.application_tier = "tier_1"
    elif simulated_sla >= 99.5:
        org.application_tier = "tier_2"
    else:
        org.application_tier = "tier_3"

    simulated_result = calculate_rri(db, org)

    # Restore original values (don't persist)
    org.sla_target = original_sla
    org.application_tier = original_tier

    # Calculate deltas
    readiness_delta = round(simulated_result.rri_score - current_result.rri_score, 1)

    # Determine required improvements
    improvements = []
    gaps = []
    if simulated_sla >= 99.99 and current_sla < 99.99:
        improvements.append("Deploy automated failover across all critical services")
        improvements.append("Implement zero-downtime deployment pipeline")
        improvements.append("Add multi-region active-active architecture")
        gaps.append("Current architecture lacks automated failover")
    elif simulated_sla >= 99.9 and current_sla < 99.9:
        improvements.append("Implement automated health checks and self-healing")
        improvements.append("Add redundant database replicas with automatic promotion")
        gaps.append("Recovery automation needed for target SLA")
    elif simulated_sla >= 99.5 and current_sla < 99.5:
        improvements.append("Document and test disaster recovery procedures")
        improvements.append("Implement basic monitoring and alerting")
        gaps.append("DR procedures need formalization")

    # Generic gaps from simulated result
    for g in simulated_result.top_gaps:
        if g not in gaps:
            gaps.append(g)

    # Cost impact proxy
    if simulated_sla >= 99.99:
        cost_impact = "Significant infrastructure investment required (~3-5x current hosting cost)"
    elif simulated_sla >= 99.9:
        cost_impact = "Moderate infrastructure upgrade (~1.5-2x current hosting cost)"
    elif simulated_sla >= 99.5:
        cost_impact = "Minor additional investment for monitoring and redundancy"
    else:
        cost_impact = "Minimal additional cost — primarily process improvements"

    return BreachSimulation(
        current_sla=current_sla,
        simulated_sla=simulated_sla,
        current_budget=calculate_downtime_budget(current_sla),
        simulated_budget=calculate_downtime_budget(simulated_sla),
        required_improvements=improvements,
        control_gaps=gaps[:5],
        readiness_delta=readiness_delta,
        cost_impact=cost_impact,
    )


# ── Helpers ──────────────────────────────────────────────────────────

def _gather_latest_answers(db: Session, org_id: str) -> Dict[str, Any]:
    """Fetch the latest assessment answers for an organization."""
    try:
        from app.models.assessment import Assessment
        from app.models.answer import Answer

        latest = (
            db.query(Assessment)
            .filter(Assessment.organization_id == org_id)
            .order_by(Assessment.created_at.desc())
            .first()
        )
        if not latest:
            return {}

        answer_rows = (
            db.query(Answer)
            .filter(Answer.assessment_id == latest.id)
            .all()
        )
        return {a.question_id: a.answer_value for a in answer_rows}
    except Exception as e:
        logger.warning("Failed to gather answers for %s: %s", org_id, e)
        return {}
