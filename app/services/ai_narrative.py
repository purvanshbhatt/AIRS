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
  - LLM_MODEL: Model to use (default: gemini-3-flash)
"""

import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS = 30
LLM_MAX_RETRIES = 2
LLM_INITIAL_BACKOFF = 1.0


import json
import re

def _extract_numerics(text: str) -> set[float]:
    pattern = r'\b\d+(?:\.\d+)?\b'
    matches = re.findall(pattern, text)
    return {float(m) for m in matches}

def _validate_numeric_trace(narrative_data: Dict[str, Any], summary_payload: Dict[str, Any]) -> bool:
    allowed = set()
    allowed.add(float(summary_payload.get("overall_score", 0)))
    for ds in summary_payload.get("domain_scores", []):
        allowed.add(float(ds.get("score_5", 0)))
        allowed.add(float(ds.get("score", 0)))
    
    findings = summary_payload.get("findings", [])
    allowed.add(float(len(findings)))
    critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
    high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
    medium_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
    allowed.add(float(critical_count))
    allowed.add(float(high_count))
    allowed.add(float(medium_count))
    
    # Common semantic/template numbers
    allowed.update([30.0, 31.0, 60.0, 61.0, 90.0, 10.0, 100.0, 1.0, 2.0, 3.0, 4.0, 5.0, 0.0])
    
    # Years are often mentioned (e.g. 2026)
    allowed.update([2023.0, 2024.0, 2025.0, 2026.0, 2027.0])
    
    all_text = ""
    for sec in narrative_data.get("sections", []):
        all_text += sec.get("content", "") + " "
    
    found_numerics = _extract_numerics(all_text)
    
    for num in found_numerics:
        if num not in allowed:
            logger.warning(f"Numeric hallucination detected: {num} not in allowed context")
            return False
            
    return True

def generate_board_story(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate 10 structured narrative sections for the Board Story.
    """
    use_llm = settings.is_llm_enabled
    
    if not use_llm:
        logger.debug("LLM disabled - using deterministic fallback narratives")
        return _generate_fallback_board_story(summary_payload, llm_failed=False)
        
    try:
        return _generate_llm_board_story(summary_payload)
    except Exception as e:
        logger.error(f"LLM board story generation failed: {e}. Falling back to deterministic text.")
        return _generate_fallback_board_story(summary_payload, llm_failed=True)

def _generate_llm_board_story(summary_payload: Dict[str, Any]) -> Dict[str, Any]:
    import time
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return _generate_fallback_board_story(summary_payload, llm_failed=True)
        
    client = None
    if settings.GCP_PROJECT_ID:
        try:
            client = genai.Client(vertexai=True, project=settings.GCP_PROJECT_ID, location=getattr(settings, 'GCP_REGION', 'us-central1'))
        except Exception:
            pass

    if client is None and settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
        except Exception:
            return _generate_fallback_board_story(summary_payload, llm_failed=True)

    if client is None:
        return _generate_fallback_board_story(summary_payload, llm_failed=True)
        
    model_name = settings.LLM_MODEL
    
    # Extract data from payload
    overall_score = summary_payload.get("overall_score", 0)
    tier = summary_payload.get("tier", {})
    tier_label = tier.get("label", "Unknown")
    
    prompt = f"""Write a professional executive Board Story narrative for {summary_payload.get('organization_name', 'the organization')}.
Overall Score: {overall_score:.1f}/100
Readiness Tier: {tier_label}

You must return EXACTLY valid JSON with the following schema:
{{
  "sections": [
    {{"section_id": "executive_summary", "title": "Executive Summary", "content": "..."}},
    {{"section_id": "risk_posture", "title": "Risk Posture", "content": "..."}},
    {{"section_id": "governance_maturity", "title": "Governance Maturity", "content": "..."}},
    {{"section_id": "control_effectiveness", "title": "Control Effectiveness", "content": "..."}},
    {{"section_id": "compliance_status", "title": "Compliance Status", "content": "..."}},
    {{"section_id": "financial_exposure", "title": "Financial Exposure", "content": "..."}},
    {{"section_id": "threat_landscape", "title": "Threat Landscape", "content": "..."}},
    {{"section_id": "resource_allocation", "title": "Resource Allocation", "content": "..."}},
    {{"section_id": "remediation_roadmap", "title": "Remediation Roadmap", "content": "..."}},
    {{"section_id": "strategic_recommendations", "title": "Strategic Recommendations", "content": "..."}}
  ]
}}
Do NOT output anything except the JSON payload. No markdown blocks."""

    def generate_with_retry(prompt: str, retry_count: int = 0) -> Optional[str]:
        try:
            # We enforce JSON response via schema/mime if possible, but for flash we can just use prompt instructions
            config = types.GenerateContentConfig(
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_TOKENS,
                response_mime_type="application/json"
            )
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            return response.text.strip() if response.text else None
        except Exception as e:
            if retry_count < LLM_MAX_RETRIES:
                time.sleep(LLM_INITIAL_BACKOFF * (2 ** retry_count))
                return generate_with_retry(prompt, retry_count + 1)
            return None
            
    result = generate_with_retry(prompt)
    if result:
        try:
            if result.startswith("```json"):
                result = result[7:-3]
            data = json.loads(result)
            if "sections" in data and len(data["sections"]) == 10:
                if not _validate_numeric_trace(data, summary_payload):
                    return _generate_fallback_board_story(summary_payload, llm_failed=True)
                data["llm_generated"] = True
                return data
        except Exception as e:
            logger.error(f"JSON parsing of LLM response failed: {e}")
            
    return _generate_fallback_board_story(summary_payload, llm_failed=True)

def _generate_fallback_board_story(summary_payload: Dict[str, Any], llm_failed: bool = False) -> Dict[str, Any]:
    org = summary_payload.get("organization_name", "the organization")
    score = summary_payload.get("overall_score", 0)
    
    sections = [
        {"section_id": "executive_summary", "title": "Executive Summary", "content": f"{org} scored {score:.1f}/100."},
        {"section_id": "risk_posture", "title": "Risk Posture", "content": "Risk posture is based on deterministic data."},
        {"section_id": "governance_maturity", "title": "Governance Maturity", "content": "Governance maturity is based on deterministic data."},
        {"section_id": "control_effectiveness", "title": "Control Effectiveness", "content": "Control effectiveness is based on deterministic data."},
        {"section_id": "compliance_status", "title": "Compliance Status", "content": "Compliance status is based on deterministic data."},
        {"section_id": "financial_exposure", "title": "Financial Exposure", "content": "Financial exposure is based on deterministic data."},
        {"section_id": "threat_landscape", "title": "Threat Landscape", "content": "Threat landscape is based on deterministic data."},
        {"section_id": "resource_allocation", "title": "Resource Allocation", "content": "Resource allocation is based on deterministic data."},
        {"section_id": "remediation_roadmap", "title": "Remediation Roadmap", "content": "Remediation roadmap is based on deterministic data."},
        {"section_id": "strategic_recommendations", "title": "Strategic Recommendations", "content": "Strategic recommendations are based on deterministic data."}
    ]
    
    return {
        "sections": sections,
        "llm_generated": False
    }

# Backward compatibility alias if needed by older tests, but we'll migrate them.
generate_narrative = generate_board_story
