"""
VerificationService — SIEM-Corroborated Finding Verification.

Cross-references ResilAI's deterministic findings against raw SIEM log
evidence from Wazuh and Splunk. Findings corroborated by live telemetry
receive a 'SOC-Verified' badge; self-attested-only findings are 'Provisional'.

All verification logic is deterministic — no LLM calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.verification import (
    VerificationStatusEnum,
    VerificationResultSchema,
    AuditTrailFindingSchema,
    AuditTrailSchema,
)

logger = logging.getLogger("airs.verification")


# ---------------------------------------------------------------------------
# Rule-to-SIEM mapping: which SIEM check applies to which finding rule
# ---------------------------------------------------------------------------

_RULE_SIEM_MAP: Dict[str, Dict[str, Any]] = {
    # EDR Coverage findings → Splunk EDR telemetry + Wazuh agent count
    "DC-001": {"siem": "splunk", "check": "edr", "fallback_siem": "wazuh", "fallback_check": "agents"},
    "DC-002": {"siem": "splunk", "check": "edr", "fallback_siem": "wazuh", "fallback_check": "agents"},
    # MFA findings → Splunk MFA logs
    "IV-001": {"siem": "splunk", "check": "mfa"},
    "IV-002": {"siem": "splunk", "check": "mfa"},
    # Centralized Logging → Splunk logging health
    "TL-002": {"siem": "splunk", "check": "logging"},
    # Vulnerability-related → Wazuh vulnerability feed
    "TL-001": {"siem": "wazuh", "check": "vulnerabilities"},
    # Aggregate rules that check domain scores — also map to SIEM where possible
    "AGG-001": {"siem": "splunk", "check": "logging"},
    "AGG-002": {"siem": "splunk", "check": "mfa"},
}


class VerificationService:
    """Deterministic SIEM-corroborated finding verification.

    Cross-references internal findings against canonical normalized
    evidence persisted by the EvidenceOrchestrator
    (Priority-1 invariant — see ADR-009). The Verification Engine
    does not issue live SIEM queries per request; all SIEM intent
    flows through `ConnectorManager.sync_connector` (which drives
    `SplunkConnector` / `WazuhConnector`), and the resulting
    `NormalizedEvidenceRecord` rows are read here.

    Only Wazuh retains a legacy direct-client fallback because the
    WazuhClient is already a stable live API driver; Splunk relies
    exclusively on the canonical SplunkConnector → SplunkMCPClient
    pipeline and is never invoked live by this class.
    """

    def __init__(
        self,
        wazuh_client: Optional[Any] = None,
        db: Optional[Any] = None,
    ):
        self._wazuh = wazuh_client
        self._db = db
        self._wazuh_cache: Dict[str, Any] = {}
        self._microsoft_cache: Optional[Dict[str, Any]] = None

    def _get_latest_microsoft_telemetry(self) -> Optional[Dict[str, Any]]:
        """Fetch the latest Microsoft telemetry payload from database."""
        if self._microsoft_cache is not None:
            return self._microsoft_cache

        if not self._db:
            return None

        from app.models.telemetry_event import TelemetryEvent
        import json

        event = (
            self._db.query(TelemetryEvent)
            .filter(TelemetryEvent.source_system == "microsoft")
            .order_by(TelemetryEvent.created_at.desc())
            .first()
        )
        if event and event.payload:
            try:
                if isinstance(event.payload, str):
                    self._microsoft_cache = json.loads(event.payload)
                else:
                    self._microsoft_cache = event.payload
            except Exception:
                self._microsoft_cache = {}
        else:
            self._microsoft_cache = {}

        return self._microsoft_cache

    def _evaluate_microsoft_evidence(self, finding: Any, payload: Dict[str, Any]) -> Optional[VerificationResultSchema]:
        """Evaluate a finding against Microsoft telemetry payload."""
        rule_id = finding.rule_id
        summary = payload.get("summary", {})
        now = datetime.now(timezone.utc).isoformat()

        if rule_id in ("DC-001", "DC-002"):
            edr_cov = summary.get("edr_coverage_pct", 100.0)
            threshold = 80.0 if rule_id == "DC-001" else 50.0
            if edr_cov < threshold:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED,
                    evidence_summary=f"SIEM-Verified (Microsoft Defender/Intune): EDR coverage is {edr_cov:.1f}%, which is below the threshold of {threshold}%.",
                    siem_source="microsoft",
                    siem_query_used="GET /deviceManagement/managedDevices",
                    event_count=summary.get("total_devices", 0),
                    log_event_ids=[d.get("device_id") for d in payload.get("intune_devices", [])[:5] if d.get("device_id")],
                    verified_at=now,
                )
            else:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.CONTRADICTED,
                    evidence_summary=f"SIEM contradiction (Microsoft Defender/Intune): EDR coverage is {edr_cov:.1f}%, which is adequate (>=90%).",
                    siem_source="microsoft",
                    siem_query_used="GET /deviceManagement/managedDevices",
                    event_count=summary.get("total_devices", 0),
                    log_event_ids=[],
                    verified_at=now,
                )

        elif rule_id in ("IV-001", "IV-002"):
            mfa_rate = summary.get("mfa_enforced_rate_pct", 100.0)
            if mfa_rate < 100.0:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED,
                    evidence_summary=f"SIEM-Verified (Microsoft Entra ID): MFA enforcement rate is {mfa_rate:.1f}%. Identity security is incomplete.",
                    siem_source="microsoft",
                    siem_query_used="GET /identity/conditionalAccess/policies",
                    event_count=summary.get("total_users", 0),
                    log_event_ids=[u.get("user_id") for u in payload.get("entra_users", [])[:5] if u.get("user_id")],
                    verified_at=now,
                )
            else:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.CONTRADICTED,
                    evidence_summary=f"SIEM contradiction (Microsoft Entra ID): MFA is 100% enforced via Conditional Access policies.",
                    siem_source="microsoft",
                    siem_query_used="GET /identity/conditionalAccess/policies",
                    event_count=summary.get("total_users", 0),
                    log_event_ids=[],
                    verified_at=now,
                )

        elif rule_id == "TL-001":
            high_alerts = summary.get("active_high_severity_alerts", 0)
            if high_alerts > 0:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED,
                    evidence_summary=f"SIEM-Verified (Microsoft Defender): Found {high_alerts} active high-severity security alerts.",
                    siem_source="microsoft",
                    siem_query_used="GET /security/alerts_v2",
                    event_count=high_alerts,
                    log_event_ids=[a.get("alert_id") for a in payload.get("defender_alerts", [])[:5] if a.get("alert_id")],
                    verified_at=now,
                )
            else:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.CONTRADICTED,
                    evidence_summary="SIEM contradiction (Microsoft Defender): 0 active high-severity alerts detected.",
                    siem_source="microsoft",
                    siem_query_used="GET /security/alerts_v2",
                    event_count=0,
                    log_event_ids=[],
                    verified_at=now,
                )

        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def verify_finding(self, finding: Any, answers: Optional[Dict[str, Any]] = None) -> VerificationResultSchema:
        """Verify a single finding against SIEM evidence.

        Args:
            finding: A Finding dataclass from the FindingsEngine.
            answers: Optional assessment answers dict for context.

        Returns:
            VerificationResultSchema with the badge status.
        """
        rule_id = finding.rule_id

        # --- NEW PIPELINE: Check NormalizedEvidenceRecord ---
        if self._db:
            from app.models.evidence import NormalizedEvidenceRecord
            from sqlalchemy import desc
            # Find any processed evidence for this control/rule
            evidence = self._db.query(NormalizedEvidenceRecord).filter(
                NormalizedEvidenceRecord.control_id == rule_id
            ).order_by(desc(NormalizedEvidenceRecord.created_at)).first()

            if evidence:
                now = datetime.now(timezone.utc).isoformat()
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED if evidence.severity != "critical" else VerificationStatusEnum.CONTRADICTED,
                    evidence_summary=f"SIEM-Verified via Adapter: Found normalized evidence hash {evidence.evidence_hash}.",
                    siem_source="evidence_adapter",
                    siem_query_used="NormalizedEvidenceRecord",
                    event_count=1,
                    log_event_ids=[evidence.evidence_hash],
                    verified_at=now,
                )

        # --- LEGACY PIPELINE: Fallback to direct integrations if no adapter evidence ---
        # First, check if Microsoft telemetry is available in database
        ms_payload = self._get_latest_microsoft_telemetry()
        if ms_payload:
            ms_result = self._evaluate_microsoft_evidence(finding, ms_payload)
            if ms_result:
                return ms_result

        mapping = _RULE_SIEM_MAP.get(rule_id)

        if not mapping:
            # No SIEM mapping → Provisional (self-attested only)
            return self._provisional_result(finding, "No SIEM verification mapping exists for this control. Status is based on self-reported questionnaire data only.")

        siem = mapping["siem"]
        check = mapping["check"]

        try:
            if siem == "splunk":
                # Canonical Splunk verification flows through
                # ``ConnectorManager.sync_connector`` →
                # ``SplunkConnector.sync`` → ``SplunkMCPClient.search``
                # → ``EvidenceOrchestrator.ingest_collection_result``
                # → ``NormalizedEvidenceRecord``.
                #
                # The only path that promotes a finding to SOC_VERIFIED
                # is the NormalizedEvidenceRecord branch above. If no
                # such record exists, the candidate SIEM has not been
                # corroborated and the result is provisional. No
                # live-Splunk-query fallback is permitted here.
                if mapping.get("fallback_siem") == "wazuh" and self._wazuh:
                    wazuh_result = await self._run_wazuh_check(mapping["fallback_check"])
                    return self._evaluate_wazuh_evidence(finding, wazuh_result, mapping["fallback_check"])
                return self._provisional_result(
                    finding,
                    "Splunk evidence normalized record absent. The Splunk "
                    "Connector has not yet corroborated this control via the "
                    "MCP-backed SplunkConnector sync.",
                )

            elif siem == "wazuh" and self._wazuh:
                result = await self._run_wazuh_check(check)
                return self._evaluate_wazuh_evidence(finding, result, check)

            else:
                return self._provisional_result(finding, f"SIEM '{siem}' is not configured. Finding remains self-attested.")

        except Exception as exc:
            logger.error("Verification failed for rule %s: %s", rule_id, exc)
            return self._connection_error_result(finding, f"SIEM query/connection failed: {exc}. Status could not be verified.")

    async def verify_all_findings(self, findings: List[Any], answers: Optional[Dict[str, Any]] = None) -> List[VerificationResultSchema]:
        """Batch-verify all findings against SIEM evidence."""
        # Clear caches for a fresh run. Splunk no longer caches — it
        # reads ``NormalizedEvidenceRecord`` rows directly which the
        # database caches transparently.
        self._wazuh_cache.clear()

        results = []
        for finding in findings:
            result = await self.verify_finding(finding, answers)
            results.append(result)
        return results

    def generate_audit_trail(
        self,
        findings: List[Any],
        verification_results: List[VerificationResultSchema],
        scores: Optional[Dict[str, Any]] = None,
        assessment_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        previous_ghi: Optional[float] = None,
    ) -> AuditTrailSchema:
        """Generate a tamper-evident JSON audit trail.

        The integrity_hash is a SHA-256 of the canonical JSON representation
        of the scores + findings payload, enabling external auditors to
        verify that the trail has not been modified.
        """
        now = datetime.now(timezone.utc).isoformat()
        current_ghi = None
        overall_score = None

        if scores:
            overall_score = scores.get("overall_score")
            current_ghi = scores.get("ghi") or scores.get("overall_score")

        # Build finding entries
        trail_findings: List[AuditTrailFindingSchema] = []
        for finding, vr in zip(findings, verification_results):
            severity_value = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
            trail_findings.append(AuditTrailFindingSchema(
                rule_id=finding.rule_id,
                title=finding.title,
                severity=severity_value,
                domain_id=finding.domain_id,
                verification_status=vr.status,
                evidence_summary=vr.evidence_summary,
                siem_source=vr.siem_source,
                log_event_ids=vr.log_event_ids,
                verified_at=vr.verified_at,
            ))

        # Counts
        soc_verified = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.SOC_VERIFIED)
        provisional = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.PROVISIONAL)
        contradicted = sum(1 for vr in verification_results if vr.status == VerificationStatusEnum.CONTRADICTED)

        # Compute integrity hash
        ghi_delta = None
        if current_ghi is not None and previous_ghi is not None:
            ghi_delta = round(current_ghi - previous_ghi, 2)

        hash_payload = {
            "assessment_id": assessment_id,
            "overall_score": overall_score,
            "ghi_current": current_ghi,
            "ghi_previous": previous_ghi,
            "findings": [
                {"rule_id": f.rule_id, "severity": f.severity, "status": f.verification_status.value}
                for f in trail_findings
            ],
        }
        canonical = json.dumps(hash_payload, sort_keys=True, separators=(",", ":"))
        integrity_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        return AuditTrailSchema(
            integrity_hash=integrity_hash,
            generated_at=now,
            assessment_id=assessment_id,
            organization_id=organization_id,
            ghi_score_current=current_ghi,
            ghi_score_previous=previous_ghi,
            ghi_score_delta=ghi_delta,
            overall_score=overall_score,
            findings=trail_findings,
            total_findings=len(trail_findings),
            soc_verified_count=soc_verified,
            provisional_count=provisional,
            contradicted_count=contradicted,
        )

    # ------------------------------------------------------------------
    # SIEM query runners (with caching)
    # ------------------------------------------------------------------

    async def _run_wazuh_check(self, check: str) -> Any:
        """Run a Wazuh evidence check, caching results."""
        if check in self._wazuh_cache:
            return self._wazuh_cache[check]

        if check == "agents":
            result = await self._wazuh.get_agent_status()
        elif check == "vulnerabilities":
            result = await self._wazuh.get_vulnerabilities()
        else:
            result = None

        self._wazuh_cache[check] = result
        return result

    # ------------------------------------------------------------------
    # Evidence evaluation — deterministic threshold comparison
    # ------------------------------------------------------------------

    def _evaluate_wazuh_evidence(self, finding: Any, wazuh_result: Any, check: str) -> VerificationResultSchema:
        """Evaluate Wazuh evidence and assign verification status."""
        now = datetime.now(timezone.utc).isoformat()

        if wazuh_result is None:
            return self._provisional_result(finding, "Wazuh check returned no data.")

        if check == "agents":
            total = getattr(wazuh_result, "total_agents", 0)
            active = getattr(wazuh_result, "active_agents", 0)
            disconnected = getattr(wazuh_result, "disconnected_agents", 0)
            disconnection_rate = getattr(wazuh_result, "disconnection_rate", 0.0)

            agent_ids = []
            for agent in getattr(wazuh_result, "agent_list", [])[:10]:
                agent_ids.append(f"agent:{getattr(agent, 'agent_id', 'unknown')}")

            if total > 0 and active > 0:
                # EDR/agent coverage confirmed by Wazuh
                coverage_pct = (active / total) * 100 if total > 0 else 0
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED,
                    evidence_summary=(
                        f"Wazuh agent telemetry confirms {active}/{total} agents active "
                        f"({coverage_pct:.0f}% coverage, {disconnection_rate:.1f}% disconnection rate)."
                    ),
                    siem_source="wazuh",
                    siem_query_used="GET /agents",
                    event_count=total,
                    log_event_ids=agent_ids,
                    verified_at=now,
                )
            else:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.CONTRADICTED,
                    evidence_summary="Wazuh reports 0 active agents. No endpoint telemetry detected.",
                    siem_source="wazuh",
                    siem_query_used="GET /agents",
                    event_count=0,
                    log_event_ids=[],
                    verified_at=now,
                )

        elif check == "vulnerabilities":
            total = getattr(wazuh_result, "total_vulnerabilities", 0)
            critical = getattr(wazuh_result, "critical_count", 0)
            high = getattr(wazuh_result, "high_count", 0)

            vuln_ids = []
            for vuln in getattr(wazuh_result, "vulnerabilities", [])[:10]:
                vuln_ids.append(f"cve:{getattr(vuln, 'cve_id', 'unknown')}")

            if total > 0:
                return VerificationResultSchema(
                    finding_id=getattr(finding, "rule_id", None),
                    rule_id=finding.rule_id,
                    title=finding.title,
                    status=VerificationStatusEnum.SOC_VERIFIED,
                    evidence_summary=(
                        f"Wazuh vulnerability scanner confirms {total} vulnerabilities "
                        f"({critical} critical, {high} high). Finding corroborated by live scan data."
                    ),
                    siem_source="wazuh",
                    siem_query_used="GET /vulnerability",
                    event_count=total,
                    log_event_ids=vuln_ids,
                    verified_at=now,
                )
            else:
                return self._provisional_result(finding, "Wazuh vulnerability scanner returned 0 results.")

        return self._provisional_result(finding, f"Unknown Wazuh check type: {check}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _provisional_result(self, finding: Any, reason: str) -> VerificationResultSchema:
        """Create a Provisional verification result."""
        return VerificationResultSchema(
            finding_id=getattr(finding, "rule_id", None),
            rule_id=finding.rule_id,
            title=finding.title,
            status=VerificationStatusEnum.PROVISIONAL,
            evidence_summary=reason,
            siem_source=None,
            siem_query_used=None,
            event_count=0,
            log_event_ids=[],
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

    def _connection_error_result(self, finding: Any, reason: str) -> VerificationResultSchema:
        """Create a Connection Error verification result."""
        return VerificationResultSchema(
            finding_id=getattr(finding, "rule_id", None),
            rule_id=finding.rule_id,
            title=finding.title,
            status=VerificationStatusEnum.CONNECTION_ERROR,
            evidence_summary=reason,
            siem_source=None,
            siem_query_used=None,
            event_count=0,
            log_event_ids=[],
            verified_at=datetime.now(timezone.utc).isoformat(),
        )
