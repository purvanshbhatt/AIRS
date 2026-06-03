"""
Integration endpoints (API keys + webhooks).

In demo mode (ENV=demo), write operations are blocked with 403 Forbidden.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.schemas.integrations import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyMetadataResponse,
    WebhookCreateRequest,
    WebhookResponse,
    WebhookTestResponse,
    SplunkSeedRequest,
    SplunkSeedResponse,
    ExternalFindingResponse,
    WebhookUrlTestRequest,
    WebhookUrlTestResponse,
    SplunkHecConfigRequest,
    SplunkEvidenceResponse,
    SplunkEvidenceResult,
    WazuhConfigRequest,
)
from app.services.integrations import (
    EVENT_ASSESSMENT_SCORED,
    IntegrationService,
    deliver_webhook,
    deliver_webhook_url_test,
)
from app.services.wazuh_client import WazuhClient
from app.services.audit import record_audit_event
from app.models.wazuh_config import WazuhConfig

router = APIRouter()


@router.post("/orgs/{org_id}/api-keys", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    org_id: str,
    data: ApiKeyCreateRequest = ApiKeyCreateRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        result = service.create_api_key(org_id, scopes=data.scopes)
        record_audit_event(
            db=db,
            org_id=org_id,
            action="api_key.created",
            actor=user.uid,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/orgs/{org_id}/api-keys", response_model=list[ApiKeyMetadataResponse])
async def list_api_keys(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.list_api_keys(org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    if not service.deactivate_api_key(key_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")


@router.post("/orgs/{org_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    org_id: str,
    data: WebhookCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.create_webhook(
            org_id=org_id,
            url=str(data.url),
            event_types=data.event_types,
            secret=data.secret,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/orgs/{org_id}/webhooks", response_model=list[WebhookResponse])
async def list_webhooks(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        return service.list_webhooks(org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    if not service.delete_webhook(webhook_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")


@router.post("/webhooks/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    webhook = service.get_webhook_for_owner(webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

    payload = {
        "event_type": EVENT_ASSESSMENT_SCORED,
        "org_id": webhook.org_id,
        "assessment_id": "test-assessment",
        "score": 75.0,
        "critical_findings": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test": True,
    }
    delivered, status_code, error = deliver_webhook(webhook, EVENT_ASSESSMENT_SCORED, payload)
    record_audit_event(
        db=db,
        org_id=webhook.org_id,
        action="webhook.triggered.manual_test",
        actor=user.uid,
    )
    return {
        "webhook_id": webhook_id,
        "delivered": delivered,
        "status_code": status_code,
        "error": error,
    }


@router.post("/integrations/mock/splunk-seed", response_model=SplunkSeedResponse)
async def seed_mock_splunk_findings(
    data: SplunkSeedRequest = SplunkSeedRequest(),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        res = service.seed_mock_splunk_findings(org_id=data.org_id)
        # Broadcast real-time GHI update over WebSockets
        from app.core.websocket_manager import telemetry_ws_manager
        await telemetry_ws_manager.broadcast_org_update(res["org_id"], db_session=db)
        return res
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/integrations/external-findings", response_model=list[ExternalFindingResponse])
async def list_external_findings(
    source: str = Query(default="splunk"),
    limit: int = Query(default=50, ge=1, le=200),
    org_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    service = IntegrationService(db, owner_uid=user.uid)
    try:
        findings = service.list_external_findings(source=source, limit=limit, org_id=org_id)
        return findings
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/integrations/webhooks/test", response_model=WebhookUrlTestResponse)
async def test_webhook_url(
    data: WebhookUrlTestRequest,
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    payload = {
        "event_type": data.event_type,
        "org_id": f"user:{user.uid}",
        "assessment_id": "test-assessment",
        "score": 78.0,
        "critical_findings": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test": True,
    }
    delivered, status_code, error = deliver_webhook_url_test(
        url=str(data.url),
        event_type=data.event_type,
        payload=payload,
        secret=data.secret,
    )
    return {
        "delivered": delivered,
        "status_code": status_code,
        "error": error,
        "event_type": data.event_type,
        "payload": payload,
    }


# ── Splunk Evidence-Based Verification ──────────────────────────────


# In-memory store replaced with Connector table backed by AES-256-GCM.


@router.post("/orgs/{org_id}/splunk-config", status_code=status.HTTP_200_OK)
async def configure_splunk_hec(
    org_id: str,
    data: SplunkHecConfigRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Save Splunk HEC credentials for an organization (staging only)."""
    from app.services.organization import OrganizationService
    svc = OrganizationService(db, owner_uid=user.uid)
    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    from app.models.connector import Connector, ConnectorType, ConnectorAuthMethod, ConnectorStatus
    import json
    
    conn = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk
    ).first()
    
    if not conn:
        conn = Connector(
            org_id=org_id,
            connector_type=ConnectorType.splunk,
            display_name="Splunk SIEM",
            auth_method=ConnectorAuthMethod.api_key,
            status=ConnectorStatus.active
        )
        db.add(conn)
        
    conn.encrypted_credentials = data.hec_token
    conn.config = {"base_url": data.base_url}
    db.commit()
    
    # Broadcast real-time GHI update over WebSockets
    from app.core.websocket_manager import telemetry_ws_manager
    await telemetry_ws_manager.broadcast_org_update(org_id, db_session=db)
    
    return {"org_id": org_id, "status": "configured", "base_url": data.base_url}


