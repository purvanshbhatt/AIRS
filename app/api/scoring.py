"""
Scoring API endpoints.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.scoring import (
    AssessmentAnswers,
    ScoringResult,
    RecommendationsResponse,
    ValidationResult
)
from app.services.scoring import (
    calculate_scores,
    get_recommendations,
    validate_answers
)
from app.core.rubric import get_rubric, get_all_question_ids, get_methodology

router = APIRouter()


@router.get(
    "/rubric",
    summary="Get Scoring Rubric",
    description="Returns the complete scoring rubric definition including all domains, questions, weights, and scoring formulas.",
    responses={
        200: {"description": "Complete rubric definition with domains and questions"}
    }
)
async def get_scoring_rubric():
    """Get the complete scoring rubric definition."""
    return get_rubric()


@router.get(
    "/methodology",
    summary="Get Scoring Methodology",
    description=(
        "Returns the transparent scoring methodology explanation — domain weights, NIST CSF 2.0 mappings, "
        "risk basis (MITRE ATT&CK prevalence, CISA guidance), and maturity-level definitions. "
        "Intended to build auditor trust and support Big-4 consulting engagements."
    ),
    responses={
        200: {"description": "Scoring methodology with NIST CSF 2.0 domain mappings and weight rationale"}
    },
    tags=["scoring"],
)
async def get_scoring_methodology():
    """
    /api/v1/methodology — transparent scoring methodology.

    Exposes:
    - Rubric version and NIST CSF version
    - Basis for scoring weights (MITRE ATT&CK prevalence, CISA ransomware guidance, NIST impact areas)
    - Per-domain weight, NIST function, and category mappings
    - Maturity level definitions with Governance Maturity, Risk Posture, and Control Effectiveness labels
    - Remediation timeline tier definitions (Immediate / Near-term / Strategic)
    """
    return get_methodology()


@router.get(
    "/rubric",
    summary="Get Scoring Rubric",
    description="Returns the complete scoring rubric definition including all domains, questions, weights, and scoring formulas.",
    responses={
        200: {"description": "Complete rubric definition with domains and questions"}
    }
)
async def get_scoring_rubric():
    """Get the complete scoring rubric definition."""
    return get_rubric()


@router.get("/questions")
async def list_all_questions():
    """Get a flat list of all question IDs."""
    rubric = get_rubric()
    questions = []
    
    for domain_id, domain in rubric["domains"].items():
        for q in domain["questions"]:
            questions.append({
                "id": q["id"],
                "domain_id": domain_id,
                "domain_name": domain["name"],
                "text": q["text"],
                "type": q["type"],
                "points": q["points"]
            })
    
    return {"questions": questions, "total": len(questions)}


@router.post("/validate", response_model=ValidationResult)
async def validate_assessment_answers(data: AssessmentAnswers):
    """Validate assessment answers before scoring."""
    return validate_answers(data.answers)


@router.post("/calculate", response_model=ScoringResult)
async def calculate_assessment_scores(data: AssessmentAnswers):
    """
    Calculate readiness scores from assessment answers.
    
    Each domain is scored 0-5, then weighted to produce an overall 0-100 score.
    """
    # Validate first
    validation = validate_answers(data.answers)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid answers", "errors": validation["errors"]}
        )
    
    return calculate_scores(data.answers)


@router.post("/recommendations", response_model=RecommendationsResponse)
async def get_assessment_recommendations(data: AssessmentAnswers):
    """
    Get prioritized recommendations based on assessment scores.
    
    Returns actionable items sorted by impact and priority.
    """
    scores = calculate_scores(data.answers)
    recommendations = get_recommendations(scores)
    
    return {
        "recommendations": recommendations,
        "total_count": len(recommendations)
    }
