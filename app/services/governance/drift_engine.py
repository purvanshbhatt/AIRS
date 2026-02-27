"""
Compliance Drift Detection Engine — Continuous Control Integrity Monitoring (CCIM).

Drift = measurable deviation from baseline compliance posture over time.

Drift types:
  - Control Regression:   control_score drops ≥ 1 tier
  - Risk Escalation:      risk_score increases ≥ 10%
  - SLA Breach:           remediation overdue
  - Evidence Expiry:      evidence_date < today
  - Tech Risk Drift:      dependency moves to deprecated/EOL
  - Audit Proximity Risk: < 30 days to audit & open high findings

Drift Impact Score (DIS):
  DIS = (control_regressions × 5)
      + (risk_escalations × 3)
      + (overdue_findings × 4)
      + (unsupported_tech × 6)
  Normalized to 0–100.

Severity bands:
   0–20 → Stable
  21–50 → Mild Drift
  51–75 → Elevated Risk
  76–100 → Critical Drift

Staging-only module — not deployed to production/demo.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding, Severity as FindingSeverity, FindingStatus
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.governance.validation_engine import (
    validate_organization,
    compute_ghi,
    compute_audit_readiness,
    compute_lifecycle,
    compute_compliance,
    compute_sla_gap,
)

logger = logging.getLogger("airs.drift_engine")


# ═══════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════

# DIS component weights
DIS_WEIGHTS = {
    "control_regressions": 5,
    "risk_escalations": 3,
    "overdue_findings": 4,
    "unsupported_tech": 6,
    "evidence_expired": 2,
    "audit_proximity": 3,
}

# DIS normalization cap (raw score that maps to DIS=100)
DIS_MAX_RAW = 50

# Severity bands
DRIFT_BANDS = [
    (0, 20, "Stable", "green"),
    (21, 50, "Mild Drift", "yellow"),
    (51, 75, "Elevated Risk", "orange"),
    (76, 100, "Critical Drift", "red"),
]

# Control score tier thresholds (0-5 scale)
CONTROL_REGRESSION_THRESHOLD = 1.0  # Drop of ≥ 1.0 = regression

# Risk escalation percentage threshold
RISK_ESCALATION_PCT = 10.0

# Audit proximity danger zone (days)
AUDIT_PROXIMITY_DAYS = 30

# Evidence expiry default window (days since last assessment)
EVIDENCE_EXPIRY_DAYS = 90


# ═══════════════════════════════════════════════════════════════════════
# Result Data Classes
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class DriftSignal:
    """A single detected drift signal."""
    signal_type: str  # control_regression | risk_escalation | sla_breach | evidence_expiry | tech_risk | audit_proximity
    severity: str     # critical | high | medium | low
    title: str
    description: str
    delta: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BaselineSnapshot:
    """Immutable baseline compliance posture snapshot."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    version: int = 1
    ghi: float = 0.0
    ghi_grade: str = "F"
    audit_readiness: float = 0.0
    lifecycle_score: float = 0.0
    sla_score: float = 0.0
    compliance_score: float = 0.0
    control_scores: Dict[str, float] = field(default_factory=dict)
    overall_score: Optional[float] = None
    risk_categories: Dict[str, int] = field(default_factory=dict)
    open_findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    eol_components: int = 0
    deprecated_components: int = 0
    total_tech_components: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DriftResult:
    """Complete drift analysis result."""
    organization_id: str = ""
    organization_name: str = ""
    baseline_id: Optional[str] = None
    baseline_date: Optional[str] = None
    current_ghi: float = 0.0
    baseline_ghi: float = 0.0
    ghi_delta: float = 0.0
    drift_impact_score: float = 0.0
    drift_band: str = "Stable"
    drift_band_color: str = "green"
    signals: List[Dict] = field(default_factory=list)
    signal_counts: Dict[str, int] = field(default_factory=dict)
    compliance_sustainability_index: Optional[float] = None
    audit_failure_probability: Optional[float] = None
    forecast_summary: Optional[str] = None
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DriftTimelineEntry:
    """A point on the drift timeline."""
    date: str
    ghi: float
    drift_score: float
    signals_count: int
    band: str
    band_color: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ═══════════════════════════════════════════════════════════════════════
# Firestore Persistence
# ═══════════════════════════════════════════════════════════════════════

def _get_firestore():
    """Get Firestore client. Returns None if unavailable."""
    try:
        from app.db.firestore import get_firestore_client, is_firestore_available
        if is_firestore_available():
            return get_firestore_client()
    except Exception:
        pass
    return None


