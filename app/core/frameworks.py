"""
Security Framework Mappings for AIRS Findings.

Maps findings to industry-standard frameworks:
- MITRE ATT&CK: Tactics and techniques
- CIS Controls v8: Control references
- OWASP: Web/Auth security references

Each mapping links a finding rule ID to relevant framework references.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class MitreReference:
    """MITRE ATT&CK reference."""
    technique_id: str
    technique_name: str
    tactic: str
    url: str


@dataclass
class CISReference:
    """CIS Controls v8 reference."""
    control_id: str
    control_name: str
    implementation_group: int  # 1, 2, or 3
    asset_type: str  # Devices, Users, Network, Data, Applications


@dataclass
class OWASPReference:
    """OWASP reference."""
    id: str
    name: str
    category: str  # Top 10, ASVS, etc.
    url: str


# =============================================================================
# MITRE ATT&CK MAPPINGS
# Techniques enabled by missing controls
# =============================================================================

MITRE_TECHNIQUES: Dict[str, MitreReference] = {
    # Credential Access
    "T1110": MitreReference("T1110", "Brute Force", "Credential Access", 
                            "https://attack.mitre.org/techniques/T1110"),
    "T1110.001": MitreReference("T1110.001", "Password Guessing", "Credential Access",
                                 "https://attack.mitre.org/techniques/T1110/001"),
    "T1110.003": MitreReference("T1110.003", "Password Spraying", "Credential Access",
                                 "https://attack.mitre.org/techniques/T1110/003"),
    "T1078": MitreReference("T1078", "Valid Accounts", "Defense Evasion",
                            "https://attack.mitre.org/techniques/T1078"),
    "T1078.001": MitreReference("T1078.001", "Default Accounts", "Persistence",
                                 "https://attack.mitre.org/techniques/T1078/001"),
    "T1078.002": MitreReference("T1078.002", "Domain Accounts", "Privilege Escalation",
                                 "https://attack.mitre.org/techniques/T1078/002"),
    "T1555": MitreReference("T1555", "Credentials from Password Stores", "Credential Access",
                            "https://attack.mitre.org/techniques/T1555"),
    "T1539": MitreReference("T1539", "Steal Web Session Cookie", "Credential Access",
                            "https://attack.mitre.org/techniques/T1539"),
    
    # Persistence
    "T1136": MitreReference("T1136", "Create Account", "Persistence",
                            "https://attack.mitre.org/techniques/T1136"),
    "T1098": MitreReference("T1098", "Account Manipulation", "Persistence",
                            "https://attack.mitre.org/techniques/T1098"),
    
    # Privilege Escalation
    "T1068": MitreReference("T1068", "Exploitation for Privilege Escalation", "Privilege Escalation",
                            "https://attack.mitre.org/techniques/T1068"),
    "T1548": MitreReference("T1548", "Abuse Elevation Control Mechanism", "Privilege Escalation",
                            "https://attack.mitre.org/techniques/T1548"),
    
    # Defense Evasion
    "T1562": MitreReference("T1562", "Impair Defenses", "Defense Evasion",
                            "https://attack.mitre.org/techniques/T1562"),
    "T1562.001": MitreReference("T1562.001", "Disable or Modify Tools", "Defense Evasion",
                                 "https://attack.mitre.org/techniques/T1562/001"),
    "T1070": MitreReference("T1070", "Indicator Removal", "Defense Evasion",
                            "https://attack.mitre.org/techniques/T1070"),
    "T1070.001": MitreReference("T1070.001", "Clear Windows Event Logs", "Defense Evasion",
                                 "https://attack.mitre.org/techniques/T1070/001"),
    
    # Discovery
    "T1087": MitreReference("T1087", "Account Discovery", "Discovery",
                            "https://attack.mitre.org/techniques/T1087"),
    "T1069": MitreReference("T1069", "Permission Groups Discovery", "Discovery",
                            "https://attack.mitre.org/techniques/T1069"),
    "T1018": MitreReference("T1018", "Remote System Discovery", "Discovery",
                            "https://attack.mitre.org/techniques/T1018"),
    
    # Lateral Movement
    "T1021": MitreReference("T1021", "Remote Services", "Lateral Movement",
                            "https://attack.mitre.org/techniques/T1021"),
    "T1021.001": MitreReference("T1021.001", "Remote Desktop Protocol", "Lateral Movement",
                                 "https://attack.mitre.org/techniques/T1021/001"),
    "T1021.002": MitreReference("T1021.002", "SMB/Windows Admin Shares", "Lateral Movement",
                                 "https://attack.mitre.org/techniques/T1021/002"),
    "T1550": MitreReference("T1550", "Use Alternate Authentication Material", "Lateral Movement",
                            "https://attack.mitre.org/techniques/T1550"),
    "T1550.002": MitreReference("T1550.002", "Pass the Hash", "Lateral Movement",
                                 "https://attack.mitre.org/techniques/T1550/002"),
    
    # Collection
    "T1530": MitreReference("T1530", "Data from Cloud Storage", "Collection",
                            "https://attack.mitre.org/techniques/T1530"),
    "T1213": MitreReference("T1213", "Data from Information Repositories", "Collection",
                            "https://attack.mitre.org/techniques/T1213"),
    
    # Command and Control
    "T1071": MitreReference("T1071", "Application Layer Protocol", "Command and Control",
                            "https://attack.mitre.org/techniques/T1071"),
    "T1095": MitreReference("T1095", "Non-Application Layer Protocol", "Command and Control",
                            "https://attack.mitre.org/techniques/T1095"),
    
    # Exfiltration
    "T1048": MitreReference("T1048", "Exfiltration Over Alternative Protocol", "Exfiltration",
                            "https://attack.mitre.org/techniques/T1048"),
    "T1567": MitreReference("T1567", "Exfiltration Over Web Service", "Exfiltration",
                            "https://attack.mitre.org/techniques/T1567"),
    
    # Impact
    "T1486": MitreReference("T1486", "Data Encrypted for Impact", "Impact",
                            "https://attack.mitre.org/techniques/T1486"),
    "T1490": MitreReference("T1490", "Inhibit System Recovery", "Impact",
                            "https://attack.mitre.org/techniques/T1490"),
    "T1489": MitreReference("T1489", "Service Stop", "Impact",
                            "https://attack.mitre.org/techniques/T1489"),
    "T1485": MitreReference("T1485", "Data Destruction", "Impact",
                            "https://attack.mitre.org/techniques/T1485"),
    
    # Initial Access
    "T1566": MitreReference("T1566", "Phishing", "Initial Access",
                            "https://attack.mitre.org/techniques/T1566"),
    "T1566.001": MitreReference("T1566.001", "Spearphishing Attachment", "Initial Access",
                                 "https://attack.mitre.org/techniques/T1566/001"),
    "T1566.002": MitreReference("T1566.002", "Spearphishing Link", "Initial Access",
                                 "https://attack.mitre.org/techniques/T1566/002"),
    "T1190": MitreReference("T1190", "Exploit Public-Facing Application", "Initial Access",
                            "https://attack.mitre.org/techniques/T1190"),
    
    # Execution
    "T1059": MitreReference("T1059", "Command and Scripting Interpreter", "Execution",
                            "https://attack.mitre.org/techniques/T1059"),
    "T1204": MitreReference("T1204", "User Execution", "Execution",
                            "https://attack.mitre.org/techniques/T1204"),
}


# =============================================================================
# CIS CONTROLS v8 MAPPINGS
# =============================================================================

CIS_CONTROLS: Dict[str, CISReference] = {
    # IG1 Controls (Basic Cyber Hygiene)
    "1.1": CISReference("1.1", "Establish and Maintain Detailed Enterprise Asset Inventory", 1, "Devices"),
    "1.2": CISReference("1.2", "Address Unauthorized Assets", 1, "Devices"),
    "2.1": CISReference("2.1", "Establish and Maintain Software Inventory", 1, "Applications"),
    "2.2": CISReference("2.2", "Ensure Authorized Software is Currently Supported", 1, "Applications"),
    "3.1": CISReference("3.1", "Establish and Maintain Data Management Process", 1, "Data"),
    "3.4": CISReference("3.4", "Enforce Data Retention", 1, "Data"),
    "4.1": CISReference("4.1", "Establish Secure Configuration Process", 1, "Devices"),
    "4.7": CISReference("4.7", "Manage Default Accounts on Enterprise Assets and Software", 1, "Devices"),
    "5.1": CISReference("5.1", "Establish and Maintain Inventory of Accounts", 1, "Users"),
    "5.2": CISReference("5.2", "Use Unique Passwords", 1, "Users"),
    "5.3": CISReference("5.3", "Disable Dormant Accounts", 1, "Users"),
    "5.4": CISReference("5.4", "Restrict Administrator Privileges", 1, "Users"),
    "6.1": CISReference("6.1", "Establish Access Granting Process", 1, "Users"),
    "6.2": CISReference("6.2", "Establish Access Revoking Process", 1, "Users"),
    "6.3": CISReference("6.3", "Require MFA for Externally-Exposed Applications", 1, "Users"),
    "6.4": CISReference("6.4", "Require MFA for Remote Network Access", 1, "Users"),
    "6.5": CISReference("6.5", "Require MFA for Administrative Access", 1, "Users"),
    "7.1": CISReference("7.1", "Establish and Maintain Vulnerability Management Process", 1, "Applications"),
    "7.2": CISReference("7.2", "Establish Remediation Process", 1, "Applications"),
    "7.3": CISReference("7.3", "Perform Automated OS Patch Management", 1, "Devices"),
    "7.4": CISReference("7.4", "Perform Automated Application Patch Management", 1, "Applications"),
    
    # IG2 Controls
    "8.1": CISReference("8.1", "Establish and Maintain Audit Log Management Process", 2, "Data"),
    "8.2": CISReference("8.2", "Collect Audit Logs", 2, "Data"),
    "8.3": CISReference("8.3", "Ensure Adequate Audit Log Storage", 2, "Data"),
    "8.5": CISReference("8.5", "Collect Detailed Audit Logs", 2, "Data"),
    "8.9": CISReference("8.9", "Centralize Audit Logs", 2, "Data"),
    "8.11": CISReference("8.11", "Conduct Audit Log Reviews", 2, "Data"),
    "9.1": CISReference("9.1", "Ensure Use of Only Fully Supported Browsers and Email Clients", 2, "Applications"),
    "9.6": CISReference("9.6", "Block Unnecessary File Types", 2, "Network"),
    "10.1": CISReference("10.1", "Deploy and Maintain Anti-Malware Software", 2, "Devices"),
    "10.2": CISReference("10.2", "Configure Automatic Updates", 2, "Devices"),
    "10.4": CISReference("10.4", "Configure Automatic Anti-Malware Scanning", 2, "Devices"),
    "10.7": CISReference("10.7", "Use Behavior-Based Anti-Malware", 2, "Devices"),
    "11.1": CISReference("11.1", "Establish Data Recovery Process", 2, "Data"),
    "11.2": CISReference("11.2", "Perform Automated Backups", 2, "Data"),
    "11.3": CISReference("11.3", "Protect Recovery Data", 2, "Data"),
    "11.4": CISReference("11.4", "Establish and Maintain Isolated Instance of Recovery Data", 2, "Data"),
    "11.5": CISReference("11.5", "Test Data Recovery", 2, "Data"),
    "12.1": CISReference("12.1", "Ensure Network Infrastructure is Up-to-Date", 2, "Network"),
    "13.1": CISReference("13.1", "Centralize Security Event Alerting", 2, "Network"),
    "13.3": CISReference("13.3", "Deploy Network-Based IDS", 2, "Network"),
    "13.6": CISReference("13.6", "Collect Network Traffic Flow Logs", 2, "Network"),
    "14.1": CISReference("14.1", "Establish and Maintain Security Awareness Program", 2, "Users"),
    "14.2": CISReference("14.2", "Train Workforce on Safe Authentication", 2, "Users"),
    "14.3": CISReference("14.3", "Train Workforce on Data Handling", 2, "Users"),
    "14.4": CISReference("14.4", "Train Workforce on Causes of Unintentional Data Exposure", 2, "Users"),
    "14.5": CISReference("14.5", "Train Workforce on Social Engineering", 2, "Users"),
    
    # IG3 Controls
    "16.1": CISReference("16.1", "Establish and Maintain Secure Application Development Process", 3, "Applications"),
    "17.1": CISReference("17.1", "Designate Personnel to Manage Incident Handling", 3, "Users"),
    "17.2": CISReference("17.2", "Establish and Maintain Contact Information for Reporting", 3, "Users"),
    "17.3": CISReference("17.3", "Establish and Maintain Enterprise Process for Reporting", 3, "Users"),
    "17.4": CISReference("17.4", "Establish and Maintain Incident Response Process", 3, "Users"),
    "17.6": CISReference("17.6", "Define Mechanisms for Communicating During Incident Response", 3, "Users"),
    "17.7": CISReference("17.7", "Conduct Routine Incident Response Exercises", 3, "Users"),
    "17.8": CISReference("17.8", "Conduct Post-Incident Reviews", 3, "Users"),
    "18.1": CISReference("18.1", "Establish and Maintain Penetration Testing Program", 3, "Network"),
}


# =============================================================================
# OWASP MAPPINGS
# =============================================================================

OWASP_REFS: Dict[str, OWASPReference] = {
    # OWASP Top 10 2021
    "A01": OWASPReference("A01:2021", "Broken Access Control", "Top 10",
                          "https://owasp.org/Top10/A01_2021-Broken_Access_Control/"),
    "A02": OWASPReference("A02:2021", "Cryptographic Failures", "Top 10",
                          "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/"),
    "A03": OWASPReference("A03:2021", "Injection", "Top 10",
                          "https://owasp.org/Top10/A03_2021-Injection/"),
    "A04": OWASPReference("A04:2021", "Insecure Design", "Top 10",
                          "https://owasp.org/Top10/A04_2021-Insecure_Design/"),
    "A05": OWASPReference("A05:2021", "Security Misconfiguration", "Top 10",
                          "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/"),
    "A06": OWASPReference("A06:2021", "Vulnerable and Outdated Components", "Top 10",
                          "https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/"),
    "A07": OWASPReference("A07:2021", "Identification and Authentication Failures", "Top 10",
                          "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/"),
    "A08": OWASPReference("A08:2021", "Software and Data Integrity Failures", "Top 10",
                          "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/"),
    "A09": OWASPReference("A09:2021", "Security Logging and Monitoring Failures", "Top 10",
                          "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/"),
    "A10": OWASPReference("A10:2021", "Server-Side Request Forgery", "Top 10",
                          "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery_%28SSRF%29/"),
}


# =============================================================================
# FINDING RULE TO FRAMEWORK MAPPINGS
# =============================================================================

FINDING_FRAMEWORK_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    # Telemetry & Logging Rules
    "TL-001": {  # Insufficient Log Retention
        "mitre": ["T1070", "T1070.001", "T1562"],
        "cis": ["8.3", "3.4"],
        "owasp": ["A09"],
    },
    "TL-002": {  # Missing Centralized Log Management
        "mitre": ["T1070", "T1562", "T1562.001"],
        "cis": ["8.2", "8.9", "8.11"],
        "owasp": ["A09"],
    },
    "TL-003": {  # Incomplete Endpoint Logging
        "mitre": ["T1059", "T1562.001", "T1070"],
        "cis": ["8.5", "8.2"],
        "owasp": ["A09"],
    },
    "TL-004": {  # No Cloud Service Logging
        "mitre": ["T1530", "T1078", "T1562"],
        "cis": ["8.2", "8.11"],
        "owasp": ["A09"],
    },
    "TL-005": {  # Authentication Events Not Logged
        "mitre": ["T1078", "T1110", "T1136", "T1098"],
        "cis": ["8.5", "8.11"],
        "owasp": ["A07", "A09"],
    },
    
    # Detection Coverage Rules
    "DC-001": {  # Inadequate EDR Coverage
        "mitre": ["T1059", "T1562.001", "T1204"],
        "cis": ["10.1", "10.7"],
        "owasp": [],
    },
    "DC-002": {  # Critical EDR Gap (<50%)
        "mitre": ["T1059", "T1562.001", "T1204", "T1486"],
        "cis": ["10.1", "10.7"],
        "owasp": [],
    },
    "DC-003": {  # No Network Traffic Monitoring
        "mitre": ["T1021", "T1048", "T1071", "T1095"],
        "cis": ["13.3", "13.6"],
        "owasp": [],
    },
    "DC-004": {  # Stale Detection Rules
        "mitre": ["T1562", "T1204"],
        "cis": ["10.4"],
        "owasp": ["A06"],
    },
    "DC-005": {  # No Email Security
        "mitre": ["T1566", "T1566.001", "T1566.002", "T1204"],
        "cis": ["9.6"],
        "owasp": [],
    },
    "DC-006": {  # Slow Alert Triage
        "mitre": ["T1562"],
        "cis": ["13.1", "17.4"],
        "owasp": [],
    },
    
    # Identity Visibility Rules
    "IV-001": {  # MFA Not Enforced for Admins
        "mitre": ["T1078", "T1078.002", "T1110", "T1110.003"],
        "cis": ["6.5", "5.4"],
        "owasp": ["A07"],
    },
    "IV-002": {  # Low MFA Coverage for All Users
        "mitre": ["T1078", "T1110", "T1110.001"],
        "cis": ["6.3", "6.4"],
        "owasp": ["A07"],
    },
    "IV-003": {  # No Privileged Account Inventory
        "mitre": ["T1078.002", "T1087", "T1069"],
        "cis": ["5.1", "5.4"],
        "owasp": ["A01"],
    },
    "IV-004": {  # Service Accounts Not Reviewed
        "mitre": ["T1078.001", "T1098"],
        "cis": ["5.1", "5.3"],
        "owasp": ["A01", "A07"],
    },
    "IV-005": {  # No PAM Solution
        "mitre": ["T1078.002", "T1550.002", "T1021"],
        "cis": ["5.4", "6.1", "6.2"],
        "owasp": ["A01"],
    },
    "IV-006": {  # No Login Anomaly Monitoring
        "mitre": ["T1110", "T1078", "T1136"],
        "cis": ["8.11"],
        "owasp": ["A07"],
    },
    
    # IR Process Rules
    "IR-001": {  # No IR Playbooks
        "mitre": [],
        "cis": ["17.4"],
        "owasp": [],
    },
    "IR-002": {  # Untested IR Playbooks
        "mitre": [],
        "cis": ["17.7"],
        "owasp": [],
    },
    "IR-003": {  # No Tabletop Exercises
        "mitre": [],
        "cis": ["17.7"],
        "owasp": [],
    },
    "IR-004": {  # No Defined IR Team
        "mitre": [],
        "cis": ["17.1", "17.2", "17.6"],
        "owasp": [],
    },
    
    # Resilience Rules
    "RS-001": {  # Backups Not Tested
        "mitre": ["T1486", "T1490"],
        "cis": ["11.5"],
        "owasp": [],
    },
    "RS-002": {  # Backups Not Immutable
        "mitre": ["T1486", "T1490", "T1485"],
        "cis": ["11.3", "11.4"],
        "owasp": [],
    },
    "RS-003": {  # Critical Systems Not Backed Up
        "mitre": ["T1486", "T1485", "T1489"],
        "cis": ["11.1", "11.2"],
        "owasp": [],
    },
    "RS-004": {  # Excessive RTO
        "mitre": ["T1486"],
        "cis": ["11.1"],
        "owasp": [],
    },
    "RS-005": {  # No DR Plan
        "mitre": ["T1486", "T1489"],
        "cis": ["11.1"],
        "owasp": [],
    },
    "RS-006": {  # No Asset Classification
        "mitre": ["T1486"],
        "cis": ["1.1", "3.1"],
        "owasp": [],
    },
}


def get_mitre_refs(rule_id: str) -> List[MitreReference]:
    """Get MITRE ATT&CK references for a finding rule."""
    mapping = FINDING_FRAMEWORK_MAPPINGS.get(rule_id, {})
    technique_ids = mapping.get("mitre", [])
    return [MITRE_TECHNIQUES[tid] for tid in technique_ids if tid in MITRE_TECHNIQUES]


def get_cis_refs(rule_id: str) -> List[CISReference]:
    """Get CIS Controls v8 references for a finding rule."""
    mapping = FINDING_FRAMEWORK_MAPPINGS.get(rule_id, {})
    control_ids = mapping.get("cis", [])
    return [CIS_CONTROLS[cid] for cid in control_ids if cid in CIS_CONTROLS]


def get_owasp_refs(rule_id: str) -> List[OWASPReference]:
    """Get OWASP references for a finding rule."""
    mapping = FINDING_FRAMEWORK_MAPPINGS.get(rule_id, {})
    ref_ids = mapping.get("owasp", [])
    return [OWASP_REFS[rid] for rid in ref_ids if rid in OWASP_REFS]


def get_all_framework_refs(rule_id: str) -> Dict[str, List]:
    """Get all framework references for a finding rule."""
    return {
        "mitre": [
            {
                "technique_id": m.technique_id,
                "technique_name": m.technique_name,
                "tactic": m.tactic,
                "url": m.url,
            }
            for m in get_mitre_refs(rule_id)
        ],
        "cis": [
            {
                "control_id": c.control_id,
                "control_name": c.control_name,
                "implementation_group": c.implementation_group,
                "asset_type": c.asset_type,
            }
            for c in get_cis_refs(rule_id)
        ],
        "owasp": [
            {
                "id": o.id,
                "name": o.name,
                "category": o.category,
                "url": o.url,
            }
            for o in get_owasp_refs(rule_id)
        ],
    }


def get_technique_coverage(finding_rules: List[str]) -> Dict[str, any]:
    """
    Analyze which MITRE tactics have coverage gaps based on triggered findings.
    
    Returns a summary of tactics and techniques that could be exploited.
    """
    enabled_techniques = set()
    tactics_affected = {}
    
    for rule_id in finding_rules:
        for ref in get_mitre_refs(rule_id):
            enabled_techniques.add(ref.technique_id)
            tactic = ref.tactic
            if tactic not in tactics_affected:
                tactics_affected[tactic] = []
            tactics_affected[tactic].append({
                "technique_id": ref.technique_id,
                "technique_name": ref.technique_name,
                "finding_rule": rule_id,
            })
    
    return {
        "techniques_enabled": len(enabled_techniques),
        "tactics_affected": tactics_affected,
        "technique_list": list(enabled_techniques),
    }


def get_cis_coverage_summary(finding_rules: List[str]) -> Dict[str, any]:
    """
    Analyze CIS Controls coverage gaps based on triggered findings.
    """
    missing_controls = {}
    ig_counts = {1: 0, 2: 0, 3: 0}
    
    for rule_id in finding_rules:
        for ref in get_cis_refs(rule_id):
            if ref.control_id not in missing_controls:
                missing_controls[ref.control_id] = {
                    "control_id": ref.control_id,
                    "control_name": ref.control_name,
                    "implementation_group": ref.implementation_group,
                    "finding_rules": [],
                }
                ig_counts[ref.implementation_group] += 1
            missing_controls[ref.control_id]["finding_rules"].append(rule_id)
    
    return {
        "missing_controls_count": len(missing_controls),
        "ig1_missing": ig_counts[1],
        "ig2_missing": ig_counts[2],
        "ig3_missing": ig_counts[3],
        "controls": list(missing_controls.values()),
    }
