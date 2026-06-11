from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.services.control_verification import VerificationService
from app.schemas.control_verification import (
    TelemetryIngestRequest,
    AttestRequest,
    VerificationSummaryResponse,
    VerificationResultResponse
)

router = APIRouter()


def get_verification_service(db: Session, user: User) -> VerificationService:
    # Assuming organization_id is accessible via user's context; 
    # for now we use user.organization_id if available, otherwise fallback to a default or require it.
    org_id = getattr(user, "organization_id", "default_org")
    return VerificationService(db, org_id)


@router.get("/summary", response_model=VerificationSummaryResponse)
def get_verification_summary(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
) -> Any:
    """
    Retrieve rollup metrics for the Trust Dashboard showing verification states.
    """
    service = get_verification_service(db, user)
    summary = service.get_summary()
    return summary


@router.post("/ingest", response_model=VerificationResultResponse)
def ingest_telemetry_evidence(
    request: TelemetryIngestRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
) -> Any:
    """
    Accept standardized telemetry payloads to deterministically verify a control.
    """
    service = get_verification_service(db, user)
    result = service.ingest_telemetry(
        control_id=request.control_id,
        telemetry_event_id=request.telemetry_event_id,
        connector_id=request.connector_id,
        status=request.status,
        evidence_payload=request.evidence_payload,
    )
    return result


@router.post("/{control_id}/attest", response_model=VerificationResultResponse)
def attest_control(
    control_id: str,
    request: AttestRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
) -> Any:
    """
    Manually attest to a control. This marks it as SELF_ATTESTED, never VERIFIED.
    """
    service = get_verification_service(db, user)
    result = service.attest_control(
        control_id=control_id,
        user_id=user.uid,
        reason=request.reason,
    )
    return result