@router.post("/integrations/wazuh/configure", status_code=status.HTTP_200_OK)
async def configure_wazuh(
    data: WazuhConfigRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """Save Wazuh manager credentials for the current user/org context."""
    import logging
    logger = logging.getLogger("airs.api.integrations")
    logger.info("Wazuh Request Received", extra={"payload": data.model_dump()})
    from app.services.organization import OrganizationService
    from app.services.wazuh_client import WazuhClientFactory, run_wazuh_connect_sync
    from app.services.audit import record_connector_audit

    svc = OrganizationService(db, owner_uid=user.uid)
    
    # Resolve org_id from user if not provided in request
    org_id = data.org_id
    if not org_id:
        orgs = svc.get_all()
        if not orgs:
            raise HTTPException(status_code=404, detail="No organization found for the current user.")
        org_id = orgs[0].id

    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    logger.info("Resolved organization for Wazuh config", extra={"org_id": org_id, "user_uid": user.uid})

    is_update = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first() is not None
    action_type = "updated" if is_update else "configured"

    # Save to database
    config = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if config:
        config.wazuh_host = data.wazuh_host
        config.wazuh_port = data.wazuh_port
        config.wazuh_api_key = data.wazuh_api_key
        config.verify_ssl = data.verify_ssl
    else:
        config = WazuhConfig(
            org_id=org_id,
            wazuh_host=data.wazuh_host,
            wazuh_port=data.wazuh_port,
            wazuh_api_key=data.wazuh_api_key,
            verify_ssl=data.verify_ssl
        )
        db.add(config)
    db.commit()

    # Invalidate client factory cache
    WazuhClientFactory.invalidate_client(org_id)

    # Dual-write to Firestore
    try:
        from app.db.firestore import firestore_save_wazuh_config
        firestore_save_wazuh_config(config)
    except Exception as exc:
        record_connector_audit(
            db=db,
            org_id=org_id,
            action=action_type,
            actor=user.uid,
            connector_type="wazuh",
            status="partial_success",
            extra_details={"warning": f"Firestore write failed: {exc}"}
        )

    # Spawn background task to connect, sync, verify, and emit progress
    background_tasks.add_task(
        run_wazuh_connect_sync,
        org_id=org_id,
        client_params={
            "wazuh_host": data.wazuh_host,
            "wazuh_port": data.wazuh_port,
            "wazuh_api_key": data.wazuh_api_key,
        },
        user_uid=user.uid
    )

    return {
        "status": "initiating",
        "host": data.wazuh_host,
        "port": data.wazuh_port,
        "message": "Wazuh configuration connection sync initiated in background",
    }


@router.get("/integrations/status")
async def get_integration_status(
    org_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Return a unified integration health snapshot for the dashboard."""
    wazuh_status = "not_configured"
    wazuh_host = None
    wazuh_port = None
    splunk_status = "not_configured"
    
    if org_id:
        cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
        if cfg:
            wazuh_status = "configured"
            wazuh_host = cfg.wazuh_host
            wazuh_port = cfg.wazuh_port
        from app.models.connector import Connector, ConnectorType
        conn = db.query(Connector).filter(
            Connector.org_id == org_id,
            Connector.connector_type == ConnectorType.splunk
        ).first()
        if conn and conn.status == "active":
            splunk_status = "configured"
            
    return {
        "wazuh_status": wazuh_status,
        "wazuh_message": "Wazuh manager connected" if wazuh_status == "configured" else "Not configured",
        "wazuh_host": wazuh_host,
        "wazuh_port": wazuh_port,
        "splunk_status": splunk_status,
        "splunk_message": "Splunk instance connected" if splunk_status == "configured" else "Not configured",
        "siem_verified_controls": 0,
        "siem_verified_percentage": 0.0,
    }


@router.get("/integrations/wazuh/agent-status")
async def get_wazuh_agent_status(
    org_id: str = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Fetch cached Wazuh agent status for the signed-in user."""
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    from app.services.wazuh_client import refresh_wazuh_cache
    from app.services.audit import record_connector_audit
    import json

    cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wazuh not configured",
                "action_required": "/api/integrations/wazuh/configure"
            }
        )

    cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()
    if not cache or not cache.agent_status:
        # Fallback to refresh cache synchronously on demand
        refreshed = await refresh_wazuh_cache(org_id, db)
        if refreshed:
            cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()

    if not cache or not cache.agent_status:
        record_connector_audit(
            db=db,
            org_id=org_id,
            action="poll_failed",
            actor=user.uid,
            connector_type="wazuh",
            status="failed",
            extra_details={"error": "Telemetry cache is empty and refresh failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wazuh telemetry not available",
                "action_required": "/api/integrations/wazuh/configure"
            }
        )

    # Log structured success poll
    record_connector_audit(
        db=db,
        org_id=org_id,
        action="poll_success",
        actor=user.uid,
        connector_type="wazuh",
        status="success"
    )

    return json.loads(cache.agent_status)