def _save_baseline_to_firestore(baseline: BaselineSnapshot) -> bool:
    """Persist baseline snapshot to Firestore."""
    client = _get_firestore()
    if not client:
        logger.warning("Firestore unavailable — baseline not persisted")
        return False
    try:
        doc_ref = (
            client.collection("organizations")
            .document(baseline.organization_id)
            .collection("baselines")
            .document(baseline.id)
        )
        doc_ref.set(baseline.to_dict())
        logger.info("Baseline %s saved for org %s", baseline.id, baseline.organization_id)
        return True
    except Exception as exc:
        logger.error("Failed to save baseline: %s", exc)
        return False


def _get_latest_baseline(organization_id: str) -> Optional[BaselineSnapshot]:
    """Retrieve the most recent baseline for an organization."""
    client = _get_firestore()
    if not client:
        return None
    try:
        docs = (
            client.collection("organizations")
            .document(organization_id)
            .collection("baselines")
            .order_by("created_at", direction="DESCENDING")
            .limit(1)
            .stream()
        )
        for doc in docs:
            data = doc.to_dict()
            return BaselineSnapshot(**{
                k: v for k, v in data.items()
                if k in BaselineSnapshot.__dataclass_fields__
            })
    except Exception as exc:
        logger.error("Failed to fetch baseline for %s: %s", organization_id, exc)
    return None


