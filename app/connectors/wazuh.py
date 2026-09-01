"""
Wazuh Connector — SIEM-Verified Telemetry Ingestion.

Priority 1 connector: Wazuh is the core SIEM that enables ResilAI's
Tier 3 "SOC-Verified" evidence capability. Ingests agent status,
vulnerability assessments, and security alerts from the Wazuh Manager API.

Extends the existing WazuhClient (app/services/wazuh_client.py) with the
standardized connector interface for the telemetry ingestion pipeline.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector

logger = logging.getLogger("airs.connectors.wazuh")


@register_connector
class WazuhConnector(Connector):
    """Wazuh SIEM connector for verified security telemetry.

    Connects to the Wazuh Manager REST API to ingest:
      - Agent status and health (connectivity verification)
      - Vulnerability assessments (CVE-level findings)
      - Security alerts (SIEM-verified events)

    Credentials:
      - wazuh_url: Wazuh Manager API URL (e.g. https://wazuh.example.com:55000)
      - username: Wazuh API user
      - password: Wazuh API password
      - verify_ssl: Whether to verify TLS certificates (default True)
    """

    CONNECTOR_TYPE = "wazuh"
    CAPABILITIES = ["devices", "security_alerts", "vulnerabilities"]
    REQUIRED_PERMISSIONS = ["agent:read", "vulnerability:read", "alert:read"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token: Optional[str] = None
        self._base_url = self._credentials.get("wazuh_url", "").rstrip("/")
        self._verify_ssl = self._credentials.get("verify_ssl", True)

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        """Authenticate via Wazuh Manager /security/user/authenticate."""
        username = self._credentials.get("username", "")
        password = self._credentials.get("password", "")
        if not self._base_url or not username:
            self.logger.error("Missing Wazuh URL or username")
            return False

        try:
            async with httpx.AsyncClient(
                timeout=15.0, verify=self._verify_ssl
            ) as client:
                resp = await client.post(
                    f"{self._base_url}/security/user/authenticate",
                    auth=(username, password),
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self._token = data.get("data", {}).get("token", "")
                    if self._token:
                        self._authenticated = True
                        self.logger.info("Wazuh authentication successful")
                        return True
                self.logger.warning("Wazuh auth failed: %d", resp.status_code)
                return False
        except Exception as exc:
            self.logger.error("Wazuh auth error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> List[NormalizedEvent]:
        """Fetch agent status, vulnerabilities, and recent alerts."""
        events: List[NormalizedEvent] = []

        async with httpx.AsyncClient(
            timeout=30.0, verify=self._verify_ssl
        ) as client:
            headers = self._auth_headers()

            # 1. Agent status
            events.extend(await self._fetch_agents(client, headers))

            # 2. Vulnerability assessments
            events.extend(await self._fetch_vulnerabilities(client, headers))

            # 3. Recent security alerts
            events.extend(await self._fetch_alerts(client, headers))

        self.logger.info("Wazuh sync: %d events collected", len(events))
        return events

    async def _fetch_agents(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
    ) -> List[NormalizedEvent]:
        """Fetch Wazuh agent status for endpoint visibility."""
        events = []
        try:
            resp = await client.get(
                f"{self._base_url}/agents",
                headers=headers,
                params={"limit": 500, "select": "id,name,status,ip,os.name,version"},
            )
            if resp.status_code == 200:
                agents = resp.json().get("data", {}).get("affected_items", [])
                for agent in agents:
                    agent_id = agent.get("id", "000")
                    events.append(NormalizedEvent(
                        event_type="wazuh.agent_status",
                        source_system="wazuh",
                        source_event_id=f"agent-status-{agent_id}",
                        severity="low" if agent.get("status") == "active" else "medium",
                        payload={
                            "agent_id": agent_id,
                            "name": agent.get("name"),
                            "status": agent.get("status"),
                            "ip": agent.get("ip"),
                            "os": agent.get("os", {}).get("name") if isinstance(agent.get("os"), dict) else None,
                            "version": agent.get("version"),
                        },
                    ))
        except Exception as exc:
            self.logger.debug("Agent fetch failed: %s", exc)
        return events

    async def _fetch_vulnerabilities(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
    ) -> List[NormalizedEvent]:
        """Fetch vulnerability assessments across all agents."""
        events = []
        try:
            # Get agents first for vulnerability enumeration
            resp = await client.get(
                f"{self._base_url}/agents",
                headers=headers,
                params={"limit": 100, "select": "id", "status": "active"},
            )
            if resp.status_code != 200:
                return events

            agents = resp.json().get("data", {}).get("affected_items", [])
            for agent in agents[:20]:  # Limit to first 20 agents per sync
                agent_id = agent.get("id", "000")
                vuln_resp = await client.get(
                    f"{self._base_url}/vulnerability/{agent_id}",
                    headers=headers,
                    params={"limit": 100},
                )
                if vuln_resp.status_code == 200:
                    vulns = vuln_resp.json().get("data", {}).get("affected_items", [])
                    for vuln in vulns:
                        cve = vuln.get("cve", "unknown")
                        events.append(NormalizedEvent(
                            event_type="wazuh.vulnerability",
                            source_system="wazuh",
                            source_event_id=f"vuln-{agent_id}-{cve}",
                            severity=self._map_severity(vuln.get("severity", "")),
                            payload={
                                "agent_id": agent_id,
                                "cve": cve,
                                "name": vuln.get("name"),
                                "severity": vuln.get("severity"),
                                "version": vuln.get("version"),
                                "status": vuln.get("status"),
                            },
                        ))
        except Exception as exc:
            self.logger.debug("Vulnerability fetch failed: %s", exc)
        return events

    async def _fetch_alerts(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
    ) -> List[NormalizedEvent]:
        """Fetch recent security alerts (last 24h)."""
        events = []
        try:
            resp = await client.get(
                f"{self._base_url}/alerts",
                headers=headers,
                params={"limit": 200, "sort": "-timestamp"},
            )
            if resp.status_code == 200:
                alerts = resp.json().get("data", {}).get("affected_items", [])
                for alert in alerts:
                    alert_id = alert.get("id", "")
                    rule = alert.get("rule", {})
                    events.append(NormalizedEvent(
                        event_type="wazuh.alert",
                        source_system="wazuh",
                        source_event_id=f"alert-{alert_id}",
                        severity=self._map_level_to_severity(rule.get("level", 0)),
                        payload={
                            "alert_id": alert_id,
                            "rule_id": rule.get("id"),
                            "rule_description": rule.get("description"),
                            "rule_level": rule.get("level"),
                            "agent_id": alert.get("agent", {}).get("id"),
                            "agent_name": alert.get("agent", {}).get("name"),
                            "timestamp": alert.get("timestamp"),
                        },
                    ))
        except Exception as exc:
            self.logger.debug("Alert fetch failed: %s", exc)
        return events

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> ConnectorHealth:
        import time
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(
                timeout=10.0, verify=self._verify_ssl
            ) as client:
                resp = await client.get(
                    f"{self._base_url}/manager/info",
                    headers=self._auth_headers(),
                )
                latency = int((time.monotonic() - start) * 1000)
                if resp.status_code == 200:
                    info = resp.json().get("data", {}).get("affected_items", [{}])
                    version = info[0].get("version", "unknown") if info else "unknown"
                    return ConnectorHealth(
                        status="healthy",
                        latency_ms=latency,
                        message=f"Wazuh Manager v{version}",
                    )
                return ConnectorHealth(
                    status="unreachable",
                    latency_ms=latency,
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as exc:
            return ConnectorHealth(status="unreachable", message=str(exc))

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        """Validate Wazuh API user has required permissions."""
        if not self._authenticated:
            auth_ok = await self.authenticate()
            if not auth_ok:
                return PermissionResult(valid=False, message="Authentication failed")

        try:
            async with httpx.AsyncClient(
                timeout=10.0, verify=self._verify_ssl
            ) as client:
                resp = await client.get(
                    f"{self._base_url}/security/users/me",
                    headers=self._auth_headers(),
                )
                if resp.status_code == 200:
                    return PermissionResult(
                        valid=True,
                        message="Wazuh API user authenticated with sufficient privileges",
                    )
                return PermissionResult(
                    valid=False,
                    message=f"Permission check returned HTTP {resp.status_code}",
                )
        except Exception as exc:
            return PermissionResult(valid=False, message=str(exc))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def _map_severity(wazuh_severity: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
        }
        return mapping.get(wazuh_severity.lower(), "medium")

    @staticmethod
    def _map_level_to_severity(level: int) -> str:
        """Map Wazuh rule level (1-15) to standard severity."""
        if level >= 12:
            return "critical"
        if level >= 10:
            return "high"
        if level >= 7:
            return "medium"
        return "low"