@router.get("/integrations/wazuh/vulnerabilities")
async def get_wazuh_vulnerabilities(
    org_id: str = Query(...),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Fetch cached Wazuh vulnerabilities for the signed-in user."""
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    from app.services.wazuh_client import refresh_wazuh_cache
    from app.services.audit import record_connector_audit
    import json

    cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wazuh not configured",
                "action_required": "/api/integrations/wazuh/configure"
            }
        )

    cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()
    if not cache or not cache.vulnerabilities:
        # Fallback to refresh cache synchronously on demand
        refreshed = await refresh_wazuh_cache(org_id, db)
        if refreshed:
            cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()

    if not cache or not cache.vulnerabilities:
        record_connector_audit(
            db=db,
            org_id=org_id,
            action="poll_failed",
            actor=user.uid,
            connector_type="wazuh",
            status="failed",
            extra_details={"error": "Vulnerabilities cache is empty and refresh failed"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Wazuh telemetry not available",
                "action_required": "/api/integrations/wazuh/configure"
            }
        )

    # Log structured success poll
    record_connector_audit(
        db=db,
        org_id=org_id,
        action="poll_success",
        actor=user.uid,
        connector_type="wazuh",
        status="success"
    )

    data = json.loads(cache.vulnerabilities)
    # Apply filtering post-cache retrieval
    if severity:
        data["vulnerabilities"] = [v for v in data.get("vulnerabilities", []) if v.get("severity") == severity.lower()]
    if limit:
        data["vulnerabilities"] = data.get("vulnerabilities", [])[:limit]
        
    return data


@router.get("/orgs/{org_id}/splunk-config")
async def get_splunk_config(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Check if Splunk HEC is configured for an organization."""
    from app.models.connector import Connector, ConnectorType
    conn = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk
    ).first()
    if not conn or conn.status != "active":
        return {"org_id": org_id, "configured": False}
        
    config_dict = conn.config or {}
    return {
        "org_id": org_id,
        "configured": True,
        "base_url": config_dict.get("base_url", ""),
        # Never return the token
    }


@router.delete("/orgs/{org_id}/splunk-config", status_code=status.HTTP_204_NO_CONTENT)
async def remove_splunk_config(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    from app.models.connector import Connector, ConnectorType
    db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk
    ).delete()
    db.commit()

    # Broadcast real-time GHI update over WebSockets
    from app.core.websocket_manager import telemetry_ws_manager
    await telemetry_ws_manager.broadcast_org_update(org_id, db_session=db)


@router.post("/orgs/{org_id}/splunk-evidence", response_model=SplunkEvidenceResponse)
async def pull_splunk_evidence(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
):
    """
    Pull live evidence from Splunk for MFA enforcement + EDR coverage.
    Returns verification status with 'Verified via Splunk' badges.
    """
    from app.services.organization import OrganizationService
    svc = OrganizationService(db, owner_uid=user.uid)
    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    from app.models.connector import Connector, ConnectorType
    conn = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk
    ).first()
    
    if not conn or conn.status != "active":
        # Return not-configured result instead of error
        return SplunkEvidenceResponse(
            org_id=org_id,
            results=[
                SplunkEvidenceResult(
                    control="MFA Enforcement",
                    status="not_configured",
                    message="Splunk HEC not configured. Add your Splunk URL and HEC token to enable evidence-based verification.",
                ),
                SplunkEvidenceResult(
                    control="EDR Coverage",
                    status="not_configured",
                    message="Splunk HEC not configured. Add your Splunk URL and HEC token to enable evidence-based verification.",
                ),
            ],
            overall_status="not_configured",
            verified_controls=0,
            total_controls=2,
        )

    from app.services.splunk import SplunkService
    config_dict = conn.config or {}
    base_url = config_dict.get("base_url", "")
    splunk = SplunkService(base_url=base_url, hec_token=conn.encrypted_credentials)
    raw_results = await splunk.pull_all_evidence()

    results = [SplunkEvidenceResult(**r) for r in raw_results]
    verified = sum(1 for r in results if r.status == "verified")
    overall = "verified" if verified == len(results) else "partial" if verified > 0 else "not_verified"

    return SplunkEvidenceResponse(
        org_id=org_id,
        results=results,
        overall_status=overall,
        verified_controls=verified,
        total_controls=len(results),
    )