def _get_baseline_history(organization_id: str, limit: int = 30) -> List[BaselineSnapshot]:
    """Retrieve baseline history for drift timeline."""
    client = _get_firestore()
    if not client:
        return []
    try:
        docs = (
            client.collection("organizations")
            .document(organization_id)
            .collection("baselines")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        results = []
        for doc in docs:
            data = doc.to_dict()
            results.append(BaselineSnapshot(**{
                k: v for k, v in data.items()
                if k in BaselineSnapshot.__dataclass_fields__
            }))
        return list(reversed(results))  # chronological order
    except Exception as exc:
        logger.error("Failed to fetch baseline history for %s: %s", organization_id, exc)
    return []


def _save_drift_result(result: DriftResult) -> bool:
    """Save drift analysis result for historical tracking."""
    client = _get_firestore()
    if not client:
        return False
    try:
        doc_ref = (
            client.collection("organizations")
            .document(result.organization_id)
            .collection("drift_analyses")
            .document()
        )
        doc_ref.set(result.to_dict())
        return True
    except Exception as exc:
        logger.error("Failed to save drift result: %s", exc)
        return False


# ═══════════════════════════════════════════════════════════════════════
# Core Engine Functions
# ═══════════════════════════════════════════════════════════════════════

def create_baseline(
    db: Session,
    organization_id: str,
) -> BaselineSnapshot:
    """
    Create an immutable baseline snapshot of the current compliance posture.

    Captures:
      - GHI score and grade
      - All dimension scores (audit, lifecycle, SLA, compliance)
      - Assessment overall score
      - Control scores per domain
      - Open findings counts by severity
      - Tech stack risk state

    Args:
        db: SQLAlchemy session
        organization_id: Organization to baseline

    Returns:
        BaselineSnapshot saved to Firestore
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise ValueError(f"Organization not found: {organization_id}")

    # Run full IGVF validation to get current state
    validation = validate_organization(db, org)

    # Get latest completed assessment score
    latest_assessment = (
        db.query(Assessment)
        .filter(
            Assessment.organization_id == organization_id,
            Assessment.status == AssessmentStatus.COMPLETED,
        )
        .order_by(Assessment.completed_at.desc())
        .first()
    )

    # Get domain-level control scores from the latest assessment
    control_scores: Dict[str, float] = {}
    overall_score: Optional[float] = None
    if latest_assessment:
        overall_score = latest_assessment.overall_score
        for score in latest_assessment.scores:
            control_scores[score.domain_id] = score.score

    # Count existing baselines for versioning
    existing = _get_baseline_history(organization_id, limit=1000)
    version = len(existing) + 1

    baseline = BaselineSnapshot(
        organization_id=organization_id,
        version=version,
        ghi=validation.governance_health_index.ghi,
        ghi_grade=validation.governance_health_index.grade,
        audit_readiness=validation.audit_readiness.score,
        lifecycle_score=validation.lifecycle.score,
        sla_score=validation.sla.score,
        compliance_score=validation.compliance.score,
        control_scores=control_scores,
        overall_score=overall_score,
        risk_categories=validation.lifecycle.risk_breakdown,
        open_findings_count=validation.audit_readiness.total_open,
        critical_findings=validation.audit_readiness.critical_count,
        high_findings=validation.audit_readiness.high_count,
        eol_components=validation.lifecycle.eol_count,
        deprecated_components=validation.lifecycle.deprecated_count,
        total_tech_components=validation.lifecycle.total_components,
    )

    _save_baseline_to_firestore(baseline)

    logger.info(
        "Baseline v%d created for org %s — GHI: %.1f (%s)",
        version, organization_id, baseline.ghi, baseline.ghi_grade,
    )

    return baseline


def _detect_control_regressions(
    current_scores: Dict[str, float],
    baseline_scores: Dict[str, float],
) -> List[DriftSignal]:
    """Detect domain-level control regressions."""
    signals = []
    for domain_id, baseline_score in baseline_scores.items():
        current_score = current_scores.get(domain_id, 0.0)
        delta = baseline_score - current_score
        if delta >= CONTROL_REGRESSION_THRESHOLD:
            severity = "critical" if delta >= 2.0 else "high" if delta >= 1.5 else "medium"
            signals.append(DriftSignal(
                signal_type="control_regression",
                severity=severity,
                title=f"Control Regression: {domain_id}",
                description=(
                    f"Domain {domain_id} score dropped from {baseline_score:.1f} to "
                    f"{current_score:.1f} (Δ = -{delta:.1f})"
                ),
                delta=-delta,
                metadata={"domain_id": domain_id, "baseline": baseline_score, "current": current_score},
            ))
    return signals


def _detect_risk_escalation(
    current_ghi: float,
    baseline_ghi: float,
) -> List[DriftSignal]:
    """Detect GHI-based risk escalation."""
    signals = []
    if baseline_ghi > 0:
        pct_change = ((baseline_ghi - current_ghi) / baseline_ghi) * 100
        if pct_change >= RISK_ESCALATION_PCT:
            severity = "critical" if pct_change >= 25 else "high" if pct_change >= 15 else "medium"
            signals.append(DriftSignal(
                signal_type="risk_escalation",
                severity=severity,
                title="GHI Risk Escalation",
                description=(
                    f"Governance Health Index dropped {pct_change:.1f}% — "
                    f"from {baseline_ghi:.1f} to {current_ghi:.1f}"
                ),
                delta=-pct_change,
                metadata={"baseline_ghi": baseline_ghi, "current_ghi": current_ghi, "pct_change": pct_change},
            ))
    return signals


def _detect_overdue_findings(
    findings: List[Finding],
) -> List[DriftSignal]:
    """Detect overdue / unresolved findings (SLA breach)."""
    signals = []
    overdue_count = 0
    for f in findings:
        if f.status in (FindingStatus.OPEN, FindingStatus.IN_PROGRESS):
            # Check if finding has been open too long
            created = f.created_at or datetime.now(timezone.utc)
            if hasattr(created, 'tzinfo') and created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            age_days = (datetime.now(timezone.utc) - created).days

            # SLA thresholds by severity
            sla_days = {"critical": 7, "high": 14, "medium": 30, "low": 90}
            sev_val = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            threshold = sla_days.get(sev_val, 30)

            if age_days > threshold:
                overdue_count += 1

    if overdue_count > 0:
        severity = "critical" if overdue_count >= 5 else "high" if overdue_count >= 3 else "medium"
        signals.append(DriftSignal(
            signal_type="sla_breach",
            severity=severity,
            title=f"{overdue_count} Overdue Finding{'s' if overdue_count != 1 else ''}",
            description=f"{overdue_count} finding(s) have exceeded their remediation SLA window",
            delta=float(overdue_count),
            metadata={"overdue_count": overdue_count},
        ))
    return signals


def _detect_tech_risk_drift(
    current_tech: List[TechStackItem],
    baseline: BaselineSnapshot,
) -> List[DriftSignal]:
    """Detect tech stack regression since baseline."""
    signals = []

    current_eol = sum(
        1 for t in current_tech
        if (t.lts_status.value if hasattr(t.lts_status, "value") else t.lts_status) == "eol"
    )
    current_deprecated = sum(
        1 for t in current_tech
        if (t.lts_status.value if hasattr(t.lts_status, "value") else t.lts_status) == "deprecated"
    )

    new_eol = current_eol - baseline.eol_components
    new_deprecated = current_deprecated - baseline.deprecated_components

    if new_eol > 0:
        signals.append(DriftSignal(
            signal_type="tech_risk",
            severity="critical",
            title=f"{new_eol} New EOL Component{'s' if new_eol != 1 else ''}",
            description=f"{new_eol} component(s) reached end-of-life since last baseline",
            delta=float(new_eol),
            metadata={"new_eol": new_eol, "total_eol": current_eol},
        ))

    if new_deprecated > 0:
        signals.append(DriftSignal(
            signal_type="tech_risk",
            severity="high",
            title=f"{new_deprecated} Newly Deprecated Component{'s' if new_deprecated != 1 else ''}",
            description=f"{new_deprecated} component(s) became deprecated since last baseline",
            delta=float(new_deprecated),
            metadata={"new_deprecated": new_deprecated, "total_deprecated": current_deprecated},
        ))

    return signals


def _detect_evidence_expiry(
    latest_assessment: Optional[Assessment],
) -> List[DriftSignal]:
    """Detect if assessment evidence has expired (stale assessment)."""
    signals = []
    if latest_assessment and latest_assessment.completed_at:
        completed = latest_assessment.completed_at
        if hasattr(completed, 'tzinfo') and completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - completed).days
        if age_days > EVIDENCE_EXPIRY_DAYS:
            severity = "high" if age_days > 180 else "medium"
            signals.append(DriftSignal(
                signal_type="evidence_expiry",
                severity=severity,
                title="Assessment Evidence Stale",
                description=(
                    f"Last completed assessment is {age_days} days old "
                    f"(threshold: {EVIDENCE_EXPIRY_DAYS} days)"
                ),
                delta=float(age_days - EVIDENCE_EXPIRY_DAYS),
                metadata={"age_days": age_days, "threshold": EVIDENCE_EXPIRY_DAYS},
            ))
    elif not latest_assessment:
        signals.append(DriftSignal(
            signal_type="evidence_expiry",
            severity="high",
            title="No Completed Assessment",
            description="Organization has no completed assessment — evidence baseline missing",
            metadata={},
        ))
    return signals


def _detect_audit_proximity(
    db: Session,
    organization_id: str,
    open_high_findings: int,
) -> List[DriftSignal]:
    """Detect audit proximity risk — upcoming audit with unresolved high findings."""
    signals = []
    try:
        from app.models.audit_calendar import AuditCalendarEntry
        upcoming = (
            db.query(AuditCalendarEntry)
            .filter(
                AuditCalendarEntry.org_id == organization_id,
                AuditCalendarEntry.audit_date >= datetime.now(timezone.utc),
                AuditCalendarEntry.audit_date <= datetime.now(timezone.utc) + timedelta(days=AUDIT_PROXIMITY_DAYS),
            )
            .all()
        )
        if upcoming and open_high_findings > 0:
            for entry in upcoming:
                days_until = (entry.audit_date - datetime.now(timezone.utc).date()).days if hasattr(entry.audit_date, 'date') else 30
                signals.append(DriftSignal(
                    signal_type="audit_proximity",
                    severity="critical" if days_until < 14 else "high",
                    title=f"Audit in {days_until} Days with Open Findings",
                    description=(
                        f"Audit '{entry.framework}' in {days_until} days — "
                        f"{open_high_findings} high/critical findings still open"
                    ),
                    delta=float(days_until),
                    metadata={
                        "audit_framework": entry.framework,
                        "days_until": days_until,
                        "open_high_findings": open_high_findings,
                    },
                ))
    except Exception as exc:
        logger.debug("Audit proximity check skipped: %s", exc)
    return signals


def _calculate_dis(signals: List[DriftSignal]) -> float:
    """
    Calculate Drift Impact Score (DIS) from signals.

    DIS = Σ(signal_weight × count_per_type) normalized to 0–100.
    """
    type_counts: Dict[str, int] = {}
    for s in signals:
        type_counts[s.signal_type] = type_counts.get(s.signal_type, 0) + 1

    raw = 0.0
    raw += type_counts.get("control_regression", 0) * DIS_WEIGHTS["control_regressions"]
    raw += type_counts.get("risk_escalation", 0) * DIS_WEIGHTS["risk_escalations"]
    raw += type_counts.get("sla_breach", 0) * DIS_WEIGHTS["overdue_findings"]
    raw += type_counts.get("tech_risk", 0) * DIS_WEIGHTS["unsupported_tech"]
    raw += type_counts.get("evidence_expiry", 0) * DIS_WEIGHTS["evidence_expired"]
    raw += type_counts.get("audit_proximity", 0) * DIS_WEIGHTS["audit_proximity"]

    # Normalize to 0–100
    dis = min(100.0, (raw / DIS_MAX_RAW) * 100)
    return round(dis, 1)


def _get_drift_band(dis: float) -> Tuple[str, str]:
    """Get drift severity band label and color from DIS score."""
    for low, high, label, color in DRIFT_BANDS:
        if low <= dis <= high:
            return label, color
    return "Critical Drift", "red"


def calculate_drift(
    db: Session,
    organization_id: str,
) -> DriftResult:
    """
    Calculate compliance drift against the most recent baseline.

    Computes Δ_drift = |GHI_current − GHI_baseline| and runs all
    drift signal detectors.

    Args:
        db: SQLAlchemy session
        organization_id: Organization to analyze

    Returns:
        DriftResult with signals, DIS, and drift band
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise ValueError(f"Organization not found: {organization_id}")

    result = DriftResult(
        organization_id=organization_id,
        organization_name=org.name,
    )

    # Get current state
    validation = validate_organization(db, org)
    result.current_ghi = validation.governance_health_index.ghi

    # Get latest assessment
    latest_assessment = (
        db.query(Assessment)
        .filter(
            Assessment.organization_id == organization_id,
            Assessment.status == AssessmentStatus.COMPLETED,
        )
        .order_by(Assessment.completed_at.desc())
        .first()
    )

    current_control_scores: Dict[str, float] = {}
    if latest_assessment:
        for score in latest_assessment.scores:
            current_control_scores[score.domain_id] = score.score

    # Get baseline
    baseline = _get_latest_baseline(organization_id)

    if baseline:
        result.baseline_id = baseline.id
        result.baseline_date = baseline.created_at
        result.baseline_ghi = baseline.ghi
        result.ghi_delta = round(result.current_ghi - baseline.ghi, 2)

        # Run all drift detectors
        all_signals: List[DriftSignal] = []

        # 1. Control regressions
        all_signals.extend(_detect_control_regressions(
            current_control_scores, baseline.control_scores,
        ))

        # 2. Risk escalation
        all_signals.extend(_detect_risk_escalation(
            result.current_ghi, baseline.ghi,
        ))

        # 3. Overdue findings (SLA breach)
        all_findings: List[Finding] = []
        for assessment in org.assessments:
            all_findings.extend(assessment.findings)
        all_signals.extend(_detect_overdue_findings(all_findings))

        # 4. Tech risk drift
        all_signals.extend(_detect_tech_risk_drift(
            list(org.tech_stack_items), baseline,
        ))

        # 5. Evidence expiry
        all_signals.extend(_detect_evidence_expiry(latest_assessment))

        # 6. Audit proximity risk
        open_high = validation.audit_readiness.critical_count + validation.audit_readiness.high_count
        all_signals.extend(_detect_audit_proximity(db, organization_id, open_high))

        # Calculate DIS
        result.drift_impact_score = _calculate_dis(all_signals)
        result.drift_band, result.drift_band_color = _get_drift_band(result.drift_impact_score)
        result.signals = [s.to_dict() for s in all_signals]

        # Signal type counts
        type_counts: Dict[str, int] = {}
        for s in all_signals:
            type_counts[s.signal_type] = type_counts.get(s.signal_type, 0) + 1
        result.signal_counts = type_counts

    else:
        # No baseline — report current state only
        result.drift_band = "No Baseline"
        result.drift_band_color = "gray"
        result.forecast_summary = (
            "No baseline exists. Create a baseline to begin tracking compliance drift."
        )

    # Calculate supplementary metrics
    result.compliance_sustainability_index = calculate_sustainability_index(db, organization_id)
    result.audit_failure_probability = calculate_audit_failure_probability(db, organization_id)

    # Save result
    _save_drift_result(result)

    logger.info(
        "Drift analysis for org %s — DIS: %.1f (%s), signals: %d, GHI delta: %+.1f",
        organization_id,
        result.drift_impact_score,
        result.drift_band,
        len(result.signals),
        result.ghi_delta,
    )

    return result


def get_drift_timeline(
    organization_id: str,
    limit: int = 30,
) -> List[DriftTimelineEntry]:
    """
    Build a drift timeline from baseline history.

    Returns chronological list of GHI/DIS data points for charting.
    """
    baselines = _get_baseline_history(organization_id, limit=limit)
    timeline: List[DriftTimelineEntry] = []

    prev_ghi = None
    for bl in baselines:
        # Simple drift score approximation from inter-baseline comparison
        drift_score = 0.0
        if prev_ghi is not None and prev_ghi > 0:
            pct_drop = max(0, ((prev_ghi - bl.ghi) / prev_ghi) * 100)
            drift_score = min(100.0, pct_drop * 2)  # amplify for visibility

        band, band_color = _get_drift_band(drift_score)
        signals_count = (
            bl.critical_findings + bl.high_findings + bl.eol_components + bl.deprecated_components
        )

        timeline.append(DriftTimelineEntry(
            date=bl.created_at,
            ghi=bl.ghi,
            drift_score=round(drift_score, 1),
            signals_count=signals_count,
            band=band,
            band_color=band_color,
        ))
        prev_ghi = bl.ghi

    return timeline


# ═══════════════════════════════════════════════════════════════════════
# Compliance Sustainability Index (CSI)
# ═══════════════════════════════════════════════════════════════════════

def calculate_sustainability_index(
    db: Session,
    organization_id: str,
) -> float:
    """
    Compliance Sustainability Index (CSI) — how sustainable is the posture?

    Factors:
      - Average remediation velocity (faster = more sustainable)
      - Reopened findings rate (lower = better)
      - Recurring drift frequency (lower = better)
      - Assessment frequency (higher = better)

    Returns: 0–100 score (higher = more sustainable)
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        return 0.0

    # Factor 1: Assessment cadence (0–25)
    assessments = (
        db.query(Assessment)
        .filter(Assessment.organization_id == organization_id)
        .order_by(Assessment.created_at.desc())
        .limit(10)
        .all()
    )
    if len(assessments) >= 3:
        cadence_score = 25.0
    elif len(assessments) >= 2:
        cadence_score = 15.0
    elif len(assessments) >= 1:
        cadence_score = 8.0
    else:
        cadence_score = 0.0

    # Factor 2: Remediation velocity (0–25)
    # Ratio of resolved findings vs total
    all_findings: List[Finding] = []
    for assessment in org.assessments:
        all_findings.extend(assessment.findings)

    total_findings = len(all_findings)
    resolved_count = sum(
        1 for f in all_findings
        if f.status in (FindingStatus.RESOLVED, FindingStatus.ACCEPTED)
    )
    if total_findings > 0:
        remediation_rate = resolved_count / total_findings
        velocity_score = remediation_rate * 25.0
    else:
        velocity_score = 25.0  # No findings = no remediation needed

    # Factor 3: Severity composition (0–25)
    # Lower severity portfolio = more sustainable
    critical_pct = (
        sum(1 for f in all_findings if f.severity == FindingSeverity.CRITICAL) / max(total_findings, 1)
    )
    high_pct = (
        sum(1 for f in all_findings if f.severity == FindingSeverity.HIGH) / max(total_findings, 1)
    )
    severity_penalty = (critical_pct * 25 + high_pct * 10)
    severity_score = max(0.0, 25.0 - severity_penalty)

    # Factor 4: Tech stack health (0–25)
    tech_items = list(org.tech_stack_items)
    if tech_items:
        healthy = sum(
            1 for t in tech_items
            if (t.lts_status.value if hasattr(t.lts_status, "value") else t.lts_status)
            in ("lts", "active")
        )
        tech_health_rate = healthy / len(tech_items)
        tech_score = tech_health_rate * 25.0
    else:
        tech_score = 12.5  # No registry = unknown

    csi = round(cadence_score + velocity_score + severity_score + tech_score, 1)
    return min(100.0, csi)


# ═══════════════════════════════════════════════════════════════════════
# Audit Failure Probability Model
# ═══════════════════════════════════════════════════════════════════════

def calculate_audit_failure_probability(
    db: Session,
    organization_id: str,
) -> float:
    """
    Predictive Audit Failure Probability — deterministic probability model.

    NOT a checklist. A probability estimate based on:
      - GHI score (weighted 30%)
      - Open critical/high findings (weighted 30%)
      - Evidence staleness (weighted 20%)
      - Tech stack risk (weighted 20%)

    Returns: 0–100 probability percentage (higher = more likely to fail)
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        return 50.0  # Unknown = 50/50

    validation = validate_organization(db, org)

    # Component 1: GHI inversion (lower GHI = higher failure probability)
    ghi = validation.governance_health_index.ghi
    ghi_risk = max(0, 100 - ghi) * 0.30

    # Component 2: Open findings severity
    audit = validation.audit_readiness
    findings_risk = max(0, 100 - audit.score) * 0.30

    # Component 3: Evidence staleness
    latest_assessment = (
        db.query(Assessment)
        .filter(
            Assessment.organization_id == organization_id,
            Assessment.status == AssessmentStatus.COMPLETED,
        )
        .order_by(Assessment.completed_at.desc())
        .first()
    )
    if latest_assessment and latest_assessment.completed_at:
        completed = latest_assessment.completed_at
        if hasattr(completed, 'tzinfo') and completed.tzinfo is None:
            completed = completed.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - completed).days
        staleness = min(100, (age_days / EVIDENCE_EXPIRY_DAYS) * 100) * 0.20
    else:
        staleness = 80.0 * 0.20  # No assessment = high risk

    # Component 4: Tech stack risk
    lifecycle = validation.lifecycle
    if lifecycle.total_components > 0:
        eol_ratio = lifecycle.eol_count / lifecycle.total_components
        deprecated_ratio = lifecycle.deprecated_count / lifecycle.total_components
        tech_risk = (eol_ratio * 80 + deprecated_ratio * 40) * 0.20
    else:
        tech_risk = 20.0 * 0.20  # Unknown

    probability = round(ghi_risk + findings_risk + staleness + tech_risk, 1)
    return min(100.0, max(0.0, probability))


