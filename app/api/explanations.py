"""
Explanations API — Business Language for Non-Technical Users.

Provides POST /api/orgs/{org_id}/explanations endpoint that transforms
deterministic backend facts into executive-friendly narratives.

INVARIANTS:
  - Gemini NEVER calculates scores
  - Gemini NEVER creates or modifies findings
  - Gemini NEVER determines framework mappings
  - All explanations are traceable to source facts
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.models.organization import Organization
from app.schemas.explanation import ExplanationRequest, ExplanationResponse
from app.services.explanation import ExplanationService

logger = logging.getLogger("airs.api.explanations")

router = APIRouter()


def _verify_org_access(db: Session, org_id: str, user: User) -> Organization:
    """Verify that the authenticated user owns the organization.
    
    Returns the Organization if access is granted.
    Raises 404 if organization not found or not owned (prevents enumeration).
    """
    org = db.query(Organization).filter(
        Organization.id == org_id,
        Organization.owner_uid == user.uid,
    ).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )
    return org


@router.post(
    "",
    response_model=ExplanationResponse,
    summary="Generate Business-Language Explanation",
    description=(
        "Transforms a deterministic finding, readiness result, connector status, "
        "or evidence record into an executive-friendly narrative using Gemini. "
        "Gemini NEVER calculates scores or modifies findings."
    ),
    responses={
        200: {"description": "Explanation generated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization or subject not found"},
        422: {"description": "Invalid request body"},
    },
)
async def create_explanation(
    org_id: str,
    body: ExplanationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Generate a business-language explanation for a deterministic subject."""
    # Tenant isolation: verify org ownership
    _verify_org_access(db, org_id, user)

    service = ExplanationService(db, org_id=org_id, owner_uid=user.uid)

    try:
        result = service.generate_explanation(
            subject_type=body.subject_type.value,
            subject_id=body.subject_id,
            audience=body.audience.value,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "SUBJECT_NOT_FOUND", "message": str(e)}},
        )
    except Exception as e:
        logger.error(f"Explanation generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "EXPLANATION_FAILED", "message": "Failed to generate explanation."}},
        )

    # Log audit event (no secrets)
    logger.info(
        f"Explanation generated: org={org_id} subject={body.subject_type.value}/{body.subject_id} "
        f"audience={body.audience.value} model={result['model']}"
    )

    return result
