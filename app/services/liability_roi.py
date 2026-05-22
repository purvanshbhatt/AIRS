"""
Liability-to-ROI Engine — Quantified Risk Reduction Metrics.

Maps every remediation action to a specific time-saved/cost-saved metric
using industry benchmarks (IBM Cost of a Breach, Ponemon, Mandiant M-Trends).

All calculations are deterministic and auditor-verifiable.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.schemas.verification import RemediationROISchema, PortfolioROISchema

logger = logging.getLogger("airs.liability_roi")

# ---------------------------------------------------------------------------
# Load benchmarks
# ---------------------------------------------------------------------------

_BENCHMARKS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "core", "roi_benchmarks.json"
)


def _load_benchmarks() -> Dict[str, Any]:
    """Load the externalized ROI benchmarks configuration."""
    try:
        with open(_BENCHMARKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load ROI benchmarks from %s: %s. Using defaults.", _BENCHMARKS_PATH, exc)
        return _DEFAULT_BENCHMARKS


_DEFAULT_BENCHMARKS: Dict[str, Any] = {
    "breach_economics": {
        "avg_breach_cost_usd": 4_450_000,
        "avg_dwell_time_days": 204,
        "avg_ransomware_downtime_days": 24,
        "avg_hourly_incident_cost_usd": 1467,
        "avg_containment_time_hours": 73,
    },
    "risk_reduction_factors": {
        "edr_deployment": {"breach_probability_reduction_pct": 0.70},
        "mfa_enforcement": {"breach_probability_reduction_pct": 0.99},
        "immutable_backups": {"ransomware_recovery_reduction_pct": 0.85},
        "centralized_logging": {"dwell_time_reduction_pct": 0.60},
        "tested_ir_plan": {"breach_cost_reduction_pct": 0.54},
        "pam_deployment": {"breach_probability_reduction_pct": 0.50},
        "email_security": {"phishing_reduction_pct": 0.75},
        "network_monitoring": {"lateral_movement_detection_pct": 0.65},
    },
    "remediation_cost_estimates": {
        "low": {"estimated_cost_usd": 5000, "estimated_days": 7},
        "medium": {"estimated_cost_usd": 25000, "estimated_days": 30},
        "high": {"estimated_cost_usd": 75000, "estimated_days": 90},
    },
    "domain_weights_for_liability": {
        "telemetry_logging": 0.15,
        "detection_coverage": 0.25,
        "identity_visibility": 0.30,
        "ir_process": 0.15,
        "resilience": 0.15,
    },
}


# ---------------------------------------------------------------------------
# Rule → Risk Reduction Model mapping
# ---------------------------------------------------------------------------

_RULE_RISK_MODEL: Dict[str, str] = {
    # EDR / Detection Coverage
    "DC-001": "edr_deployment",
    "DC-002": "edr_deployment",
    "DC-003": "network_monitoring",
    "DC-004": "edr_deployment",
    "DC-005": "email_security",
    "DC-006": "edr_deployment",
    # Identity / MFA
    "IV-001": "mfa_enforcement",
    "IV-002": "mfa_enforcement",
    "IV-003": "mfa_enforcement",
    "IV-004": "pam_deployment",
    "IV-005": "pam_deployment",
    # Incident Response
    "IR-001": "tested_ir_plan",
    "IR-002": "tested_ir_plan",
    "IR-003": "tested_ir_plan",
    "IR-004": "tested_ir_plan",
    # Resilience / Backups
    "RS-001": "immutable_backups",
    "RS-002": "immutable_backups",
    "RS-003": "immutable_backups",
    "RS-004": "immutable_backups",
    "RS-005": "immutable_backups",
    "RS-006": "immutable_backups",
    # Telemetry / Logging
    "TL-001": "centralized_logging",
    "TL-002": "centralized_logging",
    "TL-003": "centralized_logging",
    "TL-004": "centralized_logging",
    "TL-005": "centralized_logging",
    # Aggregates
    "AGG-001": "centralized_logging",
    "AGG-002": "mfa_enforcement",
    "AGG-003": "tested_ir_plan",
}

# Severity multipliers for scaling impact
_SEVERITY_MULTIPLIER = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.50,
    "low": 0.25,
    "info": 0.10,
}


class LiabilityROIEngine:
    """Deterministic engine that calculates ROI for each remediation action."""

    def __init__(self, benchmarks: Optional[Dict[str, Any]] = None):
        self._benchmarks = benchmarks or _load_benchmarks()
        self._economics = self._benchmarks["breach_economics"]
        self._risk_factors = self._benchmarks["risk_reduction_factors"]
        self._cost_estimates = self._benchmarks["remediation_cost_estimates"]
        self._domain_weights = self._benchmarks.get("domain_weights_for_liability", {})

    def calculate_roi(self, finding: Any) -> RemediationROISchema:
        """Calculate ROI for a single finding/remediation action.

        Args:
            finding: A Finding dataclass from the FindingsEngine.

        Returns:
            RemediationROISchema with quantified metrics.
        """
        rule_id = finding.rule_id
        severity_str = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        effort = getattr(finding, "remediation_effort", "medium") or "medium"
        domain_id = finding.domain_id

        # Resolve risk model
        risk_model_key = _RULE_RISK_MODEL.get(rule_id, "centralized_logging")
        risk_model = self._risk_factors.get(risk_model_key, {})

        # Core breach economics
        avg_breach_cost = self._economics["avg_breach_cost_usd"]
        avg_dwell_days = self._economics["avg_dwell_time_days"]
        avg_hourly_cost = self._economics["avg_hourly_incident_cost_usd"]
        avg_containment_hours = self._economics["avg_containment_time_hours"]
        avg_ransomware_days = self._economics["avg_ransomware_downtime_days"]

        # Severity multiplier
        sev_mult = _SEVERITY_MULTIPLIER.get(severity_str.lower(), 0.5)

        # Domain weight
        domain_weight = self._domain_weights.get(domain_id, 0.15)

        # Calculate primary risk reduction factor
        # Pick the first available metric from the risk model
        primary_reduction_pct = (
            risk_model.get("breach_probability_reduction_pct")
            or risk_model.get("ransomware_recovery_reduction_pct")
            or risk_model.get("dwell_time_reduction_pct")
            or risk_model.get("breach_cost_reduction_pct")
            or risk_model.get("phishing_reduction_pct")
            or risk_model.get("lateral_movement_detection_pct")
            or 0.30  # default fallback
        )

        # Liability reduction = primary_reduction × severity_mult × domain_weight
        liability_reduction = round(primary_reduction_pct * sev_mult * domain_weight * 100, 2)

        # Cost avoided = avg_breach_cost × primary_reduction × severity_mult × domain_weight
        cost_avoided = round(avg_breach_cost * primary_reduction_pct * sev_mult * domain_weight, 2)

        # Hours saved = containment_hours × primary_reduction × severity_mult
        hours_saved = round(avg_containment_hours * primary_reduction_pct * sev_mult, 2)

        # For backup/resilience findings, add ransomware downtime savings
        if risk_model_key == "immutable_backups":
            ransomware_hours = avg_ransomware_days * 24 * primary_reduction_pct * sev_mult
            hours_saved = round(hours_saved + ransomware_hours, 2)

        # For logging/SIEM findings, add dwell time reduction
        if risk_model_key == "centralized_logging":
            dwell_hours = avg_dwell_days * 24 * primary_reduction_pct * sev_mult * 0.1  # scale factor
            hours_saved = round(hours_saved + dwell_hours, 2)

        # Remediation cost
        cost_info = self._cost_estimates.get(effort.lower(), self._cost_estimates["medium"])
        remediation_cost = cost_info["estimated_cost_usd"]
        time_to_value = cost_info["estimated_days"]

        # ROI percentage
        roi_pct = round(((cost_avoided - remediation_cost) / max(remediation_cost, 1)) * 100, 2)

        # Methodology explanation
        risk_model_name = risk_model_key.replace("_", " ").title()
        methodology = (
            f"Cost avoided = ${avg_breach_cost:,.0f} (avg breach cost, IBM 2023) "
            f"× {primary_reduction_pct:.0%} ({risk_model_name} risk reduction) "
            f"× {sev_mult:.0%} (severity: {severity_str}) "
            f"× {domain_weight:.0%} (domain weight: {domain_id}). "
            f"Remediation cost estimated at ${remediation_cost:,} for {effort}-effort implementation "
            f"over {time_to_value} days. "
            f"ROI = (${cost_avoided:,.0f} - ${remediation_cost:,}) / ${remediation_cost:,} × 100 = {roi_pct:.0f}%."
        )

        return RemediationROISchema(
            finding_rule_id=rule_id,
            finding_title=finding.title,
            severity=severity_str,
            remediation_effort=effort,
            estimated_hours_saved=hours_saved,
            estimated_cost_avoided_usd=cost_avoided,
            liability_reduction_pct=liability_reduction,
            roi_percentage=roi_pct,
            remediation_cost_usd=float(remediation_cost),
            time_to_value_days=time_to_value,
            calculation_methodology=methodology,
        )

    def calculate_portfolio_roi(self, findings: List[Any]) -> PortfolioROISchema:
        """Calculate aggregate ROI across all findings.

        Args:
            findings: List of Finding dataclass instances.

        Returns:
            PortfolioROISchema with total metrics and per-finding breakdown.
        """
        items: List[RemediationROISchema] = []
        total_cost_avoided = 0.0
        total_remediation_cost = 0.0
        total_hours = 0.0

        # Track unique risk models to avoid double-counting liability reduction
        seen_risk_models: set = set()
        weighted_liability_sum = 0.0

        for finding in findings:
            roi = self.calculate_roi(finding)
            items.append(roi)
            total_cost_avoided += roi.estimated_cost_avoided_usd
            total_remediation_cost += roi.remediation_cost_usd
            total_hours += roi.estimated_hours_saved

            # Aggregate liability reduction (cap overlapping controls)
            risk_key = _RULE_RISK_MODEL.get(finding.rule_id, "unknown")
            if risk_key not in seen_risk_models:
                seen_risk_models.add(risk_key)
                weighted_liability_sum += roi.liability_reduction_pct

        # Cap aggregate liability at 95% (can't reduce risk to zero)
        aggregate_liability = min(round(weighted_liability_sum, 2), 95.0)

        total_roi = round(
            ((total_cost_avoided - total_remediation_cost) / max(total_remediation_cost, 1)) * 100, 2
        )

        return PortfolioROISchema(
            total_cost_avoided_usd=round(total_cost_avoided, 2),
            total_remediation_cost_usd=round(total_remediation_cost, 2),
            total_roi_percentage=total_roi,
            total_hours_saved=round(total_hours, 2),
            aggregate_liability_reduction_pct=aggregate_liability,
            items=items,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )
