"""
AIRS Analytics Service

Generates derived analytics from assessment findings:
- Top Attack Paths Enabled (based on missing controls)
- Detection Gaps breakdown
- Response Gaps breakdown
- Risk Distribution analysis

All analytics are deterministic based on finding data.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from app.core.frameworks import get_framework_refs, MITRE_TECHNIQUES, FRAMEWORK_MAPPINGS


@dataclass
class AttackPath:
    """Represents a potential attack path enabled by missing controls."""
    id: str
    name: str
    description: str
    risk_level: str  # critical, high, medium, low
    techniques: List[Dict[str, str]]  # MITRE technique refs
    enabling_gaps: List[str]  # Finding rule_ids that enable this path
    likelihood: int  # 1-5
    impact: int  # 1-5


# Predefined attack paths based on common attack patterns
ATTACK_PATH_DEFINITIONS = {
    "credential_compromise": AttackPath(
        id="AP-001",
        name="Credential Compromise to Domain Takeover",
        description="Attacker gains valid credentials through phishing or brute force, "
                    "then escalates privileges to domain admin due to lack of MFA and PAM controls.",
        risk_level="critical",
        techniques=[
            {"id": "T1566", "name": "Phishing"},
            {"id": "T1078", "name": "Valid Accounts"},
            {"id": "T1550", "name": "Pass the Hash"},
            {"id": "T1098", "name": "Account Manipulation"}
        ],
        enabling_gaps=["IV-001", "IV-002", "IV-005", "DC-005"],
        likelihood=4,
        impact=5
    ),
    "ransomware": AttackPath(
        id="AP-002",
        name="Ransomware with Backup Destruction",
        description="Ransomware deploys across environment, then destroys backups before encrypting systems. "
                    "Recovery is impossible due to lack of immutable backups.",
        risk_level="critical",
        techniques=[
            {"id": "T1486", "name": "Data Encrypted for Impact"},
            {"id": "T1490", "name": "Inhibit System Recovery"},
            {"id": "T1485", "name": "Data Destruction"}
        ],
        enabling_gaps=["RS-002", "RS-003", "RS-006", "DC-001"],
        likelihood=4,
        impact=5
    ),
    "lateral_movement": AttackPath(
        id="AP-003",
        name="Undetected Lateral Movement",
        description="Attacker moves laterally through the network undetected due to lack of NDR "
                    "and endpoint visibility, eventually reaching critical systems.",
        risk_level="high",
        techniques=[
            {"id": "T1021", "name": "Remote Services"},
            {"id": "T1087", "name": "Account Discovery"},
            {"id": "T1069", "name": "Permission Groups Discovery"}
        ],
        enabling_gaps=["DC-003", "TL-003", "TL-002"],
        likelihood=4,
        impact=4
    ),
    "data_exfiltration": AttackPath(
        id="AP-004",
        name="Data Exfiltration via Cloud Services",
        description="Attacker exfiltrates data through cloud services without detection "
                    "due to lack of network monitoring and cloud logging.",
        risk_level="high",
        techniques=[
            {"id": "T1567", "name": "Exfiltration Over Web Service"},
            {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
            {"id": "T1119", "name": "Automated Collection"}
        ],
        enabling_gaps=["DC-003", "TL-004", "TL-002"],
        likelihood=3,
        impact=4
    ),
    "log_tampering": AttackPath(
        id="AP-005",
        name="Evidence Destruction via Log Tampering",
        description="Attacker clears or modifies logs to hide their activities, "
                    "enabled by insufficient log retention and lack of immutable logging.",
        risk_level="medium",
        techniques=[
            {"id": "T1070", "name": "Indicator Removal"},
            {"id": "T1070.001", "name": "Clear Windows Event Logs"},
            {"id": "T1562.002", "name": "Disable Event Logging"}
        ],
        enabling_gaps=["TL-001", "TL-002"],
        likelihood=3,
        impact=3
    ),
    "bec_attack": AttackPath(
        id="AP-006",
        name="Business Email Compromise",
        description="Attacker compromises executive email account and conducts fraud, "
                    "undetected due to lack of email security and authentication logging.",
        risk_level="high",
        techniques=[
            {"id": "T1566.002", "name": "Spearphishing Link"},
            {"id": "T1114", "name": "Email Collection"},
            {"id": "T1078", "name": "Valid Accounts"}
        ],
        enabling_gaps=["DC-005", "IV-002", "TL-005"],
        likelihood=4,
        impact=4
    ),
}


def analyze_attack_paths(finding_rule_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Identify attack paths enabled by the current set of findings.
    
    Args:
        finding_rule_ids: List of triggered finding rule IDs
        
    Returns:
        List of enabled attack paths sorted by risk
    """
    enabled_paths = []
    finding_set = set(finding_rule_ids)
    
    for path_id, path in ATTACK_PATH_DEFINITIONS.items():
        # Check how many enabling gaps are present
        matched_gaps = [gap for gap in path.enabling_gaps if gap in finding_set]
        
        if len(matched_gaps) >= 2:  # At least 2 enabling gaps required
            coverage = len(matched_gaps) / len(path.enabling_gaps)
            
            enabled_paths.append({
                "id": path.id,
                "name": path.name,
                "description": path.description,
                "risk_level": path.risk_level,
                "techniques": path.techniques,
                "enabling_gaps": matched_gaps,
                "all_gaps_required": path.enabling_gaps,
                "gap_coverage_pct": round(coverage * 100, 1),
                "likelihood": path.likelihood,
                "impact": path.impact,
                "risk_score": path.likelihood * path.impact
            })
    
    # Sort by risk score descending
    enabled_paths.sort(key=lambda p: p["risk_score"], reverse=True)
    return enabled_paths


def analyze_detection_gaps(finding_rule_ids: List[str]) -> Dict[str, Any]:
    """
    Analyze detection capability gaps from findings.
    
    Args:
        finding_rule_ids: List of triggered finding rule IDs
        
    Returns:
        Detection gaps analysis with categories
    """
    finding_set = set(finding_rule_ids)
    
    gaps = {
        "categories": [],
        "total_gaps": 0
    }
    
    # EDR/Endpoint Detection
    edr_gaps = []
    if "DC-001" in finding_set:
        edr_gaps.append("EDR coverage below 80%")
    if "DC-002" in finding_set:
        edr_gaps.append("Critical EDR coverage gap (<50%)")
    if "TL-003" in finding_set:
        edr_gaps.append("Endpoint logs not collected")
    
    if edr_gaps:
        gaps["categories"].append({
            "name": "Endpoint Detection",
            "gaps": edr_gaps,
            "severity": "critical" if "DC-002" in finding_set else "high"
        })
        gaps["total_gaps"] += len(edr_gaps)
    
    # Network Detection
    network_gaps = []
    if "DC-003" in finding_set:
        network_gaps.append("No network traffic monitoring (NDR/IDS)")
    if "TL-004" in finding_set:
        network_gaps.append("Cloud service logs not collected")
    
    if network_gaps:
        gaps["categories"].append({
            "name": "Network Detection",
            "gaps": network_gaps,
            "severity": "high"
        })
        gaps["total_gaps"] += len(network_gaps)
    
    # Email/Phishing Detection
    email_gaps = []
    if "DC-005" in finding_set:
        email_gaps.append("No email security/anti-phishing protection")
    
    if email_gaps:
        gaps["categories"].append({
            "name": "Email Security",
            "gaps": email_gaps,
            "severity": "high"
        })
        gaps["total_gaps"] += len(email_gaps)
    
    # Log Visibility
    log_gaps = []
    if "TL-001" in finding_set:
        log_gaps.append("Log retention below 30 days")
    if "TL-002" in finding_set:
        log_gaps.append("No centralized log management (SIEM)")
    if "TL-005" in finding_set:
        log_gaps.append("Authentication events not logged")
    
    if log_gaps:
        gaps["categories"].append({
            "name": "Log Visibility",
            "gaps": log_gaps,
            "severity": "high" if "TL-002" in finding_set else "medium"
        })
        gaps["total_gaps"] += len(log_gaps)
    
    # Detection Operations
    ops_gaps = []
    if "DC-004" in finding_set:
        ops_gaps.append("Detection rules not updated weekly")
    if "DC-006" in finding_set:
        ops_gaps.append("Alerts not triaged within 24 hours")
    
    if ops_gaps:
        gaps["categories"].append({
            "name": "Detection Operations",
            "gaps": ops_gaps,
            "severity": "medium"
        })
        gaps["total_gaps"] += len(ops_gaps)
    
    return gaps


