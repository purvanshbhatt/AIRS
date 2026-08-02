"""
Splunk Connector — MCP-based SIEM telemetry ingestion.

Priority 1 connector. Connects ResilAI to a Splunk MCP Server to ingest
verified security telemetry (MFA enforcement, EDR coverage, centralized
logging health, and ad-hoc SPL search results) into the
NormalizedEvent pipeline.

This is the ONLY production Splunk path in the platform. The legacy
direct-HEC REST client (app/services/splunk.py::SplunkService) is kept
as a thin facade for backward compatibility but internally routes its
searches through SplunkMCPClient.

Credentials:
  - mcp_url: Splunk MCP Server base URL (e.g. https://splunk-mcp.example.com)
  - api_key: Bearer token for the Splunk MCP Server (the old "HEC token"
             is reused as the MCP bearer token for migration continuity)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    RawEvent,
    PermissionResult,
)
from app.services.clinic_engine.v2.schema import ConnectorCapability
from app.connectors.registry import register_connector
from app.integrations.splunk.client import SplunkMCPClient
from app.integrations.splunk.schemas import SplunkHealthResponse

logger = logging.getLogger("airs.connectors.splunk")


@register_connector
class SplunkConnector(Connector):
    """Splunk SIEM connector backed by the Splunk MCP Server.

    Pulls four canonical telemetry streams per sync:
      - MFA enforcement evidence (sourcetype=mfa_logs)
      - EDR coverage evidence (sourcetype=edr_telemetry)
      - Centralized logging heartbeat (sourcetype=resilai_drift /
        index=security_alerts)
      - Recent notable events (index=notable)

    The returned NormalizedEvent list is consumed by the
    ConnectorManager and persisted via the EvidenceOrchestrator into
    the immutable EvidenceLedger + NormalizedEvidenceRecord tables.
    """

    CONNECTOR_TYPE = "splunk"
    REQUIRED_PERMISSIONS = ["mcp:search"]
    CAPABILITIES = [ConnectorCapability.LOGS]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._mcp_url: str = self._credentials.get("mcp_url", "") or self._config.get("mcp_url", "")
        # The legacy "hec_token" credential slot is reused as the MCP bearer.
        self._api_key: str = (
            self._credentials.get("api_key", "")
            or self._credentials.get("hec_token", "")
            or self._credentials.get("token", "")
        )
        self._verify_ssl: bool = bool(self._config.get("verify_ssl", True))
        self._client: Optional[SplunkMCPClient] = None
        if self._mcp_url and self._api_key:
            self._client = SplunkMCPClient(
                mcp_url=self._mcp_url,
                api_key=self._api_key,
                verify_ssl=self._verify_ssl,
            )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        if not self._client:
            self.logger.error(
                "Splunk MCP client not configured (missing mcp_url or api_key)"
            )
            return False
        try:
            health: SplunkHealthResponse = await self._client.get_health()
            self._authenticated = health.status == "ok"
            if self._authenticated:
                self.logger.info(
                    "Splunk MCP authentication successful (v%s)",
                    getattr(health, "version", "unknown"),
                )
            else:
                self.logger.warning("Splunk MCP health returned status=%s", health.status)
            return self._authenticated
        except Exception as exc:
            self.logger.error("Splunk MCP authentication failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> List[RawEvent]:
        """Fetch priority security telemetry via Splunk MCP."""
        if not self._client:
            self.logger.error("Splunk MCP client not initialized")
            return []

        events: List[RawEvent] = []
        events.extend(await self._sync_mfa())
        events.extend(await self._sync_edr())
        events.extend(await self._sync_logging_health())
        events.extend(await self._sync_notable())

        self.logger.info("Splunk MCP sync: %d events collected", len(events))
        return events

    async def _sync_mfa(self) -> List[RawEvent]:
        return await self._run_search(
            query="index=main sourcetype=mfa_logs | head 50",
            event_type="splunk.mfa_evidence",
            control_id="IV-001",
        )

    async def _sync_edr(self) -> List[RawEvent]:
        return await self._run_search(
            query="index=main sourcetype=edr_telemetry | head 50",
            event_type="splunk.edr_evidence",
            control_id="DC-001",
        )

    async def _sync_logging_health(self) -> List[RawEvent]:
        return await self._run_search(
            query='index=security_alerts sourcetype=resilai_drift | head 10',
            event_type="splunk.logging_health",
            control_id="TL-002",
        )

    async def _sync_notable(self) -> List[RawEvent]:
        return await self._run_search(
            query="index=notable | head 50",
            event_type="splunk.notable_event",
            control_id=None,
        )

    async def _run_search(
        self,
        *,
        query: str,
        event_type: str,
        control_id: Optional[str],
    ) -> List[RawEvent]:
        events: List[RawEvent] = []
        response = await self._client.search(query=query, earliest_time="-24h", latest_time="now")
        for ev in response.events:
            parsed = ev.parsed_fields or {}
            events.append(
                RawEvent(
                    event_type=event_type,
                    source_system="splunk",
                    source_event_id=ev.id or f"splunk-{event_type}-{ev.time}",
                    severity=self._map_severity(parsed.get("severity", "info")),
                    payload={
                        "control_id": control_id,
                        "raw": ev.raw,
                        "host": ev.host,
                        "sourcetype": ev.sourcetype,
                        "source": ev.source,
                        "time": str(ev.time),
                        "parsed_fields": parsed,
                    },
                    timestamp=str(ev.time) if ev.time else None,
                )
            )
        return events

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> ConnectorHealth:
        import time
        start = time.monotonic()
        if not self._client:
            return ConnectorHealth(
                status="unreachable",
                message="Splunk MCP client not configured",
            )
        try:
            health = await self._client.get_health()
            latency = int((time.monotonic() - start) * 1000)
            if health.status == "ok":
                return ConnectorHealth(
                    status="healthy",
                    latency_ms=latency,
                    message=f"Splunk MCP v{health.version}",
                )
            return ConnectorHealth(
                status="degraded",
                latency_ms=latency,
                message=f"Splunk MCP status={health.status}",
            )
        except Exception as exc:
            return ConnectorHealth(status="unreachable", message=str(exc))

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        if not self._authenticated:
            ok = await self.authenticate()
            if not ok:
                return PermissionResult(valid=False, message="Splunk MCP unreachable")
        return PermissionResult(
            valid=True,
            message="Splunk MCP health check succeeded; search access implied",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_severity(value: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "info",
        }
        return mapping.get((value or "info").lower(), "info")
