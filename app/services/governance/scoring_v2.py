"""
GHI Scoring Engine V2 — SIEM Verification Enhancement.

This module extends the deterministic Governance Health Index with SIEM/XDR
context from Wazuh and Splunk. The implementation preserves the existing GHI
formula and applies a 1.2x multiplier only when evidence is verified.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.services.governance.validation_engine import GovernanceHealthIndex, compute_ghi

logger = logging.getLogger("airs.scoring_v2")


@dataclass
class SIEMVerificationContext:
    wazuh_available: bool = False
    wazuh_agents_connected: bool = False
    wazuh_agent_disconnection_rate: float = 0.0
    wazuh_critical_vulns: int = 0
    wazuh_high_vulns: int = 0
    splunk_available: bool = False
    splunk_logging_enabled: bool = False
    splunk_event_count_24h: int = 0
    siem_verified_controls: int = 0
    siem_verification_score: float = 0.0


def evaluate_siem_context(
    wazuh_agent_status: Optional[Dict[str, Any]] = None,
    wazuh_vulns: Optional[Dict[str, Any]] = None,
    splunk_logging_health: Optional[Dict[str, Any]] = None,
) -> SIEMVerificationContext:
    """Derive a SIEMVerificationContext from integration payloads."""
    wazuh_agent_status = wazuh_agent_status or {}
    wazuh_vulns = wazuh_vulns or {}
    splunk_logging_health = splunk_logging_health or {}

    total_agents = int(wazuh_agent_status.get("total_agents", 0) or 0)
    disconnected_agents = int(wazuh_agent_status.get("disconnected_agents", 0) or 0)
    disconnection_rate = float(
        wazuh_agent_status.get("disconnection_rate_percent")
        or wazuh_agent_status.get("disconnection_rate")
        or (disconnected_agents / total_agents * 100 if total_agents else 0.0)
    )
    wazuh_available = total_agents > 0
    wazuh_agents_connected = wazuh_available and disconnection_rate <= 10.0

    critical_vulns = int(wazuh_vulns.get("critical_count", 0) or 0)
    high_vulns = int(wazuh_vulns.get("high_count", 0) or 0)
    splunk_available = bool(splunk_logging_health.get("logging_enabled"))
    splunk_event_count_24h = int(splunk_logging_health.get("event_count_24h", 0) or 0)

    verified_controls = 0
    if wazuh_available and wazuh_agents_connected:
        verified_controls += 1
    if splunk_available:
        verified_controls += 1

    siem_verification_score = verified_controls / 2.0

    return SIEMVerificationContext(
        wazuh_available=wazuh_available,
        wazuh_agents_connected=wazuh_agents_connected,
        wazuh_agent_disconnection_rate=disconnection_rate,
        wazuh_critical_vulns=critical_vulns,
        wazuh_high_vulns=high_vulns,
        splunk_available=splunk_available,
        splunk_logging_enabled=splunk_available,
        splunk_event_count_24h=splunk_event_count_24h,
        siem_verified_controls=verified_controls,
        siem_verification_score=siem_verification_score,
    )


def apply_siem_multiplier(
    base_ghi: GovernanceHealthIndex,
    siem_context: SIEMVerificationContext,
) -> GovernanceHealthIndex:
    """Apply a 1.2x multiplier when any SIEM control is verified."""
    if siem_context.siem_verified_controls > 0:
        final_ghi = min(100.0, base_ghi.ghi * 1.2)
    else:
        final_ghi = base_ghi.ghi

    final_ghi = round(final_ghi, 2)
    if final_ghi >= 90:
        grade = "A"
    elif final_ghi >= 80:
        grade = "B"
    elif final_ghi >= 60:
        grade = "C"
    elif final_ghi >= 40:
        grade = "D"
    else:
        grade = "F"

    return GovernanceHealthIndex(
        ghi=final_ghi,
        dimensions=base_ghi.dimensions,
        weights=base_ghi.weights,
        grade=grade,
    )


# Backwards-compatible alias expected by older test surfaces.
def apply_siem_multipliers(validation_result, siem_evidence: Dict[str, str]):
    """Apply control-based SIEM multipliers to a validation result.

    This helper is kept for compatibility with the earlier implementation.
    """
    audit_score = validation_result.audit_readiness.score
    lifecycle_score = validation_result.lifecycle.score
    sla_score = validation_result.sla.score
    compliance_score = validation_result.compliance.score

    if any(str(status).lower() == "verified" for status in siem_evidence.values()):
        audit_score = min(100.0, audit_score * 1.2)

    return compute_ghi(
        audit_score=audit_score,
        lifecycle_score=lifecycle_score,
        sla_score=sla_score,
        compliance_score=compliance_score,
    )


def compute_ghi_with_siem(
    db: Session,
    organization_id: str,
    audit_score: float,
    lifecycle_score: float,
    sla_score: float,
    compliance_score: float,
    siem_context: Optional[SIEMVerificationContext] = None,
) -> Dict[str, Any]:
    """Compute GHI with SIEM enhancement and return a response payload."""
    base_ghi = compute_ghi(audit_score, lifecycle_score, sla_score, compliance_score)
    siem_context = siem_context or SIEMVerificationContext()
    enhanced_ghi = apply_siem_multiplier(base_ghi, siem_context)

    return {
        "base_ghi": base_ghi.ghi,
        "final_ghi": enhanced_ghi.ghi,
        "siem_multiplier": 1.2 if siem_context.siem_verified_controls > 0 else 1.0,
        "siem_verified": siem_context.siem_verified_controls > 0,
        "siem_verified_controls": siem_context.siem_verified_controls,
        "grade": enhanced_ghi.grade,
        "dimensions": enhanced_ghi.dimensions,
        "weights": enhanced_ghi.weights,
    }
