"""
AIRS Framework Mappings

Maps security control findings to industry frameworks:
- MITRE ATT&CK Enterprise Techniques
- CIS Controls v8
- OWASP Top 10 (where applicable)

Each finding rule_id maps to relevant technique IDs with metadata.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class MITRERef:
    """MITRE ATT&CK technique reference."""
    id: str  # e.g., "T1078"
    name: str  # e.g., "Valid Accounts"
    tactic: str  # e.g., "Initial Access"
    url: str = ""
    
    def __post_init__(self):
        if not self.url:
            self.url = f"https://attack.mitre.org/techniques/{self.id.replace('.', '/')}/"
    
    def to_dict(self) -> Dict[str, str]:
        return {"id": self.id, "name": self.name, "tactic": self.tactic, "url": self.url}


@dataclass 
class CISRef:
    """CIS Controls v8 reference."""
    id: str  # e.g., "8.3"
    name: str  # e.g., "Ensure Adequate Audit Log Storage"
    ig_level: int  # Implementation Group 1, 2, or 3
    url: str = ""
    
    def __post_init__(self):
        if not self.url:
            control_num = self.id.split('.')[0] if '.' in self.id else self.id
            self.url = f"https://www.cisecurity.org/controls/v8"
    
    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "ig_level": self.ig_level, "url": self.url}


@dataclass
class OWASPRef:
    """OWASP Top 10 reference."""
    id: str  # e.g., "A07:2021"
    name: str  # e.g., "Identification and Authentication Failures"
    url: str = ""
    
    def __post_init__(self):
        if not self.url:
            self.url = f"https://owasp.org/Top10/A{self.id.split('A')[1].split(':')[0].zfill(2)}_2021/"
    
    def to_dict(self) -> Dict[str, str]:
        return {"id": self.id, "name": self.name, "url": self.url}


# =============================================================================
# MITRE ATT&CK ENTERPRISE TECHNIQUES
# =============================================================================

MITRE_TECHNIQUES = {
    # Credential Access
    "T1078": MITRERef("T1078", "Valid Accounts", "Defense Evasion, Initial Access"),
    "T1078.001": MITRERef("T1078.001", "Valid Accounts: Default Accounts", "Defense Evasion"),
    "T1078.002": MITRERef("T1078.002", "Valid Accounts: Domain Accounts", "Defense Evasion"),
    "T1078.004": MITRERef("T1078.004", "Valid Accounts: Cloud Accounts", "Defense Evasion"),
    "T1556": MITRERef("T1556", "Modify Authentication Process", "Credential Access, Defense Evasion"),
    "T1556.006": MITRERef("T1556.006", "Multi-Factor Authentication Request Generation", "Credential Access"),
    "T1110": MITRERef("T1110", "Brute Force", "Credential Access"),
    "T1110.001": MITRERef("T1110.001", "Password Guessing", "Credential Access"),
    "T1110.003": MITRERef("T1110.003", "Password Spraying", "Credential Access"),
    
    # Discovery
    "T1087": MITRERef("T1087", "Account Discovery", "Discovery"),
    "T1087.001": MITRERef("T1087.001", "Local Account Discovery", "Discovery"),
    "T1087.002": MITRERef("T1087.002", "Domain Account Discovery", "Discovery"),
    "T1069": MITRERef("T1069", "Permission Groups Discovery", "Discovery"),
    "T1069.002": MITRERef("T1069.002", "Domain Groups Discovery", "Discovery"),
    
    # Defense Evasion
    "T1070": MITRERef("T1070", "Indicator Removal", "Defense Evasion"),
    "T1070.001": MITRERef("T1070.001", "Clear Windows Event Logs", "Defense Evasion"),
    "T1070.002": MITRERef("T1070.002", "Clear Linux or Mac System Logs", "Defense Evasion"),
    "T1562": MITRERef("T1562", "Impair Defenses", "Defense Evasion"),
    "T1562.001": MITRERef("T1562.001", "Disable or Modify Tools", "Defense Evasion"),
    "T1562.002": MITRERef("T1562.002", "Disable Windows Event Logging", "Defense Evasion"),
    "T1562.006": MITRERef("T1562.006", "Disable or Modify Cloud Firewall", "Defense Evasion"),
    
    # Lateral Movement
    "T1021": MITRERef("T1021", "Remote Services", "Lateral Movement"),
    "T1021.001": MITRERef("T1021.001", "Remote Desktop Protocol", "Lateral Movement"),
    "T1021.002": MITRERef("T1021.002", "SMB/Windows Admin Shares", "Lateral Movement"),
    "T1021.004": MITRERef("T1021.004", "SSH", "Lateral Movement"),
    "T1550": MITRERef("T1550", "Use Alternate Authentication Material", "Defense Evasion, Lateral Movement"),
    "T1550.002": MITRERef("T1550.002", "Pass the Hash", "Lateral Movement"),
    
    # Persistence
    "T1098": MITRERef("T1098", "Account Manipulation", "Persistence"),
    "T1098.001": MITRERef("T1098.001", "Additional Cloud Credentials", "Persistence"),
    "T1098.003": MITRERef("T1098.003", "Additional Cloud Roles", "Persistence"),
    "T1136": MITRERef("T1136", "Create Account", "Persistence"),
    "T1136.003": MITRERef("T1136.003", "Cloud Account", "Persistence"),
    
    # Impact
    "T1485": MITRERef("T1485", "Data Destruction", "Impact"),
    "T1486": MITRERef("T1486", "Data Encrypted for Impact", "Impact"),
    "T1490": MITRERef("T1490", "Inhibit System Recovery", "Impact"),
    "T1491": MITRERef("T1491", "Defacement", "Impact"),
    "T1561": MITRERef("T1561", "Disk Wipe", "Impact"),
    
    # Exfiltration
    "T1041": MITRERef("T1041", "Exfiltration Over C2 Channel", "Exfiltration"),
    "T1048": MITRERef("T1048", "Exfiltration Over Alternative Protocol", "Exfiltration"),
    "T1567": MITRERef("T1567", "Exfiltration Over Web Service", "Exfiltration"),
    
    # Command and Control
    "T1071": MITRERef("T1071", "Application Layer Protocol", "Command and Control"),
    "T1105": MITRERef("T1105", "Ingress Tool Transfer", "Command and Control"),
    
    # Collection
    "T1114": MITRERef("T1114", "Email Collection", "Collection"),
    "T1114.002": MITRERef("T1114.002", "Remote Email Collection", "Collection"),
    "T1119": MITRERef("T1119", "Automated Collection", "Collection"),
    
    # Execution
    "T1059": MITRERef("T1059", "Command and Scripting Interpreter", "Execution"),
    "T1059.001": MITRERef("T1059.001", "PowerShell", "Execution"),
    "T1204": MITRERef("T1204", "User Execution", "Execution"),
    "T1204.001": MITRERef("T1204.001", "Malicious Link", "Execution"),
    "T1204.002": MITRERef("T1204.002", "Malicious File", "Execution"),
    
    # Initial Access
    "T1566": MITRERef("T1566", "Phishing", "Initial Access"),
    "T1566.001": MITRERef("T1566.001", "Spearphishing Attachment", "Initial Access"),
    "T1566.002": MITRERef("T1566.002", "Spearphishing Link", "Initial Access"),
    "T1190": MITRERef("T1190", "Exploit Public-Facing Application", "Initial Access"),
    "T1133": MITRERef("T1133", "External Remote Services", "Initial Access"),
}


# =============================================================================
# CIS CONTROLS v8
# =============================================================================

CIS_CONTROLS = {
    # Control 4: Secure Configuration
    "4.1": CISRef("4.1", "Establish and Maintain a Secure Configuration Process", 1),
    "4.2": CISRef("4.2", "Establish and Maintain a Secure Configuration Process for Network Infrastructure", 1),
    "4.7": CISRef("4.7", "Manage Default Accounts on Enterprise Assets and Software", 1),
    
    # Control 5: Account Management
    "5.1": CISRef("5.1", "Establish and Maintain an Inventory of Accounts", 1),
    "5.2": CISRef("5.2", "Use Unique Passwords", 1),
    "5.3": CISRef("5.3", "Disable Dormant Accounts", 1),
    "5.4": CISRef("5.4", "Restrict Administrator Privileges to Dedicated Administrator Accounts", 1),
    
    # Control 6: Access Control Management
    "6.1": CISRef("6.1", "Establish an Access Granting Process", 1),
    "6.2": CISRef("6.2", "Establish an Access Revoking Process", 1),
    "6.3": CISRef("6.3", "Require MFA for Externally-Exposed Applications", 1),
    "6.4": CISRef("6.4", "Require MFA for Remote Network Access", 2),
    "6.5": CISRef("6.5", "Require MFA for Administrative Access", 1),
    "6.6": CISRef("6.6", "Establish and Maintain an Inventory of Authentication and Authorization Systems", 2),
    "6.7": CISRef("6.7", "Centralize Access Control", 2),
    "6.8": CISRef("6.8", "Define and Maintain Role-Based Access Control", 2),
    
    # Control 8: Audit Log Management
    "8.1": CISRef("8.1", "Establish and Maintain an Audit Log Management Process", 1),
    "8.2": CISRef("8.2", "Collect Audit Logs", 1),
    "8.3": CISRef("8.3", "Ensure Adequate Audit Log Storage", 1),
    "8.5": CISRef("8.5", "Collect Detailed Audit Logs", 2),
    "8.9": CISRef("8.9", "Centralize Audit Logs", 2),
    "8.11": CISRef("8.11", "Conduct Audit Log Reviews", 2),
    
    # Control 9: Email and Web Browser Protections
    "9.1": CISRef("9.1", "Ensure Use of Only Fully Supported Browsers and Email Clients", 1),
    "9.2": CISRef("9.2", "Use DNS Filtering Services", 1),
    "9.3": CISRef("9.3", "Maintain and Enforce Network-Based URL Filters", 2),
    "9.6": CISRef("9.6", "Block Unnecessary File Types", 2),
    "9.7": CISRef("9.7", "Deploy and Maintain Email Server Anti-Malware Protections", 2),
    
    # Control 10: Malware Defenses
    "10.1": CISRef("10.1", "Deploy and Maintain Anti-Malware Software", 1),
    "10.2": CISRef("10.2", "Configure Automatic Anti-Malware Signature Updates", 1),
    "10.4": CISRef("10.4", "Configure Automatic Anti-Malware Scanning of Removable Media", 2),
    "10.5": CISRef("10.5", "Enable Anti-Exploitation Features", 2),
    "10.6": CISRef("10.6", "Centrally Manage Anti-Malware Software", 2),
    "10.7": CISRef("10.7", "Use Behavior-Based Anti-Malware Software", 2),
    
    # Control 11: Data Recovery
    "11.1": CISRef("11.1", "Establish and Maintain a Data Recovery Process", 1),
    "11.2": CISRef("11.2", "Perform Automated Backups", 1),
    "11.3": CISRef("11.3", "Protect Recovery Data", 1),
    "11.4": CISRef("11.4", "Establish and Maintain an Isolated Instance of Recovery Data", 1),
    "11.5": CISRef("11.5", "Test Data Recovery", 2),
    
    # Control 13: Network Monitoring and Defense
    "13.1": CISRef("13.1", "Centralize Security Event Alerting", 2),
    "13.2": CISRef("13.2", "Deploy a Host-Based Intrusion Detection Solution", 2),
    "13.3": CISRef("13.3", "Deploy a Network Intrusion Detection Solution", 2),
    "13.6": CISRef("13.6", "Collect Network Traffic Flow Logs", 2),
    "13.8": CISRef("13.8", "Deploy a Network Intrusion Prevention Solution", 3),
    "13.10": CISRef("13.10", "Perform Application Layer Filtering", 3),
    
    # Control 17: Incident Response Management
    "17.1": CISRef("17.1", "Designate Personnel to Manage Incident Handling", 1),
    "17.2": CISRef("17.2", "Establish and Maintain Contact Information for Reporting Security Incidents", 1),
    "17.3": CISRef("17.3", "Establish and Maintain an Enterprise Process for Reporting Incidents", 1),
    "17.4": CISRef("17.4", "Establish and Maintain an Incident Response Process", 2),
    "17.5": CISRef("17.5", "Assign Key Roles and Responsibilities", 2),
    "17.6": CISRef("17.6", "Define Mechanisms for Communicating During Incident Response", 2),
    "17.7": CISRef("17.7", "Conduct Routine Incident Response Exercises", 2),
    "17.8": CISRef("17.8", "Conduct Post-Incident Reviews", 2),
    "17.9": CISRef("17.9", "Establish and Maintain Security Incident Thresholds", 3),
}


# =============================================================================
# OWASP TOP 10 2021
# =============================================================================

OWASP_TOP10 = {
    "A01:2021": OWASPRef("A01:2021", "Broken Access Control"),
    "A02:2021": OWASPRef("A02:2021", "Cryptographic Failures"),
    "A03:2021": OWASPRef("A03:2021", "Injection"),
    "A04:2021": OWASPRef("A04:2021", "Insecure Design"),
    "A05:2021": OWASPRef("A05:2021", "Security Misconfiguration"),
    "A06:2021": OWASPRef("A06:2021", "Vulnerable and Outdated Components"),
    "A07:2021": OWASPRef("A07:2021", "Identification and Authentication Failures"),
    "A08:2021": OWASPRef("A08:2021", "Software and Data Integrity Failures"),
    "A09:2021": OWASPRef("A09:2021", "Security Logging and Monitoring Failures"),
    "A10:2021": OWASPRef("A10:2021", "Server-Side Request Forgery"),
}


# =============================================================================
# FINDING RULE TO FRAMEWORK MAPPINGS
# =============================================================================

FRAMEWORK_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    # TELEMETRY & LOGGING
    "TL-001": {  # Insufficient Log Retention
        "mitre": ["T1070", "T1070.001", "T1070.002", "T1562.002"],
        "cis": ["8.3", "8.1"],
        "owasp": ["A09:2021"]
    },
    "TL-002": {  # Missing Centralized Logging
        "mitre": ["T1070", "T1562", "T1562.001"],
        "cis": ["8.9", "8.2", "13.1"],
        "owasp": ["A09:2021"]
    },
    "TL-003": {  # Incomplete Endpoint Logging
        "mitre": ["T1059", "T1059.001", "T1562.001"],
        "cis": ["8.5", "8.2"],
        "owasp": ["A09:2021"]
    },
    "TL-004": {  # No Cloud Logging
        "mitre": ["T1078.004", "T1562.006", "T1098.001"],
        "cis": ["8.11", "8.2"],
        "owasp": ["A09:2021"]
    },
    "TL-005": {  # Auth Events Not Logged
        "mitre": ["T1078", "T1110", "T1110.003"],
        "cis": ["8.5", "8.2"],
        "owasp": ["A09:2021", "A07:2021"]
    },
    "TL-006": {  # Network Device Logging Missing
        "mitre": ["T1070", "T1562", "T1040"],
        "cis": ["8.2", "8.5", "13.6"],
        "owasp": ["A09:2021"]
    },
    
    # DETECTION COVERAGE
    "DC-001": {  # Inadequate EDR Coverage
        "mitre": ["T1059", "T1059.001", "T1105", "T1204.002"],
        "cis": ["10.1", "10.6", "10.7"],
        "owasp": []
    },
    "DC-002": {  # Critical EDR Gap
        "mitre": ["T1486", "T1485", "T1059", "T1105"],
        "cis": ["10.1", "10.6"],
        "owasp": []
    },
    "DC-003": {  # No Network Monitoring
        "mitre": ["T1041", "T1048", "T1071", "T1021"],
        "cis": ["13.3", "13.6", "13.8"],
        "owasp": []
    },
    "DC-004": {  # Stale Detection Rules
        "mitre": ["T1562.001", "T1059"],
        "cis": ["10.2", "10.4"],
        "owasp": []
    },
    "DC-005": {  # No Email Security
        "mitre": ["T1566", "T1566.001", "T1566.002", "T1204.001"],
        "cis": ["9.6", "9.7"],
        "owasp": []
    },
    "DC-006": {  # Slow Alert Triage
        "mitre": ["T1070", "T1562"],
        "cis": ["13.1", "17.4"],
        "owasp": []
    },
    "DC-007": {  # No Custom Detection Rules
        "mitre": ["T1059", "T1204.002", "T1562.001"],
        "cis": ["10.2", "10.4"],
        "owasp": []
    },
    
    # IDENTITY VISIBILITY
    "IV-001": {  # MFA Not Enforced for Admins
        "mitre": ["T1078", "T1078.002", "T1556", "T1110"],
        "cis": ["6.5", "6.3"],
        "owasp": ["A07:2021"]
    },
    "IV-002": {  # MFA Not Enforced Org-Wide
        "mitre": ["T1078", "T1110", "T1556.006"],
        "cis": ["6.4", "6.3"],
        "owasp": ["A07:2021"]
    },
    "IV-003": {  # No Privileged Account Inventory
        "mitre": ["T1087", "T1087.002", "T1078.002", "T1098"],
        "cis": ["5.1", "6.6"],
        "owasp": ["A01:2021"]
    },
    "IV-004": {  # Service Accounts Not Managed
        "mitre": ["T1078", "T1078.001", "T1098"],
        "cis": ["5.4", "5.3"],
        "owasp": ["A07:2021"]
    },
    "IV-005": {  # No PAM Solution
        "mitre": ["T1550", "T1550.002", "T1078.002", "T1098.003"],
        "cis": ["6.8", "6.7", "5.4"],
        "owasp": ["A01:2021"]
    },
    "IV-006": {  # Failed Login Not Monitored
        "mitre": ["T1110", "T1110.001", "T1110.003", "T1078"],
        "cis": ["8.5", "8.11"],
        "owasp": ["A07:2021"]
    },
    
    # INCIDENT RESPONSE
    "IR-001": {  # No IR Playbooks
        "mitre": ["T1486", "T1485"],
        "cis": ["17.4", "17.3"],
        "owasp": []
    },
    "IR-002": {  # IR Playbooks Not Tested
        "mitre": ["T1486"],
        "cis": ["17.7", "17.8"],
        "owasp": []
    },
    "IR-003": {  # No Tabletop Exercises
        "mitre": ["T1486"],
        "cis": ["17.7"],
        "owasp": []
    },
    "IR-004": {  # No IR Team Defined
        "mitre": ["T1486", "T1485"],
        "cis": ["17.1", "17.5"],
        "owasp": []
    },
    "IR-005": {  # No Communication Templates
        "mitre": ["T1486"],
        "cis": ["17.6", "17.2"],
        "owasp": []
    },
    "IR-006": {  # No Escalation Matrix
        "mitre": ["T1486"],
        "cis": ["17.5", "17.6"],
        "owasp": []
    },
    
    # RESILIENCE
    "RS-001": {  # Backups Not Tested
        "mitre": ["T1490", "T1486"],
        "cis": ["11.5", "11.2"],
        "owasp": []
    },
    "RS-002": {  # Backups Not Immutable
        "mitre": ["T1490", "T1485", "T1561"],
        "cis": ["11.3", "11.4"],
        "owasp": []
    },
    "RS-003": {  # Critical Systems Not Backed Up
        "mitre": ["T1486", "T1485", "T1561"],
        "cis": ["11.1", "11.2"],
        "owasp": []
    },
    "RS-004": {  # Excessive RTO
        "mitre": ["T1486"],
        "cis": ["11.1"],
        "owasp": []
    },
    "RS-005": {  # No DR Plan
        "mitre": ["T1490", "T1486"],
        "cis": ["11.1"],
        "owasp": []
    },
    "RS-006": {  # Backup Credentials Not Isolated
        "mitre": ["T1078", "T1490", "T1485"],
        "cis": ["11.3", "11.4", "5.4"],
        "owasp": []
    },
    
    # AGGREGATE RULES
    "AGG-001": {  # Critical Weakness in Telemetry
        "mitre": ["T1070", "T1562"],
        "cis": ["8.1", "8.9"],
        "owasp": ["A09:2021"]
    },
    "AGG-002": {  # Critical Weakness in Identity
        "mitre": ["T1078", "T1556"],
        "cis": ["6.3", "6.5"],
        "owasp": ["A07:2021"]
    },
    "AGG-003": {  # Inadequate Overall Posture
        "mitre": ["T1078", "T1486"],
        "cis": ["17.4"],
        "owasp": []
    },
}


def get_framework_refs(rule_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get framework references for a finding rule_id.
    
    Args:
        rule_id: The finding rule identifier (e.g., "TL-001")
        
    Returns:
        Dict with 'mitre', 'cis', 'owasp' arrays of ref objects
    """
    mapping = FRAMEWORK_MAPPINGS.get(rule_id, {"mitre": [], "cis": [], "owasp": []})
    
    result = {
        "mitre": [],
        "cis": [],
        "owasp": []
    }
    
    # Build MITRE refs
    for tech_id in mapping.get("mitre", []):
        if tech_id in MITRE_TECHNIQUES:
            result["mitre"].append(MITRE_TECHNIQUES[tech_id].to_dict())
    
    # Build CIS refs
    for ctrl_id in mapping.get("cis", []):
        if ctrl_id in CIS_CONTROLS:
            result["cis"].append(CIS_CONTROLS[ctrl_id].to_dict())
    
    # Build OWASP refs
    for owasp_id in mapping.get("owasp", []):
        if owasp_id in OWASP_TOP10:
            result["owasp"].append(OWASP_TOP10[owasp_id].to_dict())
    
    return result


