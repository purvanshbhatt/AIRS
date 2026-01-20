"""
AIRS Findings Rules Engine

Deterministic rule-based engine that generates consultant-grade findings
based on assessment answers and domain scores.

Rules are organized by domain and severity, with clear thresholds,
evidence extraction, and specific remediation recommendations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from app.core.rubric import get_rubric, get_question


class Severity(str, Enum):
    """Finding severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FindingRule:
    """Definition of a finding rule."""
    rule_id: str
    title: str
    domain_id: str
    severity: Severity
    condition: callable  # Function that takes (answers, scores) and returns bool
    evidence_fn: callable  # Function that generates evidence string
    recommendation: str
    reference: Optional[str] = None  # NIST, CIS, etc.
    remediation_effort: str = "medium"  # low, medium, high
    

@dataclass
class Finding:
    """Generated finding from a rule."""
    rule_id: str
    title: str
    domain_id: str
    domain_name: str
    severity: Severity
    evidence: str
    recommendation: str
    reference: Optional[str] = None
    remediation_effort: str = "medium"
    question_ids: List[str] = None


def get_answer(answers: Dict[str, Any], question_id: str, default=None):
    """Safely get an answer value."""
    return answers.get(question_id, default)


def get_bool(answers: Dict[str, Any], question_id: str) -> bool:
    """Get answer as boolean."""
    val = answers.get(question_id)
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "yes", "1")
    return bool(val)


def get_numeric(answers: Dict[str, Any], question_id: str, default: float = 0) -> float:
    """Get answer as numeric value."""
    val = answers.get(question_id, default)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def get_domain_score(scores: Dict[str, Any], domain_id: str) -> float:
    """Get domain score (0-5 scale)."""
    if not scores:
        return 0.0
    
    domains = scores.get("domains", [])
    for domain in domains:
        if isinstance(domain, dict) and domain.get("domain_id") == domain_id:
            return domain.get("score", 0.0)
        elif hasattr(domain, "domain_id") and domain.domain_id == domain_id:
            return domain.score
    return 0.0


# =============================================================================
# RULE DEFINITIONS - At least 15 consultant-grade rules
# =============================================================================