# ═══════════════════════════════════════════════════════════════════════
# Shadow AI Governance
# ═══════════════════════════════════════════════════════════════════════

# AI Model tiers for governance classification
AI_MODEL_TIERS = {
    "sanctioned": "Approved for production use — vetted by security team",
    "conditional": "Approved with restrictions — requires data classification review",
    "unsanctioned": "Not approved — requires security review before deployment",
    "banned": "Explicitly prohibited — violates organizational policy",
}


def check_shadow_ai_risk(
    tech_items: List[TechStackItem],
) -> List[DriftSignal]:
    """
    Detect Shadow AI governance violations.

    Detection rules (layered):
      1. Metadata-based: notes field JSON with data_sensitivity / ai_model_tier.
      2. Approval-status-based: if the item has an ``approval_status`` attribute
         and it is not 'APPROVED', flag it regardless of metadata.
      3. Tier-based: unsanctioned → HIGH, banned → CRITICAL.

    The notes field is used to store metadata as JSON:
      {"data_sensitivity": "HIGH", "ai_model_tier": "unsanctioned"}
    """
    signals = []
    for item in tech_items:
        if not item.category or item.category.lower() != "ai model":
            continue

        # Parse metadata from notes field
        metadata: Dict[str, str] = {}
        if item.notes:
            try:
                metadata = json.loads(item.notes)
            except (json.JSONDecodeError, TypeError):
                # Try key=value parsing
                for part in item.notes.split(","):
                    if "=" in part:
                        k, v = part.strip().split("=", 1)
                        metadata[k.strip().lower()] = v.strip().lower()

        data_sensitivity = metadata.get("data_sensitivity", "").upper()
        ai_tier = metadata.get("ai_model_tier", "").lower()

        # ── Rule 2: Approval-status check (model attribute) ──────────
        approval = getattr(item, "approval_status", None) or metadata.get("approval_status", "")
        if isinstance(approval, str):
            approval = approval.strip().upper()

        if approval and approval not in ("APPROVED", "SANCTIONED", ""):
            # Not approved → at minimum HIGH
            sev = "critical" if data_sensitivity == "HIGH" or ai_tier == "banned" else "high"
            signals.append(DriftSignal(
                signal_type="shadow_ai",
                severity=sev,
                title=f"Unapproved AI Model: {item.component_name}",
                description=(
                    f"AI model '{item.component_name}' (v{item.version}) has "
                    f"approval_status='{approval}'. Models must be APPROVED before "
                    f"production use."
                ),
                metadata={
                    "component": item.component_name,
                    "version": item.version,
                    "approval_status": approval,
                    "data_sensitivity": data_sensitivity,
                    "ai_model_tier": ai_tier or "unknown",
                },
            ))
            continue  # Don't double-flag via metadata rules below

        # ── Rule 1 & 3: Metadata / tier-based ────────────────────────
        if data_sensitivity == "HIGH" and ai_tier == "unsanctioned":
            signals.append(DriftSignal(
                signal_type="shadow_ai",
                severity="critical",
                title=f"Unsanctioned AI Model: {item.component_name}",
                description=(
                    f"AI model '{item.component_name}' (v{item.version}) is classified as "
                    f"UNSANCTIONED but processes HIGH sensitivity data. "
                    f"Immediate security review required."
                ),
                metadata={
                    "component": item.component_name,
                    "version": item.version,
                    "data_sensitivity": data_sensitivity,
                    "ai_model_tier": ai_tier,
                },
            ))
        elif ai_tier == "unsanctioned":
            signals.append(DriftSignal(
                signal_type="shadow_ai",
                severity="high",
                title=f"Unsanctioned AI Model: {item.component_name}",
                description=(
                    f"AI model '{item.component_name}' (v{item.version}) is not approved. "
                    f"Security review required before production use."
                ),
                metadata={
                    "component": item.component_name,
                    "version": item.version,
                    "ai_model_tier": ai_tier,
                },
            ))
        elif ai_tier == "banned":
            signals.append(DriftSignal(
                signal_type="shadow_ai",
                severity="critical",
                title=f"BANNED AI Model in Use: {item.component_name}",
                description=(
                    f"AI model '{item.component_name}' is BANNED by organizational policy. "
                    f"Remove immediately."
                ),
                metadata={
                    "component": item.component_name,
                    "ai_model_tier": ai_tier,
                },
            ))

    return signals


