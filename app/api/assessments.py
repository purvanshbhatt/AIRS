"""
Assessment API routes.

All endpoints in this router require authentication when AUTH_REQUIRED=true.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO
from app.db.database import get_db
from app.core.logging import event_logger
from app.core.auth import require_auth, User
from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentDetail,
    AssessmentSummary,
    AssessmentSummaryResponse,
    AnswerBulkSubmit,
    AnswerResponse,
    ComputeScoreResponse,
    FindingCreate,
    FindingResponse,
    ScoreResponse,
)
from app.services.assessment import AssessmentService
from app.reports.pdf import ProfessionalPDFGenerator

router = APIRouter()


# ----- Assessment CRUD -----

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment",
    description="Create a new AI readiness assessment for an organization. The assessment starts in DRAFT status.",
    responses={
        201: {"description": "Assessment created successfully"},
        400: {"description": "Invalid request (e.g., organization not found)"},
        401: {"description": "Authentication required (when AUTH_REQUIRED=true)"}
    }
)
async def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Create a new assessment for an organization."""
    service = AssessmentService(db)
    try:
        assessment = service.create(data)
        event_logger.assessment_created(
            assessment_id=assessment.id,
            organization_id=assessment.organization_id,
            title=assessment.title or ""
        )
        return assessment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[AssessmentSummary])