FINDING_RULES: List[FindingRule] = [
    
    # =========================================================================
    # TELEMETRY & LOGGING RULES
    # =========================================================================
    
    FindingRule(
        rule_id="TL-001",
        title="Insufficient Log Retention Period",
        domain_id="telemetry_logging",
        severity=Severity.HIGH,
        condition=lambda a, s: get_numeric(a, "tl_05", 0) < 30,
        evidence_fn=lambda a, s: f"Current log retention is {get_numeric(a, 'tl_05', 0):.0f} days. "
                                  f"Industry best practice requires minimum 90 days, with 365 days recommended for compliance.",
        recommendation="Increase log retention to at least 90 days for security investigations. "
                      "For compliance with regulations like GDPR, HIPAA, or PCI-DSS, consider 365+ days. "
                      "Implement tiered storage (hot/warm/cold) to manage costs while maintaining retention.",
        reference="NIST SP 800-92, CIS Control 8.3",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="TL-002",
        title="Missing Centralized Log Management",
        domain_id="telemetry_logging",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "tl_04"),
        evidence_fn=lambda a, s: "Logs are not centralized in a SIEM or log management platform. "
                                  "This significantly hampers incident detection and response capabilities.",
        recommendation="Deploy a centralized SIEM solution (e.g., Microsoft Sentinel, Splunk, Elastic SIEM). "
                      "Ensure all critical systems forward logs. Implement real-time alerting for security events. "
                      "Start with authentication logs, firewall logs, and endpoint detection logs as priorities.",
        reference="NIST CSF DE.CM-1, CIS Control 8.2",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="TL-003",
        title="Incomplete Endpoint Logging Coverage",
        domain_id="telemetry_logging",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "tl_02"),
        evidence_fn=lambda a, s: "Endpoint logs (workstations, servers) are not being collected. "
                                  "Endpoint visibility is critical for detecting lateral movement and malware.",
        recommendation="Deploy endpoint logging agents across all workstations and servers. "
                      "Collect Windows Security, PowerShell, and Sysmon logs at minimum. "
                      "For Linux systems, collect auth.log, syslog, and auditd events.",
        reference="CIS Control 8.5",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="TL-004",
        title="No Cloud Service Logging",
        domain_id="telemetry_logging",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "tl_03"),
        evidence_fn=lambda a, s: "Cloud service logs (Azure/AWS/GCP) are not being collected. "
                                  "Cloud environments are frequent attack targets and require visibility.",
        recommendation="Enable and centralize cloud audit logs: Azure Activity Log and Entra ID logs, "
                      "AWS CloudTrail and GuardDuty, or GCP Cloud Audit Logs. "
                      "Forward these to your SIEM for correlation with on-premises events.",
        reference="CIS Control 8.11, CSA CCM LOG-01",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="TL-005",
        title="Authentication Events Not Logged",
        domain_id="telemetry_logging",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "tl_06"),
        evidence_fn=lambda a, s: "Authentication and authorization events are not logged across critical systems. "
                                  "This is a fundamental security gap that prevents detection of unauthorized access.",
        recommendation="Implement comprehensive authentication logging including: successful and failed logins, "
                      "privilege escalation, account lockouts, password changes, and MFA events. "
                      "Configure alerts for anomalous authentication patterns (brute force, impossible travel).",
        reference="NIST SP 800-53 AU-2, CIS Control 8.5",
        remediation_effort="medium"
    ),
    
    # =========================================================================
    # DETECTION COVERAGE RULES
    # =========================================================================
    
    FindingRule(
        rule_id="DC-001",
        title="Inadequate EDR Coverage",
        domain_id="detection_coverage",
        severity=Severity.HIGH,
        condition=lambda a, s: get_numeric(a, "dc_01", 0) < 80,
        evidence_fn=lambda a, s: f"EDR agent coverage is {get_numeric(a, 'dc_01', 0):.0f}%. "
                                  f"Target coverage should be 95%+ for effective endpoint protection.",
        recommendation="Deploy EDR agents to all endpoints including workstations, servers, and VDI instances. "
                      "Prioritize high-value assets (domain controllers, file servers, developer machines). "
                      "Implement automated deployment via group policy or endpoint management tools. "
                      "Track coverage metrics weekly and investigate any gaps.",
        reference="NIST CSF DE.CM-4, CIS Control 10.1",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="DC-002",
        title="Critical EDR Gap - Less Than 50% Coverage",
        domain_id="detection_coverage",
        severity=Severity.CRITICAL,
        condition=lambda a, s: get_numeric(a, "dc_01", 0) < 50,
        evidence_fn=lambda a, s: f"EDR coverage is critically low at {get_numeric(a, 'dc_01', 0):.0f}%. "
                                  f"More than half of endpoints lack detection capabilities, creating major blind spots.",
        recommendation="URGENT: Initiate emergency EDR deployment program. Identify and prioritize unprotected "
                      "endpoints immediately. Consider temporary compensating controls (host-based firewall rules, "
                      "network segmentation) for high-risk unprotected systems. Escalate to leadership as critical risk.",
        reference="NIST CSF DE.CM-4",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="DC-003",
        title="No Network Traffic Monitoring",
        domain_id="detection_coverage",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "dc_02"),
        evidence_fn=lambda a, s: "Network traffic monitoring (NDR/IDS/IPS) is not deployed. "
                                  "Network-level visibility is essential for detecting lateral movement and data exfiltration.",
        recommendation="Deploy network detection capabilities at key network segments: perimeter, "
                      "data center, and between security zones. Consider NDR solutions with behavioral analytics. "
                      "At minimum, enable NetFlow/IPFIX collection for traffic analysis.",
        reference="NIST CSF DE.CM-1, CIS Control 13.3",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="DC-004",
        title="Stale Detection Rules",
        domain_id="detection_coverage",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "dc_03"),
        evidence_fn=lambda a, s: "Detection rules and signatures are not updated at least weekly. "
                                  "Threat actors continuously evolve tactics; stale rules create detection gaps.",
        recommendation="Configure automatic signature updates for all detection tools. "
                      "Subscribe to threat intelligence feeds. Review and tune custom detection rules monthly. "
                      "Implement detection-as-code practices for version control and CI/CD of detection logic.",
        reference="CIS Control 10.4",
        remediation_effort="low"
    ),
    
    FindingRule(
        rule_id="DC-005",
        title="No Email Security Protection",
        domain_id="detection_coverage",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "dc_05"),
        evidence_fn=lambda a, s: "Email security/anti-phishing protection is not in place. "
                                  "Email remains the #1 attack vector; 90%+ of breaches start with phishing.",
        recommendation="Deploy comprehensive email security: anti-spam, anti-malware, URL sandboxing, "
                      "and attachment detonation. Enable DMARC, DKIM, and SPF for email authentication. "
                      "Implement user-reported phishing workflow. Consider advanced solutions with AI-based "
                      "business email compromise (BEC) detection.",
        reference="CIS Control 9.6, NIST SP 800-177",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="DC-006",
        title="Slow Alert Triage",
        domain_id="detection_coverage",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "dc_06"),
        evidence_fn=lambda a, s: "Security alerts are not triaged within 24 hours. "
                                  "Delayed triage allows attackers extended dwell time to achieve objectives.",
        recommendation="Establish 24-hour SLA for initial alert triage. Implement alert prioritization based on "
                      "asset criticality and threat severity. Consider SOAR automation for initial enrichment. "
                      "If resources are limited, prioritize by: authentication anomalies, malware detections, "
                      "data exfiltration indicators.",
        reference="NIST CSF RS.AN-1",
        remediation_effort="medium"
    ),
    
    # =========================================================================
    # IDENTITY VISIBILITY RULES
    # =========================================================================
    
    FindingRule(
        rule_id="IV-001",
        title="MFA Not Enforced for Administrators",
        domain_id="identity_visibility",
        severity=Severity.CRITICAL,
        condition=lambda a, s: not get_bool(a, "iv_02"),
        evidence_fn=lambda a, s: "Multi-factor authentication is not enforced for privileged/admin accounts. "
                                  "Compromised admin credentials without MFA enable complete environment takeover.",
        recommendation="IMMEDIATE ACTION REQUIRED: Enable MFA for all administrative accounts within 48 hours. "
                      "Prioritize: Domain Admins, Azure/AWS admins, backup admins, security tool admins. "
                      "Use phishing-resistant MFA (FIDO2, Windows Hello) where possible. "
                      "Implement Conditional Access policies to enforce MFA from any location.",
        reference="NIST SP 800-63B, CIS Control 6.3, CISA Known Exploited Vulnerability guidance",
        remediation_effort="low"
    ),
    
    FindingRule(
        rule_id="IV-002",
        title="MFA Not Enforced Organization-Wide",
        domain_id="identity_visibility",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "iv_01"),
        evidence_fn=lambda a, s: "Multi-factor authentication is not enforced for all users. "
                                  "Credential theft and phishing attacks succeed without MFA protection.",
        recommendation="Implement MFA for all users across all applications. Start with cloud applications "
                      "and VPN access. Use Conditional Access to enforce based on risk level. "
                      "Provide user training on MFA enrollment and usage. Target 100% coverage within 90 days.",
        reference="NIST SP 800-63B, CIS Control 6.4",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="IV-003",
        title="No Privileged Account Inventory",
        domain_id="identity_visibility",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "iv_03"),
        evidence_fn=lambda a, s: "There is no complete inventory of privileged accounts. "
                                  "Unknown admin accounts are common attack targets and persistence mechanisms.",
        recommendation="Conduct immediate privileged account discovery across AD, cloud platforms, and applications. "
                      "Document all accounts with elevated permissions. Remove unnecessary admin rights. "
                      "Implement quarterly access reviews. Use PAM tools to maintain ongoing inventory.",
        reference="CIS Control 5.1, NIST SP 800-53 AC-2",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="IV-004",
        title="Service Accounts Not Managed",
        domain_id="identity_visibility",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "iv_04"),
        evidence_fn=lambda a, s: "Service accounts are not inventoried or regularly reviewed. "
                                  "Service accounts often have excessive permissions and rarely-rotated passwords.",
        recommendation="Create a service account inventory with owner, purpose, and permissions documented. "
                      "Implement service account password rotation (90 days or less). "
                      "Use Group Managed Service Accounts (gMSA) where possible. "
                      "Remove interactive logon rights from service accounts.",
        reference="CIS Control 5.4",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="IV-005",
        title="No Privileged Access Management Solution",
        domain_id="identity_visibility",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "iv_05"),
        evidence_fn=lambda a, s: "No Privileged Access Management (PAM) solution is deployed. "
                                  "PAM provides critical controls for credential vaulting, session recording, and JIT access.",
        recommendation="Evaluate and deploy a PAM solution for credential vaulting, just-in-time access, "
                      "and session monitoring. Prioritize protection of: domain admin credentials, "
                      "cloud admin accounts, database admin accounts, and backup system credentials.",
        reference="NIST SP 800-53 AC-6, CIS Control 6.8",
        remediation_effort="high"
    ),
    
    # =========================================================================
    # INCIDENT RESPONSE RULES
    # =========================================================================
    
    FindingRule(
        rule_id="IR-001",
        title="No Documented IR Playbooks",
        domain_id="ir_process",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "ir_01"),
        evidence_fn=lambda a, s: "Incident response playbooks do not exist. "
                                  "Without documented procedures, incident response is ad-hoc and error-prone.",
        recommendation="Develop playbooks for common incident types: ransomware, phishing, data breach, "
                      "insider threat, DDoS, and business email compromise. Include: detection criteria, "
                      "containment steps, eradication procedures, recovery steps, and communication templates. "
                      "Base playbooks on NIST SP 800-61 framework.",
        reference="NIST SP 800-61, CIS Control 17.4",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="IR-002",
        title="IR Playbooks Not Tested",
        domain_id="ir_process",
        severity=Severity.HIGH,
        condition=lambda a, s: get_bool(a, "ir_01") and not get_bool(a, "ir_02"),
        evidence_fn=lambda a, s: "IR playbooks exist but have not been tested in the last 12 months. "
                                  "Untested procedures often fail during real incidents due to outdated information or gaps.",
        recommendation="Conduct tabletop exercises for each playbook annually at minimum. "
                      "Include cross-functional participants (IT, Security, Legal, Communications). "
                      "Document lessons learned and update playbooks accordingly. "
                      "Consider purple team exercises to validate detection and response capabilities.",
        reference="NIST SP 800-61, CIS Control 17.7",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="IR-003",
        title="No Tabletop Exercises Conducted",
        domain_id="ir_process",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "ir_06"),
        evidence_fn=lambda a, s: "Tabletop exercises have not been conducted in the past year. "
                                  "Regular exercises build muscle memory and identify gaps before real incidents.",
        recommendation="Schedule quarterly tabletop exercises covering different scenarios. "
                      "Year 1 focus: ransomware, phishing with credential theft, insider data theft, "
                      "third-party breach notification. Involve executives in at least one annual exercise.",
        reference="NIST CSF PR.IP-10, CIS Control 17.7",
        remediation_effort="low"
    ),
    
    FindingRule(
        rule_id="IR-004",
        title="No Defined IR Team or Roles",
        domain_id="ir_process",
        severity=Severity.MEDIUM,
        condition=lambda a, s: not get_bool(a, "ir_03"),
        evidence_fn=lambda a, s: "There is no defined incident response team with clear roles. "
                                  "Role ambiguity during incidents leads to delays and miscommunication.",
        recommendation="Establish a formal IR team with defined roles: Incident Commander, Technical Lead, "
                      "Communications Lead, Legal Liaison. Document escalation procedures. "
                      "Ensure 24/7 coverage through on-call rotation or managed security services.",
        reference="NIST SP 800-61 Section 2.4",
        remediation_effort="low"
    ),
    
    # =========================================================================
    # RESILIENCE RULES
    # =========================================================================
    
    FindingRule(
        rule_id="RS-001",
        title="Backups Not Tested",
        domain_id="resilience",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "rs_03"),
        evidence_fn=lambda a, s: "Backup restores have not been tested in the last 6 months. "
                                  "Untested backups may fail when needed most during a ransomware attack or disaster.",
        recommendation="Implement quarterly backup restoration tests for critical systems. "
                      "Test full system recovery, not just file-level restores. Document recovery time "
                      "and compare against RTO targets. Include Active Directory, email, ERP, and file servers.",
        reference="CIS Control 11.5, NIST SP 800-34",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="RS-002",
        title="Backups Not Immutable or Air-Gapped",
        domain_id="resilience",
        severity=Severity.CRITICAL,
        condition=lambda a, s: get_bool(a, "rs_01") and not get_bool(a, "rs_02"),
        evidence_fn=lambda a, s: "Backups exist but are not stored offline, immutable, or air-gapped. "
                                  "Ransomware specifically targets backup systems to prevent recovery.",
        recommendation="CRITICAL: Implement immutable backup storage immediately. Options include: "
                      "cloud immutable storage (Azure Immutable Blob, AWS S3 Object Lock), "
                      "offline tape rotation, or air-gapped backup infrastructure. "
                      "Ensure backup admin credentials are separate from domain credentials. "
                      "Test that backups cannot be deleted by compromised admin accounts.",
        reference="CISA Ransomware Guide, CIS Control 11.3",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="RS-003",
        title="Critical Systems Not Backed Up",
        domain_id="resilience",
        severity=Severity.CRITICAL,
        condition=lambda a, s: not get_bool(a, "rs_01"),
        evidence_fn=lambda a, s: "Critical systems are not backed up regularly. "
                                  "Without backups, any destructive attack or failure results in permanent data loss.",
        recommendation="IMMEDIATE: Identify and backup all critical systems including: domain controllers, "
                      "file servers, databases, email, ERP/CRM, and security tools. "
                      "Implement 3-2-1 backup rule: 3 copies, 2 different media types, 1 offsite. "
                      "Document backup schedules and verify completion daily.",
        reference="CIS Control 11.1, NIST SP 800-34",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="RS-004",
        title="Excessive Recovery Time Objective",
        domain_id="resilience",
        severity=Severity.MEDIUM,
        condition=lambda a, s: get_numeric(a, "rs_05", 999) > 72,
        evidence_fn=lambda a, s: f"Recovery Time Objective (RTO) is {get_numeric(a, 'rs_05', 999):.0f} hours. "
                                  f"Extended downtime significantly impacts business operations and revenue.",
        recommendation="Review and reduce RTO for critical systems. Consider: pre-staged recovery environments, "
                      "automated failover capabilities, or disaster recovery as a service (DRaaS). "
                      "Align RTO with business impact analysis. Most organizations target 24 hours or less "
                      "for critical systems.",
        reference="NIST SP 800-34",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="RS-005",
        title="No Disaster Recovery Plan",
        domain_id="resilience",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "rs_04"),
        evidence_fn=lambda a, s: "A documented disaster recovery plan does not exist. "
                                  "Without a DR plan, recovery from major incidents is chaotic and prolonged.",
        recommendation="Develop a comprehensive DR plan covering: recovery priorities, RTO/RPO targets, "
                      "recovery procedures, communication plans, and alternate site procedures. "
                      "Test the DR plan annually. Ensure the plan is accessible during an incident "
                      "(not only stored on systems that may be unavailable).",
        reference="NIST SP 800-34, ISO 22301",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="RS-006",
        title="Backup Credentials Not Isolated",
        domain_id="resilience",
        severity=Severity.HIGH,
        condition=lambda a, s: not get_bool(a, "rs_06"),
        evidence_fn=lambda a, s: "Backup system credentials are not separate from primary domain credentials. "
                                  "If domain is compromised, attackers can access and destroy backups.",
        recommendation="Create separate, dedicated accounts for backup administration. "
                      "Do not join backup infrastructure to the primary domain. "
                      "Use separate MFA tokens for backup admin access. "
                      "Consider separate network segment for backup infrastructure.",
        reference="CISA Ransomware Guide, CIS Control 11.4",
        remediation_effort="medium"
    ),
    
    # =========================================================================
    # DOMAIN-LEVEL AGGREGATE RULES
    # =========================================================================
    
    FindingRule(
        rule_id="AGG-001",
        title="Critical Weakness in Telemetry & Logging",
        domain_id="telemetry_logging",
        severity=Severity.HIGH,
        condition=lambda a, s: get_domain_score(s, "telemetry_logging") < 2.0,
        evidence_fn=lambda a, s: f"Telemetry & Logging domain score is {get_domain_score(s, 'telemetry_logging'):.1f}/5.0. "
                                  f"Fundamental visibility gaps exist that prevent effective threat detection.",
        recommendation="Prioritize logging infrastructure improvements. Start with: "
                      "1) Deploy centralized log management, 2) Enable authentication logging, "
                      "3) Increase retention to 90+ days. Consider engaging a managed security service "
                      "provider (MSSP) to accelerate maturity.",
        reference="NIST CSF DE.CM-1",
        remediation_effort="high"
    ),
    
    FindingRule(
        rule_id="AGG-002",
        title="Critical Weakness in Identity Security",
        domain_id="identity_visibility",
        severity=Severity.CRITICAL,
        condition=lambda a, s: get_domain_score(s, "identity_visibility") < 2.0,
        evidence_fn=lambda a, s: f"Identity Visibility domain score is {get_domain_score(s, 'identity_visibility'):.1f}/5.0. "
                                  f"Identity is the new perimeter; critical gaps enable credential-based attacks.",
        recommendation="URGENT: Address identity security gaps immediately. Priority actions: "
                      "1) Enable MFA for all admins within 48 hours, 2) Inventory all privileged accounts, "
                      "3) Enable MFA for all users within 30 days. Identity attacks are the most common "
                      "initial access vector.",
        reference="NIST CSF PR.AC-1",
        remediation_effort="medium"
    ),
    
    FindingRule(
        rule_id="AGG-003",
        title="Inadequate Overall Security Posture",
        domain_id="ir_process",  # Assign to IR as it's about overall readiness
        severity=Severity.HIGH,
        condition=lambda a, s: s.get("overall_score", 0) < 40 if isinstance(s, dict) else False,
        evidence_fn=lambda a, s: f"Overall security readiness score is {s.get('overall_score', 0):.0f}/100. "
                                  f"This indicates significant gaps across multiple security domains.",
        recommendation="Develop a prioritized security improvement roadmap. Focus on high-impact, "
                      "low-effort improvements first: MFA, EDR coverage, backup testing. "
                      "Consider engaging external security consultants for gap assessment and roadmap development. "
                      "Present findings to executive leadership with risk context.",
        reference="NIST CSF",
        remediation_effort="high"
    ),
]


