"""External integration endpoints (API key secured, rate-limited)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.api_key_auth import get_api_key_dependency
from app.db.database import get_db
from app.models.api_key import ApiKey
from app.schemas.integrations import ExternalLatestScoreResponse
from app.services.integrations import build_external_latest_score_payload
from app.core.security.webhooks import verify_telemetry_webhook, TelemetryPayloadSchema

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/external/latest-score", response_model=ExternalLatestScoreResponse)
@limiter.limit("30/minute")
async def get_latest_score_for_external(
    request: Request,
    api_key: ApiKey = Depends(get_api_key_dependency(required_scopes=["scores:read"])),
    db: Session = Depends(get_db),
):
    payload = build_external_latest_score_payload(db, api_key.owner_org_id)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed assessment found for this organization",
        )
    return payload

@router.post("/external/telemetry/webhook", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("100/minute")
async def receive_telemetry_webhook(
    request: Request,
    payload: TelemetryPayloadSchema = Depends(verify_telemetry_webhook),
    db: Session = Depends(get_db),
):
    """
    Ingest external telemetry events.
    Strictly protected by TelemetryInterceptor which enforces HMAC-SHA256,
    size limits, and payload schema boundaries.
    """
    from app.services.audit import record_connector_audit
    
    # Store event for async evaluation loops
    record_connector_audit(
        db=db,
        org_id="webhook-telemetry",  # In reality, map source/token to org_id
        action="telemetry.received",
        actor="external_webhook",
        connector_type="telemetry",
        status="success",
        extra_details={"event_type": payload.event_type}
    )
    
    return {"status": "accepted", "event_type": payload.event_type}