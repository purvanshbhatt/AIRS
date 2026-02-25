"""
Audit Calendar service — business logic for audit scheduling and forecasting.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.audit_calendar import AuditCalendarEntry, AuditType
from app.models.finding import Finding, Severity
from app.models.assessment import Assessment
from app.schemas.audit_calendar import (
    AuditCalendarCreate,
    AuditCalendarUpdate,
    AuditCalendarResponse,
    AuditForecast,
)

logger = logging.getLogger(__name__)

# ── Framework keyword mapping for finding cross-reference ─────────────
FRAMEWORK_KEYWORDS = {
    "HIPAA": ["hipaa", "phi", "health", "medical"],
    "SOC 2": ["soc", "soc2", "trust", "availability", "confidentiality"],
    "SOC 2 Type II": ["soc", "soc2", "trust", "availability", "confidentiality"],
    "PCI-DSS": ["pci", "cardholder", "payment", "card"],
    "PCI-DSS v4.0": ["pci", "cardholder", "payment", "card"],
    "GDPR": ["gdpr", "privacy", "pii", "data protection", "consent"],
    "CMMC": ["cmmc", "cui", "dod", "defense"],
    "CMMC Level 2": ["cmmc", "cui", "dod", "defense"],
    "NIST CSF": ["nist", "csf", "cybersecurity", "framework"],
    "NIST CSF 2.0": ["nist", "csf", "cybersecurity", "framework"],
    "NIST AI RMF": ["ai", "machine learning", "model", "bias"],
    "NIST SP 800-171": ["nist", "cui", "controlled", "unclassified"],
    "FFIEC": ["ffiec", "financial", "examination"],
    "FedRAMP": ["fedramp", "federal", "government", "cloud"],
}


class AuditCalendarService:
    """Service for audit calendar CRUD and forecasting."""

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def create(self, data: AuditCalendarCreate) -> AuditCalendarEntry:
        """Create a new audit calendar entry."""
        entry = AuditCalendarEntry(
            org_id=self.org_id,
            framework=data.framework,
            audit_date=data.audit_date,
            audit_type=AuditType(data.audit_type),
            reminder_days_before=data.reminder_days_before,
            notes=data.notes,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get(self, entry_id: str) -> Optional[AuditCalendarEntry]:
        """Get a single entry by ID."""
        return (
            self.db.query(AuditCalendarEntry)
            .filter(
                AuditCalendarEntry.id == entry_id,
                AuditCalendarEntry.org_id == self.org_id,
            )
            .first()
        )

    def list_all(self) -> List[AuditCalendarEntry]:
        """List all audit calendar entries for the org."""
        return (
            self.db.query(AuditCalendarEntry)
            .filter(AuditCalendarEntry.org_id == self.org_id)
            .order_by(AuditCalendarEntry.audit_date.asc())
            .all()
        )

    def update(self, entry_id: str, data: AuditCalendarUpdate) -> Optional[AuditCalendarEntry]:
        """Update an existing entry."""
        entry = self.get(entry_id)
        if not entry:
            return None
        update_data = data.model_dump(exclude_unset=True)
        if "audit_type" in update_data:
            update_data["audit_type"] = AuditType(update_data["audit_type"])
        for key, value in update_data.items():
            setattr(entry, key, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry_id: str) -> bool:
        """Delete an entry."""
        entry = self.get(entry_id)
        if not entry:
            return False
        self.db.delete(entry)
        self.db.commit()
        return True

    def enrich_response(self, entry: AuditCalendarEntry) -> AuditCalendarResponse:
        """Convert model to response with computed fields."""
        now = datetime.now(timezone.utc)
        audit_dt = entry.audit_date
        if audit_dt.tzinfo is None:
            audit_dt = audit_dt.replace(tzinfo=timezone.utc)
        days_until = (audit_dt - now).days
        is_upcoming = 0 <= days_until <= entry.reminder_days_before

        return AuditCalendarResponse(
            id=entry.id,
            org_id=entry.org_id,
            framework=entry.framework,
            audit_date=entry.audit_date,
            audit_type=entry.audit_type.value if isinstance(entry.audit_type, AuditType) else entry.audit_type,
            reminder_days_before=entry.reminder_days_before,
            notes=entry.notes,
            days_until_audit=max(days_until, 0),
            is_upcoming=is_upcoming,
            created_at=entry.created_at,
            updated_at=entry.updated_at,
        )

    def get_forecast(self, entry: AuditCalendarEntry) -> AuditForecast:
        """
        Generate pre-audit risk forecast by cross-referencing 
        findings with the audit framework.
        """
        now = datetime.now(timezone.utc)
        audit_dt = entry.audit_date
        if audit_dt.tzinfo is None:
            audit_dt = audit_dt.replace(tzinfo=timezone.utc)
        days_until = max((audit_dt - now).days, 0)

        # Find keywords for this framework
        keywords = FRAMEWORK_KEYWORDS.get(entry.framework, [entry.framework.lower()])

        # Query open findings for this org's assessments
        findings = (
            self.db.query(Finding)
            .join(Assessment, Finding.assessment_id == Assessment.id)
            .filter(Assessment.organization_id == self.org_id)
            .all()
        )

        # Cross-reference: find findings related to the audit framework
        related = []
        for f in findings:
            text = f"{f.title} {f.description or ''} {f.domain_name or ''}".lower()
            if any(kw in text for kw in keywords):
                related.append(f)

        critical_count = sum(1 for f in related if f.severity == Severity.CRITICAL)
        high_count = sum(1 for f in related if f.severity == Severity.HIGH)
        medium_count = sum(1 for f in related if f.severity == Severity.MEDIUM)
        critical_high = critical_count + high_count

        # Audit readiness score: 100 - (critical×15) - (high×8) - (medium×3)
        readiness = 100 - (critical_count * 15) - (high_count * 8) - (medium_count * 3)
        audit_readiness_score = max(0, min(100, readiness))

        # Determine risk level
        if critical_high >= 3 or (days_until < 30 and critical_high > 0):
            risk_level = "critical"
        elif critical_high >= 1 or len(related) >= 5:
            risk_level = "high"
        elif len(related) >= 2:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Generate recommendation
        if risk_level in ("critical", "high"):
            recommendation = (
                f"⚠️ {critical_high} critical/high findings related to {entry.framework}. "
                f"Prioritize remediation before audit in {days_until} days."
            )
        elif risk_level == "medium":
            recommendation = (
                f"📋 {len(related)} findings related to {entry.framework}. "
                f"Review and address before audit date."
            )
        else:
            recommendation = (
                f"✅ No significant {entry.framework}-related findings. "
                f"Continue monitoring."
            )

        return AuditForecast(
            audit_id=entry.id,
            framework=entry.framework,
            audit_date=entry.audit_date,
            days_until_audit=days_until,
            related_findings_count=len(related),
            critical_high_count=critical_high,
            risk_level=risk_level,
            recommendation=recommendation,
            audit_readiness_score=audit_readiness_score,
        )