def analyze_response_gaps(finding_rule_ids: List[str]) -> Dict[str, Any]:
    """
    Analyze incident response capability gaps from findings.
    
    Args:
        finding_rule_ids: List of triggered finding rule IDs
        
    Returns:
        Response gaps analysis with categories
    """
    finding_set = set(finding_rule_ids)
    
    gaps = {
        "categories": [],
        "total_gaps": 0
    }
    
    # IR Process
    ir_gaps = []
    if "IR-001" in finding_set:
        ir_gaps.append("No documented IR playbooks")
    if "IR-002" in finding_set:
        ir_gaps.append("IR playbooks not tested")
    if "IR-003" in finding_set:
        ir_gaps.append("No tabletop exercises conducted")
    if "IR-004" in finding_set:
        ir_gaps.append("No defined IR team or roles")
    
    if ir_gaps:
        gaps["categories"].append({
            "name": "Incident Response Process",
            "gaps": ir_gaps,
            "severity": "high" if "IR-001" in finding_set else "medium"
        })
        gaps["total_gaps"] += len(ir_gaps)
    
    # Recovery Capability
    recovery_gaps = []
    if "RS-001" in finding_set:
        recovery_gaps.append("Backups not tested")
    if "RS-002" in finding_set:
        recovery_gaps.append("Backups not immutable/air-gapped")
    if "RS-003" in finding_set:
        recovery_gaps.append("Critical systems not backed up")
    if "RS-004" in finding_set:
        recovery_gaps.append("RTO exceeds 72 hours")
    if "RS-005" in finding_set:
        recovery_gaps.append("No disaster recovery plan")
    if "RS-006" in finding_set:
        recovery_gaps.append("Backup credentials not isolated")
    
    if recovery_gaps:
        gaps["categories"].append({
            "name": "Recovery Capability",
            "gaps": recovery_gaps,
            "severity": "critical" if "RS-003" in finding_set or "RS-002" in finding_set else "high"
        })
        gaps["total_gaps"] += len(recovery_gaps)
    
    return gaps


def analyze_identity_gaps(finding_rule_ids: List[str]) -> Dict[str, Any]:
    """
    Analyze identity and access management gaps from findings.
    
    Args:
        finding_rule_ids: List of triggered finding rule IDs
        
    Returns:
        Identity gaps analysis with categories
    """
    finding_set = set(finding_rule_ids)
    
    gaps = {
        "categories": [],
        "total_gaps": 0
    }
    
    # MFA
    mfa_gaps = []
    if "IV-001" in finding_set:
        mfa_gaps.append("MFA not enforced for administrators")
    if "IV-002" in finding_set:
        mfa_gaps.append("MFA not enforced organization-wide")
    
    if mfa_gaps:
        gaps["categories"].append({
            "name": "Multi-Factor Authentication",
            "gaps": mfa_gaps,
            "severity": "critical" if "IV-001" in finding_set else "high"
        })
        gaps["total_gaps"] += len(mfa_gaps)
    
    # Privileged Access
    pam_gaps = []
    if "IV-003" in finding_set:
        pam_gaps.append("No privileged account inventory")
    if "IV-004" in finding_set:
        pam_gaps.append("Service accounts not managed")
    if "IV-005" in finding_set:
        pam_gaps.append("No PAM solution deployed")
    
    if pam_gaps:
        gaps["categories"].append({
            "name": "Privileged Access Management",
            "gaps": pam_gaps,
            "severity": "high"
        })
        gaps["total_gaps"] += len(pam_gaps)
    
    return gaps


