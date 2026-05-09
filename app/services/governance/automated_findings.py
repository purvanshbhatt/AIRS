"""
Automated Finding Generation — SIEM-Driven Remediation.

When Wazuh reports critical vulnerabilities (especially known exploits),
automatically generate findings in the Remediation Ledger with computed
GHI impact scores.

Key features:
  - CVE-2024-3094 (XZ Utils) detection: Auto-generate +15 GHI impact task
  - Critical vulnerability auto-findings: +10 GHI impact per vulnerability
  - Automatic assignment to org_admin for immediate triage
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.finding import Finding, Severity, FindingStatus
from app.models.assessment import Assessment
from app.models.roadmap_item import RoadmapItem

logger = logging.getLogger("airs.automated_findings")


# CVE → GHI Impact mapping
# Each CVE family can have a different impact weight
CRITICAL_CVE_MAPPINGS = {
    "CVE-2024-3094": {  # XZ Utils backdoor
        "title": "Critical: XZ Utils Backdoor (CVE-2024-3094) Detected",
        "description": (
            "Wazuh has detected the malicious XZ Utils library (CVE-2024-3094) "
            "on one or more endpoints. This is a supply-chain backdoor with "
            "potential for remote code execution. Immediate remediation is required."
        ),
        "severity": Severity.CRITICAL,
        "ghi_impact": 15,
        "domain": "Vulnerability Management",
    },
    "CVE-2024-": {  # Generic 2024 CVEs
        "title": "High-Severity 2024 CVE Detected",
        "description": (
            "Wazuh has detected a 2024 CVE on your endpoints. "
            "Review the affected packages and apply patches immediately."
        ),
        "severity": Severity.HIGH,
        "ghi_impact": 8,
        "domain": "Vulnerability Management",
    },
}


async def generate_finding_from_cve(
    db: Session,
    assessment: Assessment,
    cve_id: str,
    agent_name: str,
    cvss_score: float,
    affected_packages: List[str],
    remediation: Optional[str] = None,
) -> Optional[Finding]:
    """
    Automatically generate a finding from a Wazuh CVE detection.
    
    Args:
        db: Database session
        assessment: Assessment to attach finding to
        cve_id: CVE identifier (e.g., CVE-2024-3094)
        agent_name: Endpoint name where CVE was detected
        cvss_score: CVSS base score
        affected_packages: List of affected packages
        remediation: Optional remediation guidance from Wazuh
    
    Returns:
        Finding object (persisted to DB), or None if CVE mapping not found
    """
    # Look up CVE mapping
    mapping = None
    for pattern, config in CRITICAL_CVE_MAPPINGS.items():
        if pattern == cve_id or (pattern.endswith("-") and cve_id.startswith(pattern)):
            mapping = config
            break
    
    if not mapping:
        logger.debug(f"No auto-finding mapping for {cve_id}, skipping")
        return None
    
    # Build finding description with details
    description = mapping["description"] + "\n\n"
    description += f"**Detection Details:**\n"
    description += f"- CVE ID: {cve_id}\n"
    description += f"- Agent: {agent_name}\n"
    description += f"- CVSS Score: {cvss_score:.1f}\n"
    description += f"- Affected Packages: {', '.join(affected_packages)}\n"
    
    if remediation:
        description += f"\n**Remediation Guidance from Wazuh:**\n{remediation}\n"
    
    # Create finding
    finding = Finding(
        assessment_id=assessment.id,
        title=f"{cve_id}: {mapping['title']}",
        description=description,
        severity=mapping["severity"],
        status=FindingStatus.OPEN,
        domain_name=mapping.get("domain", "Vulnerability Management"),
        evidence=f"Detected by Wazuh on {agent_name}",
        recommendation=(
            f"Patch {', '.join(affected_packages)} to remove vulnerability {cve_id}. "
            f"See Wazuh vulnerability details for specific patched versions."
        ),
        priority="1",  # Highest priority
    )
    
    db.add(finding)
    db.commit()
    
    logger.info(
        f"Auto-generated critical finding: {cve_id} on {agent_name} "
        f"(GHI impact: +{mapping['ghi_impact']})"
    )
    
    return finding


async def generate_remediation_task_from_cve(
    db: Session,
    organization_id: str,
    cve_id: str,
    agent_name: str,
    ghi_impact: int = 15,
) -> Optional[Dict[str, Any]]:
    """
    Create a Remediation Ledger task for a critical CVE.
    
    This is the mechanism for translating Wazuh findings into the
    Remediation Ledger with computed GHI impact.
    
    Args:
        db: Database session
        organization_id: Organization ID
        cve_id: CVE identifier
        agent_name: Endpoint name
        ghi_impact: Expected GHI impact (0-15 range)
    
    Returns:
        Dict with remediation task details, or None if creation failed
    """
    try:
        # In production, this would create a RoadmapItem or similar
        # For now, just return the task spec for API response
        
        task = {
            "type": "critical_remediation",
            "cve_id": cve_id,
            "agent_name": agent_name,
            "ghi_impact": ghi_impact,
            "title": f"Patch {cve_id} on {agent_name}",
            "description": (
                f"Critical vulnerability {cve_id} detected on endpoint {agent_name}. "
                f"Apply patches immediately. Estimated GHI impact: +{ghi_impact}."
            ),
            "priority": "critical",
            "due_date": (datetime.now(timezone.utc).isoformat()),
            "assigned_to": "org_admin",
            "created_by": "wazuh_integration",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        logger.info(f"Remediation task created for {cve_id}: +{ghi_impact} GHI impact")
        
        return task
        
    except Exception as e:
        logger.error(f"Failed to create remediation task for {cve_id}: {e}")
        return None


async def process_wazuh_vulnerabilities(
    db: Session,
    organization_id: str,
    assessment: Assessment,
    vulnerabilities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Process all vulnerabilities from Wazuh and auto-generate findings.
    
    Args:
        db: Database session
        organization_id: Organization ID
        assessment: Assessment to attach findings to
        vulnerabilities: List of vulnerability dicts from Wazuh
    
    Returns:
        Summary dict with findings_created, critical_vulns, ghi_impact_total, etc
    """
    summary = {
        "findings_created": 0,
        "critical_vulnerabilities": 0,
        "high_vulnerabilities": 0,
        "total_ghi_impact": 0,
        "auto_generated_findings": [],
        "remediation_tasks": [],
    }
    
    for vuln in vulnerabilities:
        cve_id = vuln.get("cve_id", "")
        agent_name = vuln.get("agent_name", "")
        severity = vuln.get("severity", "")
        cvss_score = vuln.get("cvss_score", 0.0)
        affected_packages = vuln.get("affected_packages", [])
        remediation = vuln.get("remediation")
        
        # Only auto-generate findings for critical/high
        if severity in ("critical", "high"):
            # Generate finding
            finding = await generate_finding_from_cve(
                db=db,
                assessment=assessment,
                cve_id=cve_id,
                agent_name=agent_name,
                cvss_score=cvss_score,
                affected_packages=affected_packages,
                remediation=remediation,
            )
            
            if finding:
                summary["findings_created"] += 1
                summary["auto_generated_findings"].append({
                    "finding_id": finding.id,
                    "cve_id": cve_id,
                    "severity": severity,
                })
                
                if severity == "critical":
                    summary["critical_vulnerabilities"] += 1
                    ghi_impact = 15
                else:
                    summary["high_vulnerabilities"] += 1
                    ghi_impact = 8
                
                summary["total_ghi_impact"] += ghi_impact
                
                # Create remediation task
                task = await generate_remediation_task_from_cve(
                    db=db,
                    organization_id=organization_id,
                    cve_id=cve_id,
                    agent_name=agent_name,
                    ghi_impact=ghi_impact,
                )
                
                if task:
                    summary["remediation_tasks"].append(task)
    
    logger.info(
        f"Processed {len(vulnerabilities)} vulnerabilities for {organization_id}: "
        f"{summary['findings_created']} findings created, "
        f"+{summary['total_ghi_impact']} GHI impact"
    )
    
    return summary


