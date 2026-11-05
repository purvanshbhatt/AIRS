from typing import Optional, List
from datetime import datetime
from app.services.clinic_engine.v2.contracts import ExecutiveExplanation, VerificationContext, ActionCard
from app.services.clinic_engine.v2.schema import ClinicMoment

# Deterministic taxonomy mapping
TAXONOMY = {
    # Access and Identity
    "unauthorized_access": {
        "business_label": "Who Can Access Your Systems",
        "technical_label": "Identity & Access Management",
        "what_it_means": "ResilAI verifies that only current, authorized staff can access clinic data.",
        "why_it_matters": "Former employees or unauthorized users could access sensitive patient records, leading to HIPAA violations.",
    },
    "suspicious_login": {
        "business_label": "Who Can Access Your Systems",
        "technical_label": "Identity & Access Management",
        "what_it_means": "ResilAI monitors for unusual sign-in activity.",
        "why_it_matters": "Attackers often try to steal passwords. Unusual logins are the first sign of a compromised account.",
    },
    "mfa_disabled": {
        "business_label": "Login Protection",
        "technical_label": "Multi-Factor Authentication (MFA)",
        "what_it_means": "ResilAI verifies that a second form of proof is required to sign in.",
        "why_it_matters": "Passwords alone are easily stolen. Without a second step, attackers can easily access email and patient data.",
    },
    "former_employee_access": {
        "business_label": "Who Can Access Your Systems",
        "technical_label": "Identity & Access Management",
        "what_it_means": "ResilAI verifies that former employees no longer have active accounts.",
        "why_it_matters": "Terminated staff retaining access is a major compliance violation and data theft risk.",
    },
    # Devices and Endpoints
    "device_compromise": {
        "business_label": "Computer Protection",
        "technical_label": "Endpoint Detection & Response (EDR)",
        "what_it_means": "ResilAI verifies that all computers are protected against malware and hackers.",
        "why_it_matters": "A single unprotected computer can allow attackers to deploy ransomware across the entire clinic.",
    },
    "missing_updates": {
        "business_label": "Finding Weaknesses Before Attackers Do",
        "technical_label": "Vulnerability Management",
        "what_it_means": "ResilAI checks if clinic computers have the latest security updates.",
        "why_it_matters": "Hackers use known vulnerabilities to break into systems. Missing updates make it easy for them.",
    },
    "av_disabled": {
        "business_label": "Computer Protection",
        "technical_label": "Antivirus / Endpoint Security",
        "what_it_means": "ResilAI verifies that security software is active on clinic computers.",
        "why_it_matters": "Without active protection, a computer will silently download malware when browsing the web or opening emails.",
    },
    # Recovery
    "recovery_readiness": {
        "business_label": "Ability to Recover Your Data",
        "technical_label": "Backup / Recovery",
        "what_it_means": "ResilAI verifies that your patient data and critical systems are regularly backed up.",
        "why_it_matters": "If ransomware strikes or a server fails, verified backups are the only way to recover operations without paying extortion.",
    },
    # Email
    "email_security": {
        "business_label": "Email Protection",
        "technical_label": "Email Security Gateway",
        "what_it_means": "ResilAI verifies that harmful links and attachments are blocked before reaching staff inboxes.",
        "why_it_matters": "Phishing emails are the #1 way attackers break into healthcare organizations.",
    },
}

FALLBACK_TAXONOMY = {
    "business_label": "Security Monitoring",
    "technical_label": "Telemetry",
    "what_it_means": "ResilAI verifies the status of your security tools.",
    "why_it_matters": "Continuous verification ensures your investments actually protect your business.",
}

class ExplainabilityEngine:
    """
    Deterministic engine that maps technical findings into plain-English
    explanations for non-technical healthcare executives.
    Never invents data or fabricates security status.
    """
    
    def _determine_evidence_state(self, verification: VerificationContext) -> str:
        """Deterministically evaluate the state of evidence."""
        if verification.confidence_pct == 0:
            if verification.verification_status == "stale":
                return "stale"
            return "unavailable"
        
        if verification.confidence_pct >= 80:
            return "verified"
            
        return "unknown"
        
    def build_explanation(
        self, 
        moment: ClinicMoment, 
        verdict_status: str, 
        verification: VerificationContext,
        actions: List[ActionCard]
    ) -> ExecutiveExplanation:
        """
        Build a deterministic explanation.
        The verdict_status MUST come from the ReadinessEngine. 
        This engine ONLY explains it.
        """
        
        capability_id = moment.capability_id
        taxonomy = TAXONOMY.get(capability_id, FALLBACK_TAXONOMY)
        
        evidence_state = self._determine_evidence_state(verification)
        
        # Base what_it_means
        what_it_means = taxonomy["what_it_means"]
        
        # Override what_it_means for unavailable/stale evidence based on invariants
        if evidence_state == "unavailable":
            what_it_means = "ResilAI could not find evidence to confirm this protection is active."
        elif evidence_state == "stale":
            what_it_means = "The evidence for this protection is out of date and can no longer be trusted."
            
        # Determine what_to_do_next
        what_to_do_next = "No immediate action required."
        if verdict_status == "fail":
            if actions:
                what_to_do_next = actions[0].recommended_action
            else:
                what_to_do_next = "Review the technical details and address the security gap."
        elif verdict_status == "unknown" or evidence_state in ["unavailable", "stale"]:
             what_to_do_next = "Check the connected security system to ensure it is sending data to ResilAI."
        elif verdict_status == "warning":
            what_to_do_next = "Review the warning to prevent it from becoming a failure."
            
        return ExecutiveExplanation(
            status=verdict_status,
            business_label=taxonomy["business_label"],
            technical_label=taxonomy.get("technical_label", capability_id),
            what_it_means=what_it_means,
            why_it_matters=taxonomy["why_it_matters"],
            what_to_do_next=what_to_do_next,
            evidence_state=evidence_state,
            last_verified_at=verification.last_verified_at
        )