# ═══════════════════════════════════════════════════════════════════════
# Regulatory Forecast — Predicted Posture Drop
# ═══════════════════════════════════════════════════════════════════════

# Regulatory events that tighten compliance requirements.
# Format: {"name": str, "effective_date": str (ISO), "impact_weight": float}
UPCOMING_REGULATIONS = [
    {
        "name": "EU AI Act — High-Risk AI Systems",
        "effective_date": "2025-08-02",
        "impact_weight": 0.25,
        "description": "Mandatory risk management, data governance, and transparency for high-risk AI.",
        "affects": ["uses_ai_in_production"],
    },
    {
        "name": "EU AI Act — General Purpose AI",
        "effective_date": "2025-08-02",
        "impact_weight": 0.15,
        "description": "Transparency and documentation requirements for GPAI models.",
        "affects": ["uses_ai_in_production"],
    },
    {
        "name": "PCI DSS v4.0 — Full Enforcement",
        "effective_date": "2025-03-31",
        "impact_weight": 0.20,
        "description": "All v4.0 requirements become mandatory (no longer best-practice).",
        "affects": ["processes_cardholder_data"],
    },
    {
        "name": "NIST CSF 2.0 — Govern Function",
        "effective_date": "2025-06-01",
        "impact_weight": 0.10,
        "description": "New 'Govern' function requires cybersecurity governance documentation.",
        "affects": [],
    },
    {
        "name": "SEC Cyber Disclosure — Annual 10-K Requirements",
        "effective_date": "2025-12-15",
        "impact_weight": 0.15,
        "description": "Annual cybersecurity risk management and strategy disclosure.",
        "affects": ["financial_services"],
    },
]