async def list_assessments(
    organization_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """List all assessments, optionally filtered by organization."""
    service = AssessmentService(db)
    assessments = service.get_all(organization_id=organization_id, skip=skip, limit=limit)
    
    # Add organization name to summaries
    result = []
    for a in assessments:
        summary = {
            "id": a.id,
            "organization_id": a.organization_id,
            "organization_name": a.organization.name if a.organization else None,
            "title": a.title,
            "status": a.status,
            "overall_score": a.overall_score,
            "maturity_level": a.maturity_level,
            "created_at": a.created_at
        }
        result.append(summary)
    
    return result


@router.get("/{assessment_id}", response_model=AssessmentDetail)
async def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get assessment detail with all related data."""
    service = AssessmentService(db)
    result = service.get_detail(assessment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return result


@router.get(
    "/{assessment_id}/summary",
    response_model=AssessmentSummaryResponse,
    summary="Get Assessment Summary",
    description="""Get comprehensive assessment summary for executive dashboard. Includes scores, 
findings, roadmap, baseline comparisons, and optional AI-generated narratives.

Returns:
- api_version: API version for forward compatibility
- Assessment metadata (title, org, created_at)
- Overall score and readiness tier (Critical/Needs Work/Good/Strong)
- Domain scores array (with 0-5 scale)
- Findings array (severity, title, evidence, recommendation)
- 30/60/90 day roadmap as structured lists
- Baseline profiles for comparison
- Optional LLM-generated executive summary and roadmap narrative""",
    responses={
        200: {"description": "Complete assessment summary with all metrics and narratives"},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required (when AUTH_REQUIRED=true)"},
        404: {"description": "Assessment not found"}
    }
)
async def get_assessment_summary(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get comprehensive assessment summary for executive dashboard."""
    service = AssessmentService(db)
    result = service.get_summary(assessment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if result.get("overall_score") == 0 and not result.get("domain_scores"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )
    
    # Log summary fetch
    event_logger.summary_fetched(
        assessment_id=assessment_id,
        llm_used=result.get("executive_summary_text") is not None
    )
    
    return result


@router.patch("/{assessment_id}", response_model=AssessmentResponse)
async def update_assessment(
    assessment_id: str,
    data: AssessmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Update an assessment."""
    service = AssessmentService(db)
    assessment = service.update(assessment_id, data)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return assessment


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Delete an assessment."""
    service = AssessmentService(db)
    if not service.delete(assessment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )


# ----- Answers -----

@router.post(
    "/{assessment_id}/answers",
    response_model=List[AnswerResponse],
    summary="Submit Answers",
    description="Submit or update answers for an assessment. Uses upsert semantics - existing answers are updated, new ones are created.",
    responses={
        200: {"description": "Answers submitted successfully"},
        404: {"description": "Assessment not found"}
    }
)
async def submit_answers(
    assessment_id: str,
    data: AnswerBulkSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Submit answers for an assessment (upsert)."""
    service = AssessmentService(db)
    try:
        answers = service.submit_answers(assessment_id, data.answers)
        event_logger.answers_submitted(
            assessment_id=assessment_id,
            answer_count=len(answers)
        )
        return answers
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{assessment_id}/answers", response_model=List[AnswerResponse])
async def get_answers(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all answers for an assessment."""
    service = AssessmentService(db)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return service.get_answers(assessment_id)


# ----- Scoring -----

@router.post(
    "/{assessment_id}/score",
    response_model=ComputeScoreResponse,
    summary="Compute Score",
    description="Calculate and persist scores and findings for an assessment. Analyzes all submitted answers against the scoring rubric.",
    responses={
        200: {"description": "Scores computed and persisted successfully"},
        401: {"description": "Authentication required (when AUTH_REQUIRED=true)"},
        404: {"description": "Assessment not found"}
    }
)
async def compute_score(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Compute and persist scores and findings for an assessment."""
    service = AssessmentService(db)
    try:
        result = service.compute_score(assessment_id)
        
        # Log scoring event
        event_logger.scoring_executed(
            assessment_id=assessment_id,
            overall_score=result["overall_score"],
            findings_count=result["findings_count"]
        )
        
        # Convert Score objects to response format
        domain_scores = []
        for score in result["domain_scores"]:
            domain_scores.append({
                "id": score.id,
                "domain_id": score.domain_id,
                "domain_name": score.domain_name,
                "score": score.score,
                "max_score": score.max_score,
                "weight": score.weight,
                "weighted_score": score.weighted_score,
                "raw_points": score.raw_points,
                "max_raw_points": score.max_raw_points,
                "created_at": score.created_at
            })
        
        return {
            "assessment_id": result["assessment_id"],
            "overall_score": result["overall_score"],
            "maturity_level": result["maturity_level"],
            "maturity_name": result["maturity_name"],
            "domain_scores": domain_scores,
            "findings_count": result["findings_count"],
            "high_severity_count": result["high_severity_count"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{assessment_id}/scores", response_model=List[ScoreResponse])
async def get_scores(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all domain scores for an assessment."""
    service = AssessmentService(db)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return assessment.scores


# ----- Findings -----

@router.get("/{assessment_id}/findings", response_model=List[FindingResponse])
async def get_findings(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all findings for an assessment."""
    service = AssessmentService(db)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return service.get_findings(assessment_id)


@router.post("/{assessment_id}/findings", response_model=FindingResponse, status_code=status.HTTP_201_CREATED)
async def add_finding(
    assessment_id: str,
    data: FindingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Add a manual finding to an assessment."""
    service = AssessmentService(db)
    try:
        finding = service.add_finding(assessment_id, data)
        return finding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ----- Reports -----

@router.get(
    "/{assessment_id}/report",
    summary="Generate PDF Report",
    description="Generate and download a professional PDF report for the assessment. Includes executive summary, domain scores, findings, and remediation roadmap.",
    responses={
        200: {"description": "PDF report file", "content": {"application/pdf": {}}},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required (when AUTH_REQUIRED=true)"},
        404: {"description": "Assessment not found"}
    }
)
async def generate_report(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Generate PDF report for an assessment."""
    service = AssessmentService(db)
    result = service.get_detail(assessment_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if result.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )
    
    # Generate PDF using professional generator
    generator = ProfessionalPDFGenerator()
    pdf_content = generator.generate(result)
    
    # Log report generation
    event_logger.report_generated(assessment_id=assessment_id, format="pdf")
    
    # Create filename
    org_name = result.get("organization_name", "unknown").replace(" ", "_")
    filename = f"AIRS_Report_{org_name}_{assessment_id[:8]}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
