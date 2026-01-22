"""
AIRS Roadmap Generator

Deterministic 30/60/90 day remediation roadmap generator.
Groups remediations by:
- Effort (low, medium, high)
- Impact (severity + affected systems)
- Dependencies

All roadmap generation is deterministic - no LLM involvement.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from app.services.findings import Finding, Severity


class Effort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Priority(str, Enum):
    IMMEDIATE = "immediate"  # Day 30
    SHORT_TERM = "short_term"  # Day 60
    MEDIUM_TERM = "medium_term"  # Day 90
    LONG_TERM = "long_term"  # Beyond 90


@dataclass
class RoadmapItem:
    """A single remediation item in the roadmap."""
    finding_id: str
    title: str
    action: str
    effort: str
    impact: str
    severity: str
    domain: str
    owner_suggestion: str
    dependencies: List[str] = field(default_factory=list)
    milestones: List[str] = field(default_factory=list)
    success_criteria: str = ""


@dataclass
class RoadmapPhase:
    """A phase (30/60/90 day) of the roadmap."""
    phase_name: str
    phase_days: int
    description: str
    items: List[RoadmapItem] = field(default_factory=list)
    estimated_effort_hours: int = 0
    risk_reduction_score: int = 0


# =============================================================================
# REMEDIATION TEMPLATES
# Detailed action steps for each finding type
# =============================================================================

REMEDIATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # Telemetry & Logging
    "TL-001": {
        "action": "Extend log retention to minimum 90 days (365 recommended for compliance)",
        "milestones": [
            "Audit current log storage costs and capacity",
            "Implement tiered storage (hot/warm/cold)",
            "Configure retention policies",
            "Validate logs are accessible for full retention period",
        ],
        "owner_suggestion": "Security Operations / IT Infrastructure",
        "success_criteria": "Logs from 90+ days ago retrievable within 4 hours",
        "effort_hours": 20,
    },
    "TL-002": {
        "action": "Deploy centralized SIEM/log management platform",
        "milestones": [
            "Evaluate SIEM options (Sentinel, Splunk, Elastic)",
            "Deploy SIEM infrastructure",
            "Configure log forwarding from critical systems",
            "Create baseline detection rules",
            "Establish log monitoring procedures",
        ],
        "owner_suggestion": "Security Operations",
        "success_criteria": "All critical system logs centralized with <1 hour latency",
        "effort_hours": 120,
    },
    "TL-003": {
        "action": "Deploy endpoint logging agents to all workstations and servers",
        "milestones": [
            "Inventory all endpoints requiring logging",
            "Deploy Sysmon or equivalent on Windows",
            "Configure auditd on Linux systems",
            "Forward logs to central SIEM",
        ],
        "owner_suggestion": "IT Operations / Endpoint Team",
        "success_criteria": "95%+ endpoint coverage with validated log ingestion",
        "effort_hours": 40,
    },
    "TL-004": {
        "action": "Enable and centralize cloud audit logging (Azure/AWS/GCP)",
        "milestones": [
            "Enable Azure Activity Log / AWS CloudTrail / GCP Audit Logs",
            "Configure log export to SIEM",
            "Enable identity provider logs (Entra ID, etc.)",
            "Create cloud-specific detection rules",
        ],
        "owner_suggestion": "Cloud Team / Security Operations",
        "success_criteria": "All cloud admin activities logged and queryable",
        "effort_hours": 24,
    },
    "TL-005": {
        "action": "Implement comprehensive authentication event logging",
        "milestones": [
            "Configure Windows Security Event logging (4624, 4625, 4672, etc.)",
            "Enable MFA event logging",
            "Configure application authentication logging",
            "Create alerts for suspicious patterns",
        ],
        "owner_suggestion": "Identity Team / Security Operations",
        "success_criteria": "All auth events logged with <5 minute alerting on anomalies",
        "effort_hours": 16,
    },
    
    # Detection Coverage
    "DC-001": {
        "action": "Expand EDR coverage to 95%+ of endpoints",
        "milestones": [
            "Generate list of unprotected endpoints",
            "Prioritize high-value targets for immediate deployment",
            "Deploy EDR agents via automated mechanism",
            "Validate agent health and telemetry",
        ],
        "owner_suggestion": "Endpoint Security Team",
        "success_criteria": "EDR dashboard shows 95%+ coverage with healthy agents",
        "effort_hours": 40,
    },
    "DC-002": {
        "action": "URGENT: Emergency EDR deployment to critical systems",
        "milestones": [
            "Identify all domain controllers, file servers, and executive endpoints",
            "Deploy EDR within 48 hours to critical systems",
            "Implement compensating controls for remaining gaps",
            "Establish weekly coverage tracking",
        ],
        "owner_suggestion": "CISO / Security Operations",
        "success_criteria": "All critical systems protected within 1 week",
        "effort_hours": 24,
    },
    "DC-003": {
        "action": "Deploy network traffic monitoring (NDR/IDS/IPS)",
        "milestones": [
            "Map network segments requiring visibility",
            "Select and deploy NDR solution or enable NetFlow",
            "Configure monitoring at perimeter and internal chokepoints",
            "Create lateral movement detection rules",
        ],
        "owner_suggestion": "Network Security Team",
        "success_criteria": "East-west traffic visible with anomaly detection active",
        "effort_hours": 80,
    },
    "DC-004": {
        "action": "Implement automated detection rule updates",
        "milestones": [
            "Configure automatic signature updates on all tools",
            "Subscribe to threat intelligence feeds",
            "Establish monthly detection rule review cadence",
        ],
        "owner_suggestion": "Security Operations",
        "success_criteria": "All detection tools auto-update with <24hr latency",
        "effort_hours": 8,
    },
    "DC-005": {
        "action": "Deploy comprehensive email security solution",
        "milestones": [
            "Evaluate email security options (Defender, Proofpoint, Mimecast)",
            "Deploy solution with anti-phishing capabilities",
            "Enable URL and attachment sandboxing",
            "Configure DMARC, DKIM, SPF",
            "Implement user-reported phishing workflow",
        ],
        "owner_suggestion": "Email / Messaging Team",
        "success_criteria": "Phishing simulation shows <10% click rate",
        "effort_hours": 40,
    },
    "DC-006": {
        "action": "Establish 24-hour alert triage SLA",
        "milestones": [
            "Define alert priority levels",
            "Create triage playbooks for common alert types",
            "Implement alert enrichment automation",
            "Staff or contract for coverage gaps",
        ],
        "owner_suggestion": "Security Operations Manager",
        "success_criteria": "95% of alerts triaged within 24 hours",
        "effort_hours": 24,
    },
    
    # Identity Visibility
    "IV-001": {
        "action": "IMMEDIATE: Enable MFA for all administrator accounts",
        "milestones": [
            "Inventory all admin accounts",
            "Enable MFA for Domain Admins within 48 hours",
            "Enable MFA for cloud admins within 1 week",
            "Enable MFA for security tool admins",
        ],
        "owner_suggestion": "Identity Team / CISO",
        "success_criteria": "100% admin accounts have MFA enforced",
        "effort_hours": 8,
    },
    "IV-002": {
        "action": "Expand MFA coverage to all users",
        "milestones": [
            "Plan MFA rollout by department/location",
            "Communicate to users and provide training",
            "Enable MFA with grace period",
            "Enforce MFA and handle exceptions",
        ],
        "owner_suggestion": "Identity Team",
        "success_criteria": "95%+ users with MFA enforced",
        "effort_hours": 40,
    },
    "IV-003": {
        "action": "Create and maintain privileged account inventory",
        "milestones": [
            "Enumerate all privileged accounts across systems",
            "Document account owners and justification",
            "Establish quarterly review process",
            "Create alerts for new privileged accounts",
        ],
        "owner_suggestion": "Identity Governance Team",
        "success_criteria": "Complete inventory with documented owners",
        "effort_hours": 24,
    },
    "IV-004": {
        "action": "Inventory and review all service accounts",
        "milestones": [
            "Discover all service accounts",
            "Document purpose and dependencies",
            "Implement password rotation where possible",
            "Flag unused accounts for removal",
        ],
        "owner_suggestion": "Identity Team / Application Owners",
        "success_criteria": "All service accounts documented with rotation plan",
        "effort_hours": 32,
    },
    "IV-005": {
        "action": "Implement Privileged Access Management (PAM) solution",
        "milestones": [
            "Evaluate PAM solutions (CyberArk, BeyondTrust, Azure PIM)",
            "Deploy PAM for most critical accounts first",
            "Enable session recording for admin access",
            "Implement just-in-time access",
        ],
        "owner_suggestion": "Identity Team",
        "success_criteria": "All domain admin access goes through PAM",
        "effort_hours": 160,
    },
    "IV-006": {
        "action": "Implement identity threat detection",
        "milestones": [
            "Configure alerts for brute force attempts",
            "Enable impossible travel detection",
            "Create alerts for privilege escalation",
            "Tune to reduce false positives",
        ],
        "owner_suggestion": "Security Operations",
        "success_criteria": "Identity attacks detected within 15 minutes",
        "effort_hours": 16,
    },
    
    # IR Process
    "IR-001": {
        "action": "Develop incident response playbooks",
        "milestones": [
            "Create ransomware response playbook",
            "Create phishing/BEC playbook",
            "Create data breach playbook",
            "Create insider threat playbook",
        ],
        "owner_suggestion": "Security Operations Manager",
        "success_criteria": "Playbooks cover 80% of expected incident types",
        "effort_hours": 40,
    },
    "IR-002": {
        "action": "Test IR playbooks with tabletop exercise",
        "milestones": [
            "Schedule tabletop with key stakeholders",
            "Walk through ransomware scenario",
            "Document gaps and lessons learned",
            "Update playbooks based on findings",
        ],
        "owner_suggestion": "CISO / IR Lead",
        "success_criteria": "All playbooks tested within 12 months",
        "effort_hours": 16,
    },
    "IR-003": {
        "action": "Conduct tabletop exercises",
        "milestones": [
            "Schedule quarterly tabletop exercises",
            "Include executives in annual exercise",
            "Document and track improvement actions",
        ],
        "owner_suggestion": "CISO",
        "success_criteria": "4 exercises per year with documented outcomes",
        "effort_hours": 8,
    },
    "IR-004": {
        "action": "Establish IR team with defined roles",
        "milestones": [
            "Define IR roles: Commander, Tech Lead, Comms, Legal",
            "Assign individuals or teams to roles",
            "Create contact matrix with 24/7 info",
            "Conduct role-based training",
        ],
        "owner_suggestion": "CISO",
        "success_criteria": "Documented team with tested communication paths",
        "effort_hours": 16,
    },
    
    # Resilience
    "RS-001": {
        "action": "Implement quarterly backup restore testing",
        "milestones": [
            "Create test plan for critical systems",
            "Schedule quarterly restore tests",
            "Document RTO actuals vs. targets",
            "Address gaps found in testing",
        ],
        "owner_suggestion": "IT Operations / Backup Team",
        "success_criteria": "All critical systems tested annually, RTO met",
        "effort_hours": 24,
    },
    "RS-002": {
        "action": "CRITICAL: Implement immutable/air-gapped backups",
        "milestones": [
            "Select immutable storage solution",
            "Configure immutability policies",
            "Test that backups cannot be deleted by admins",
            "Implement air-gapped copy for most critical data",
        ],
        "owner_suggestion": "Backup Team / Security",
        "success_criteria": "Backups survive simulated ransomware attack",
        "effort_hours": 40,
    },
    "RS-003": {
        "action": "CRITICAL: Implement backup coverage for all critical systems",
        "milestones": [
            "Inventory critical systems requiring backup",
            "Deploy backup agents/policies",
            "Verify successful backup completion",
            "Implement backup monitoring alerts",
        ],
        "owner_suggestion": "IT Operations",
        "success_criteria": "All critical systems in backup with daily verification",
        "effort_hours": 40,
    },
    "RS-004": {
        "action": "Reduce Recovery Time Objective (RTO)",
        "milestones": [
            "Document current RTO for critical systems",
            "Identify bottlenecks in recovery process",
            "Implement improvements (automation, DRaaS, etc.)",
            "Validate reduced RTO with testing",
        ],
        "owner_suggestion": "IT Operations / DR Team",
        "success_criteria": "RTO reduced to 24 hours or business-acceptable level",
        "effort_hours": 80,
    },
    "RS-005": {
        "action": "Document disaster recovery plan",
        "milestones": [
            "Define recovery priorities",
            "Document recovery procedures for each critical system",
            "Identify DR team and responsibilities",
            "Establish DR testing schedule",
        ],
        "owner_suggestion": "IT Operations / Business Continuity",
        "success_criteria": "DR plan documented and tested annually",
        "effort_hours": 40,
    },
    "RS-006": {
        "action": "Classify assets by criticality",
        "milestones": [
            "Create asset classification framework",
            "Work with business to classify systems",
            "Tag systems with classification",
            "Use classification for backup/DR prioritization",
        ],
        "owner_suggestion": "IT Asset Management / Business",
        "success_criteria": "All systems classified with documented RTO/RPO",
        "effort_hours": 24,
    },
}


def calculate_priority(finding: Finding) -> Priority:
    """
    Calculate remediation priority based on severity and effort.
    
    Priority Matrix:
    - IMMEDIATE (Day 30): Critical severity OR High severity + low effort
    - SHORT_TERM (Day 60): High severity + medium effort OR Medium severity + low effort
    - MEDIUM_TERM (Day 90): Medium severity + medium effort OR Low severity
    - LONG_TERM: High effort items regardless of severity (after quick wins)
    """
    severity = finding.severity
    effort = finding.remediation_effort
    
    # Critical findings are always immediate
    if severity == Severity.CRITICAL:
        return Priority.IMMEDIATE
    
    # High severity: prioritize by effort
    if severity == Severity.HIGH:
        if effort == "low":
            return Priority.IMMEDIATE
        elif effort == "medium":
            return Priority.SHORT_TERM
        else:
            return Priority.MEDIUM_TERM
    
    # Medium severity
    if severity == Severity.MEDIUM:
        if effort == "low":
            return Priority.SHORT_TERM
        elif effort == "medium":
            return Priority.MEDIUM_TERM
        else:
            return Priority.LONG_TERM
    
    # Low/Info severity
    return Priority.LONG_TERM


def create_roadmap_item(finding: Finding) -> RoadmapItem:
    """Create a roadmap item from a finding."""
    template = REMEDIATION_TEMPLATES.get(finding.rule_id, {})
    
    return RoadmapItem(
        finding_id=finding.rule_id,
        title=finding.title,
        action=template.get("action", finding.recommendation),
        effort=finding.remediation_effort,
        impact=f"{finding.severity.value.upper()} - {finding.domain_name}",
        severity=finding.severity.value,
        domain=finding.domain_name,
        owner_suggestion=template.get("owner_suggestion", "Security Team"),
        milestones=template.get("milestones", []),
        success_criteria=template.get("success_criteria", ""),
    )


def generate_roadmap(findings: List[Finding]) -> Dict[str, Any]:
    """
    Generate a 30/60/90 day remediation roadmap from findings.
    
    Returns:
        Dict with phases (day30, day60, day90, beyond) and summary stats.
    """
    # Categorize findings by priority
    prioritized: Dict[Priority, List[RoadmapItem]] = {
        Priority.IMMEDIATE: [],
        Priority.SHORT_TERM: [],
        Priority.MEDIUM_TERM: [],
        Priority.LONG_TERM: [],
    }
    
    for finding in findings:
        priority = calculate_priority(finding)
        item = create_roadmap_item(finding)
        prioritized[priority].append(item)
    
    # Sort within each priority by severity then effort
    effort_order = {"low": 0, "medium": 1, "high": 2}
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    
    for items in prioritized.values():
        items.sort(key=lambda i: (severity_order.get(i.severity, 5), effort_order.get(i.effort, 2)))
    
    # Calculate effort hours for each phase
    def calc_effort(items: List[RoadmapItem]) -> int:
        total = 0
        for item in items:
            template = REMEDIATION_TEMPLATES.get(item.finding_id, {})
            total += template.get("effort_hours", 16)  # Default 16 hours
        return total
    
    # Calculate risk reduction (based on severity)
    def calc_risk_reduction(items: List[RoadmapItem]) -> int:
        severity_scores = {"critical": 25, "high": 15, "medium": 10, "low": 5, "info": 2}
        return sum(severity_scores.get(i.severity, 5) for i in items)
    
    phases = {
        "day30": RoadmapPhase(
            phase_name="Day 30 - Immediate Actions",
            phase_days=30,
            description="Critical and quick-win items to address highest risks",
            items=prioritized[Priority.IMMEDIATE],
            estimated_effort_hours=calc_effort(prioritized[Priority.IMMEDIATE]),
            risk_reduction_score=calc_risk_reduction(prioritized[Priority.IMMEDIATE]),
        ),
        "day60": RoadmapPhase(
            phase_name="Day 60 - Short Term",
            phase_days=60,
            description="High-impact items requiring moderate effort",
            items=prioritized[Priority.SHORT_TERM],
            estimated_effort_hours=calc_effort(prioritized[Priority.SHORT_TERM]),
            risk_reduction_score=calc_risk_reduction(prioritized[Priority.SHORT_TERM]),
        ),
        "day90": RoadmapPhase(
            phase_name="Day 90 - Medium Term",
            phase_days=90,
            description="Important improvements requiring sustained effort",
            items=prioritized[Priority.MEDIUM_TERM],
            estimated_effort_hours=calc_effort(prioritized[Priority.MEDIUM_TERM]),
            risk_reduction_score=calc_risk_reduction(prioritized[Priority.MEDIUM_TERM]),
        ),
        "beyond": RoadmapPhase(
            phase_name="Beyond 90 Days",
            phase_days=180,
            description="Strategic initiatives and major infrastructure changes",
            items=prioritized[Priority.LONG_TERM],
            estimated_effort_hours=calc_effort(prioritized[Priority.LONG_TERM]),
            risk_reduction_score=calc_risk_reduction(prioritized[Priority.LONG_TERM]),
        ),
    }
    
    # Summary statistics
    total_items = sum(len(items) for items in prioritized.values())
    total_effort = sum(p.estimated_effort_hours for p in phases.values())
    total_risk_reduction = sum(p.risk_reduction_score for p in phases.values())
    
    return {
        "summary": {
            "total_items": total_items,
            "total_effort_hours": total_effort,
            "total_risk_reduction": total_risk_reduction,
            "critical_items": len([i for i in prioritized[Priority.IMMEDIATE] if i.severity == "critical"]),
            "quick_wins": len([i for i in findings if i.remediation_effort == "low"]),
        },
        "phases": {
            "day30": {
                "name": phases["day30"].phase_name,
                "description": phases["day30"].description,
                "item_count": len(phases["day30"].items),
                "effort_hours": phases["day30"].estimated_effort_hours,
                "risk_reduction": phases["day30"].risk_reduction_score,
                "items": [
                    {
                        "finding_id": i.finding_id,
                        "title": i.title,
                        "action": i.action,
                        "effort": i.effort,
                        "severity": i.severity,
                        "domain": i.domain,
                        "owner": i.owner_suggestion,
                        "milestones": i.milestones,
                        "success_criteria": i.success_criteria,
                    }
                    for i in phases["day30"].items
                ],
            },
            "day60": {
                "name": phases["day60"].phase_name,
                "description": phases["day60"].description,
                "item_count": len(phases["day60"].items),
                "effort_hours": phases["day60"].estimated_effort_hours,
                "risk_reduction": phases["day60"].risk_reduction_score,
                "items": [
                    {
                        "finding_id": i.finding_id,
                        "title": i.title,
                        "action": i.action,
                        "effort": i.effort,
                        "severity": i.severity,
                        "domain": i.domain,
                        "owner": i.owner_suggestion,
                        "milestones": i.milestones,
                        "success_criteria": i.success_criteria,
                    }
                    for i in phases["day60"].items
                ],
            },
            "day90": {
                "name": phases["day90"].phase_name,
                "description": phases["day90"].description,
                "item_count": len(phases["day90"].items),
                "effort_hours": phases["day90"].estimated_effort_hours,
                "risk_reduction": phases["day90"].risk_reduction_score,
                "items": [
                    {
                        "finding_id": i.finding_id,
                        "title": i.title,
                        "action": i.action,
                        "effort": i.effort,
                        "severity": i.severity,
                        "domain": i.domain,
                        "owner": i.owner_suggestion,
                        "milestones": i.milestones,
                        "success_criteria": i.success_criteria,
                    }
                    for i in phases["day90"].items
                ],
            },
            "beyond": {
                "name": phases["beyond"].phase_name,
                "description": phases["beyond"].description,
                "item_count": len(phases["beyond"].items),
                "effort_hours": phases["beyond"].estimated_effort_hours,
                "risk_reduction": phases["beyond"].risk_reduction_score,
                "items": [
                    {
                        "finding_id": i.finding_id,
                        "title": i.title,
                        "action": i.action,
                        "effort": i.effort,
                        "severity": i.severity,
                        "domain": i.domain,
                        "owner": i.owner_suggestion,
                        "milestones": i.milestones,
                        "success_criteria": i.success_criteria,
                    }
                    for i in phases["beyond"].items
                ],
            },
        },
    }
