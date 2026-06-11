import json
from typing import Union

class ExecutiveNarrativePromptBuilder:
    """
    Builds and isolates narrative generation prompts to prevent mathematical hallucinations.
    Enforces strict deterministic values as inputs.
    """

    # The exact injection framework prompt base
    EXECUTIVE_NARRATIVE_PROMPT_BASE = (
        "{verification_context}\n"
        "SYSTEM: You are the ResilAI Boardroom Interpreter. You take deterministic risk indices and format them into clear narrative business summaries.\n"
        "INPUT PARAMS: GHI: {ghi_score}, RRI: {rri_score}, Target SLA: {target_sla}, Active Breach Exposure: {breach_delta}.\n"
        "CONSTRAINT: You are strictly forbidden from calculating, inventing, or altering any numeric value. Translate the existing data into an executive-level impact report outlining the immediate 30/60/90-day remediation strategy."
    )

    @staticmethod
    def generate_prompt(
        ghi_score: Union[int, float],
        rri_score: Union[int, float],
        missing_nist_controls: int,
        active_critical_vulns: int,
        target_sla: str,
        is_siem_verified: bool,
    ) -> str:
        """
        Forces user input to strictly accept deterministic values produced by the DGE:
        GHI, RRI, missing NIST controls, and active critical vulnerability counts.
        """
        # Force strict typing to prevent injection or halluciation triggers
        if not isinstance(ghi_score, (int, float)):
            raise TypeError("ghi_score must be a deterministic numeric value.")
        if not isinstance(rri_score, (int, float)):
            raise TypeError("rri_score must be a deterministic numeric value.")
        if not isinstance(missing_nist_controls, int):
            raise TypeError("missing_nist_controls must be an integer count.")
        if not isinstance(active_critical_vulns, int):
            raise TypeError("active_critical_vulns must be an integer count.")
        if not isinstance(is_siem_verified, bool):
            raise TypeError("is_siem_verified must be a boolean value.")
        
        # Determine verification context statement
        if is_siem_verified:
            verification_context = "This Governance Health Index (GHI) is cryptographically verified against live infrastructure telemetry and audit ledgers, representing a Tier 3 Assurance state."
        else:
            verification_context = "This Governance Health Index (GHI) score is provisional and relies on self-attested configuration data."
        
        # Formulate Active Breach Exposure dynamically from the strictly validated deterministic counts
        breach_delta = f"{active_critical_vulns} critical vulnerabilities, {missing_nist_controls} missing NIST controls"

        return ExecutiveNarrativePromptBuilder.EXECUTIVE_NARRATIVE_PROMPT_BASE.format(
            verification_context=verification_context,
            ghi_score=ghi_score,
            rri_score=rri_score,
            target_sla=target_sla,
            breach_delta=breach_delta
        )
