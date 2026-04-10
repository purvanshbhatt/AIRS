"""API endpoints for strict Gemini intelligence packet ingestion."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.db.firestore import FirestoreUnavailableError, firestore_upsert_remediation_ledger
from app.schemas.intelligence_packet import (
    IntelligencePacketIngestResponse,
    ResilAIIntelligencePacket,
)
from app.services.organization import OrganizationService

router = APIRouter()


@router.post(
    "/orgs/{org_id}/workspaces/{workspace_id}/audits/{audit_id}/intelligence-packet",
    response_model=IntelligencePacketIngestResponse,
)
async def ingest_intelligence_packet(
    org_id: str,
    workspace_id: str,
    audit_id: str,
    packet: ResilAIIntelligencePacket,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """
    Validate Gemini JSON contract and persist remediation tasks to Firestore.

    Endpoint contract is intentionally strict (extra fields are rejected) so the
    React UI can consume deterministic data for score updates, task tracking,
    and attack simulation timelines.
    """
    org_service = OrganizationService(db, owner_uid=user.uid)
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    try:
        result = firestore_upsert_remediation_ledger(
            org_id=org_id,
            workspace_id=workspace_id,
            audit_id=audit_id,
            owner_uid=user.uid,
            packet=packet.model_dump(mode="json"),
        )
    except FirestoreUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return IntelligencePacketIngestResponse(
        status="ok",
        org_id=org_id,
        workspace_id=workspace_id,
        audit_id=audit_id,
        tasks_upserted=result["tasks_upserted"],
        ledger_collection_path=result["ledger_collection_path"],
    )