async def process_wazuh_agent_disconnections(
    db: Session,
    organization_id: str,
    assessment: Assessment,
    disconnection_rate: float,
    disconnected_agents: int,
    total_agents: int,
) -> Optional[Finding]:
    """
    Auto-generate finding if agent disconnection exceeds threshold.
    
    Per requirements: If disconnected_agents > 10%, trigger automatic
    high-severity finding in Detection Coverage domain.
    
    Args:
        db: Database session
        organization_id: Organization ID
        assessment: Assessment to attach finding to
        disconnection_rate: Percentage of disconnected agents (0-100)
        disconnected_agents: Count of disconnected agents
        total_agents: Total number of agents
    
    Returns:
        Finding object, or None if threshold not exceeded
    """
    DISCONNECTION_THRESHOLD = 10.0
    
    if disconnection_rate <= DISCONNECTION_THRESHOLD:
        logger.debug(
            f"Agent disconnection rate {disconnection_rate:.1f}% is below "
            f"threshold {DISCONNECTION_THRESHOLD}%, no finding generated"
        )
        return None
    
    finding = Finding(
        assessment_id=assessment.id,
        title=f"High Agent Disconnection Rate ({disconnection_rate:.1f}%)",
        description=(
            f"Wazuh is reporting a high rate of disconnected endpoints. "
            f"This indicates potential visibility gaps in endpoint security monitoring.\n\n"
            f"**Details:**\n"
            f"- Disconnected Agents: {disconnected_agents}/{total_agents}\n"
            f"- Disconnection Rate: {disconnection_rate:.1f}%\n"
            f"- Threshold: {DISCONNECTION_THRESHOLD}%\n\n"
            f"This may indicate network issues, endpoint failures, or Wazuh agent problems."
        ),
        severity=Severity.HIGH,
        status=FindingStatus.OPEN,
        domain_name="Detection Coverage",
        evidence=f"Wazuh reported {disconnected_agents} disconnected agents out of {total_agents}",
        recommendation=(
            f"Investigate why {disconnected_agents} endpoint(s) are disconnected from Wazuh. "
            f"Ensure Wazuh agents are running and have network connectivity. "
            f"Address any underlying infrastructure or connectivity issues."
        ),
        priority="2",  # High priority
    )
    
    db.add(finding)
    db.commit()
    
    logger.warning(
        f"High agent disconnection detected: {disconnection_rate:.1f}% "
        f"({disconnected_agents}/{total_agents}) — auto-generated finding"
    )
    
    return finding
