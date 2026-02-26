"""
Governance Forecasting Service – AI-powered compliance predictions.

Uses Google Gemini (via google-genai SDK) to generate forward-looking
governance insights such as SOC 2 CC7.1 readiness predictions based
on the organization's current tech stack and governance profile.

If LLM is unavailable, returns a deterministic fallback blurb.
"""

import json
import logging
from typing import Any, Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_forecast_prompt(org_data: Dict[str, Any]) -> str:
    """Build a concise prompt for governance forecasting."""
    return f"""You are a governance compliance analyst. Based on the following organization profile,
generate a brief (3-5 sentence) forward-looking forecast about their SOC 2 CC7.1 (System Operations)
readiness. Reference specific technologies from their stack and highlight the most likely gaps.

Organization Profile:
- Name: {org_data.get('name', 'Unknown')}
- Revenue Band: {org_data.get('revenue_band', 'Not specified')}
- Employee Count: {org_data.get('employee_count', 'Not specified')}
- Application Tier: {org_data.get('application_tier', 'Not configured')}
- SLA Target: {org_data.get('sla_target', 'Not set')}%
- Processes PII: {org_data.get('processes_pii', False)}
- Processes PHI: {org_data.get('processes_phi', False)}
- Uses AI in Production: {org_data.get('uses_ai_in_production', False)}
- Tech Stack: {json.dumps(org_data.get('tech_stack', []), default=str)}
- Geo Regions: {json.dumps(org_data.get('geo_regions', []))}

Requirements:
1. Focus on SOC 2 CC7.1 (System Operations) controls
2. Mention specific technology risks from their stack
3. Provide an actionable prediction (what will likely lag)
4. Keep the tone professional and advisory
5. Maximum 5 sentences

Respond with ONLY the forecast paragraph, no headers or bullet points."""


def _generate_fallback_forecast(org_data: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback when LLM is unavailable."""
    tier = org_data.get("application_tier", "")
    has_ai = org_data.get("uses_ai_in_production", False)
    pii = org_data.get("processes_pii", False)

    risks = []
    if tier in ("tier_1", "tier_2", "Tier 1", "Tier 2"):
        risks.append(
            f"Your {tier.replace('_', ' ').title()} classification triggers SOC 2 CC7.1 "
            "audit requirements for system operations monitoring and incident response."
        )
    if has_ai:
        risks.append(
            "AI/ML production usage introduces model governance gaps that SOC 2 CC7.1 "
            "does not yet explicitly address — document your AI monitoring controls proactively."
        )
    if pii:
        risks.append(
            "PII processing increases CC7.1 scope for data flow monitoring and "
            "breach notification readiness."
        )

    if not risks:
        risks.append(
            "Based on your current profile, standard SOC 2 CC7.1 controls for "
            "system monitoring, incident detection, and recovery procedures apply."
        )

    forecast = " ".join(risks) + (
        " We recommend completing a gap assessment within the next 30 days "
        "to identify specific control deficiencies before your next audit cycle."
    )

    return {
        "forecast": forecast,
        "focus_area": "SOC 2 CC7.1 — System Operations",
        "confidence": "medium",
        "llm_generated": False,
        "model": "deterministic-fallback",
    }


async def generate_governance_forecast(org_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a governance forecast for an organization.

    Attempts Gemini LLM first, falls back to deterministic template.

    Args:
        org_data: Dict containing org profile, tech stack, etc.

    Returns:
        Dict with forecast text, confidence, and metadata.
    """
    if not settings.AIRS_USE_LLM:
        logger.info("LLM disabled — using deterministic forecast")
        return _generate_fallback_forecast(org_data)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        logger.warning("google-genai SDK not available. Using fallback forecast.")
        return _generate_fallback_forecast(org_data)

    # Initialize client (same pattern as ai_narrative)
    client = None
    if settings.GCP_PROJECT_ID:
        try:
            client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=getattr(settings, "GCP_REGION", "us-central1"),
            )
        except Exception as e:
            logger.warning("Vertex AI init failed for forecast: %s", e)

    if client is None and settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.error("API key init failed for forecast: %s", e)
            return _generate_fallback_forecast(org_data)

    if client is None:
        logger.warning("No Gemini credentials for forecast. Using fallback.")
        return _generate_fallback_forecast(org_data)

    model_name = settings.LLM_MODEL
    prompt = _build_forecast_prompt(org_data)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
                max_output_tokens=300,
            ),
        )

        forecast_text = response.text.strip() if response.text else None

        if not forecast_text:
            logger.warning("Empty forecast response from Gemini")
            return _generate_fallback_forecast(org_data)

        return {
            "forecast": forecast_text,
            "focus_area": "SOC 2 CC7.1 — System Operations",
            "confidence": "high",
            "llm_generated": True,
            "model": model_name,
        }

    except Exception as e:
        logger.error("Gemini forecast failed: %s", e)
        return _generate_fallback_forecast(org_data)
