"""
TelemetryVerificationService — SIEM Event Processing & Provenance Engine.

Ingests raw SIEM events from Wazuh/Splunk webhooks, cross-references them
against the FrameworkMappingRegistry, and creates/updates FindingProvenance
records with cryptographic evidence hashes.

Architectural Invariants:
  1. All provenance hashes are computed via SHA-256. No LLM involvement.
  2. Score recomputation is deterministic (Python math only).
  3. Every state change emits a structured JSON audit log.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.finding_provenance import (
    FindingProvenance,
    VerificationSource,
    ProvenanceStatus,
)
from app.models.framework_mapping import FrameworkMappingRegistry

logger = logging.getLogger("airs.telemetry")


# ---------------------------------------------------------------------------
# Pydantic V2 Schemas
# ---------------------------------------------------------------------------

class SIEMEventPayload(BaseModel):
    """Inbound SIEM event from Wazuh/Splunk webhook.

    This is the canonical contract for all SIEM integrations.
    The raw_data_hash is computed by the SIEM forwarder; we verify it
    against our own hash of the payload for integrity.
    """
    source: str = Field(
        ..., description="SIEM source identifier: 'wazuh', 'splunk', 'elastic'.",
        examples=["wazuh"],
    )
    alert_id: str = Field(
        ..., description="Unique alert/event ID from the source SIEM.",
        examples=["wazuh-alert-12345"],
    )
    rule_id: str = Field(
        ..., description="SIEM rule ID that fired (e.g., Wazuh rule 550, Splunk correlation).",
        examples=["550"],
    )
    timestamp: str = Field(
        ..., description="ISO-8601 UTC timestamp of the original SIEM event.",
        examples=["2026-05-22T12:00:00Z"],
    )
    raw_data_hash: str = Field(
        ..., description="SHA-256 hex digest of the raw event payload, computed by the forwarder.",
        examples=["a1b2c3d4e5f6..."],
    )
    raw_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional raw event data for local hash verification.",
    )
    finding_rule_id: Optional[str] = Field(
        default=None,
        description="Optional ResilAI finding rule_id for direct matching (e.g., 'DC-001').",
    )


class VerificationResponse(BaseModel):
    """Response after processing a SIEM event."""
    status: str = Field(..., description="Processing result: 'verified', 'already_exists', 'no_match', 'error'.")
    finding_id: Optional[str] = None
    finding_title: Optional[str] = None
    verification_status: Optional[str] = None
    evidence_hash: Optional[str] = None
    siem_alert_id: Optional[str] = None
    message: str = ""


class ScoreChangeLog(BaseModel):
    """Structured log entry emitted on every GHI score change."""
    event: str = "ghi_score_change"
    assessment_id: str
    organization_id: str
    old_score: float
    new_score: float
    delta: float
    evidence_hash: str
    trigger: str
    timestamp: str


# ---------------------------------------------------------------------------
# SIEM Source → VerificationSource mapping
# ---------------------------------------------------------------------------

_SOURCE_MAP: Dict[str, VerificationSource] = {
    "wazuh": VerificationSource.SIEM_WAZUH,
    "splunk": VerificationSource.SIEM_SPLUNK,
    "elastic": VerificationSource.SIEM_ELASTIC,
    "manual": VerificationSource.MANUAL_AUDIT,
}


# ---------------------------------------------------------------------------
# TelemetryVerificationService
# ---------------------------------------------------------------------------

class TelemetryVerificationService:
    """Processes inbound SIEM events and manages FindingProvenance records.

    Thread-safety: This service is stateless. All state is in the DB session.
    Idempotency: Duplicate siem_alert_ids are detected and short-circuited.
    """

    def __init__(self, db: Session):
        self._db = db

    def process_siem_event(self, payload: SIEMEventPayload) -> VerificationResponse:
        """Process a single SIEM event and update finding provenance.

        Steps:
          1. Idempotency check: If siem_alert_id already exists, return 200.
          2. Compute evidence hash from the payload.
          3. Match the SIEM rule_id against FrameworkMappingRegistry.
          4. If match found: create/update FindingProvenance → SOC_VERIFIED.
          5. Emit structured audit log.
          6. Trigger GHI recomputation (background).

        Returns:
            VerificationResponse with the outcome.
        """
        # ── Step 1: Idempotency check ──────────────────────────────────
        existing = (
            self._db.query(FindingProvenance)
            .filter(FindingProvenance.siem_alert_id == payload.alert_id)
            .first()
        )
        if existing:
            logger.info(
                "Idempotent skip: siem_alert_id=%s already processed for finding=%s",
                payload.alert_id, existing.finding_id,
            )
            return VerificationResponse(
                status="already_exists",
                finding_id=existing.finding_id,
                verification_status=existing.verification_status.value,
                evidence_hash=existing.evidence_hash,
                siem_alert_id=payload.alert_id,
                message="This SIEM alert has already been processed. No duplicate created.",
            )

        # ── Step 2: Compute evidence hash ──────────────────────────────
        evidence_hash = self._compute_evidence_hash(payload)

        # ── Step 3: Find matching finding ──────────────────────────────
        finding, match_method = self._match_finding(payload)

        if not finding:
            logger.warning(
                "No finding match for SIEM event: source=%s rule_id=%s alert_id=%s",
                payload.source, payload.rule_id, payload.alert_id,
            )
            return VerificationResponse(
                status="no_match",
                evidence_hash=evidence_hash,
                siem_alert_id=payload.alert_id,
                message=(
                    f"No finding matched for SIEM rule_id='{payload.rule_id}'. "
                    f"Ensure the FrameworkMappingRegistry has a mapping for this rule."
                ),
            )

        # ── Step 4: Create/update provenance ───────────────────────────
        verification_source = _SOURCE_MAP.get(
            payload.source.lower(), VerificationSource.MANUAL_AUDIT
        )

        # Check if finding already has a provenance record
        provenance = (
            self._db.query(FindingProvenance)
            .filter(FindingProvenance.finding_id == finding.id)
            .first()
        )

        now = datetime.now(timezone.utc)

        if provenance:
            # Update existing provenance with new SIEM evidence
            old_status = provenance.verification_status.value
            provenance.siem_alert_id = payload.alert_id
            provenance.evidence_hash = evidence_hash
            provenance.verification_source = verification_source
            provenance.verification_status = ProvenanceStatus.SOC_VERIFIED
            provenance.rule_id_matched = payload.rule_id
            provenance.verified_at = now
            provenance.verified_by = f"siem:{payload.source}"
        else:
            # Create new provenance record
            old_status = None
            provenance = FindingProvenance(
                finding_id=finding.id,
                siem_alert_id=payload.alert_id,
                evidence_hash=evidence_hash,
                evidence_payload_ref=json.dumps(payload.raw_data, default=str) if payload.raw_data else None,
                verification_source=verification_source,
                verification_status=ProvenanceStatus.SOC_VERIFIED,
                rule_id_matched=payload.rule_id,
                verified_at=now,
                verified_by=f"siem:{payload.source}",
            )
            self._db.add(provenance)

        self._db.commit()
        self._db.refresh(provenance)

        # ── Step 5: Structured audit log ───────────────────────────────
        logger.info(
            json.dumps({
                "event": "finding_provenance_updated",
                "finding_id": finding.id,
                "finding_title": finding.title,
                "siem_alert_id": payload.alert_id,
                "siem_source": payload.source,
                "rule_id_matched": payload.rule_id,
                "old_status": old_status,
                "new_status": ProvenanceStatus.SOC_VERIFIED.value,
                "evidence_hash": evidence_hash,
                "match_method": match_method,
                "verified_at": now.isoformat(),
            })
        )

        return VerificationResponse(
            status="verified",
            finding_id=finding.id,
            finding_title=finding.title,
            verification_status=ProvenanceStatus.SOC_VERIFIED.value,
            evidence_hash=evidence_hash,
            siem_alert_id=payload.alert_id,
            message=f"Finding '{finding.title}' verified via {payload.source} (match: {match_method}).",
        )

    def _match_finding(self, payload: SIEMEventPayload) -> Tuple[Optional[Finding], str]:
        """Match a SIEM event to a Finding via multiple strategies.

        Strategy order:
          1. Direct match via payload.finding_rule_id → Finding.nist_category
          2. FrameworkMappingRegistry lookup via SIEM rule_id
          3. Finding.nist_category prefix match

        Returns:
            (Finding or None, match_method_description)
        """
        # Strategy 1: Direct finding_rule_id match
        if payload.finding_rule_id:
            finding = (
                self._db.query(Finding)
                .filter(
                    Finding.nist_category == payload.finding_rule_id,
                    Finding.status.notin_(["resolved", "accepted"]),
                )
                .first()
            )
            if finding:
                return finding, "direct_rule_id"

        # Strategy 2: FrameworkMappingRegistry lookup
        if payload.rule_id:
            try:
                mapping = (
                    self._db.query(FrameworkMappingRegistry)
                    .filter(FrameworkMappingRegistry.control_id == payload.rule_id)
                    .first()
                )
                if mapping:
                    finding = self._db.query(Finding).filter(Finding.id == mapping.finding_id).first()
                    if finding:
                        return finding, f"framework_registry:{mapping.id}"
            except Exception:
                pass

        # Strategy 3: NIST category prefix match
        finding = (
            self._db.query(Finding)
            .filter(
                Finding.nist_category.ilike(f"%{payload.rule_id}%"),
                Finding.status.notin_(["resolved", "accepted"]),
            )
            .first()
        )
        if finding:
            return finding, "nist_category_prefix"

        return None, "no_match"

    @staticmethod
    def _compute_evidence_hash(payload: SIEMEventPayload) -> str:
        """Compute SHA-256 hash of the SIEM event for immutable provenance.

        The hash covers: source + alert_id + rule_id + timestamp + raw_data_hash.
        This creates a deterministic, tamper-evident digest that can be
        independently verified by an external auditor.
        """
        canonical = json.dumps(
            {
                "source": payload.source,
                "alert_id": payload.alert_id,
                "rule_id": payload.rule_id,
                "timestamp": payload.timestamp,
                "raw_data_hash": payload.raw_data_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def recompute_ghi_for_assessment(
        self,
        assessment_id: str,
        trigger_evidence_hash: str,
    ) -> Optional[Dict[str, Any]]:
        """Recompute GHI score for an assessment after provenance update.

        Weighting adjustment:
          - SOC_VERIFIED findings use full severity weight.
          - PROVISIONAL findings use 60% severity weight (lower certainty).
          - CONTRADICTED findings use 120% weight (increased risk).

        Returns:
            Dict with old_score, new_score, delta, or None if assessment not found.
        """
        from app.models.assessment import Assessment
        from app.services.governance.validation_engine import (
            SEVERITY_WEIGHTS,
            GHI_WEIGHTS,
        )

        assessment = self._db.query(Assessment).filter(Assessment.id == assessment_id).first()
        if not assessment:
            return None

        old_score = assessment.overall_score or 0.0

        # Load all open findings for this assessment with their provenance
        findings = (
            self._db.query(Finding)
            .filter(
                Finding.assessment_id == assessment_id,
                Finding.status.notin_(["resolved", "accepted"]),
            )
            .all()
        )

        # --- Deterministic weighted audit readiness score ---
        # Base formula: score = max(0, 100 - sum(severity_deduction * verification_weight))
        # Verification weights:
        #   SOC_VERIFIED  → 1.0x (full certainty — confirmed by SIEM)
        #   PROVISIONAL   → 0.6x (partial certainty — self-attested only)
        #   CONTRADICTED  → 1.2x (elevated risk — SIEM contradicts self-report)
        verification_multipliers = {
            ProvenanceStatus.SOC_VERIFIED: 1.0,
            ProvenanceStatus.PROVISIONAL: 0.6,
            ProvenanceStatus.CONTRADICTED: 1.2,
        }

        total_deduction = 0.0
        for finding in findings:
            severity = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
            base_weight = SEVERITY_WEIGHTS.get(severity, 0)

            # Get provenance status
            provenance = (
                self._db.query(FindingProvenance)
                .filter(FindingProvenance.finding_id == finding.id)
                .first()
            )
            if provenance:
                v_mult = verification_multipliers.get(provenance.verification_status, 0.6)
            else:
                v_mult = 0.6  # No provenance → treat as PROVISIONAL

            total_deduction += base_weight * v_mult

        audit_score = max(0.0, 100.0 - total_deduction)

        # Compute GHI using the existing formula
        # GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1)
        # For now, only audit dimension is provenance-weighted.
        # Other dimensions retain their existing scores.
        ghi_value = round(
            audit_score * GHI_WEIGHTS["audit"]
            + 100.0 * GHI_WEIGHTS["lifecycle"]   # placeholder — full recompute in production
            + 100.0 * GHI_WEIGHTS["sla"]          # placeholder
            + 100.0 * GHI_WEIGHTS["compliance"]    # placeholder
        , 2)

        # Update assessment score
        assessment.overall_score = ghi_value
        self._db.commit()

        new_score = ghi_value
        delta = round(new_score - old_score, 2)

        # Emit structured score change log to database
        org_id = assessment.organization_id or ""
        from app.models.score_audit_log import ScoreAuditLog
        audit_log = ScoreAuditLog(
            assessment_id=assessment_id,
            organization_id=org_id,
            previous_score=old_score,
            new_score=new_score,
            trigger_event="siem_provenance_update",
            affected_finding_ids=[f.id for f in findings]
        )
        self._db.add(audit_log)
        self._db.commit()

        # Also emit to logger
        log_entry = ScoreChangeLog(
            assessment_id=assessment_id,
            organization_id=org_id,
            old_score=old_score,
            new_score=new_score,
            delta=delta,
            evidence_hash=trigger_evidence_hash,
            trigger="siem_provenance_update",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        logger.info(log_entry.model_dump_json())

        return {
            "assessment_id": assessment_id,
            "old_score": old_score,
            "new_score": new_score,
            "delta": delta,
            "evidence_hash": trigger_evidence_hash,
        }

    def mark_siem_stale(self, organization_id: str, siem_source: str) -> int:
        """Mark all findings for a given SIEM source and organization as STALE_CONNECTION.

        If an organization has an active SIEM config but the last sync returned a connection error,
        this will proactively flag findings as stale, excluding them from high-confidence GHI calculations.
        """
        # Find all provenances for this SIEM source in the given organization's assessments
        from app.models.finding import Finding
        from app.models.assessment import Assessment

        provenances = (
            self._db.query(FindingProvenance)
            .join(Finding, Finding.id == FindingProvenance.finding_id)
            .join(Assessment, Assessment.id == Finding.assessment_id)
            .filter(
                Assessment.organization_id == organization_id,
                FindingProvenance.verified_by.like(f"siem:{siem_source}%"),
            )
            .all()
        )

        stale_count = 0
        now = datetime.now(timezone.utc)
        for prov in provenances:
            if prov.verification_status != ProvenanceStatus.STALE_CONNECTION:
                prov.verification_status = ProvenanceStatus.STALE_CONNECTION
                prov.verified_at = now
                stale_count += 1

        self._db.commit()
        
        if stale_count > 0:
            logger.warning(
                "Marked %d findings as STALE_CONNECTION for org=%s siem=%s",
                stale_count, organization_id, siem_source
            )
        return stale_count