def calculate_risk_summary(
    attack_paths: List[Dict],
    detection_gaps: Dict,
    response_gaps: Dict,
    identity_gaps: Dict
) -> Dict[str, Any]:
    """
    Calculate overall risk summary from all gap analyses.
    
    Args:
        attack_paths: Enabled attack paths
        detection_gaps: Detection gap analysis
        response_gaps: Response gap analysis
        identity_gaps: Identity gap analysis
        
    Returns:
        Overall risk summary
    """
    # Determine overall risk level
    critical_attack_paths = len([p for p in attack_paths if p["risk_level"] == "critical"])
    high_attack_paths = len([p for p in attack_paths if p["risk_level"] == "high"])
    
    total_gaps = (
        detection_gaps.get("total_gaps", 0) +
        response_gaps.get("total_gaps", 0) +
        identity_gaps.get("total_gaps", 0)
    )
    
    if critical_attack_paths >= 2 or (critical_attack_paths >= 1 and total_gaps >= 10):
        overall_risk = "critical"
    elif critical_attack_paths >= 1 or high_attack_paths >= 2 or total_gaps >= 8:
        overall_risk = "high"
    elif high_attack_paths >= 1 or total_gaps >= 5:
        overall_risk = "medium"
    else:
        overall_risk = "low"
    
    # Compile key risks
    key_risks = []
    for path in attack_paths[:3]:
        key_risks.append(f"{path['name']} ({path['risk_level']})")
    
    # Mitigating factors
    mitigating_factors = []
    if detection_gaps.get("total_gaps", 0) == 0:
        mitigating_factors.append("Strong detection capabilities in place")
    if identity_gaps.get("total_gaps", 0) == 0:
        mitigating_factors.append("Robust identity controls implemented")
    if response_gaps.get("total_gaps", 0) == 0:
        mitigating_factors.append("Mature incident response program")
    
    return {
        "overall_risk_level": overall_risk,
        "key_risks": key_risks,
        "mitigating_factors": mitigating_factors,
        "attack_paths_enabled": len(attack_paths),
        "total_gaps_identified": total_gaps
    }


def generate_analytics(finding_rule_ids: List[str]) -> Dict[str, Any]:
    """
    Generate complete analytics package for an assessment.
    
    Args:
        finding_rule_ids: List of triggered finding rule IDs
        
    Returns:
        Complete analytics with attack paths, gaps, and risk summary
    """
    # Analyze all gaps
    attack_paths = analyze_attack_paths(finding_rule_ids)
    detection_gaps = analyze_detection_gaps(finding_rule_ids)
    response_gaps = analyze_response_gaps(finding_rule_ids)
    identity_gaps = analyze_identity_gaps(finding_rule_ids)
    
    # Calculate risk summary
    risk_summary = calculate_risk_summary(
        attack_paths, detection_gaps, response_gaps, identity_gaps
    )
    
    # Calculate risk distribution
    risk_distribution = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    for path in attack_paths:
        level = path.get("risk_level", "medium")
        if level in risk_distribution:
            risk_distribution[level] += 1
    
    # Top improvement recommendations
    improvement_recs = []
    
    # Identity first (highest impact)
    if identity_gaps.get("total_gaps", 0) > 0:
        improvement_recs.append("Implement MFA for all accounts, starting with administrators")
    
    # Detection next
    if detection_gaps.get("total_gaps", 0) > 0:
        improvement_recs.append("Deploy EDR across all endpoints and enable centralized logging")
    
    # Response capability
    if response_gaps.get("total_gaps", 0) > 0:
        improvement_recs.append("Develop and test incident response playbooks")
    
    # Always include backup recommendation if gaps exist
    if any("RS-" in r for r in finding_rule_ids):
        improvement_recs.append("Implement immutable backup storage and test recovery procedures")
    
    return {
        "attack_paths": attack_paths,
        "detection_gaps": detection_gaps,
        "response_gaps": response_gaps,
        "identity_gaps": identity_gaps,
        "risk_distribution": risk_distribution,
        "risk_summary": risk_summary,
        "top_risks": risk_summary["key_risks"],
        "improvement_recommendations": improvement_recs[:5]
    }
