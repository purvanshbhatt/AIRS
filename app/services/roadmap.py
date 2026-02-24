"""
AIRS Roadmap Generator Service

Generates deterministic 30/60/90 day remediation roadmaps based on:
- Finding severity (critical → 30 day, high → 60 day, medium/low → 90 day)
- Remediation effort (low, medium, high)
- Impact score (derived from severity and affected techniques)
- Dependencies between controls

Output is structured for executive presentation with clear deliverables.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RoadmapItem:
    """Enhanced roadmap item with detailed metadata."""
    id: str
    title: str
    action: str
    priority: str  # critical, high, medium, low
    phase: str  # "30", "60", "90"
    # Enterprise timeline labels (Task 3: Executive Roadmap)
    timeline_label: str = "Immediate"  # Immediate | Near-term | Strategic
    timeline_range: str = "0–30 days"   # Human-readable range
    effort: str = "medium"  # low, medium, high  (Implementation Effort)
    effort_hours: str = ""  # Estimated hours range
    # Risk Reduction Impact (effort-vs-impact matrix)
    risk_impact: str = "medium"  # low | medium | high
    domain: Optional[str] = None
    finding_id: Optional[str] = None
    nist_category: Optional[str] = None
    owner: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    milestones: List[str] = field(default_factory=list)
    success_criteria: Optional[str] = None
    status: str = "not_started"


# Effort estimates in hours
EFFORT_ESTIMATES = {
    "low": "4-16 hours",
    "medium": "2-5 days",
    "high": "1-4 weeks"
}

# Suggested owners by domain
DOMAIN_OWNERS = {
    "telemetry_logging": "Security Operations",
    "detection_coverage": "Security Operations",
    "identity_visibility": "Identity & Access Management",
    "ir_process": "Incident Response Team",
    "resilience": "IT Operations / Backup Admin"
}

# Default milestones by effort level
DEFAULT_MILESTONES = {
    "low": ["Plan approved", "Implementation complete", "Validation done"],
    "medium": ["Plan approved", "Resources allocated", "Implementation 50%", "Testing complete"],
    "high": ["Business case approved", "Vendor/tool selected", "POC complete", "Rollout 50%", "Full deployment"]
}

# Success criteria templates
SUCCESS_CRITERIA = {
    "TL-001": "Log retention extended to 90+ days with verification",
    "TL-002": "SIEM deployed with all critical log sources connected",
    "TL-003": "95%+ endpoint coverage for log collection",
    "TL-004": "Cloud audit logs flowing to SIEM",
    "TL-005": "All authentication events logged and alerting configured",
    "DC-001": "95%+ EDR agent coverage across all endpoints",
    "DC-002": "100% coverage on critical assets, 80%+ overall",
    "DC-003": "Network monitoring deployed at key segments",
    "DC-004": "Automated signature updates with weekly custom rule review",
    "DC-005": "Email security gateway with phishing detection active",
    "DC-006": "24-hour SLA for alert triage with documented process",
    "IV-001": "100% MFA coverage for all admin accounts",
    "IV-002": "100% MFA coverage for all users",
    "IV-003": "Complete privileged account inventory with quarterly review process",
    "IV-004": "Service account inventory with rotation schedule",
    "IV-005": "PAM solution deployed for credential vaulting and JIT access",
    "IR-001": "Playbooks documented for top 5 incident types",
    "IR-002": "Annual playbook validation with documented lessons learned",
    "IR-003": "Quarterly tabletop exercise schedule established",
    "IR-004": "IR team charter with 24/7 on-call rotation",
    "RS-001": "Quarterly backup restore tests with documented RTO",
    "RS-002": "Immutable backup storage with separate credentials",
    "RS-003": "All critical systems backed up with 3-2-1 rule",
    "RS-004": "RTO reduced to 24 hours for critical systems",
    "RS-005": "DR plan documented and tested annually",
    "RS-006": "Backup admin credentials in separate credential store"
}

# Dependencies between findings
FINDING_DEPENDENCIES = {
    "TL-002": [],  # SIEM is foundational
    "TL-001": ["TL-002"],  # Need SIEM before extending retention
    "TL-003": ["TL-002"],  # Need SIEM to send endpoint logs
    "TL-004": ["TL-002"],  # Need SIEM for cloud logs
    "TL-005": ["TL-002"],  # Auth logging needs centralization
    "DC-001": [],  # EDR is independent
    "DC-003": ["TL-002"],  # NDR benefits from SIEM integration
    "DC-005": [],  # Email security is independent
    "IV-001": [],  # Admin MFA is urgent, no dependencies
    "IV-002": ["IV-001"],  # Org-wide MFA after admin MFA
    "IV-003": ["IV-001"],  # Inventory after MFA in place
    "IV-005": ["IV-003"],  # PAM after account inventory
    "RS-002": ["RS-003"],  # Immutable requires backup existence
    "RS-001": ["RS-003"],  # Can't test non-existent backups
    "RS-005": ["RS-003"],  # DR plan needs backup foundation
}


# Enterprise timeline label mapping from phase key
PHASE_TIMELINE = {
    "30": {"label": "Immediate",  "range": "0\u201330 days"},
    "60": {"label": "Near-term",  "range": "30\u201390 days"},
    "90": {"label": "Strategic",  "range": "90+ days"},
}

# Effort-vs-Impact matrix: maps (severity, effort) -> risk_impact
_RISK_IMPACT_MATRIX: dict = {
    ("critical", "low"):    "high",
    ("critical", "medium"): "high",
    ("critical", "high"):   "high",
    ("high",     "low"):    "high",
    ("high",     "medium"): "high",
    ("high",     "high"):   "medium",
    ("medium",   "low"):    "medium",
    ("medium",   "medium"): "medium",
    ("medium",   "high"):   "low",
    ("low",      "low"):    "medium",
    ("low",      "medium"): "low",
    ("low",      "high"):   "low",
}


def get_phase_for_finding(severity: str, effort: str) -> str:
    """
    Determine roadmap phase based on severity and effort.
    
    Critical/High severity + Low/Medium effort → 30 day
    High severity + High effort → 60 day
    Medium severity → 60 day
    Low severity → 90 day
    """
    severity = severity.lower()
    effort = effort.lower()
    
    if severity == "critical":
        return "30"  # Critical always goes first
    elif severity == "high":
        if effort in ("low", "medium"):
            return "30"
        else:
            return "60"
    elif severity == "medium":
        return "60"
    else:  # low
        return "90"


def generate_roadmap_item(finding: Dict[str, Any]) -> RoadmapItem:
    """
    Generate a detailed roadmap item from a finding.
    
    Args:
        finding: Finding dict with rule_id, title, severity, domain, etc.
        
    Returns:
        RoadmapItem with full metadata
    """
    rule_id = finding.get("rule_id", finding.get("id", ""))
    severity = finding.get("severity", "medium")
    effort = finding.get("remediation_effort", "medium")
    domain_id = finding.get("domain_id", finding.get("domain", ""))
    
    # Determine phase and enterprise timeline label
    phase = get_phase_for_finding(severity, effort)
    timeline = PHASE_TIMELINE.get(phase, {"label": "Immediate", "range": "0\u201330 days"})
    
    # Effort-vs-Impact matrix
    risk_impact = _RISK_IMPACT_MATRIX.get(
        (severity.lower(), effort.lower()), "medium"
    )
    
    # Map severity to priority
    priority_map = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low"
    }
    priority = priority_map.get(severity.lower(), "medium")
    
    # Get recommendation or generate action
    recommendation = finding.get("recommendation", finding.get("action", ""))
    if recommendation:
        # Truncate long recommendations for action
        action = recommendation[:200] + "..." if len(recommendation) > 200 else recommendation
    else:
        action = f"Remediate {finding.get('title', 'finding')}"
    
    # Get dependencies
    dependencies = FINDING_DEPENDENCIES.get(rule_id, [])
    
    # Get success criteria
    success_criteria = SUCCESS_CRITERIA.get(rule_id, f"Finding {rule_id} resolved and verified")
    
    # Get owner
    owner = DOMAIN_OWNERS.get(domain_id, "Security Team")
    
    # Get milestones
    milestones = DEFAULT_MILESTONES.get(effort, DEFAULT_MILESTONES["medium"])
    
    return RoadmapItem(
        id=f"RI-{rule_id}",
        title=finding.get("title", "Untitled Finding"),
        action=action,
        priority=priority,
        phase=phase,
        timeline_label=timeline["label"],
        timeline_range=timeline["range"],
        effort=effort,
        effort_hours=EFFORT_ESTIMATES.get(effort, "Unknown"),
        risk_impact=risk_impact,
        domain=finding.get("domain_name", domain_id),
        finding_id=rule_id,
        nist_category=finding.get("nist_category"),
        owner=owner,
        dependencies=dependencies,
        milestones=milestones,
        success_criteria=success_criteria,
        status="not_started"
    )


def roadmap_item_to_dict(item: RoadmapItem) -> Dict[str, Any]:
    """Convert RoadmapItem to serializable dict."""
    return {
        "id": item.id,
        "title": item.title,
        "action": item.action,
        "priority": item.priority,
        "phase": item.phase,
        "timeline_label": item.timeline_label,
        "timeline_range": item.timeline_range,
        "effort": item.effort,
        "effort_estimate": item.effort_hours,
        "risk_impact": item.risk_impact,
        "domain": item.domain,
        "finding_id": item.finding_id,
        "nist_category": item.nist_category,
        "owner": item.owner,
        "dependencies": item.dependencies,
        "milestones": item.milestones,
        "success_criteria": item.success_criteria,
        "status": item.status
    }


def generate_detailed_roadmap(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a complete 30/60/90 day roadmap from findings.
    
    Args:
        findings: List of finding dicts from FindingsEngine
        
    Returns:
        Detailed roadmap with phases and items
    """
    # Generate roadmap items for all findings
    items = [generate_roadmap_item(f) for f in findings]
    
    # Group by phase
    phases = {
        "30": [],
        "60": [],
        "90": []
    }
    
    for item in items:
        if item.phase in phases:
            phases[item.phase].append(item)
    
    # Sort within each phase by priority (critical first)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    
    for phase_key in phases:
        phases[phase_key].sort(key=lambda x: priority_order.get(x.priority, 4))
    
    # Helper to compute effort hours from item effort levels
    def sum_effort_hours(phase_items: List[RoadmapItem]) -> int:
        effort_hours_map = {"low": 8, "medium": 24, "high": 80}  # Conservative estimates
        return sum(effort_hours_map.get(i.effort, 24) for i in phase_items)

    # Build structured output with enterprise timeline labels
    # phases is a DICT keyed by "day30", "day60", "day90" for frontend compatibility
    result = {
        "phases": {
            "day30": {
                "title": "Immediate — 0–30 Days",
                "name": "Immediate (0–30 Days)",
                "description": "Critical risk-reduction and quick wins — highest Control Effectiveness ROI",
                "item_count": len(phases["30"]),
                "effort_hours": sum_effort_hours(phases["30"]),
                "items": [roadmap_item_to_dict(item) for item in phases["30"]]
            },
            "day60": {
                "title": "Near-term — 30–90 Days",
                "name": "Near-term (30–90 Days)",
                "description": "Foundation building, Governance Maturity improvements, and process hardening",
                "item_count": len(phases["60"]),
                "effort_hours": sum_effort_hours(phases["60"]),
                "items": [roadmap_item_to_dict(item) for item in phases["60"]]
            },
            "day90": {
                "title": "Strategic — 90+ Days",
                "name": "Strategic (90+ Days)",
                "description": "Operational Resilience advancement and long-term Risk Posture optimisation",
                "item_count": len(phases["90"]),
                "effort_hours": sum_effort_hours(phases["90"]),
                "items": [roadmap_item_to_dict(item) for item in phases["90"]]
            }
        },
        "summary": {
            "total_items": len(items),
            "day30_count": len(phases["30"]),
            "day60_count": len(phases["60"]),
            "day90_count": len(phases["90"]),
            # Fields expected by RoadmapTab UI
            "critical_items": sum(1 for i in items if i.priority == "critical"),
            "quick_wins": sum(1 for i in items if i.effort == "low" and i.priority in ("critical", "high")),
            "total_effort_hours": sum_effort_hours(phases["30"]) + sum_effort_hours(phases["60"]) + sum_effort_hours(phases["90"]),
            "total_risk_reduction": "High" if any(i.priority == "critical" for i in items) else "Medium",
            "by_priority": {
                "critical": sum(1 for i in items if i.priority == "critical"),
                "high": sum(1 for i in items if i.priority == "high"),
                "medium": sum(1 for i in items if i.priority == "medium"),
                "low": sum(1 for i in items if i.priority == "low")
            },
            "by_effort": {
                "low": sum(1 for i in items if i.effort == "low"),
                "medium": sum(1 for i in items if i.effort == "medium"),
                "high": sum(1 for i in items if i.effort == "high")
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    }
    
    return result


def generate_simple_roadmap(findings: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """
    Generate simplified roadmap for legacy compatibility.
    
    Args:
        findings: List of findings sorted by severity
        
    Returns:
        Simple dict with day30, day60, day90 lists
    """
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_findings = sorted(
        findings,
        key=lambda f: severity_order.get(f.get("severity", "medium").lower(), 4)
    )
    
    roadmap = {"day30": [], "day60": [], "day90": []}
    
    critical = [f for f in sorted_findings if f.get("severity", "").lower() == "critical"]
    high = [f for f in sorted_findings if f.get("severity", "").lower() == "high"]
    medium = [f for f in sorted_findings if f.get("severity", "").lower() == "medium"]
    low = [f for f in sorted_findings if f.get("severity", "").lower() == "low"]
    
    # 30-day: Critical findings (up to 5)
    for f in critical[:5]:
        roadmap["day30"].append({
            "title": f.get("title", ""),
            "action": f.get("recommendation", "Address immediately"),
            "severity": f.get("severity", "critical"),
            "domain": f.get("domain_name", f.get("domain", ""))
        })
    
    # Add high findings with low effort to 30-day
    for f in high[:3]:
        if f.get("remediation_effort", "medium") == "low":
            roadmap["day30"].append({
                "title": f.get("title", ""),
                "action": f.get("recommendation", "Address within 30 days"),
                "severity": f.get("severity", "high"),
                "domain": f.get("domain_name", f.get("domain", ""))
            })
    
    # 60-day: High findings (up to 5)
    for f in high[:5]:
        if f.get("remediation_effort", "medium") != "low":  # Skip ones already in 30-day
            roadmap["day60"].append({
                "title": f.get("title", ""),
                "action": f.get("recommendation", "Remediate within 60 days"),
                "severity": f.get("severity", "high"),
                "domain": f.get("domain_name", f.get("domain", ""))
            })
    
    # 90-day: Medium and Low (up to 5 total)
    remaining = (medium + low)[:5]
    for f in remaining:
        roadmap["day90"].append({
            "title": f.get("title", ""),
            "action": f.get("recommendation", "Plan for remediation"),
            "severity": f.get("severity", "medium"),
            "domain": f.get("domain_name", f.get("domain", ""))
        })
    
    return roadmap
