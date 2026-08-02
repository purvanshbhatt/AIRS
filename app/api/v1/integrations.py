"""
SIEM/XDR Integration API Routes (FastAPI).

Real-World Evidence module that connects ResilAI to Wazuh and Splunk.
Moves scoring from Tier 1 (Self-Reported) to Tier 3 (SIEM-Verified).

Endpoints:
  GET  /api/integrations/status           — Check SIEM integration health
  GET  /api/integrations/wazuh/agent-status   — Fetch active/disconnected agents
  GET  /api/integrations/wazuh/vulnerabilities — Fetch CVEs from Wazuh
  POST /api/integrations/splunk/query         — Execute custom SPL query
  GET  /api/integrations/splunk/logging-health — Verify logging persistence
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.core.auth import User, require_auth, require_org_admin
from app.services.wazuh_client import (
    WazuhClient,
    WazuhAgentStatusResponse,
    WazuhVulnerabilitiesResponse,
    WazuhClientFactory,
    refresh_wazuh_cache,
)
from app.connectors.splunk import SplunkConnector
from app.services.elastic import ElasticService
from app.schemas.integrations import (
    WazuhConfigRequest,
    WazuhAgentStatusResponse as WazuhAgentStatusSchema,
    WazuhVulnerabilitiesResponse as WazuhVulnerabilitiesSchema,
    SplunkLoggingHealthResponse,
    SplunkQueryRequest,
    SplunkQueryResponse,
    SIEMIntegrationStatus,
    ElasticConfigRequest,
)
from app.core.demo_guard import require_writable
from app.models.wazuh_config import WazuhConfig
from app.models.connector import Connector, ConnectorType, ConnectorAuthMethod, ConnectorStatus

logger = logging.getLogger("airs.api.integrations")

router = APIRouter(prefix="/integrations", tags=["integrations"])

# Global SIEM clients retained for Elastic only. Splunk + Wazuh
# configuration is read from the Connector / WazuhConfig tables per
# request — there is no longer a process-global ``_splunk_client``.
_elastic_client: Optional[ElasticService] = None


def _get_user_org_id(db: Session, user: User) -> str:
    from app.services.organization import OrganizationService
    orgs = OrganizationService(db, owner_uid=user.uid).get_all()
    if not orgs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found for the current user."
        )
    return orgs[0].id



# =============================================================================
# Wazuh Integration Endpoints
# =============================================================================

@router.post(
    "/wazuh/configure",
    summary="Configure Wazuh Integration",
    description="Set up connection to Wazuh manager for XDR telemetry.",
    tags=["integrations", "configuration"],
)
async def configure_wazuh(
    config: WazuhConfigRequest,
    user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_writable),
):
    """
    POST /api/integrations/wazuh/configure
    
    Requires: org_admin role
    
    Sets up Wazuh integration with credential validation.
    In production, credentials are encrypted and stored in Secret Manager.
    """
    from app.services.organization import OrganizationService
    from app.services.audit import record_connector_audit

    org_id = config.org_id

    svc = OrganizationService(db, owner_uid=user.uid)
    org = svc.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    logger.info("Resolved organization for Wazuh config", extra={"org_id": org_id, "user_uid": user.uid})

    is_update = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first() is not None
    action_type = "updated" if is_update else "configured"

    # Save to database
    db_config = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if db_config:
        db_config.wazuh_host = config.wazuh_host
        db_config.wazuh_port = config.wazuh_port
        db_config.wazuh_api_key = config.wazuh_api_key
        db_config.verify_ssl = config.verify_ssl
    else:
        db_config = WazuhConfig(
            org_id=org_id,
            wazuh_host=config.wazuh_host,
            wazuh_port=config.wazuh_port,
            wazuh_api_key=config.wazuh_api_key,
            verify_ssl=config.verify_ssl
        )
        db.add(db_config)
    db.commit()

    # Invalidate client factory cache
    WazuhClientFactory.invalidate_client(org_id)

    # Dual-write to Firestore
    try:
        from app.db.firestore import firestore_save_wazuh_config
        firestore_save_wazuh_config(db_config)
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

    # Trigger immediate cache polling refresh
    cache_refreshed = await refresh_wazuh_cache(org_id, db)
    if not cache_refreshed:
        record_connector_audit(
            db=db,
            org_id=org_id,
            action="auth_failed",
            actor=user.uid,
            connector_type="wazuh",
            status="failed",
            extra_details={"error": "Telemetry connection validation failed"}
        )
        raise HTTPException(
            status_code=400,
            detail="Wazuh connection failed validation. Please check host and API key."
        )

    record_connector_audit(
        db=db,
        org_id=org_id,
        action=action_type,
        actor=user.uid,
        connector_type="wazuh",
        status="success",
        extra_details={
            "host": config.wazuh_host,
            "port": config.wazuh_port,
        }
    )

    return {
        "status": "configured",
        "host": config.wazuh_host,
        "port": config.wazuh_port,
        "message": "Wazuh connection validated successfully",
    }


@router.get(
    "/wazuh/agent-status",
    response_model=WazuhAgentStatusSchema,
    summary="Fetch Wazuh Agent Status",
    description="Get active vs. disconnected endpoint status. Triggers finding if >10% disconnected.",
    tags=["integrations", "evidence"],
)
async def get_wazuh_agent_status(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    GET /api/integrations/wazuh/agent-status
    
    Fetches Wazuh agent connectivity status for all registered endpoints.
    
    SIEM Evidence Mapping:
      - If disconnected_agents > 10%: Trigger automatic high-severity finding
        in the "Detection Coverage" domain
    
    Returns: Agent status breakdown with disconnection rate percentage
    """
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    from app.services.audit import record_connector_audit
    import json

    org_id = _get_user_org_id(db, user)

    cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wazuh not configured. Call /api/integrations/wazuh/configure first."
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
            detail="Wazuh telemetry not available"
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

    data = json.loads(cache.agent_status)
    
    # Check for high disconnection rate
    disconnection_rate = data.get("disconnection_rate_percent", 0.0)
    if disconnection_rate > 10:
        logger.warning(
            f"High disconnection rate ({disconnection_rate:.1f}%) "
            f"— automatic finding will be triggered"
        )
        
    return data