def get_all_unique_techniques(rule_ids: List[str]) -> Dict[str, Any]:
    """
    Get unique technique counts across multiple findings.
    
    Args:
        rule_ids: List of finding rule_ids
        
    Returns:
        Dict with unique technique counts and coverage stats
    """
    unique_mitre = set()
    unique_cis = set()
    unique_owasp = set()
    
    for rule_id in rule_ids:
        mapping = FRAMEWORK_MAPPINGS.get(rule_id, {})
        unique_mitre.update(mapping.get("mitre", []))
        unique_cis.update(mapping.get("cis", []))
        unique_owasp.update(mapping.get("owasp", []))
    
    # Calculate IG coverage
    ig1_controls = [c for c, ref in CIS_CONTROLS.items() if ref.ig_level == 1]
    ig2_controls = [c for c, ref in CIS_CONTROLS.items() if ref.ig_level <= 2]
    ig3_controls = [c for c, ref in CIS_CONTROLS.items() if ref.ig_level <= 3]
    
    ig1_covered = len([c for c in unique_cis if c in ig1_controls])
    ig2_covered = len([c for c in unique_cis if c in ig2_controls])
    ig3_covered = len([c for c in unique_cis if c in ig3_controls])
    
    return {
        "mitre_techniques_total": len(unique_mitre),
        "mitre_techniques": list(unique_mitre),
        "cis_controls_total": len(unique_cis),
        "cis_controls": list(unique_cis),
        "owasp_total": len(unique_owasp),
        "owasp_items": list(unique_owasp),
        "ig1_coverage_pct": round((ig1_covered / len(ig1_controls)) * 100, 1) if ig1_controls else 0,
        "ig2_coverage_pct": round((ig2_covered / len(ig2_controls)) * 100, 1) if ig2_controls else 0,
        "ig3_coverage_pct": round((ig3_covered / len(ig3_controls)) * 100, 1) if ig3_controls else 0,
    }


# Total technique counts for coverage calculation
TOTAL_MITRE_ENTERPRISE_TECHNIQUES = 201  # Approximate count
TOTAL_CIS_V8_CONTROLS = 153
TOTAL_OWASP_TOP10 = 10
