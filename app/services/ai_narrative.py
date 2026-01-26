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
  - LLM_MODEL: Model to use (default: gemini-2.0-flash)

SDK: Uses google-genai SDK with Vertex AI mode on GCP, falls back to API key.
Resilience: 30s timeout, 2 retries with exponential backoff.
"""

import logging
import time
from typing import Dict, Any, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# LLM Request Configuration
LLM_TIMEOUT_SECONDS = 30
LLM_MAX_RETRIES = 2
LLM_INITIAL_BACKOFF = 1.0  # seconds


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
        return _generate_fallback_narrative(summary_payload)
    
    # Log demo mode warning
    if settings.is_demo_mode:
        logger.warning("LLM running in demo mode - generates narratives only, no score modification")
    
    try:
        return _generate_llm_narrative(summary_payload)
    except Exception as e:
        logger.error(f"LLM narrative generation failed: {e}. Falling back to deterministic text.")
        return _generate_fallback_narrative(summary_payload)


def _generate_llm_narrative(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate narratives using Google Gemini LLM via google-genai SDK.
    
    Uses Vertex AI mode when running on GCP (with ADC), falls back to API key mode.
    Includes 30s timeout and 2 retries with exponential backoff.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai package not installed. Using fallback.")
        return _generate_fallback_narrative(summary_payload)
    
    # Initialize client - prefer Vertex AI on GCP, fallback to API key
    client = None
    client_mode = "unknown"
    
    try:
        # Try Vertex AI mode first (uses Application Default Credentials)
        if settings.GCP_PROJECT_ID:
            try:
                client = genai.Client(
                    vertexai=True,
                    project=settings.GCP_PROJECT_ID,
                    location="us-central1"
                )
                client_mode = "vertex_ai"
                logger.info(f"Using Vertex AI mode with project: {settings.GCP_PROJECT_ID}")
            except Exception as vertex_err:
                logger.warning(f"Vertex AI init failed: {vertex_err}. Trying API key mode.")
        
        # Fallback to API key mode
        if client is None and settings.GEMINI_API_KEY:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            client_mode = "api_key"
            logger.info("Using Gemini API key mode")
        
        if client is None:
            logger.error("No valid LLM client configuration. Need GCP_PROJECT_ID or GEMINI_API_KEY.")
            return _generate_fallback_narrative(summary_payload)
            
    except Exception as init_err:
        logger.error(f"Failed to initialize Gemini client: {init_err}")
        return _generate_fallback_narrative(summary_payload)
    
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
    
    # Generate executive summary
    exec_prompt = f"""Write a professional 2-3 paragraph executive summary for {org_name}'s AI Security Readiness Assessment.

ASSESSMENT RESULTS (DO NOT CHANGE THESE NUMBERS):
- Overall Score: {overall_score:.1f}/100
- Readiness Tier: {tier_label}
- Total Findings: {len(findings)} ({critical_count} critical, {high_count} high, {medium_count} medium)

DOMAIN SCORES:
{domain_context}
{baseline_context}

TOP FINDINGS:
{findings_context if findings_context else "No significant findings identified."}

Write in a professional, consultant tone suitable for board presentation. Focus on:
1. Overall security posture assessment
2. Key strengths and areas of concern
3. High-level strategic recommendation

Be concise and actionable. Do not include any numeric values other than those provided above."""

    # Generate roadmap narrative
    roadmap_prompt = f"""Create a 30/60/90 day remediation roadmap narrative for {org_name}.

CURRENT STATE:
- Overall Score: {overall_score:.1f}/100 ({tier_label})
- Critical Findings: {critical_count}
- High Findings: {high_count}
- Medium Findings: {medium_count}

TOP FINDINGS TO ADDRESS:
{findings_context if findings_context else "No significant findings requiring immediate attention."}

Write a clear, actionable roadmap with:
- FIRST 30 DAYS: Immediate priorities and quick wins
- DAYS 31-60: Foundation building and process improvements  
- DAYS 61-90: Maturity advancement and long-term initiatives

Use business-friendly language. Be specific about actions and expected outcomes.
Format as clear paragraphs, not bullet lists."""

    # Helper function for LLM call with retry
    def _call_with_retry(prompt: str) -> str:
        """Make LLM call with timeout and exponential backoff retry."""
        last_error = None
        
        for attempt in range(LLM_MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    backoff = LLM_INITIAL_BACKOFF * (2 ** (attempt - 1))
                    logger.info(f"Retry attempt {attempt}/{LLM_MAX_RETRIES} after {backoff}s backoff")
                    time.sleep(backoff)
                
                # Configure generation with timeout
                config = types.GenerateContentConfig(
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.LLM_MAX_TOKENS,
                    http_options=types.HttpOptions(timeout=LLM_TIMEOUT_SECONDS * 1000)  # ms
                )
                
                response = client.models.generate_content(
                    model=settings.LLM_MODEL,
                    contents=prompt,
                    config=config
                )
                
                # Extract text from response
                if response and response.text:
                    return response.text.strip()
                else:
                    raise ValueError("Empty response from LLM")
                    
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt >= LLM_MAX_RETRIES:
                    raise
        
        raise last_error or Exception("LLM call failed after retries")
    
    try:
        # Generate both narratives with retry logic
        exec_text = _call_with_retry(exec_prompt)
        roadmap_text = _call_with_retry(roadmap_prompt)
        
        logger.info(f"Successfully generated narratives via {client_mode} mode")
        
        return {
            "executive_summary_text": exec_text,
            "roadmap_narrative_text": roadmap_text,
            "llm_generated": True
        }
        
    except Exception as e:
        logger.error(f"Gemini API call failed after {LLM_MAX_RETRIES} retries: {e}")
        return _generate_fallback_narrative(summary_payload)


def _generate_fallback_narrative(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
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
        exec_summary = (
            f"{org_name} received an overall AI readiness score of {overall_score:.0f}/100, "
            f"placing them in the Critical tier. This assessment identified {len(findings)} findings, "
            f"including {critical_count} critical and {high_count} high-severity issues that require "
            f"immediate attention. Key areas of concern include {' and '.join(weak_domain_names)}. "
            f"Urgent action is recommended to address fundamental security gaps before expanding AI initiatives."
        )
    elif tier_label == "Needs Work":
        exec_summary = (
            f"{org_name}'s AI readiness assessment resulted in a score of {overall_score:.0f}/100, "
            f"indicating the organization Needs Work before production AI deployment. "
            f"The assessment identified {len(findings)} findings across multiple domains. "
            f"While {' and '.join(strong_domain_names)} show adequate maturity, "
            f"{' and '.join(weak_domain_names)} require focused improvement. "
            f"A structured remediation program is recommended over the next 60-90 days."
        )
    elif tier_label == "Good":
        exec_summary = (
            f"{org_name} achieved a Good readiness score of {overall_score:.0f}/100, "
            f"demonstrating solid foundational security practices for AI operations. "
            f"Strong performance was observed in {' and '.join(strong_domain_names)}. "
            f"The {len(findings)} identified findings are primarily optimization opportunities "
            f"rather than critical gaps. Continued investment in {' and '.join(weak_domain_names)} "
            f"will further strengthen the organization's AI security posture."
        )
    else:  # Strong
        exec_summary = (
            f"{org_name} has achieved a Strong AI readiness score of {overall_score:.0f}/100, "
            f"reflecting excellent security practices across all assessed domains. "
            f"The organization demonstrates mature capabilities in {' and '.join(strong_domain_names)}, "
            f"with only {len(findings)} minor findings identified. "
            f"The focus should shift to maintaining this posture and exploring advanced security capabilities."
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