class FindingsEngine:
    """
    Deterministic rule-based findings engine.
    
    Evaluates assessment answers and scores against defined rules
    to generate consultant-grade findings with specific recommendations.
    """
    
    def __init__(self, rules: List[FindingRule] = None):
        self.rules = rules or FINDING_RULES
        self._rubric = get_rubric()
    
    def _get_domain_name(self, domain_id: str) -> str:
        """Get domain display name from rubric."""
        domain = self._rubric["domains"].get(domain_id, {})
        return domain.get("name", domain_id)
    
    def evaluate(self, answers: Dict[str, Any], scores: Dict[str, Any] = None) -> List[Finding]:
        """
        Evaluate all rules against answers and scores.
        
        Args:
            answers: Dict mapping question_id to answer value
            scores: Optional scoring result from calculate_scores()
        
        Returns:
            List of Finding objects for triggered rules
        """
        findings = []
        scores = scores or {}
        
        for rule in self.rules:
            try:
                # Check if rule condition is met
                if rule.condition(answers, scores):
                    # Generate finding
                    finding = Finding(
                        rule_id=rule.rule_id,
                        title=rule.title,
                        domain_id=rule.domain_id,
                        domain_name=self._get_domain_name(rule.domain_id),
                        severity=rule.severity,
                        evidence=rule.evidence_fn(answers, scores),
                        recommendation=rule.recommendation,
                        reference=rule.reference,
                        remediation_effort=rule.remediation_effort,
                        question_ids=self._get_related_questions(rule.rule_id)
                    )
                    findings.append(finding)
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error evaluating rule {rule.rule_id}: {e}")
                continue
        
        # Sort by severity (critical first) then by rule_id
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        findings.sort(key=lambda f: (severity_order.get(f.severity, 5), f.rule_id))
        
        return findings
    
    def _get_related_questions(self, rule_id: str) -> List[str]:
        """Map rule IDs to related question IDs."""
        # Mapping based on rule patterns
        rule_question_map = {
            "TL-001": ["tl_05"],
            "TL-002": ["tl_04"],
            "TL-003": ["tl_02"],
            "TL-004": ["tl_03"],
            "TL-005": ["tl_06"],
            "DC-001": ["dc_01"],
            "DC-002": ["dc_01"],
            "DC-003": ["dc_02"],
            "DC-004": ["dc_03"],
            "DC-005": ["dc_05"],
            "DC-006": ["dc_06"],
            "IV-001": ["iv_02"],
            "IV-002": ["iv_01"],
            "IV-003": ["iv_03"],
            "IV-004": ["iv_04"],
            "IV-005": ["iv_05"],
            "IR-001": ["ir_01"],
            "IR-002": ["ir_01", "ir_02"],
            "IR-003": ["ir_06"],
            "IR-004": ["ir_03"],
            "RS-001": ["rs_03"],
            "RS-002": ["rs_01", "rs_02"],
            "RS-003": ["rs_01"],
            "RS-004": ["rs_05"],
            "RS-005": ["rs_04"],
            "RS-006": ["rs_06"],
        }
        return rule_question_map.get(rule_id, [])
    
    def get_summary(self, findings: List[Finding]) -> Dict[str, Any]:
        """
        Generate summary statistics for findings.
        
        Args:
            findings: List of findings from evaluate()
        
        Returns:
            Summary dict with counts and priorities
        """
        summary = {
            "total": len(findings),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            },
            "by_domain": {},
            "by_effort": {
                "low": 0,
                "medium": 0,
                "high": 0
            },
            "top_priorities": []
        }
        
        for finding in findings:
            # Count by severity
            severity_key = finding.severity.value if hasattr(finding.severity, 'value') else finding.severity
            if severity_key in summary["by_severity"]:
                summary["by_severity"][severity_key] += 1
            
            # Count by domain
            domain = finding.domain_name
            summary["by_domain"][domain] = summary["by_domain"].get(domain, 0) + 1
            
            # Count by effort
            effort = finding.remediation_effort
            if effort in summary["by_effort"]:
                summary["by_effort"][effort] += 1
        
        # Top priorities: critical and high with low/medium effort
        priority_findings = [
            f for f in findings 
            if f.severity in (Severity.CRITICAL, Severity.HIGH)
            and f.remediation_effort in ("low", "medium")
        ]
        summary["top_priorities"] = [
            {"rule_id": f.rule_id, "title": f.title, "severity": f.severity.value}
            for f in priority_findings[:5]
        ]
        
        return summary


def generate_findings(answers: Dict[str, Any], scores: Dict[str, Any] = None) -> List[Finding]:
    """
    Convenience function to generate findings from answers and scores.
    
    Args:
        answers: Dict mapping question_id to answer value
        scores: Optional scoring result from calculate_scores()
    
    Returns:
        List of Finding objects
    """
    engine = FindingsEngine()
    return engine.evaluate(answers, scores)


def get_findings_summary(findings: List[Finding]) -> Dict[str, Any]:
    """
    Convenience function to get findings summary.
    
    Args:
        findings: List of findings
    
    Returns:
        Summary dict
    """
    engine = FindingsEngine()
    return engine.get_summary(findings)
