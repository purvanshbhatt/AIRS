"""
DailyReadinessReport — The Immutable Product Contract.

Everything in the system exists to populate this single object.
Connectors, Evidence, Capabilities, Moments, Risk, Trust, Coverage —
all of them feed into one answer:

    "Can this clinic safely open today?"

Rules:
  - No internal IDs (evidence hashes, connector UUIDs, source_ids) in
    any field that serializes to the customer.
  - All timestamps are UTC.
  - AI explains. AI never decides. Every score and status is deterministic.
  - Unknown is a valid state. "We don't know" is more trustworthy than silence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Core Decision
# ─────────────────────────────────────────────────────────────────────────────

class ReadinessStatus(str, Enum):
    """The three states a clinic can be in."""
    safe_to_open = "safe_to_open"
    action_needed = "action_needed"
    critical_risk = "critical_risk"
    unknown = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Executive Timeline
# ─────────────────────────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    """One entry in the overnight timeline. Chronological."""
    timestamp: datetime
    icon: str                   # "check", "warning", "error", "info"
    label: str                  # "Backup completed"
    detail: Optional[str] = None
    source: str                 # "Backup System" (human-readable, never internal)


# ─────────────────────────────────────────────────────────────────────────────
# Coverage — what we checked AND what we didn't
# ─────────────────────────────────────────────────────────────────────────────

class CoverageArea(BaseModel):
    """One security area that can be monitored."""
    area: str                   # "Users", "Email", "Firewalls", "Medical Devices"
    monitored: bool
    source: Optional[str] = None  # "Microsoft 365" — which connector covers this


class CoverageReport(BaseModel):
    """Security Visibility: what we can see and what we can't."""
    coverage_pct: int           # 0–100
    monitored: List[CoverageArea] = Field(default_factory=list)
    not_monitored: List[CoverageArea] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Verification — why we're confident (or not)
# ─────────────────────────────────────────────────────────────────────────────

class VerificationReason(BaseModel):
    """One reason contributing to verification or distrust."""
    icon: str                   # "check", "warning", "error"
    text: str                   # "Microsoft synchronized 2 minutes ago"


class VerificationExplanation(BaseModel):
    """Why we believe our assessment. Doctors trust explanations, not numbers."""
    confidence_pct: int
    reasons: List[VerificationReason] = Field(default_factory=list)


class VerificationContext(BaseModel):
    """Per-item verification metadata. Answers 'Why are you telling me this?'"""
    verification_source: str    # "Microsoft 365" (never internal IDs)
    last_verified_at: Optional[datetime] = None
    connector_health: str       # "healthy", "degraded", "unreachable"
    confidence_pct: int
    verification_status: str    # "verified", "unverified", "stale"
    data_age_description: str   # "Checked 2 minutes ago"
    can_reverify: bool = True
    verification_method: str    # "Live API check", "Cached from last sync"



# ─────────────────────────────────────────────────────────────────────────────
# Action Cards — what the customer can do
# ─────────────────────────────────────────────────────────────────────────────

class ActionCard(BaseModel):
    """Customer-facing action. Replaces raw ActionIntent at the product boundary."""
    action_id: str
    problem: str                # "Former Receptionist Account is active"
    why_it_matters: str         # "They could access patient records"
    recommended_action: str     # "This will immediately lock jane@clinic.com..."
    can_be_undone: bool         # True
    estimated_time_minutes: int # 5
    fix_now_available: bool     # True
    
    verification: Optional[VerificationContext] = None
    
    category: str               # "access_control", "device_security", "backup"
    approval_needed: bool
    required_permissions: List[str]  # ["Microsoft 365 Admin"]
    success_message: str        # "Account disabled. Access to patient records revoked."
    
    # Internal automation routing — excluded from serialization
    automation_type: Optional[str] = Field(default=None, exclude=True)
    automation_params: Dict[str, Any] = Field(default_factory=dict, exclude=True)


# ─────────────────────────────────────────────────────────────────────────────
# Readiness Checks — pass / fail / warning / unknown
# ─────────────────────────────────────────────────────────────────────────────

class ExecutiveExplanation(BaseModel):
    """Plain-English explanation of a security finding for non-technical executives."""
    status: str = Field(..., description="Deterministic verdict status (verified, failed, warning, unknown, unavailable, stale)")
    business_label: str = Field(..., description="Plain-English name for the capability (e.g., 'Who Can Access Your Systems')")
    technical_label: str = Field(..., description="Original technical name (e.g., 'Identity & Access Management')")
    what_it_means: str = Field(..., description="Simple explanation of what is verified or not verified")
    why_it_matters: str = Field(..., description="Business impact if this protection fails or is missing")
    what_to_do_next: str = Field(..., description="Recommended next action for the user")
    evidence_state: str = Field(..., description="Explicit state of the evidence (e.g., 'verified', 'missing', 'stale')")
    last_verified_at: Optional[datetime] = Field(None, description="When this state was last confirmed by telemetry")

