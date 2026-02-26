"""
Smart Annotations Service — Gemini Flash executive context blurbs.

Generates 1-sentence executive-context annotations for assessment findings
using Google Gemini (Flash model) for speed.

Falls back to deterministic template annotations when LLM is unavailable.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import get_settings

logger = logging.getLogger("airs.smart_annotations")

settings = get_settings()

# Maximum findings to annotate in a single batch (cost control)
MAX_BATCH_SIZE = 25


def _get_genai_client():
    """Lazy-load the Gemini client (same pattern as ai_narrative.py)."""
    try:
        from google import genai
    except ImportError:
        logger.warning("google-genai SDK not available")
        return None

    client = None

    if settings.GCP_PROJECT_ID:
        try:
            client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=getattr(settings, "GCP_REGION", "us-central1"),
            )
        except Exception as e:
            logger.warning(f"Vertex AI init failed: {e}")

    if client is None and settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception as e:
            logger.warning(f"API key init failed: {e}")

    return client


def _build_prompt(findings: List[Dict[str, Any]]) -> str:
    """Build a batch prompt for executive context annotations."""
    lines = []
    for i, f in enumerate(findings):
        severity = f.get("severity", "medium").upper()
        title = f.get("title", "Unknown")
        domain = f.get("domain_name") or f.get("domain") or ""
        nist = f.get("nist_category") or ""
        recommendation = (f.get("recommendation") or "")[:200]
        lines.append(
            f"[{i}] severity={severity} | domain={domain} | nist={nist} | "
            f"title={title} | recommendation={recommendation}"
        )

    findings_block = "\n".join(lines)

    return f"""You are a cybersecurity executive advisor. For each finding below, 
write exactly ONE sentence of executive context explaining why this matters 
to business leadership. Be concise, specific, and non-technical.

Return ONLY a JSON array of strings, one per finding, in the same order.
Example: ["This gap exposes...", "Without this control..."]

FINDINGS:
{findings_block}

Return the JSON array now:"""


def _generate_fallback_annotations(findings: List[Dict[str, Any]]) -> List[str]:
    """Deterministic fallback annotations when LLM is unavailable."""
    templates = {
        "critical": "This critical-severity finding requires immediate executive attention as it represents a significant risk to business operations and regulatory compliance.",
        "high": "This high-severity gap could materially impact the organization's security posture and should be prioritized in the next remediation cycle.",
        "medium": "This finding represents a moderate risk that should be addressed as part of the organization's continuous improvement program.",
        "low": "This low-severity observation is a best-practice enhancement that strengthens the overall security baseline.",
    }
    result = []
    for f in findings:
        severity = str(f.get("severity", "medium")).lower()
        result.append(templates.get(severity, templates["medium"]))
    return result


async def generate_annotations(
    findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate executive context annotations for a list of findings.
    
    Args:
        findings: List of finding dicts with title, severity, domain, etc.
    
    Returns:
        Dict with 'annotations' (list of strings) and 'llm_generated' (bool).
    """
    if not findings:
        return {"annotations": [], "llm_generated": False}

    # Cap batch size
    capped = findings[:MAX_BATCH_SIZE]

    # Check if LLM is available
    if not settings.AIRS_USE_LLM:
        return {
            "annotations": _generate_fallback_annotations(capped),
            "llm_generated": False,
        }

    client = _get_genai_client()
    if client is None:
        return {
            "annotations": _generate_fallback_annotations(capped),
            "llm_generated": False,
        }

    try:
        from google.genai import types
        import json

        prompt = _build_prompt(capped)
        model_name = settings.LLM_MODEL

        config = types.GenerateContentConfig(
            temperature=0.3,  # Lower temp for consistency
            max_output_tokens=2048,
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config,
        )

        raw = response.text.strip() if response.text else ""

        # Parse JSON array from response (handle markdown code blocks)
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0].strip()

        annotations = json.loads(raw)

        if isinstance(annotations, list) and len(annotations) == len(capped):
            return {"annotations": annotations, "llm_generated": True}
        else:
            logger.warning(
                f"LLM returned {len(annotations) if isinstance(annotations, list) else 'non-list'} "
                f"annotations for {len(capped)} findings. Using fallback."
            )
            return {
                "annotations": _generate_fallback_annotations(capped),
                "llm_generated": False,
            }

    except Exception as e:
        logger.error(f"Smart annotation generation failed: {e}")
        return {
            "annotations": _generate_fallback_annotations(capped),
            "llm_generated": False,
        }