def calculate_regulatory_lag(
    db: Session,
    org_id: str,
    horizon_days: int = 180,
) -> Dict[str, Any]:
    """
    Predict the compliance posture drop from upcoming regulatory changes.

    For each upcoming regulation within *horizon_days*:
      - Check if the org is affected (based on boolean flags).
      - Calculate a weighted impact on the current GHI score.

    Returns a forecast dict:
      {
        "current_ghi": float,
        "predicted_ghi": float,
        "predicted_drop": float,
        "horizon_days": int,
        "upcoming_regulations": [...],
        "affected_count": int,
      }
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise ValueError(f"Organization not found: {org_id}")

    # Compute current posture
    validation = validate_organization(db, org_id)
    current_ghi = compute_ghi(validation)

    now = datetime.now(timezone.utc)
    horizon_end = now + timedelta(days=horizon_days)

    affected_regulations = []
    total_impact = 0.0

    for reg in UPCOMING_REGULATIONS:
        try:
            effective = datetime.fromisoformat(reg["effective_date"]).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue

        if effective > horizon_end:
            continue  # Beyond forecast window

        # Determine if org is affected
        affected = False
        if not reg["affects"]:
            affected = True  # Universal regulation
        else:
            for flag_name in reg["affects"]:
                if getattr(org, flag_name, False):
                    affected = True
                    break

        if not affected:
            continue

        # Time-weight: regulations that are closer have more impact
        days_until = max((effective - now).days, 0)
        time_factor = 1.0 - (days_until / max(horizon_days, 1))
        weighted_impact = reg["impact_weight"] * time_factor

        total_impact += weighted_impact
        affected_regulations.append({
            "name": reg["name"],
            "effective_date": reg["effective_date"],
            "days_until": days_until,
            "impact_weight": reg["impact_weight"],
            "time_weighted_impact": round(weighted_impact, 3),
            "description": reg["description"],
        })

    # Cap total impact at 40% (regulations won't drop GHI to zero)
    total_impact = min(total_impact, 0.40)

    predicted_drop = round(current_ghi * total_impact, 1)
    predicted_ghi = round(max(0.0, current_ghi - predicted_drop), 1)

    return {
        "current_ghi": round(current_ghi, 1),
        "predicted_ghi": predicted_ghi,
        "predicted_drop": predicted_drop,
        "drop_percentage": round(total_impact * 100, 1),
        "horizon_days": horizon_days,
        "upcoming_regulations": sorted(
            affected_regulations, key=lambda r: r["days_until"]
        ),
        "affected_count": len(affected_regulations),
        "forecast_generated_at": now.isoformat(),
    }
