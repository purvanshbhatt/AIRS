"""
Assessment API routes.

All endpoints enforce tenant isolation using Firebase user UID.
Users can only access their own assessments and related data.
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
from app.schemas.report import ReportCreate, ReportResponse
from app.services.assessment import AssessmentService
from app.services.report import ReportService
from app.reports.pdf import ProfessionalPDFGenerator

router = APIRouter()


def get_assessment_service(db: Session, user: User) -> AssessmentService:
    """Get assessment service with tenant isolation."""
    return AssessmentService(db, owner_uid=user.uid if user else None)


def get_report_service(db: Session, user: User) -> ReportService:
    """Get report service with tenant isolation."""
    return ReportService(db, owner_uid=user.uid)


# ----- Assessment CRUD -----

@router.post(
    "",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment",
    description="Create a new AI readiness assessment for an organization owned by the authenticated user.",
    responses={
        201: {"description": "Assessment created successfully"},
        400: {"description": "Invalid request (e.g., organization not found or not owned by user)"},
        401: {"description": "Authentication required"}
    }
)
async def create_assessment(
    data: AssessmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Create a new assessment for an organization owned by the current user."""
    service = get_assessment_service(db, user)
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
    recent: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    List assessments owned by the current user, optionally filtered by organization.
    
    Use `recent=N` for dashboard to efficiently fetch only the N most recent assessments.
    """
    service = get_assessment_service(db, user)
    
    # Use recent parameter for efficient dashboard queries
    effective_limit = min(recent, 20) if recent else limit
    
    assessments = service.get_all(organization_id=organization_id, skip=skip, limit=effective_limit)
    
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
    """Get assessment detail (must be owned by current user)."""
    service = get_assessment_service(db, user)
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
    description="""Get comprehensive assessment summary for executive dashboard (must be owned by current user). 
Includes scores, findings, roadmap, baseline comparisons, and optional AI-generated narratives.""",
    responses={
        200: {"description": "Complete assessment summary with all metrics and narratives"},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def get_assessment_summary(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get comprehensive assessment summary for executive dashboard (owned by current user)."""
    service = get_assessment_service(db, user)
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
    """Update an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
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
    """Delete an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
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
    description="Submit or update answers for an assessment (must be owned by current user). Uses upsert semantics.",
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
    """Submit answers for an assessment owned by current user."""
    service = get_assessment_service(db, user)
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


@router.put(
    "/{assessment_id}/answers",
    response_model=List[AnswerResponse],
    summary="Update Answers",
    description="Update answers for an assessment (must be owned by current user). Same as POST but with PUT semantics.",
    responses={
        200: {"description": "Answers updated successfully"},
        404: {"description": "Assessment not found"}
    }
)
async def update_answers(
    assessment_id: str,
    data: AnswerBulkSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Update answers for an assessment owned by current user."""
    return await submit_answers(assessment_id, data, db, user)


@router.get("/{assessment_id}/answers", response_model=List[AnswerResponse])
async def get_answers(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all answers for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    assessment = service.get(assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return service.get_answers(assessment_id)


# ----- Edit Mode -----

@router.get("/{assessment_id}/edit")
async def get_assessment_edit_context(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Get context for editing an assessment (simple answer map).
    """
    service = get_assessment_service(db, user)
    result = service.get_edit_context(assessment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    return result


@router.put("/{assessment_id}/edit")
async def update_assessment_answers(
    assessment_id: str,
    data: AnswerBulkSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Update answers for an assessment (Edit Mode). 
    Effectively alias to submit_answers but semantically distinct for UI.
    """
    return await submit_answers(assessment_id, data, db, user)



# ----- Scoring -----

@router.post(
    "/{assessment_id}/score",
    response_model=ComputeScoreResponse,
    summary="Compute Score",
    description="Calculate and persist scores and findings for an assessment (must be owned by current user).",
    responses={
        200: {"description": "Scores computed and persisted successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def compute_score(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Compute and persist scores and findings for an assessment owned by current user."""
    service = get_assessment_service(db, user)
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


@router.post(
    "/{assessment_id}/refresh-narrative",
    summary="Refresh AI Narrative",
    description="Force regenerate AI-generated narratives for an assessment. Use this when llm_status is 'pending' to get fresh AI insights.",
    responses={
        200: {"description": "Narratives regenerated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"},
        503: {"description": "LLM service unavailable"}
    }
)
async def refresh_narrative(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Regenerate AI narratives for an assessment.
    
    Called when the frontend detects llm_status='pending' and the user
    clicks "Refresh" to generate AI insights.
    """
    service = get_assessment_service(db, user)
    try:
        result = service.refresh_narratives(assessment_id)
        
        event_logger.custom_event("narrative_refreshed", {
            "assessment_id": assessment_id,
            "llm_status": result.get("llm_status", "unknown")
        })
        
        return {
            "assessment_id": assessment_id,
            "llm_status": result.get("llm_status", "disabled"),
            "executive_summary_text": result.get("executive_summary_text"),
            "roadmap_narrative_text": result.get("roadmap_narrative_text"),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to generate narratives: {str(e)}"
        )


@router.get("/{assessment_id}/scores", response_model=List[ScoreResponse])
async def get_scores(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Get all domain scores for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
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
    """Get all findings for an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
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
    """Add a manual finding to an assessment (must be owned by current user)."""
    service = get_assessment_service(db, user)
    try:
        finding = service.add_finding(assessment_id, data)
        return finding
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ----- Reports -----

@router.post(
    "/{assessment_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and Save Report",
    description="Generate a new report for the assessment and save it persistently. The report captures a snapshot of the assessment data at generation time.",
    responses={
        201: {"description": "Report created successfully"},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def create_report(
    assessment_id: str,
    data: ReportCreate = ReportCreate(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Generate and save a report for an assessment owned by current user."""
    assessment_service = get_assessment_service(db, user)
    assessment_detail = assessment_service.get_detail(assessment_id)
    
    if not assessment_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment not found: {assessment_id}"
        )
    
    # Check if assessment has been scored
    if assessment_detail.get("overall_score") is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assessment has not been scored yet. Call POST /assessments/{id}/score first."
        )
    
    # Create persistent report
    report_service = get_report_service(db, user)
    try:
        report = report_service.create(assessment_id, data)
        
        # Log report creation
        event_logger.report_generated(assessment_id=assessment_id, format="pdf")
        
        return {
            "id": report.id,
            "owner_uid": report.owner_uid,
            "organization_id": report.organization_id,
            "organization_name": report.organization.name if report.organization else None,
            "assessment_id": report.assessment_id,
            "assessment_title": report.assessment.title if report.assessment else None,
            "report_type": report.report_type,
            "title": report.title,
            "overall_score": report.overall_score,
            "maturity_level": report.maturity_level,
            "maturity_name": report.maturity_name,
            "findings_count": report.findings_count,
            "created_at": report.created_at,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{assessment_id}/report",
    summary="Generate PDF Report (Legacy)",
    description="Generate and download a professional PDF report for the assessment (must be owned by current user). Consider using POST /assessments/{id}/reports to create a persistent report.",
    responses={
        200: {"description": "PDF report file", "content": {"application/pdf": {}}},
        400: {"description": "Assessment has not been scored yet"},
        401: {"description": "Authentication required"},
        404: {"description": "Assessment not found"}
    }
)
async def generate_report(
    assessment_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Generate PDF report for an assessment owned by current user."""
    service = get_assessment_service(db, user)
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
