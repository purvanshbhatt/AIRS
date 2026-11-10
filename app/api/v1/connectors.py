"""
Connector Management API — Register, sync, and monitor telemetry connectors.

All endpoints are org-scoped via Firebase Auth. Credentials are encrypted
at rest and NEVER exposed in API responses.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth, get_user_org_id
from app.core.entitlements import require_entitlement
from app.db.database import get_db
from app.services.billing.entitlements import Entitlement
from app.schemas.connector import (
    ConnectorCreateRequest,
    ConnectorHealthResponse,
    ConnectorListResponse,
    ConnectorResponse,
    ConnectorSyncLogResponse,
    ConnectorSyncResponse,
    ConnectorUpdateRequest,
    WazuhConnectRequest,
)
from app.services.connector_manager import (
    ConnectorManager,
    ConnectorNotFoundError,
)

logger = logging.getLogger("airs.api.connectors")

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _get_org_id(user: User, db: Session, org_id: Optional[str] = None) -> str:
    """Resolve the organization this request operates on.

    When the client passes ``?org_id=`` (the active workspace in the UI) it
    must belong to the signed-in user; otherwise fall back to the user's
    first organization.
    """
    if org_id:
        from app.services.organization import OrganizationService
        org = OrganizationService(db, owner_uid=user.uid if user else None).get(org_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return org.id
    return get_user_org_id(user, db)


ORG_ID_QUERY = Query(None, description="Organization ID (defaults to the user's first organization)")


# =============================================================================
# CRUD
# =============================================================================

@router.post(
    "",
    response_model=ConnectorResponse,
    status_code=201,
    summary="Register a new telemetry connector",
    description="Register an external integration connector. Credentials are encrypted at rest.",
)
async def create_connector(
    body: ConnectorCreateRequest,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    _ent: None = Depends(require_entitlement(Entitlement.CONNECTORS_MANAGE)),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)

    try:
        connector = mgr.register_connector(
            connector_type=body.connector_type,
            display_name=body.display_name,
            auth_method=body.auth_method,
            credentials=body.credentials,
            config=body.config,
            sync_interval_minutes=body.sync_interval_minutes,
            created_by=user.uid,
        )
        return ConnectorResponse.model_validate(connector)
    except Exception as exc:
        logger.error("Connector registration failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "",
    response_model=ConnectorListResponse,
    summary="List organization connectors",
    description="Returns all connectors belonging to the authenticated user's organization.",
)
async def list_connectors(
    connector_type: Optional[str] = Query(None, description="Filter by connector type"),
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    connectors = mgr.list_connectors(connector_type=connector_type)

    return ConnectorListResponse(
        connectors=[ConnectorResponse.model_validate(c) for c in connectors],
        total=len(connectors),
    )



# =============================================================================
# Confidence
# =============================================================================

from app.schemas.evidence import OrgConfidenceResponse

@router.get(
    "/confidence",
    response_model=OrgConfidenceResponse,
    summary="Get evidence confidence scores",
    description="Returns confidence scores for all connectors and an organization aggregate.",
)
async def get_confidence(
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    # The instructions require 422 for missing org_id (though get_user_org_id raises 404 if missing)
    if not org_id:
        raise HTTPException(status_code=422, detail="Missing org_id")

    from app.services.evidence.registry import get_instance
    from app.services.evidence_confidence import calculate_evidence_confidence
    from app.schemas.evidence import ConnectorConfidenceDetail
    
    registry = get_instance()
    adapters = registry.adapters()
    
    details = []
    total_score = 0.0
    
    for adapter in adapters:
        try:
            health = await adapter.health()
        except Exception:
            from app.services.evidence.base_adapter import AdapterHealth
            from datetime import datetime, timezone
            health = AdapterHealth(healthy=False, last_failure_at=datetime.now(timezone.utc), failure_count=1)
            
        conf = calculate_evidence_confidence(health)
        details.append(
            ConnectorConfidenceDetail(
                connector_name=adapter.connector_name,
                confidence_score=conf["confidence_score"],
                factors=conf["factors"]
            )
        )
        total_score += conf["confidence_score"]
        
    aggregate_score = round(total_score / len(details), 2) if details else 0.0
    
    return OrgConfidenceResponse(
        org_id=org_id,
        aggregate_score=aggregate_score,
        connectors=details,
    )


# =============================================================================
# Wazuh Integration Endpoints
# =============================================================================

@router.post(
    "/wazuh/connect",
    response_model=ConnectorResponse,
    summary="Connect Wazuh XDR manager",
)
async def connect_wazuh(
    body: WazuhConnectRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = body.org_id
    mgr = ConnectorManager(db, org_id)

    try:
        from app.models.wazuh_config import WazuhConfig
        
        # 0. Save WazuhConfig (required by WazuhClientFactory)
        db_config = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
        if db_config:
            db_config.wazuh_host = body.manager_host
            db_config.wazuh_port = body.port
            db_config.wazuh_api_key = body.credentials
            db_config.verify_ssl = True
        else:
            db_config = WazuhConfig(
                org_id=org_id,
                wazuh_host=body.manager_host,
                wazuh_port=body.port,
                wazuh_api_key=body.credentials,
                verify_ssl=True
            )
            db.add(db_config)
        db.commit()

        # 1. Store generic connector configuration
        connector = mgr.register_connector(
            connector_type="wazuh",
            display_name="Wazuh XDR",
            auth_method="api_key",
            credentials={"api_key": body.credentials},
            config={
                "host": body.manager_host,
                "port": body.port,
            },
            sync_interval_minutes=60,
            created_by=user.uid,
        )

        # 2. Test API authentication & pull data
        from app.services.wazuh_client import WazuhClientFactory, refresh_wazuh_cache
        
        try:
            # Re-initialize client cache to pick up new config
            WazuhClientFactory.invalidate_client(org_id)
            client = WazuhClientFactory.get_client(org_id, db)
            if client:
                # 3, 4, 5. Pull agent list, pull vulnerability data, store evidence
                # Implicitly tests authentication (falls back to lab mode if auth fails)
                await refresh_wazuh_cache(org_id, db)
        except Exception as api_exc:
            logger.error("Wazuh API fetch failed: %s", api_exc)
            raise HTTPException(
                status_code=400,
                detail=f"Wazuh connection failed: {api_exc}"
            )

        return ConnectorResponse.model_validate(connector)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# =============================================================================
# Microsoft Custom Integration Endpoints
# =============================================================================

@router.post(
    "/microsoft/sync",
    response_model=ConnectorSyncResponse,
    summary="Trigger manual pull for Microsoft connector",
    description="Locates the active Microsoft connector for the organization and triggers a sync.",
)
async def trigger_microsoft_sync(
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)

    from app.models.connector import Connector, ConnectorType
    connector = (
        db.query(Connector)
        .filter(
            Connector.org_id == org_id,
            Connector.connector_type == ConnectorType.microsoft,
        )
        .first()
    )
    if not connector:
        raise HTTPException(
            status_code=404,
            detail="Active Microsoft connector not found for this organization.",
        )

    try:
        result = await mgr.sync_connector(connector.id)
        
        if result.success and result.events_ingested > 0:
            from app.core.websocket_manager import telemetry_ws_manager
            import asyncio
            asyncio.create_task(telemetry_ws_manager.broadcast_org_update(org_id))
            
        return ConnectorSyncResponse(
            success=result.success,
            events_ingested=result.events_ingested,
            errors_count=result.errors_count,
            duration_ms=result.duration_ms,
            error_details=result.error_details,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/microsoft/health",
    response_model=ConnectorHealthResponse,
    summary="Check token validity and connection health for Microsoft connector",
)
async def check_microsoft_health(
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)

    from app.models.connector import Connector, ConnectorType
    connector = (
        db.query(Connector)
        .filter(
            Connector.org_id == org_id,
            Connector.connector_type == ConnectorType.microsoft,
        )
        .first()
    )
    if not connector:
        raise HTTPException(
            status_code=404,
            detail="Microsoft connector not found for this organization.",
        )

    try:
        health = await mgr.health_check(connector.id)
        return ConnectorHealthResponse(
            status=health.status,
            latency_ms=health.latency_ms,
            message=health.message,
            checked_at=health.checked_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/{connector_id}",
    response_model=ConnectorResponse,
    summary="Get connector details",
    description="Returns a single connector by ID. Verifies org ownership.",
)
async def get_connector(
    connector_id: str,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        connector = mgr.get_connector(connector_id)
        return ConnectorResponse.model_validate(connector)
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")


@router.patch(
    "/{connector_id}",
    response_model=ConnectorResponse,
    summary="Update connector configuration",
)
async def update_connector(
    connector_id: str,
    body: ConnectorUpdateRequest,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        connector = mgr.update_connector(
            connector_id,
            display_name=body.display_name,
            config=body.config,
            sync_interval_minutes=body.sync_interval_minutes,
            status=body.status,
            credentials=body.credentials,
        )
        return ConnectorResponse.model_validate(connector)
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")


@router.delete(
    "/{connector_id}",
    status_code=204,
    summary="Deactivate connector",
    description="Soft-deletes a connector. Audit trail and telemetry events are preserved.",
)
async def deactivate_connector(
    connector_id: str,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        mgr.deactivate_connector(connector_id)
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")


# =============================================================================
# Sync Operations
# =============================================================================

@router.post(
    "/{connector_id}/sync",
    response_model=ConnectorSyncResponse,
    summary="Trigger manual sync",
    description="Triggers an immediate sync for the connector and returns the result.",
)
async def trigger_sync(
    connector_id: str,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    _ent: None = Depends(require_entitlement(Entitlement.CONNECTORS_MANAGE)),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        result = await mgr.sync_connector(connector_id)
        
        if result.success and result.events_ingested > 0:
            from app.core.websocket_manager import telemetry_ws_manager
            import asyncio
            asyncio.create_task(telemetry_ws_manager.broadcast_org_update(org_id))
            
        return ConnectorSyncResponse(
            success=result.success,
            events_ingested=result.events_ingested,
            errors_count=result.errors_count,
            duration_ms=result.duration_ms,
            error_details=result.error_details,
        )
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/{connector_id}/health",
    response_model=ConnectorHealthResponse,
    summary="Health check",
    description="Probes the connector's external API to verify connectivity.",
)
async def check_health(
    connector_id: str,
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        health = await mgr.health_check(connector_id)
        return ConnectorHealthResponse(
            status=health.status,
            latency_ms=health.latency_ms,
            message=health.message,
            checked_at=health.checked_at,
        )
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")


@router.get(
    "/{connector_id}/sync-history",
    response_model=List[ConnectorSyncLogResponse],
    summary="Sync audit trail",
    description="Returns the sync history for a connector (most recent first).",
)
async def get_sync_history(
    connector_id: str,
    limit: int = Query(20, ge=1, le=100),
    org_id: Optional[str] = ORG_ID_QUERY,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db, org_id)
    mgr = ConnectorManager(db, org_id)
    try:
        logs = mgr.get_sync_history(connector_id, limit=limit)
        return [ConnectorSyncLogResponse.model_validate(log) for log in logs]
    except ConnectorNotFoundError:
        raise HTTPException(status_code=404, detail="Connector not found")





# =============================================================================
# Webhook Receiver (with signature verification)
# =============================================================================

@router.post(
    "/webhook/{connector_type}",
    summary="Webhook event receiver",
    description=(
        "Receives pushed telemetry for an organization's webhook connector. "
        "Generic webhooks authenticate with the X-Webhook-Secret header; GitHub "
        "webhooks with X-Hub-Signature-256. Payloads are stored as telemetry events."
    ),
)
async def receive_webhook(
    connector_type: str,
    request: Request,
    org_id: str = Query(..., description="Organization that owns the webhook connector"),
    db: Session = Depends(get_db),
):
    """Ingest a pushed webhook payload as a telemetry event.

    Security: the shared secret is read from the connector's encrypted
    credentials (``webhook_secret``); a request without a valid secret or
    signature is rejected with 401. Unauthenticated webhook endpoints WILL
    fail pen-testing.
    """
    import hashlib
    import hmac
    import json
    from datetime import datetime, timezone

    from app.connectors.base import NormalizedEvent
    from app.connectors.webhook import NETWORK_SNAPSHOT_EVENT
    from app.models.connector import Connector, ConnectorStatus, ConnectorType

    body = await request.body()
    connector_type = connector_type.lower()
    lookup_type = ConnectorType.github if connector_type == "github" else ConnectorType.webhook

    connector = (
        db.query(Connector)
        .filter(
            Connector.org_id == org_id,
            Connector.connector_type == lookup_type,
            Connector.status != ConnectorStatus.inactive,
        )
        .order_by(Connector.created_at.desc())
        .first()
    )
    if not connector:
        raise HTTPException(status_code=404, detail="No webhook connector registered for this organization")

    mgr = ConnectorManager(db, org_id)
    creds = mgr._decrypt_credentials(connector.encrypted_credentials)
    secret = str(creds.get("webhook_secret") or creds.get("secret") or "")

    if connector_type == "github":
        from app.connectors.github import GitHubConnector

        signature = request.headers.get("X-Hub-Signature-256", "")
        if not secret or not GitHubConnector.verify_webhook_signature(body, signature, secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    else:
        provided = request.headers.get("X-Webhook-Secret", "")
        if not secret or not provided or not hmac.compare_digest(provided, secret):
            raise HTTPException(status_code=401, detail="Invalid or missing X-Webhook-Secret header")

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    if not isinstance(payload, dict):
        payload = {"data": payload}

    now = datetime.now(timezone.utc)
    event_type = str(
        payload.get("event_type")
        or request.headers.get("X-GitHub-Event")
        or f"{connector_type}.event"
    )
    explicit_id = (
        payload.get("event_id")
        or payload.get("id")
        or request.headers.get("X-GitHub-Delivery")
    )
    if explicit_id:
        source_event_id = str(explicit_id)
    else:
        source_event_id = hashlib.sha256(body).hexdigest()[:32]
        if event_type.lower() == NETWORK_SNAPSHOT_EVENT:
            # A network that has not changed is re-sent byte for byte. Keep one
            # row per hour so the network map (which reads recent telemetry)
            # still sees a stable network instead of losing it to deduplication.
            source_event_id = f"{source_event_id}-{now.strftime('%Y%m%d%H')}"
    event = NormalizedEvent(
        event_type=event_type,
        source_system=lookup_type.value,
        source_event_id=source_event_id,
        severity=str(payload.get("severity") or "info"),
        payload=payload,
        timestamp=now.isoformat(),
    )

    ingested = await mgr._ingest_events(connector.id, [event])

    connector.last_sync_at = now
    if connector.status != ConnectorStatus.active:
        connector.status = ConnectorStatus.active.value
        connector.health_status = "healthy"
    db.commit()

    logger.info(
        "Webhook ingested: type=%s org=%s connector=%s events=%d size=%d bytes",
        connector_type, org_id, connector.id, ingested, len(body),
    )
    return {"status": "accepted", "connector_type": connector_type, "events_ingested": ingested}
