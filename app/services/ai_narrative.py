"""
AIRS AI Narrative Generator

Generates consultant-grade text narratives (executive summary + roadmap) 
from deterministic assessment data. The AI ONLY generates text - it does 
NOT compute or alter any numeric scores.

IMPORTANT - LLM Scope Limitations:
  The LLM is strictly limited to generating narrative text:
    ✓ Executive summary paragraph
    ✓ 30/60/90 day roadmap narrative
  
  The LLM does NOT modify:
    ✗ Numeric scores (overall_score, domain_scores)
    ✗ Maturity tier/level
    ✗ Findings (count, severity, recommendations)
    ✗ Any structured data

Demo Mode:
  When DEMO_MODE=true, LLM can run without strict API key validation.
  This is useful for CISO demos and sales presentations.
  Falls back to deterministic text if LLM fails.

Feature flags:
  - AIRS_USE_LLM: Enable/disable LLM features (default: False)
  - DEMO_MODE: Allow LLM without strict validation (default: False)
  - GEMINI_API_KEY: API key for Google Gemini (optional in demo mode)
  - LLM_MODEL: Model to use (default: gemini-3-flash-preview)
"""

import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 30
LLM_MAX_RETRIES = 2
LLM_INITIAL_BACKOFF = 1.0


def generate_narrative(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate AI-powered narrative text from assessment summary data.
    
    This function ONLY generates text. It does NOT modify any scores or findings.
    All numeric data is passed through unchanged.
    
    Args:
        summary_payload: Dict containing:
            - overall_score: float (0-100)
            - tier: dict with label, color
            - domain_scores: list of domain score dicts
            - findings: list of finding dicts (top findings)
            - organization_name: str (optional)
            - baseline_profiles: dict (optional) - for baseline comparison context
            - selected_baseline: str (optional) - which baseline to compare against
    
    Returns:
        Dict with:
            - executive_summary_text: str - AI-generated executive summary
            - roadmap_narrative_text: str - AI-generated 30/60/90 day roadmap narrative
            - llm_generated: bool - whether LLM was used or fallback
    
    Note: This function NEVER modifies scores, tiers, or findings.
    All numeric data passes through unchanged.
    """
    # Use the is_llm_enabled property which handles demo mode logic
    use_llm = settings.is_llm_enabled
    
    if not use_llm:
        logger.debug("LLM disabled - using deterministic fallback narratives")
        return _generate_fallback_narrative(summary_payload, llm_failed=False)
    
    # Log demo mode warning
    if settings.is_demo_mode:
        logger.warning("LLM running in demo mode - generates narratives only, no score modification")
    
    try:
        return _generate_llm_narrative(summary_payload)
    except Exception as e:
        logger.error(f"LLM narrative generation failed: {e}. Falling back to deterministic text.")
        return _generate_fallback_narrative(summary_payload, llm_failed=True)


def _generate_llm_narrative(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate narratives using Google Gemini LLM with new google-genai SDK.
    
    Features:
    - Prefers Vertex AI mode when GCP_PROJECT_ID is set
    - Falls back to API key mode
    - 30 second timeout per request
    - 2 retries with exponential backoff
    """
    import time
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai SDK not available. Using fallback.")
        return _generate_fallback_narrative(summary_payload, llm_failed=True)
    
    # Initialize client based on available credentials
    client = None
    # Prefer Vertex AI mode if GCP project is set
    if settings.GCP_PROJECT_ID:
        try:
            client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=getattr(settings, 'GCP_REGION', 'us-central1')
            )
            logger.info(f"Using Vertex AI mode with project {settings.GCP_PROJECT_ID}")
        except Exception as e:
            logger.warning(f"Vertex AI init failed: {e}, trying API key mode")

    # Fallback to API key mode
    if client is None and settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Using API key mode for Gemini")
        except Exception as e:
            logger.error(f"API key init failed: {e}")
            return _generate_fallback_narrative(summary_payload, llm_failed=True)

    if client is None:
        logger.warning("No valid credentials for Gemini. Using fallback.")
        return _generate_fallback_narrative(summary_payload, llm_failed=True)
    
    # Use model from settings (default: gemini-3-flash-preview)
    model_name = settings.LLM_MODEL
    
    # Extract data from payload
    overall_score = summary_payload.get("overall_score", 0)
    tier = summary_payload.get("tier", {})
    tier_label = tier.get("label", "Unknown")
    domain_scores = summary_payload.get("domain_scores", [])
    findings = summary_payload.get("findings", [])
    org_name = summary_payload.get("organization_name", "the organization")
    baseline_profiles = summary_payload.get("baseline_profiles", {})
    selected_baseline = summary_payload.get("selected_baseline")
    
    # Build domain scores context
    domain_context = "\n".join([
        f"  - {ds.get('domain_name', ds.get('domain_id', 'Unknown'))}: {ds.get('score_5', ds.get('score', 0)):.1f}/5.0"
        for ds in domain_scores
    ])
    
    # Build findings context (top 5)
    findings_context = ""
    if findings:
        top_findings = findings[:5]
        findings_lines = []
        for f in top_findings:
            severity = f.get("severity", "unknown").upper()
            title = f.get("title", "Unknown finding")
            domain = f.get("domain", "")
            recommendation = f.get("recommendation", "")
            findings_lines.append(f"  - [{severity}] {title} ({domain}): {recommendation}")
        findings_context = "\n".join(findings_lines)
    
    # Build baseline comparison context if available
    baseline_context = ""
    if selected_baseline and baseline_profiles.get(selected_baseline):
        baseline = baseline_profiles[selected_baseline]
        comparisons = []
        for ds in domain_scores:
            domain_id = ds.get("domain_id", "")
            current_score = ds.get("score_5", 0)
            baseline_score = baseline.get(domain_id)
            if baseline_score is not None:
                diff = current_score - baseline_score
                direction = "above" if diff > 0 else "below" if diff < 0 else "at"
                comparisons.append(f"  - {ds.get('domain_name', domain_id)}: {direction} baseline by {abs(diff):.1f}")
        if comparisons:
            baseline_context = f"\nComparison to {selected_baseline} baseline:\n" + "\n".join(comparisons)
    
    # Count findings by severity
    critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
    high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
    medium_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
    
    # Build resource links instruction based on implementation assistance mode
    if settings.IMPLEMENTATION_ASSISTANCE_MODE:
        resource_links_instruction = """   - A direct implementation guide link from one of: CISA (https://www.cisa.gov/stopransomware),
     NIST (https://csrc.nist.gov/publications), or OWASP (https://owasp.org/www-project-top-ten/)"""
    else:
        resource_links_instruction = "   - The expected business outcome if this priority is completed within 30 days"

    # Generate executive summary
    exec_prompt = f"""Write a professional executive narrative for {org_name}'s AI Security Readiness Assessment.
Use enterprise risk terminology throughout: Operational Resilience, Risk Posture, Governance Maturity,
and Control Effectiveness.

ASSESSMENT RESULTS (DO NOT CHANGE THESE NUMBERS):
- Overall Score: {overall_score:.1f}/100
- Readiness Tier: {tier_label}
- Total Findings: {len(findings)} ({critical_count} critical, {high_count} high, {medium_count} medium)

DOMAIN SCORES:
{domain_context}
{baseline_context}

TOP FINDINGS:
{findings_context if findings_context else "No significant findings identified."}

Output requirements (must follow exactly):
1. Start with a heading line: "Readiness Score"
2. Include 2 short paragraphs describing Risk Posture, Governance Maturity, and Control Effectiveness
   implications. Focus on business impact and executive actions rather than repeating raw scores.
3. Add a heading: "Top 3 Remediation Priorities"
4. Under that heading, provide exactly 3 bullet points. Each bullet MUST include:
   - The specific action (using enterprise language about control effectiveness or operational resilience)
   - The risk category addressed (e.g. Credential Compromise, Ransomware Recovery)
{resource_links_instruction}
5. Do not repeat raw questionnaire answers; focus on business impact and next actions.
6. Do not include any numeric values other than those provided above."""

    # Build roadmap resource references based on implementation assistance mode
    if settings.IMPLEMENTATION_ASSISTANCE_MODE:
        roadmap_references = """- IMMEDIATE (0-30 DAYS): Critical risk reduction and quick wins. Reference specific CISA or NIST guidance
  where applicable (e.g. https://www.cisa.gov/stopransomware).
- NEAR-TERM (30-90 DAYS): Foundation building, Control Effectiveness improvements, and process
  maturation. Reference relevant NIST CSF 2.0 categories.
- STRATEGIC (90+ DAYS): Governance Maturity advancement, Operational Resilience, and long-term Risk
  Posture hardening. Reference OWASP or NIST SP publications where relevant."""
    else:
        roadmap_references = """- IMMEDIATE (0-30 DAYS): Critical risk reduction and quick wins. Focus on specific actions,
  responsible teams, and expected measurable outcomes.
- NEAR-TERM (30-90 DAYS): Foundation building, Control Effectiveness improvements, and process
  maturation. Highlight dependencies and success criteria.
- STRATEGIC (90+ DAYS): Governance Maturity advancement, Operational Resilience, and long-term Risk
  Posture hardening. Describe target maturity state and KPIs."""

    # Generate roadmap narrative
    roadmap_prompt = f"""Create a tiered remediation roadmap narrative for {org_name} using enterprise
risk language: Operational Resilience, Risk Posture, Governance Maturity, and Control Effectiveness.

CURRENT STATE:
- Overall Score: {overall_score:.1f}/100 ({tier_label})
- Critical Findings: {critical_count}
- High Findings: {high_count}
- Medium Findings: {medium_count}

TOP FINDINGS TO ADDRESS:
{findings_context if findings_context else "No significant findings requiring immediate attention."}

Write a clear, actionable remediation roadmap with three tiers:
{roadmap_references}

Use business-friendly language. Be specific about actions and expected outcomes.
Format as clear paragraphs, not bullet lists."""

    # Retry logic with exponential backoff
    max_retries = LLM_MAX_RETRIES

    def generate_with_retry(prompt: str, retry_count: int = 0) -> Optional[str]:
        """Generate content with retry logic."""
        try:
            config = types.GenerateContentConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            return response.text.strip() if response.text else None

        except Exception as e:
            if retry_count < max_retries:
                wait_time = LLM_INITIAL_BACKOFF * (2 ** retry_count)
                logger.warning(f"LLM request failed (attempt {retry_count + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                return generate_with_retry(prompt, retry_count + 1)
            else:
                logger.error(f"LLM request failed after {max_retries + 1} attempts: {e}")
                return None
    
    try:
        # Generate both narratives with retry logic
        exec_summary = generate_with_retry(exec_prompt)
        roadmap_narrative = generate_with_retry(roadmap_prompt)
        
        if exec_summary and roadmap_narrative:
            return {
                "executive_summary_text": exec_summary,
                "roadmap_narrative_text": roadmap_narrative,
                "llm_generated": True
            }
        else:
            logger.warning("One or more LLM responses were empty. Using fallback.")
            return _generate_fallback_narrative(summary_payload, llm_failed=True)
        
    except Exception as e:
        logger.error(f"Gemini API call failed: {e}")
        return _generate_fallback_narrative(summary_payload, llm_failed=True)


def _generate_fallback_narrative(summary_payload: Dict[str, Any], llm_failed: bool = False) -> Dict[str, Any]:
    """
    Generate deterministic fallback narratives when LLM is unavailable.
    
    These are template-based narratives that still provide useful context.
    """
    overall_score = summary_payload.get("overall_score", 0)
    tier = summary_payload.get("tier", {})
    tier_label = tier.get("label", "Unknown")
    domain_scores = summary_payload.get("domain_scores", [])
    findings = summary_payload.get("findings", [])
    org_name = summary_payload.get("organization_name", "the organization")
    
    # Count findings by severity
    critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
    high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
    
    # Find weakest domains
    weak_domains = sorted(domain_scores, key=lambda d: d.get("score_5", d.get("score", 0)))[:2]
    weak_domain_names = [d.get("domain_name", d.get("domain_id", "Unknown")) for d in weak_domains]
    
    # Find strongest domains  
    strong_domains = sorted(domain_scores, key=lambda d: d.get("score_5", d.get("score", 0)), reverse=True)[:2]
    strong_domain_names = [d.get("domain_name", d.get("domain_id", "Unknown")) for d in strong_domains]
    
    # Build executive summary based on tier
    if tier_label == "Critical":
        context_text = (
            f"{org_name} received an overall score of {overall_score:.0f}/100 and is in the Critical tier. "
            f"{len(findings)} findings were identified, including {critical_count} critical and {high_count} high-severity issues. "
            f"The largest Control Effectiveness gaps are in {' and '.join(weak_domain_names)}. "
            "Risk Posture is at maximum exposure — immediate executive action is required to restore "
            "Operational Resilience."
        )
    elif tier_label == "Needs Work":
        context_text = (
            f"{org_name} scored {overall_score:.0f}/100 and is in the Needs Work tier. "
            f"The assessment identified {len(findings)} findings across multiple security domains. "
            f"While {' and '.join(strong_domain_names)} demonstrate reasonable Control Effectiveness, "
            f"{' and '.join(weak_domain_names)} carry the highest Operational Resilience risk and require "
            "focused remediation to improve Governance Maturity."
        )
    elif tier_label == "Good":
        context_text = (
            f"{org_name} scored {overall_score:.0f}/100 and is in the Good tier with strong Control Effectiveness "
            f"in {' and '.join(strong_domain_names)}. "
            f"The {len(findings)} remaining findings are primarily Governance Maturity and optimisation gaps "
            f"concentrated in {' and '.join(weak_domain_names)}."
        )
    else:  # Strong
        context_text = (
            f"{org_name} scored {overall_score:.0f}/100 and is in the Strong tier, indicating a mature Risk Posture "
            f"and high Control Effectiveness across assessed domains. "
            f"Only {len(findings)} lower-priority findings were identified, with the strongest Operational Resilience "
            f"in {' and '.join(strong_domain_names)}."
        )

    priorities = [
        f"Close highest Operational Resilience gaps in {weak_domain_names[0] if weak_domain_names else 'core controls'} "
        f"with executive sponsorship. Reference: https://www.cisa.gov/stopransomware",
        "Assign control owners and delivery dates for critical and high-severity remediation items to improve "
        "Governance Maturity. Reference: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final",
        "Establish a 30/60/90-day operating cadence with measurable Risk Posture checkpoints. "
        "Reference: https://www.nist.gov/cyberframework",
    ]
    if llm_failed:
        exec_summary = (
            "Readiness Score\n"
            f"{org_name} is currently rated {tier_label} at {overall_score:.0f}/100.\n\n"
            "Executive narrative unavailable. Based on analysis, priority should focus on:\n"
            "1. Access controls\n"
            "2. Monitoring\n"
            "3. Incident response planning"
        )
    else:
        exec_summary = (
            "Readiness Score\n"
            f"{context_text}\n\n"
            "Top 3 Remediation Priorities\n"
            f"- {priorities[0]}\n"
            f"- {priorities[1]}\n"
            f"- {priorities[2]}"
        )
    
    # Build roadmap narrative
    if critical_count > 0 or high_count > 0:
        roadmap_narrative = (
            f"The remediation roadmap for {org_name} prioritizes {critical_count} critical and "
            f"{high_count} high-severity findings. In the first 30 days, focus should be on "
            f"addressing critical security gaps, particularly in {weak_domain_names[0] if weak_domain_names else 'key domains'}. "
            f"Days 31-60 should establish foundational security processes and deploy necessary tooling. "
            f"The final phase (days 61-90) should focus on policy refinement, team training, and "
            f"establishing ongoing monitoring capabilities."
        )
    else:
        roadmap_narrative = (
            f"With no critical or high-severity findings, {org_name}'s roadmap focuses on "
            f"optimization and maturity advancement. The first 30 days should address any medium-severity "
            f"findings and quick wins. Days 31-60 can focus on process improvements and expanding "
            f"detection capabilities. The final phase should establish advanced monitoring, "
            f"conduct tabletop exercises, and refine incident response procedures."
        )
    
    return {
        "executive_summary_text": exec_summary,
        "roadmap_narrative_text": roadmap_narrative,
        "llm_generated": False
    }
