"""
Control Verification Service
Deterministic business logic for transitioning control verification states.
LLMs are NOT used in this path. All transitions are rule-based and logged.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.verification import (
    VerificationResult,
    ControlEvidence,
    VerificationAuditLog,
    VerificationState,
    VerificationConfidence,
)
from app.models.telemetry_event import TelemetryEvent


class VerificationService:
    """Service handling strict deterministic rule-based verification of controls."""

    def __init__(self, db: Session, organization_id: str):
        self.db = db
        self.organization_id = organization_id

    def _audit_state_change(
        self,
        result: VerificationResult,
        new_state: VerificationState,
        reason: str,
        confidence: VerificationConfidence = VerificationConfidence.LOW
    ) -> None:
        """Immutably log any state transition in VerificationResult."""
        previous_state = result.state

        if previous_state == new_state and result.confidence_level == confidence:
            return  # No state change

        # Update result
        result.state = new_state
        result.confidence_level = confidence

        # Create audit log
        audit = VerificationAuditLog(
            verification_result_id=result.id,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason,
        )
        self.db.add(audit)
        
        # Flush to ensure relationships resolve
        self.db.flush()

    def get_or_create_result(self, control_id: str) -> VerificationResult:
        """Get the current verification result or create a NOT_VERIFIED stub."""
        result = self.db.query(VerificationResult).filter(
            and_(
                VerificationResult.organization_id == self.organization_id,
                VerificationResult.control_id == control_id
            )
        ).first()

        if not result:
            result = VerificationResult(
                organization_id=self.organization_id,
                control_id=control_id,
                state=VerificationState.NOT_VERIFIED,
                confidence_level=VerificationConfidence.LOW,
            )
            self.db.add(result)
            self.db.flush()

        return result

    def ingest_telemetry(
        self,
        control_id: str,
        telemetry_event_id: Optional[str] = None,
        connector_id: Optional[str] = None,
        status: str = "PASS",
        evidence_payload: Optional[Dict[str, Any]] = None,
    ) -> VerificationResult:
        """
        Process a new telemetry signal and re-verify the control.
        A single PASS from a connector is sufficient to verify the control.
        """
        result = self.get_or_create_result(control_id)

        # 1. Record the evidence
        evidence = ControlEvidence(
            verification_result_id=result.id,
            telemetry_event_id=telemetry_event_id,
            connector_id=connector_id,
            status=status,
            evidence_payload=evidence_payload or {},
        )
        self.db.add(evidence)
        self.db.flush()

        # 2. Deterministic Verification Logic
        # Look at all recorded evidence for this control.
        all_evidence = self.db.query(ControlEvidence).filter(
            ControlEvidence.verification_result_id == result.id
        ).all()

        has_pass = any(e.status.upper() == "PASS" for e in all_evidence)

        if has_pass:
            # We have hard telemetry evidence passing the control.
            self._audit_state_change(
                result=result,
                new_state=VerificationState.VERIFIED,
                reason=f"Telemetry event {telemetry_event_id or 'unknown'} reported PASS",
                confidence=VerificationConfidence.HIGH
            )
        else:
            # If all evidence fails, the control might degrade.
            if result.state == VerificationState.VERIFIED:
                self._audit_state_change(
                    result=result,
                    new_state=VerificationState.NOT_VERIFIED,
                    reason=f"Telemetry event {telemetry_event_id or 'unknown'} reported {status}",
                    confidence=VerificationConfidence.LOW
                )

        self.db.commit()
        self.db.refresh(result)
        return result

    def attest_control(self, control_id: str, user_id: str, reason: str = "Manual Attestation") -> VerificationResult:
        """
        Manually self-attest a control.
        This operates strictly as SELF_ATTESTED with LOW/MEDIUM confidence, never VERIFIED.
        """
        result = self.get_or_create_result(control_id)

        # Deterministic Verification Logic for Attestation
        # If it's already mathematically VERIFIED, do not downgrade or override it with an attestation.
        if result.state == VerificationState.VERIFIED:
            return result
        
        self._audit_state_change(
            result=result,
            new_state=VerificationState.SELF_ATTESTED,
            reason=f"User {user_id} attested: {reason}",
            confidence=VerificationConfidence.MEDIUM
        )

        self.db.commit()
        self.db.refresh(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """
        Get rollup metrics for the Trust Dashboard.
        """
        results = self.db.query(VerificationResult).filter(
            VerificationResult.organization_id == self.organization_id
        ).all()

        summary = {
            "total_controls": len(results),
            "verified": sum(1 for r in results if r.state == VerificationState.VERIFIED),
            "partial": sum(1 for r in results if r.state == VerificationState.PARTIAL),
            "self_attested": sum(1 for r in results if r.state == VerificationState.SELF_ATTESTED),
            "not_verified": sum(1 for r in results if r.state == VerificationState.NOT_VERIFIED),
            "high_confidence": sum(1 for r in results if r.confidence_level == VerificationConfidence.HIGH),
        }

        # Include detailed lists
        summary["details"] = [
            {
                "control_id": r.control_id,
                "state": r.state.value,
                "confidence_level": r.confidence_level.value,
                "last_verified_at": r.last_verified_at.isoformat() if r.last_verified_at else None,
            }
            for r in results
        ]

        return summary