class ReadinessCheck(BaseModel):
    """One item in the readiness report. Includes verification and optional action."""
    status: str                 # "pass", "fail", "warning", "unknown"
    label: str                  # "No active former employees" or "Backup Appliance not reporting"
    detail: Optional[str] = None
    verification: Optional[VerificationContext] = None
    action: Optional[ActionCard] = None
    explanation: Optional[ExecutiveExplanation] = Field(None, description="Executive-friendly explanation of this check")


# ─────────────────────────────────────────────────────────────────────────────
# Unknown Items — things we CAN'T verify (differentiator)
# ─────────────────────────────────────────────────────────────────────────────

class UnknownItem(BaseModel):
    """Something we can't verify. 'We don't know' is more trustworthy than silence."""
    label: str                  # "Backup Appliance hasn't reported in 18 hours"
    last_seen: Optional[datetime] = None
    last_seen_description: Optional[str] = None  # "18 hours ago"
    impact: str                 # "Confidence reduced. Backup status unverified."
    source: str                 # "Backup System"


# ─────────────────────────────────────────────────────────────────────────────
# Connector Readiness
# ─────────────────────────────────────────────────────────────────────────────

class ConnectorReadiness(BaseModel):
    """Health and coverage of one integration."""
    name: str                   # "Microsoft 365"
    status: str                 # "healthy", "degraded", "unreachable"
    connected: bool
    last_verified_at: Optional[datetime] = None
    coverage: List[str] = Field(default_factory=list)  # ["Users", "Email", "MFA"]
    missing_visibility: List[str] = Field(default_factory=list)   # ["Conditional Access"]
    confidence_pct: int = 100


# ─────────────────────────────────────────────────────────────────────────────
# Readiness History & Trends
# ─────────────────────────────────────────────────────────────────────────────

class ReadinessTrendPoint(BaseModel):
    """One day's readiness snapshot."""
    date: str
    clinic_health_pct: int
    delta_reasons: List[str] = Field(default_factory=list)  # ["+ MFA enabled", "- Backup failed"]


class ReadinessTrend(BaseModel):
    """Are we improving? Historical daily snapshots with explanations."""
    points: List[ReadinessTrendPoint] = Field(default_factory=list)
    improving: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Business Continuity
# ─────────────────────────────────────────────────────────────────────────────

class OperationalReadiness(BaseModel):
    """Answers core business continuity questions."""
    can_operate_today: bool
    can_recover: bool
    current_blockers: List[str] = Field(default_factory=list)
    estimated_downtime_minutes: int = 0
    critical_systems_verified: List[str] = Field(default_factory=list)
    critical_systems_assumed: List[str] = Field(default_factory=list)

class BusinessContinuity(BaseModel):
    """Top-level container for continuity and operational metrics."""
    operational_readiness: OperationalReadiness


# ─────────────────────────────────────────────────────────────────────────────
# Value Summary — what renews subscriptions
# ─────────────────────────────────────────────────────────────────────────────

class ValueSummary(BaseModel):
    """Business value delivered. These are what convince customers to renew."""
    period_label: str           # "This Month", "Last 30 Days"
    accounts_protected: int = 0
    devices_protected: int = 0
    backups_verified: int = 0
    problems_prevented: int = 0
    estimated_downtime_avoided_hours: float = 0.0
    estimated_hipaa_records_protected: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Business Risk Assessment — internal enrichment from Risk Engine
# ─────────────────────────────────────────────────────────────────────────────

class PatientImpact(str, Enum):
    none = "none"
    indirect = "indirect"
    direct = "direct"
    critical = "critical"


class ComplianceExposure(str, Enum):
    none = "none"
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class Urgency(str, Enum):
    routine = "routine"
    soon = "soon"
    urgent = "urgent"
    immediate = "immediate"


class BusinessRiskAssessment(BaseModel):
    """Deterministic business impact assessment. AI never decides — rules do."""
    patient_impact: PatientImpact = PatientImpact.none
    financial_impact_usd: int = 0
    downtime_hours: float = 0.0
    compliance_exposure: ComplianceExposure = ComplianceExposure.none
    automation_possible: bool = False
    urgency: Urgency = Urgency.routine
    estimated_fix_minutes: int = 5
    overall_priority: int = 0  # 1–100, higher = more urgent
    risk_factors: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Clinic Context — aggregated domain model for engines
# ─────────────────────────────────────────────────────────────────────────────

