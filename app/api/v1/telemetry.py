"""
Telemetry Events API — SIEM Webhook Ingestion Endpoint.

Exposes:
  POST /api/v1/integrations/siem/event
    Ingests SIEM events from Wazuh/Splunk/Elastic via webhook.
    Protected by either:
      a) HMAC-SHA256 signature verification (X-AIRS-Signature header), or
      b) Machine-to-machine API key (X-AIRS-API-Key header).

Security Design:
  - HMAC verification uses a shared webhook secret stored in settings.
  - The signature covers the raw request body to prevent tampering.
  - Idempotent: duplicate siem_alert_ids return 200 OK.
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
from app.core.api_key_auth import get_api_key_dependency
from app.db.database import get_db
from app.services.telemetry import (
    SIEMEventPayload,
    TelemetryVerificationService,
    VerificationResponse,
)

router = APIRouter(prefix="/integrations/siem")
logger = logging.getLogger("airs.api.telemetry")


# ---------------------------------------------------------------------------
# HMAC Signature Verification Dependency
# ---------------------------------------------------------------------------

async def verify_webhook_signature(
    request: Request,
    x_airs_signature: Optional[str] = Header(default=None, alias="X-AIRS-Signature"),
    x_airs_api_key: Optional[str] = Header(default=None, alias="X-AIRS-API-Key"),
    db: Session = Depends(get_db),
) -> str:
    """Verify the inbound request via HMAC signature OR API key.

    Security flow:
      1. If X-AIRS-Signature header is present → verify HMAC-SHA256.
      2. Else if X-AIRS-API-Key header is present → verify API key.
      3. Else → 401 Unauthorized.

    The HMAC signature format: sha256=<hex_digest>
    The digest covers the raw request body bytes.
    """
    # Path 1: HMAC Signature
    if x_airs_signature:
        webhook_secret = getattr(settings, "WEBHOOK_SECRET", None) or getattr(settings, "SIEM_WEBHOOK_SECRET", None)
        if not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured on server.",
            )

        body = await request.body()
        expected_sig = "sha256=" + hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(x_airs_signature, expected_sig):
            logger.warning(
                "HMAC signature mismatch: received=%s expected=%s",
                x_airs_signature[:20] + "...",
                expected_sig[:20] + "...",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature.",
            )
        return "hmac_verified"

    # Path 2: API Key
    if x_airs_api_key:
        from app.services.integrations import validate_api_key
        key = validate_api_key(db, x_airs_api_key, required_scopes=["telemetry:write"])
        if not key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key or insufficient scope.",
            )
        return "api_key_verified"

    # Path 3: No auth
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication: provide X-AIRS-Signature or X-AIRS-API-Key header.",
    )


# ---------------------------------------------------------------------------
# POST /api/v1/integrations/siem/event
# ---------------------------------------------------------------------------

@router.post(
    "/event",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest SIEM Telemetry Event",
    description=(
        "Receives a SIEM event from Wazuh, Splunk, or Elastic. "
        "Cross-references the event against the FrameworkMappingRegistry, "
        "creates/updates the FindingProvenance trust anchor, and triggers "
        "a deterministic GHI score recomputation. Idempotent: duplicate "
        "siem_alert_ids return 200 OK without side effects."
    ),
)
async def ingest_siem_event(
    payload: SIEMEventPayload,
    db: Session = Depends(get_db),
    auth_method: str = Depends(verify_webhook_signature),
) -> VerificationResponse:
    """Process a single SIEM telemetry event."""
    logger.info(
        json.dumps({
            "event": "siem_event_received",
            "source": payload.source,
            "alert_id": payload.alert_id,
            "rule_id": payload.rule_id,
            "auth_method": auth_method,
        })
    )

    service = TelemetryVerificationService(db)
    result = service.process_siem_event(payload)

    # If a finding was verified, trigger GHI recomputation
    if result.status == "verified" and result.finding_id:
        # Find the assessment for this finding
        from app.models.finding import Finding as FindingModel
        finding = db.query(FindingModel).filter(FindingModel.id == result.finding_id).first()
        if finding:
            score_update = service.recompute_ghi_for_assessment(
                assessment_id=finding.assessment_id,
                trigger_evidence_hash=result.evidence_hash,
            )
            if score_update:
                logger.info(
                    json.dumps({
                        "event": "ghi_recomputed",
                        "assessment_id": finding.assessment_id,
                        "old_score": score_update["old_score"],
                        "new_score": score_update["new_score"],
                        "delta": score_update["delta"],
                        "evidence_hash": score_update["evidence_hash"],
                    })
                )

    return result


# ---------------------------------------------------------------------------
# GET /api/v1/telemetry/health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    summary="Telemetry Ingestion Health Check",
    description="Returns the status of the telemetry ingestion pipeline.",
)
async def telemetry_health():
    return {
        "status": "healthy",
        "service": "TelemetryVerificationService",
        "hmac_configured": bool(
            getattr(settings, "WEBHOOK_SECRET", None)
            or getattr(settings, "SIEM_WEBHOOK_SECRET", None)
        ),
    }