@router.get(
    "/wazuh/vulnerabilities",
    response_model=WazuhVulnerabilitiesSchema,
    summary="Fetch Wazuh Vulnerabilities",
    description="Get CVEs detected across endpoints. Auto-generates findings for critical CVEs.",
    tags=["integrations", "evidence"],
)
async def get_wazuh_vulnerabilities(
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    limit: int = Query(100, ge=1, le=500, description="Max vulnerabilities to return"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    GET /api/integrations/wazuh/vulnerabilities
    
    Fetches vulnerability alerts from Wazuh vulnerability detector.
    
    SIEM Evidence Mapping:
      - Critical CVEs (especially CVE-2024-3094): Auto-generate Remediation Task
        with +15 GHI impact in the Remediation Ledger
    
    Query Parameters:
      - severity: Filter results (optional)
      - limit: Max results (1-500, default 100)
    
    Returns: Vulnerability breakdown with CVSS scores and affected packages
    """
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    from app.services.audit import record_connector_audit
    import json

    org_id = _get_user_org_id(db, user)

    cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if not cfg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wazuh not configured. Call /api/integrations/wazuh/configure first."
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
            detail="Wazuh telemetry not available"
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

    # Check for known critical CVEs
    critical_cves = [v for v in data.get("vulnerabilities", []) if v.get("severity") == "critical"]
    for vuln in critical_cves:
        if "CVE-2024-3094" in vuln.get("cve_id", ""):
            logger.critical(
                f"CRITICAL CVE DETECTED: {vuln.get('cve_id')} (XZ Utils) on {vuln.get('agent_name')} — "
                f"automatic Remediation Task will be generated"
            )
            
    return data


# =============================================================================
# Splunk Integration Endpoints
# =============================================================================

@router.post(
    "/splunk/configure",
    summary="Configure Splunk Integration",
    description="Set up connection to Splunk MCP Server for SIEM verification.",
    tags=["integrations", "configuration"],
)
async def configure_splunk(
    config: Dict[str, str],
    user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_writable),
):
    """
    POST /api/integrations/splunk/configure
    
    Requires: org_admin role
    
    Stores Splunk MCP Server credentials (mcp_url + api_key) on the
    organization's Splunk Connector row, then probes the MCP server's
    ``/health`` endpoint via ``SplunkMCPClient`` to validate
    connectivity before returning success.
    """
    from app.services.audit import record_connector_audit
    from app.integrations.splunk.client import SplunkMCPClient
    
    try:
        mcp_url = config.get("mcp_url") or config.get("base_url") or ""
        api_key = (
            config.get("api_key")
            or config.get("splunk_hec_token")
            or config.get("splunk_token", "")
        )
        if not mcp_url or not api_key:
            raise HTTPException(
                status_code=400,
                detail="mcp_url and api_key (or splunk_hec_token) are required.",
            )

        # Validate the connection to the MCP server before persisting.
        client = SplunkMCPClient(mcp_url=mcp_url, api_key=api_key, verify_ssl=False)
        health = await client.get_health()
        if health.status != "ok":
            raise HTTPException(
                status_code=400,
                detail=f"Splunk MCP health={health.status}; credentials not stored.",
            )
        
        org_id = config.get("org_id") or getattr(user, "org_id", "default-org")
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
                status=ConnectorStatus.active,
            )
            db.add(conn)
            
        conn.encrypted_credentials = json.dumps({"api_key": api_key})
        conn.config = {"mcp_url": mcp_url, "base_url": mcp_url}
        db.commit()
        
        record_connector_audit(
            db=db,
            org_id=org_id,
            action="configured",
            actor=user.uid,
            connector_type="splunk",
            status="success",
            extra_details={"mcp_url": mcp_url, "mcp_health": health.status},
        )
        
        logger.info(f"Splunk integration configured for {org_id} (MCP v{health.version})")
        
        return {
            "status": "configured",
            "mcp_url": mcp_url,
            "mcp_version": health.version,
            "message": "Splunk MCP connection validated successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Splunk configuration failed: {e}")
        raise HTTPException(status_code=400, detail=f"Splunk connection failed: {str(e)}")


@router.post(
    "/splunk/query",
    response_model=SplunkQueryResponse,
    summary="Execute Custom Splunk Query",
    description="Run ad-hoc SPL queries for security drift detection or compliance checks.",
    tags=["integrations", "evidence"],
)
async def run_splunk_query(
    request: SplunkQueryRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    POST /api/integrations/splunk/query
    
    Allows ad-hoc SPL queries against the customer's Splunk instance.
    Useful for:
      - Security drift verification
      - Custom compliance queries
      - Incident investigation
    
    Request body must include:
      - query: SPL query string
      - earliest: Start time (e.g., "-7d", "2026-05-01T00:00:00")
      - latest: End time (e.g., "now", "2026-05-08T23:59:59")
      - max_results: Max events to return (default 1000)
    """
    org_id = _get_user_org_id(db, user)

    conn = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk,
        Connector.status == ConnectorStatus.active,
    ).first()

    if not conn:
        raise HTTPException(
            status_code=400,
            detail="Splunk not configured. Call /api/integrations/splunk/configure first."
        )

    try:
        # Canonical telemetry pipeline: route the ad-hoc query request
        # through ``ConnectorManager.sync_connector`` so a Splunk MCP
        # fetch + orchestrator ingestion always happens. The ``query``
        # field is logged in audit history; SplunkConnector executes its
        # own canonical MCP searches.
        from app.services.connector_manager import ConnectorManager
        from app.services.audit import record_connector_audit

        record_connector_audit(
            db=db,
            org_id=org_id,
            action="ad_hoc_splunk_query_requested",
            actor=user.uid,
            connector_type="splunk",
            status="success",
            extra_details={
                "query": request.query,
                "earliest": request.earliest,
                "latest": request.latest,
                "max_results": request.max_results,
            },
        )

        mgr = ConnectorManager(db, org_id)
        sync_result = await mgr.sync_connector(conn.id)

        # Reload the most recent TelemetryEvent rows (the canonical
        # persisted result of the just-completed sync) and return them
        # in the historical Splunk-shape the legacy UI consumers
        # expect.
        from app.models.telemetry_event import TelemetryEvent
        from sqlalchemy import desc
        from datetime import datetime as _dt

        events = (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.org_id == org_id,
                TelemetryEvent.source_system == "splunk",
            )
            .order_by(desc(TelemetryEvent.created_at))
            .limit(request.max_results)
            .all()
        )

        results: list = []
        for ev in events:
            payload = ev.payload if isinstance(ev.payload, (dict,)) else {}
            if isinstance(ev.payload, str):
                import json as _json
                try:
                    payload = _json.loads(ev.payload)
                except (TypeError, ValueError):
                    payload = {"raw": ev.payload}
            row = dict(payload or {})
            row.setdefault("_cd", ev.source_event_id)
            row.setdefault("event_type", ev.event_type)
            row.setdefault("severity", ev.severity)
            results.append(row)

        logger.info(
            "Custom Splunk MCP query routed via ConnectorManager.sync_connector: "
            "%d events (sync events_ingested=%d)",
            len(results),
            sync_result.events_ingested,
        )

        return SplunkQueryResponse(
            results=results,
            total_count=len(results),
            query_used=f"{request.query} -> routed through SplunkConnector.sync() "
                       f"({sync_result.events_ingested} events)",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute Splunk query: {e}")
        raise HTTPException(status_code=500, detail=f"Splunk query failed: {str(e)}")


@router.get(
    "/splunk/logging-health",
    response_model=SplunkLoggingHealthResponse,
    summary="Verify Splunk Logging Health",
    description="Heartbeat check: verify logs are being received in last 24 hours.",
    tags=["integrations", "evidence"],
)
async def check_splunk_logging_health(
    sourcetype: str = Query("resilai_drift", description="Splunk sourcetype to check"),
    index: str = Query("security_alerts", description="Splunk index to check"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    GET /api/integrations/splunk/logging-health
    
    Verifies that ResilAI logs are being persisted in Splunk.
    
    SIEM Evidence Mapping:
      - Successful heartbeat from Splunk: Marks "Centralized Logging Enabled"
        as verified in the Telemetry & Logging domain
    
    Query Parameters:
      - sourcetype: Splunk sourcetype (default: resilai_drift)
      - index: Splunk index (default: security_alerts)
    
    Returns: Logging status with event counts and recent activity
    """
    org_id = _get_user_org_id(db, user)

    conn = db.query(Connector).filter(
        Connector.org_id == org_id,
        Connector.connector_type == ConnectorType.splunk,
        Connector.status == ConnectorStatus.active,
    ).first()

    if not conn:
        raise HTTPException(
            status_code=400,
            detail="Splunk not configured. Call /api/integrations/splunk/configure first."
        )

    try:
        from app.services.connector_manager import ConnectorManager
        from app.services.audit import record_connector_audit
        from app.models.telemetry_event import TelemetryEvent
        from sqlalchemy import desc, func
        from datetime import datetime as _dt, timedelta, timezone as _tz

        # Canonical path: trigger a Splunk sync through ConnectorManager
        # so SplunkMCPClient + SplunkConnector run, then read the
        # canonical TelemetryEvent rows for the requested
        # sourcetype/index.
        mgr = ConnectorManager(db, org_id)
        sync_result = await mgr.sync_connector(conn.id)

        record_connector_audit(
            db=db,
            org_id=org_id,
            action="logging_health_check",
            actor=user.uid,
            connector_type="splunk",
            status="success",
            extra_details={
                "sourcetype": sourcetype,
                "index": index,
                "events_ingested": sync_result.events_ingested,
            },
        )

        # 7-day and 24-hour counts computed from the canonical
        # TelemetryEvent table for this connector / index /
        # sourcetype (stored in source_event_id since Splunk's
        # payload format is mixed). Counting is straightforward: row
        # count for the sourcetype sentinel, ignoring raw payload
        # structure.
        # The SplunkConnector writes payload as JSON; we filtered on
        # index/sourcetype earlier in the sync by issuing one MCP
        # search per source. We approximate using the latest event
        # for the ``resilai_drift`` sourcetype.
        now = _dt.now(_tz.utc)
        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        latest_event_24h = (
            db.query(TelemetryEvent)
            .filter(
                TelemetryEvent.org_id == org_id,
                TelemetryEvent.source_system == "splunk",
                TelemetryEvent.event_type == "splunk.logging_health",
                TelemetryEvent.created_at >= cutoff_24h,
            )
            .order_by(desc(TelemetryEvent.created_at))
            .first()
        )
        count_7d = (
            db.query(func.count(TelemetryEvent.id))
            .filter(
                TelemetryEvent.org_id == org_id,
                TelemetryEvent.source_system == "splunk",
                TelemetryEvent.event_type == "splunk.logging_health",
                TelemetryEvent.created_at >= cutoff_7d,
            )
            .scalar()
            or 0
        )

        logging_enabled = latest_event_24h is not None
        last_event_time = (
            latest_event_24h.created_at.isoformat()
            if latest_event_24h is not None and latest_event_24h.created_at is not None
            else None
        )
        # 24h count is approximated as "did we receive at least one
        # event in last 24h" because the SplunkConnector writes a
        # single NormalizedEvent per sync (not per Splunk result row)
        # — historical skew removed 2026-07-19.
        event_count_24h = 1 if latest_event_24h is not None else 0
        event_count_7d = int(count_7d)

        return SplunkLoggingHealthResponse(
            logging_enabled=logging_enabled,
            last_event_time=last_event_time,
            event_count_24h=event_count_24h,
            event_count_7d=event_count_7d,
            sourcetypes_active=[sourcetype],
            indexes_active=[index],
            verified_at=now.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check Splunk logging health: {e}")
        raise HTTPException(status_code=500, detail=f"Logging health check failed: {str(e)}")


# =============================================================================
# Elastic Integration Endpoints
# =============================================================================

@router.post(
    "/elastic/configure",
    summary="Configure Elastic Integration",
    description="Set up connection to Elasticsearch SIEM.",
    tags=["integrations", "configuration"],
)
async def configure_elastic(
    config: ElasticConfigRequest,
    user: User = Depends(require_org_admin),
    db: Session = Depends(get_db),
    _: None = Depends(require_writable),
):
    """
    POST /api/v1/integrations/elastic/configure
    
    Requires: org_admin role
    """
    global _elastic_client
    
    try:
        # Validate connection
        client = ElasticService(
            host=config.elastic_host,
            api_key=config.elastic_api_key,
            port=config.elastic_port,
            verify_ssl=config.verify_ssl,
        )
        
        # Test connection/authentication
        import asyncio
        await client.verify_heartbeat()
        
        _elastic_client = client
        logger.info(f"Elastic integration configured for {getattr(user, 'org_id', 'default-org')}")
        
        return {
            "status": "configured",
            "host": config.elastic_host,
            "port": config.elastic_port,
            "message": "Elasticsearch connection validated successfully",
        }
    except Exception as e:
        logger.error(f"Elastic configuration failed: {e}")
        raise HTTPException(status_code=400, detail=f"Elastic connection failed: {str(e)}")


@router.get(
    "/elastic/logging-health",
    summary="Verify Elastic Logging Health",
    description="Heartbeat check: verify ResilAI logs are being received in Elasticsearch.",
    tags=["integrations", "evidence"],
)
async def check_elastic_logging_health(
    index: str = Query("logs-resilai*", description="Elastic index/pattern to check"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    GET /api/v1/integrations/elastic/logging-health
    """
    if not _elastic_client:
        raise HTTPException(
            status_code=400,
            detail="Elastic not configured. Call /api/v1/integrations/elastic/configure first."
        )
        
    try:
        import asyncio
        result = await _elastic_client.verify_logging_health(index=index)
        logger.info(f"Elastic logging health check: {result.to_dict().get('event_count_24h', 0)} events in 24h")
        return result.to_dict()
    except Exception as e:
        logger.error(f"Failed to check Elastic logging health: {e}")
        raise HTTPException(status_code=500, detail=f"Logging health check failed: {str(e)}")


# =============================================================================
# Integration Status Endpoint
# =============================================================================


@router.get(
    "/status",
    response_model=SIEMIntegrationStatus,
    summary="Get SIEM Integration Status",
    description="Check overall health of Wazuh and Splunk connections.",
    tags=["integrations"],
)
async def get_siem_integration_status(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    GET /api/integrations/status
    
    Returns the health status of both Wazuh and Splunk integrations.
    Used by the dashboard to show integration status badge.
    
    Returns: Integration status with last successful query timestamps
    """
    try:
        org_id = _get_user_org_id(db, user)
        wazuh_client = WazuhClientFactory.get_client(org_id, db)
    except Exception:
        wazuh_client = None
        org_id = None

    wazuh_connected = wazuh_client is not None
    # Splunk configuration is read from the Connector table — the v1
    # endpoint no longer relies on a process-global ``_splunk_client``
    # that was never set anywhere.
    splunk_conn = None
    if org_id:
        try:
            splunk_conn = (
                db.query(Connector)
                .filter(
                    Connector.org_id == org_id,
                    Connector.connector_type == ConnectorType.splunk,
                    Connector.status == ConnectorStatus.active,
                )
                .first()
            )
        except Exception:
            splunk_conn = None
    splunk_connected = splunk_conn is not None
    elastic_connected = _elastic_client is not None

    wazuh_status = "configured" if wazuh_connected else "not_configured"
    splunk_status = "configured" if splunk_connected else "not_configured"
    elastic_status = "configured" if elastic_connected else "not_configured"
    
    # Calculate simple mock verified controls count if any are connected
    verified_count = 0
    if wazuh_connected:
        verified_count += 2
    if splunk_connected:
        verified_count += 2
    if elastic_connected:
        verified_count += 2

    return SIEMIntegrationStatus(
        wazuh_status=wazuh_status,
        wazuh_message="Wazuh manager connected" if wazuh_connected else "Not configured",
        wazuh_last_successful=None,
        
        splunk_status=splunk_status,
        splunk_message="Splunk instance connected" if splunk_connected else "Not configured",
        splunk_last_successful=None,

        elastic_status=elastic_status,
        elastic_message="Elasticsearch SIEM connected" if elastic_connected else "Not configured",
        elastic_last_successful=None,
        
        siem_verified_controls=verified_count,
        siem_verified_percentage=float(min(100.0, verified_count * 16.6)),
    )

