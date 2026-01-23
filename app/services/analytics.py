"""
AIRS Analytics Service

Provides derived analytics from assessment findings:
- Top Attack Paths Enabled (based on missing controls)
- Detection Gaps breakdown
- Response Gaps breakdown
- Framework coverage analysis

All analytics are deterministic - no LLM involvement.
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from app.services.findings import Finding, Severity
from app.core.frameworks import (
    get_technique_coverage,
    get_cis_coverage_summary,
    MITRE_TECHNIQUES,
)


@dataclass
class AttackPath:
    """A potential attack path enabled by missing controls."""
    name: str
    description: str
    risk_level: str  # critical, high, medium
    entry_point: str
    techniques_used: List[str]
    enabling_findings: List[str]
    impact: str


@dataclass
class GapCategory:
    """A category of security gaps."""
    category: str
    gap_count: int
    critical_count: int
    findings: List[Dict]
    recommendation: str


# =============================================================================
# ATTACK PATH DEFINITIONS
# Based on common attack scenarios enabled by missing controls
# =============================================================================

ATTACK_PATH_PATTERNS = {
    "credential_compromise_to_domain_takeover": {
        "name": "Credential Compromise → Domain Takeover",
        "description": "Attackers exploit weak authentication to compromise credentials, "
                      "then use pass-the-hash or privilege escalation to take over the domain.",
        "risk_level": "critical",
        "entry_point": "Phishing or brute force attack",
        "techniques": ["T1078", "T1110", "T1550.002", "T1078.002"],
        "required_findings": ["IV-001", "IV-002", "IV-005"],  # MFA gaps
        "impact": "Complete domain compromise, full access to all systems and data",
    },
    "ransomware_with_no_recovery": {
        "name": "Ransomware with Unrecoverable Data",
        "description": "Ransomware encrypts systems with no viable recovery path due to "
                      "untested or non-immutable backups.",
        "risk_level": "critical",
        "entry_point": "Phishing email or RDP exposure",
        "techniques": ["T1566", "T1486", "T1490"],
        "required_findings": ["RS-001", "RS-002", "RS-003"],  # Backup gaps
        "impact": "Extended downtime (weeks+), potential business failure, ransom payment",
    },
    "undetected_lateral_movement": {
        "name": "Undetected Lateral Movement",
        "description": "Attackers move laterally through the network undetected due to "
                      "lack of endpoint and network visibility.",
        "risk_level": "high",
        "entry_point": "Compromised workstation",
        "techniques": ["T1021", "T1021.001", "T1021.002"],
        "required_findings": ["DC-001", "DC-003"],  # EDR and network monitoring gaps
        "impact": "Attackers establish persistence, exfiltrate data over extended period",
    },
    "data_exfiltration_undetected": {
        "name": "Silent Data Exfiltration",
        "description": "Sensitive data is exfiltrated without detection due to lack of "
                      "network monitoring and logging.",
        "risk_level": "high",
        "entry_point": "Insider threat or compromised account",
        "techniques": ["T1048", "T1567", "T1530"],
        "required_findings": ["DC-003", "TL-002", "TL-004"],  # Network and log gaps
        "impact": "Regulatory fines, reputation damage, competitive disadvantage",
    },
    "log_tampering_cover_up": {
        "name": "Evidence Destruction & Cover-up",
        "description": "Attackers delete or tamper with logs to cover their tracks, "
                      "preventing forensic investigation.",
        "risk_level": "medium",
        "entry_point": "Privileged account compromise",
        "techniques": ["T1070", "T1070.001", "T1562.001"],
        "required_findings": ["TL-001", "TL-002"],  # Log retention and centralization gaps
        "impact": "Unable to determine attack scope, regulatory non-compliance",
    },
    "phishing_to_bec": {
        "name": "Phishing → Business Email Compromise",
        "description": "Successful phishing leads to email account takeover and fraudulent "
                      "wire transfers or data theft.",
        "risk_level": "high",
        "entry_point": "Phishing email",
        "techniques": ["T1566", "T1566.002", "T1539"],
        "required_findings": ["DC-005", "IV-002"],  # Email security and MFA gaps
        "impact": "Financial fraud, typically $50k-$1M per incident",
    },
    "delayed_incident_response": {
        "name": "Delayed Response Amplifies Impact",
        "description": "Lack of IR processes and slow alert triage allows attackers extended "
                      "dwell time to achieve objectives.",
        "risk_level": "medium",
        "entry_point": "Any initial access",
        "techniques": ["T1562"],
        "required_findings": ["IR-001", "IR-004", "DC-006"],  # IR and triage gaps
        "impact": "Median dwell time increases from days to months, greater damage",
    },
}


def analyze_attack_paths(findings: List[Finding]) -> List[Dict[str, Any]]:
    """
    Analyze potential attack paths based on triggered findings.
    
    Returns attack paths sorted by risk level.
    """
    triggered_rule_ids = {f.rule_id for f in findings}
    enabled_paths = []
    
    for path_id, path_def in ATTACK_PATH_PATTERNS.items():
        # Check if any of the required findings are triggered
        matching_findings = [
            rid for rid in path_def["required_findings"]
            if rid in triggered_rule_ids
        ]
        
        # Path is "enabled" if at least 1 of the required findings is present
        if matching_findings:
            # Calculate enablement percentage
            enablement = len(matching_findings) / len(path_def["required_findings"])
            
            enabled_paths.append({
                "id": path_id,
                "name": path_def["name"],
                "description": path_def["description"],
                "risk_level": path_def["risk_level"],
                "entry_point": path_def["entry_point"],
                "techniques": [
                    {
                        "id": tid,
                        "name": MITRE_TECHNIQUES[tid].technique_name if tid in MITRE_TECHNIQUES else tid,
                    }
                    for tid in path_def["techniques"]
                ],
                "enabling_findings": matching_findings,
                "enablement_percentage": round(enablement * 100),
                "impact": path_def["impact"],
            })
    
    # Sort by risk level (critical first) then enablement
    risk_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    enabled_paths.sort(key=lambda p: (risk_order.get(p["risk_level"], 4), -p["enablement_percentage"]))
    
    return enabled_paths


def analyze_detection_gaps(findings: List[Finding]) -> Dict[str, Any]:
    """
    Analyze detection capability gaps.
    
    Categories:
    - Endpoint visibility
    - Network visibility
    - Cloud visibility
    - Log management
    - Alert handling
    """
    detection_rules = {
        "endpoint_visibility": {
            "name": "Endpoint Visibility",
            "rules": ["DC-001", "DC-002"],
            "description": "Ability to detect threats on endpoints",
        },
        "network_visibility": {
            "name": "Network Visibility",
            "rules": ["DC-003"],
            "description": "Ability to detect network-based threats and lateral movement",
        },
        "cloud_visibility": {
            "name": "Cloud Visibility",
            "rules": ["TL-004"],
            "description": "Ability to detect threats in cloud environments",
        },
        "log_collection": {
            "name": "Log Collection & Retention",
            "rules": ["TL-001", "TL-002", "TL-003", "TL-005"],
            "description": "Foundation for threat detection and forensics",
        },
        "detection_currency": {
            "name": "Detection Rule Currency",
            "rules": ["DC-004"],
            "description": "Detection rules updated with current threat intelligence",
        },
        "email_security": {
            "name": "Email Security",
            "rules": ["DC-005"],
            "description": "Protection against phishing and email-borne threats",
        },
        "alert_triage": {
            "name": "Alert Triage",
            "rules": ["DC-006"],
            "description": "Timely response to security alerts",
        },
    }
    
    triggered_rules = {f.rule_id for f in findings}
    gaps = []
    total_gaps = 0
    critical_gaps = 0
    
    for category_id, category_def in detection_rules.items():
        matching = [r for r in category_def["rules"] if r in triggered_rules]
        if matching:
            # Find the findings for this category
            category_findings = [
                {"rule_id": f.rule_id, "title": f.title, "severity": f.severity.value}
                for f in findings if f.rule_id in matching
            ]
            
            is_critical = any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings if f.rule_id in matching)
            
            gaps.append({
                "category": category_def["name"],
                "description": category_def["description"],
                "gap_count": len(matching),
                "is_critical": is_critical,
                "findings": category_findings,
            })
            
            total_gaps += len(matching)
            if is_critical:
                critical_gaps += 1
    
    return {
        "total_gaps": total_gaps,
        "critical_categories": critical_gaps,
        "categories": gaps,
        "coverage_score": max(0, 100 - (total_gaps * 10)),  # Simple coverage metric
    }


def analyze_response_gaps(findings: List[Finding]) -> Dict[str, Any]:
    """
    Analyze incident response capability gaps.
    
    Categories:
    - IR Planning & Documentation
    - IR Team & Roles
    - IR Testing
    - Recovery Capabilities
    """
    response_rules = {
        "ir_planning": {
            "name": "IR Planning & Documentation",
            "rules": ["IR-001", "IR-002"],
            "description": "Documented procedures for handling incidents",
        },
        "ir_team": {
            "name": "IR Team & Communication",
            "rules": ["IR-004"],
            "description": "Defined team with clear roles and escalation paths",
        },
        "ir_testing": {
            "name": "IR Testing & Exercises",
            "rules": ["IR-003"],
            "description": "Regular testing of IR capabilities",
        },
        "backup_recovery": {
            "name": "Backup & Recovery",
            "rules": ["RS-001", "RS-002", "RS-003"],
            "description": "Ability to restore systems and data after an incident",
        },
        "dr_planning": {
            "name": "Disaster Recovery",
            "rules": ["RS-004", "RS-005"],
            "description": "Recovery time objectives and DR documentation",
        },
        "asset_classification": {
            "name": "Asset Classification",
            "rules": ["RS-006"],
            "description": "Prioritization of recovery efforts",
        },
    }
    
    triggered_rules = {f.rule_id for f in findings}
    gaps = []
    total_gaps = 0
    critical_gaps = 0
    
    for category_id, category_def in response_rules.items():
        matching = [r for r in category_def["rules"] if r in triggered_rules]
        if matching:
            category_findings = [
                {"rule_id": f.rule_id, "title": f.title, "severity": f.severity.value}
                for f in findings if f.rule_id in matching
            ]
            
            is_critical = any(f.severity in (Severity.CRITICAL, Severity.HIGH) for f in findings if f.rule_id in matching)
            
            gaps.append({
                "category": category_def["name"],
                "description": category_def["description"],
                "gap_count": len(matching),
                "is_critical": is_critical,
                "findings": category_findings,
            })
            
            total_gaps += len(matching)
            if is_critical:
                critical_gaps += 1
    
    return {
        "total_gaps": total_gaps,
        "critical_categories": critical_gaps,
        "categories": gaps,
        "readiness_score": max(0, 100 - (total_gaps * 12)),  # Response is weighted higher
    }


def analyze_identity_gaps(findings: List[Finding]) -> Dict[str, Any]:
    """
    Analyze identity and access management gaps.
    """
    identity_rules = {
        "mfa": {
            "name": "Multi-Factor Authentication",
            "rules": ["IV-001", "IV-002"],
            "description": "Protection against credential compromise",
        },
        "privileged_access": {
            "name": "Privileged Access Management",
            "rules": ["IV-003", "IV-004", "IV-005"],
            "description": "Control and visibility into privileged accounts",
        },
        "monitoring": {
            "name": "Identity Monitoring",
            "rules": ["IV-006"],
            "description": "Detection of identity-based attacks",
        },
    }
    
    triggered_rules = {f.rule_id for f in findings}
    gaps = []
    
    for category_id, category_def in identity_rules.items():
        matching = [r for r in category_def["rules"] if r in triggered_rules]
        if matching:
            category_findings = [
                {"rule_id": f.rule_id, "title": f.title, "severity": f.severity.value}
                for f in findings if f.rule_id in matching
            ]
            
            gaps.append({
                "category": category_def["name"],
                "description": category_def["description"],
                "gap_count": len(matching),
                "findings": category_findings,
            })
    
    return {
        "total_gaps": len([r for r in ["IV-001", "IV-002", "IV-003", "IV-004", "IV-005", "IV-006"] if r in triggered_rules]),
        "categories": gaps,
    }


def analyze_risk_summary(findings: List[Finding]) -> Dict[str, Any]:
    """
    Generate high-level risk metrics.
    """
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0
    }
    
    for f in findings:
        sev = f.severity.value.lower()
        if sev in severity_counts:
            severity_counts[sev] += 1
            
    # Identify top risks (Critical/High findings)
    # Sort by severity (Critical > High)
    priority_map = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 4
    }
    
    sorted_findings = sorted(
        findings,
        key=lambda x: priority_map.get(x.severity.value.lower(), 5)
    )
    
    top_risks = [f.title for f in sorted_findings[:3]]
    
    # Calculate an aggregate risk score (0-100, lower is better)
    # Simple weighted sum
    weights = {"critical": 10, "high": 5, "medium": 2, "low": 1}
    total_risk_points = sum(weights.get(f.severity.value.lower(), 0) for f in findings)
    
    return {
        "severity_counts": severity_counts,
        "top_risks": top_risks,
        "total_risk_score": total_risk_points,
        "findings_count": len(findings)
    }


def get_full_analytics(findings: List[Finding]) -> Dict[str, Any]:
    """
    Generate complete analytics package for an assessment.
    
    Returns:
        Dict with attack_paths, detection_gaps, response_gaps, identity_gaps,
        framework_summary, and risk_summary.
    """
    # Get rule IDs for framework analysis
    rule_ids = [f.rule_id for f in findings]
    
    # MITRE technique coverage
    technique_coverage = get_technique_coverage(rule_ids)
    
    # CIS control gaps
    cis_coverage = get_cis_coverage_summary(rule_ids)
    
    return {
        "attack_paths": analyze_attack_paths(findings),
        "detection_gaps": analyze_detection_gaps(findings),
        "response_gaps": analyze_response_gaps(findings),
        "identity_gaps": analyze_identity_gaps(findings),
        "risk_summary": analyze_risk_summary(findings),
        "framework_summary": {
            "mitre": {
                "techniques_enabled": technique_coverage["enabled"],
                "total_techniques": technique_coverage["total"],
                "coverage_pct": technique_coverage["coverage_pct"],
                "technique_list": technique_coverage["technique_list"],
            },
            "cis": {
                "controls_missing": cis_coverage["missing"],
                "controls_met": cis_coverage["met"],
                "coverage_pct": cis_coverage["coverage_pct"],
                "ig1_pct": cis_coverage["ig1_pct"],
                "ig2_pct": cis_coverage["ig2_pct"],
                "ig3_pct": cis_coverage["ig3_pct"],
            },
        },
    }