class StaffSummary(BaseModel):
    """Lightweight staff record for risk assessment."""
    id: str
    display_name: str
    role: str
    department: str
    employment_status: str
    access_systems: List[str] = Field(default_factory=list)
    business_impact_level: str = "medium"
    external_identity_id: Optional[str] = None
    email: Optional[str] = None


class DeviceSummary(BaseModel):
    """Lightweight device record for risk assessment."""
    id: str
    device_name: str
    device_type: str
    location: Optional[str] = None
    assigned_staff_name: Optional[str] = None
    critical_system_name: Optional[str] = None
    business_impact_level: str = "medium"
    external_device_id: Optional[str] = None


class SystemSummary(BaseModel):
    """Lightweight critical system record."""
    id: str
    system_name: str
    system_type: str
    hipaa_relevant: bool = False
    backup_required: bool = False
    downtime_tolerance_hours: int = 24


class MSPSummary(BaseModel):
    """MSP contact info for escalation."""
    msp_name: str
    contact_email: str
    escalation_email: Optional[str] = None
    response_sla_hours: int = 4


class ClinicContext(BaseModel):
    """Aggregated clinic state. Built from domain models, consumed by engines."""
    org_id: str
    clinic_name: str
    clinic_type: str = "medical"
    org_mode: str = "pilot"  # "demo", "pilot", "production"
    primary_contact: Optional[str] = None
    primary_contact_role: Optional[str] = None
    staff: List[StaffSummary] = Field(default_factory=list)
    devices: List[DeviceSummary] = Field(default_factory=list)
    critical_systems: List[SystemSummary] = Field(default_factory=list)
    msp: Optional[MSPSummary] = None


# ═══════════════════════════════════════════════════════════════════════════════
# THE PRODUCT
# ═══════════════════════════════════════════════════════════════════════════════

class DailyReadinessReport(BaseModel):
    """The immutable product contract.

    Everything in the system — every connector, capability, evidence provider,
    business rule, action, and trust signal — exists ONLY to populate this object.

    This is what the customer sees. This is what they pay for.
    This is what answers: "Can this clinic safely open today?"
    """

    # ── Identity ──────────────────────────────────────────────────────────
    report_id: str
    org_id: str = Field(exclude=True)   # Never leak org ID to frontend
    report_date: str                     # "2026-08-01"
    generated_at: datetime

    # ── Core Decision ─────────────────────────────────────────────────────
    status: ReadinessStatus              # safe_to_open | action_needed | critical_risk
    clinic_health_pct: int               # Business health (0–100)
    connector_health_pct: int            # Technical health (0–100), separate from clinic

    # ── Narrative ─────────────────────────────────────────────────────────
    greeting: str                        # "Good Morning Dr. Smith"
    summary: str                         # "Your clinic is ready. We checked..."

    # ── Executive Timeline (what changed overnight) ───────────────────────
    timeline: List[TimelineEvent] = Field(default_factory=list)

    # ── Business Continuity ───────────────────────────────────────────────
    business_continuity: BusinessContinuity

    # ── Readiness Checks ──────────────────────────────────────────────────
    passed_checks: List[ReadinessCheck] = Field(default_factory=list)   # ✔ items
    failed_checks: List[ReadinessCheck] = Field(default_factory=list)   # ✖ items
    warnings: List[ReadinessCheck] = Field(default_factory=list)        # ⚠ items

    # ── Unknowns (things we can't verify — differentiator) ────────────────
    unknowns: List[UnknownItem] = Field(default_factory=list)

    # ── Immediate Actions ─────────────────────────────────────────────────
    immediate_actions: List[ActionCard] = Field(default_factory=list)

    # ── Coverage (what we monitor vs. what we don't) ──────────────────────
    coverage: CoverageReport = Field(default_factory=lambda: CoverageReport(
        coverage_pct=0, monitored=[], not_monitored=[]
    ))

    # ── Connector Health ──────────────────────────────────────────────────
    connectors: List[ConnectorReadiness] = Field(default_factory=list)

    # ── Verification Explanation ──────────────────────────────────────────
    verification: VerificationExplanation = Field(default_factory=lambda: VerificationExplanation(
        confidence_pct=0, reasons=[]
    ))

    # ── Historical Trend ──────────────────────────────────────────────────
    trend: ReadinessTrend = Field(default_factory=lambda: ReadinessTrend(
        points=[], improving=True
    ))

    # ── Value Delivered ───────────────────────────────────────────────────
    value: ValueSummary = Field(default_factory=lambda: ValueSummary(
        period_label="This Month"
    ))

    # ── Audit ─────────────────────────────────────────────────────────────
    audit_snapshot_id: str = ""          # Links to ReadinessLedgerEntry for audit trail

    # ── Stats ─────────────────────────────────────────────────────────────
    checks_performed: int = 0
    devices_checked: int = 0
    accounts_checked: int = 0
    backups_verified: int = 0
