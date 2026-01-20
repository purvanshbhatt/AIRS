"""
Narrative API routes for LLM-assisted content generation.

The LLM CANNOT modify scores - it only generates narratives.
Uses Google Gemini for generation.

Note: /status endpoint is public. All other endpoints require auth when AUTH_REQUIRED=true.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.config import settings
from app.core.auth import require_auth, User
from app.schemas.narrative import (
    NarrativeRequest,
    NarrativeResponse,
    NarrativeContent,
    FindingRewrite,
    LLMStatusResponse,
    NarrativeType,
)
from app.services.assessment import AssessmentService
from app.services.llm_narrative import (
    get_narrative_generator,
    ScoreContext,
    FindingContext,
)
from app.services.findings import generate_findings

router = APIRouter()


@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """
    Get LLM feature status.
    
    Returns whether LLM narratives are enabled and available.
    """
    generator = get_narrative_generator()
    
    if not settings.AIRS_USE_LLM:
        return LLMStatusResponse(
            enabled=False,
            available=False,
            model=None,
            message="LLM features disabled. Set AIRS_USE_LLM=true to enable."
        )
    
    if not settings.GEMINI_API_KEY:
        return LLMStatusResponse(
            enabled=True,
            available=False,
            model=settings.LLM_MODEL,
            message="LLM enabled but GEMINI_API_KEY not configured."
        )
    
    available = generator.is_available()
    return LLMStatusResponse(
        enabled=True,
        available=available,
        model=settings.LLM_MODEL if available else None,
        message="LLM features available and ready (Gemini)." if available else "LLM initialization failed."
    )


@router.post("/{assessment_id}/narratives", response_model=NarrativeResponse)
async def generate_narratives(
    assessment_id: str,
    request: NarrativeRequest = NarrativeRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Generate AI-assisted narratives for an assessment.
    
    IMPORTANT: The LLM cannot modify scores. Scores are computed
    deterministically and passed as read-only context.
    
    Returns:
    - Executive summary (business-friendly paragraph)
    - 30/60/90 day roadmap narrative
    - Optionally: findings rewritten in business tone
    
    If LLM is disabled, returns deterministic fallback narratives.
    """
    # Get assessment with scores
    service = AssessmentService(db)
    assessment = service.get_detail(assessment_id)
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    if assessment.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Compute scores first."
        )
    
    # Build immutable score context (LLM cannot modify this)
    score_context = ScoreContext(
        overall_score=assessment["overall_score"],
        maturity_level=assessment.get("maturity_level", 1),
        maturity_name=assessment.get("maturity_name", "Initial"),
        domain_scores=[
            {
                "domain_id": s.get("domain_id"),
                "domain_name": s.get("domain_name"),
                "score": s.get("score", 0),
                "weight": s.get("weight", 0)
            }
            for s in assessment.get("scores", [])
        ]
    )
    
    # Get findings
    answers = {a["question_id"]: a["value"] for a in assessment.get("answers", [])}
    domain_scores = {s["domain_id"]: s["score"] for s in assessment.get("scores", [])}
    findings_raw = generate_findings(answers, domain_scores)
    
    # Convert to FindingContext
    finding_contexts = [
        FindingContext(
            rule_id=f.rule_id,
            title=f.title,
            domain_name=f.domain_name,
            severity=f.severity.value if hasattr(f.severity, 'value') else str(f.severity),
            evidence=f.evidence,
            recommendation=f.recommendation
        )
        for f in findings_raw
    ]
    
    # Get organization name
    org_name = assessment.get("organization_name", "the organization")
    
    # Generate narratives
    generator = get_narrative_generator()
    response = NarrativeResponse(
        assessment_id=assessment_id,
        llm_enabled=settings.AIRS_USE_LLM,
        original_score=assessment["overall_score"],
        original_maturity_level=assessment.get("maturity_level", 1),
        original_maturity_name=assessment.get("maturity_name", "Initial")
    )
    
    # Determine which narratives to generate
    types = request.narrative_types
    generate_all = NarrativeType.ALL in types
    
    if generate_all or NarrativeType.EXECUTIVE_SUMMARY in types:
        result = generator.generate_executive_summary(
            score_context, finding_contexts, org_name
        )
        response.executive_summary = NarrativeContent(
            narrative_type=result.narrative_type.value,
            content=result.content,
            llm_generated=result.llm_generated,
            model_used=result.model_used,
            tokens_used=result.tokens_used
        )
    
    if generate_all or NarrativeType.ROADMAP in types:
        result = generator.generate_roadmap_narrative(
            score_context, finding_contexts, org_name
        )
        response.roadmap = NarrativeContent(
            narrative_type=result.narrative_type.value,
            content=result.content,
            llm_generated=result.llm_generated,
            model_used=result.model_used,
            tokens_used=result.tokens_used
        )
    
    # Optionally rewrite findings
    if request.include_finding_rewrites:
        for fc in finding_contexts[:10]:  # Limit to top 10
            result = generator.rewrite_finding_business_tone(fc)
            response.finding_rewrites.append(FindingRewrite(
                original_title=fc.title,
                original_severity=fc.severity,
                business_content=result.content,
                llm_generated=result.llm_generated
            ))
    
    return response


@router.get("/{assessment_id}/executive-summary")
async def get_executive_summary(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Get just the executive summary narrative.
    
    Convenience endpoint for quick access.
    """
    request = NarrativeRequest(narrative_types=[NarrativeType.EXECUTIVE_SUMMARY])
    response = await generate_narratives(assessment_id, request, db)
    
    return {
        "assessment_id": assessment_id,
        "executive_summary": response.executive_summary.content if response.executive_summary else None,
        "llm_generated": response.executive_summary.llm_generated if response.executive_summary else False,
        "original_score": response.original_score
    }


@router.get("/{assessment_id}/roadmap")
async def get_roadmap(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Get just the 30/60/90 day roadmap narrative.
    
    Convenience endpoint for quick access.
    """
    request = NarrativeRequest(narrative_types=[NarrativeType.ROADMAP])
    response = await generate_narratives(assessment_id, request, db)
    
    return {
        "assessment_id": assessment_id,
        "roadmap": response.roadmap.content if response.roadmap else None,
        "llm_generated": response.roadmap.llm_generated if response.roadmap else False,
        "original_score": response.original_score
    }
