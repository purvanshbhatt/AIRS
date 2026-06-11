"""
Governance Webhook Ingestion — POST /api/v1/telemetry/webhook/event

Canonical SIEM telemetry ingestion endpoint per the Governance-as-Code
Controller blueprint (Module 2). Distinct from the legacy
/api/v1/integrations/siem/event which uses the older SIEMEventPayload schema.

Security Design:
  - HMAC-SHA256 signature verification OR machine API key required.
  - Multi-tenant: organization_id in body is authoritative.
  - Idempotent: (alert_id, organization_id) composite guard.
  - HTTP 422 on invalid schema (Pydantic V2 native).
  - HTTP 401 on missing authentication.
  - HTTP 404 on unresolvable organization.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas.telemetry_webhook import SIEMEventWebhookPayload, WebhookIngestionResponse
from app.services.telemetry import TelemetryVerificationService

router = APIRouter(prefix="/telemetry/webhook")
logger = logging.getLogger("airs.api.governance_webhook")


# ---------------------------------------------------------------------------
# HMAC Signature Dependency
# ---------------------------------------------------------------------------

async def _verify_auth(
    request: Request,
    x_airs_signature: Optional[str] = Header(default=None, alias="X-AIRS-Signature"),
    x_airs_api_key: Optional[str] = Header(default=None, alias="X-AIRS-API-Key"),
    db: Session = Depends(get_db),
) -> str:
    """Dual-path M2M authentication: HMAC signature OR API key."""

    # Path 1: HMAC Signature
    if x_airs_signature:
        webhook_secret = (
            getattr(settings, "WEBHOOK_SECRET", None)
            or getattr(settings, "SIEM_WEBHOOK_SECRET", None)
        )
        if not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured on server.",
            )
        body = await request.body()
        expected = "sha256=" + hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(x_airs_signature, expected):
            logger.warning("HMAC mismatch for governance webhook.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature. HMAC verification failed.",
            )
        return "hmac_verified"

    # Path 2: API Key
    if x_airs_api_key:
        from app.services.integrations import validate_api_key
        key = validate_api_key(db, x_airs_api_key, required_scopes=["telemetry:write"])
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key or insufficient scope (requires telemetry:write).",
            )
        return "api_key_verified"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Authentication required. Provide X-AIRS-Signature (HMAC-SHA256) "
            "or X-AIRS-API-Key header."
        ),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/telemetry/webhook/event
# ---------------------------------------------------------------------------

@router.post(
    "/event",
    response_model=WebhookIngestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest SIEM Telemetry Webhook Event",
    description=(
        "Canonical SIEM telemetry ingestion endpoint. Accepts a structured "
        "SIEM event payload, resolves the matching finding via ControlRuleRegistry, "
        "creates an immutable FindingProvenance trust anchor with SHA-256 evidence hash, "
        "and triggers deterministic GHI score recomputation. "
        "Idempotent: duplicate (alert_id, organization_id) pairs return HTTP 200 without side effects. "
        "HTTP 422 on schema validation errors. HTTP 401 on missing/invalid auth."
    ),
)
async def ingest_webhook_event(
    payload: SIEMEventWebhookPayload,
    db: Session = Depends(get_db),
    auth_method: str = Depends(_verify_auth),
) -> WebhookIngestionResponse:
    """Process a single SIEM webhook event via the Governance Engine."""

    logger.info(
        json.dumps({
            "event": "governance_webhook.received",
            "alert_id": payload.alert_id,
            "rule_id": payload.rule_id,
            "source_integration": payload.source_integration,
            "organization_id": payload.organization_id,
            "auth_method": auth_method,
        })
    )

    # Validate that the organization exists
    from app.models.organization import Organization
    org = db.query(Organization).filter(
        Organization.id == payload.organization_id
    ).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "organization_not_found",
                "organization_id": payload.organization_id,
                "message": (
                    f"Organization '{payload.organization_id}' not found. "
                    "Ensure organization_id matches a valid tenant."
                ),
            },
        )

    service = TelemetryVerificationService(db)
    result = service.ingest_siem_telemetry(
        alert_id=payload.alert_id,
        rule_id=payload.rule_id,
        source_integration=payload.source_integration,
        organization_id=payload.organization_id,
        raw_telemetry_dump=payload.raw_telemetry_dump,
    )

    # Broadcast real-time GHI update over WebSockets
    from app.core.websocket_manager import telemetry_ws_manager
    await telemetry_ws_manager.broadcast_org_update(payload.organization_id, db_session=db)

    return WebhookIngestionResponse(
        status=result["status"],
        finding_id=result.get("finding_id"),
        finding_title=result.get("finding_title"),
        verification_status=result.get("verification_status"),
        evidence_hash=result.get("evidence_hash"),
        siem_alert_id=result["siem_alert_id"],
        organization_id=result["organization_id"],
        message=result.get("message", ""),
        processed_at=result.get("processed_at"),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/telemetry/webhook/health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    summary="Governance Webhook Health Check",
    tags=["config"],
)
async def webhook_health():
    """Return liveness status of the governance webhook ingestion pipeline."""
    return {
        "status": "healthy",
        "service": "GovernanceWebhookIngestion",
        "hmac_configured": bool(
            getattr(settings, "WEBHOOK_SECRET", None)
            or getattr(settings, "SIEM_WEBHOOK_SECRET", None)
        ),
        "endpoint": "POST /api/v1/telemetry/webhook/event",
    }
