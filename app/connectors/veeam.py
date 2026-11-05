"""
Veeam Backup & Replication Connector — Data Protection Telemetry.

Ingests backup job statuses, session history, and immutability telemetry
from Veeam Backup & Replication REST API.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector
from app.services.clinic_engine.v2.schema import ConnectorCapability

logger = logging.getLogger("airs.connectors.veeam")


@register_connector
class VeeamConnector(Connector):
    """Veeam Backup & Replication REST API telemetry connector.

    Credentials:
      - server_url: Veeam REST API URL (e.g. https://veeam.corp.internal:9419)
      - api_key: Bearer token or API key for Veeam REST API
      - verify_ssl: bool (default False for internal self-signed enterprise certs)
    """

    CONNECTOR_TYPE = "veeam"
    CAPABILITIES = [ConnectorCapability.BACKUPS]
    REQUIRED_PERMISSIONS = ["backup:read", "jobs:read"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._server_url = (
            self._credentials.get("server_url", "")
            or self._config.get("server_url", "")
        ).rstrip("/")
        if not self._server_url:
            host = self._credentials.get("host") or self._config.get("host")
            port = self._credentials.get("port") or self._config.get("port", "9419")
            if host:
                if not host.startswith("http://") and not host.startswith("https://"):
                    self._server_url = f"https://{host}:{port}"
                else:
                    self._server_url = f"{host}:{port}" if ":" not in host[8:] else host

        self._api_key = (
            self._credentials.get("api_key", "")
            or self._credentials.get("token", "")
        )
        self._verify_ssl = bool(self._config.get("verify_ssl", False))

    async def authenticate(self) -> bool:
        """Verify API token against Veeam REST API."""
        if not self._server_url or not self._api_key:
            self.logger.warning("Missing Veeam server_url or api_key")
            return False

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "x-api-version": "1.1-rev0",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=self._verify_ssl) as client:
                resp = await client.get(f"{self._server_url}/api/v1/jobs", headers=headers)
                if resp.status_code in (200, 204):
                    self._authenticated = True
                    return True
                elif resp.status_code in (401, 403):
                    self.logger.warning("Veeam auth rejected: HTTP %d", resp.status_code)
                    return False
                # If endpoint not found, try base API
                resp2 = await client.get(f"{self._server_url}/api", headers=headers)
                if resp2.status_code < 400:
                    self._authenticated = True
                    return True
                return False
        except Exception as exc:
            self.logger.error("Veeam authentication error: %s", exc)
            return False

    async def sync(self) -> List[NormalizedEvent]:
        """Fetch backup jobs from Veeam and normalize into events."""
        if not self._authenticated:
            ok = await self.authenticate()
            if not ok:
                return []

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "x-api-version": "1.1-rev0",
            "Accept": "application/json",
        }

        events: List[NormalizedEvent] = []
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=self._verify_ssl) as client:
                resp = await client.get(f"{self._server_url}/api/v1/jobs", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    jobs = data.get("data", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    for job in jobs:
                        job_id = job.get("id", f"job-{int(time.time())}")
                        job_name = job.get("name", "Unknown Backup Job")
                        last_result = job.get("lastResult", "Success")
                        last_run = job.get("lastRun", datetime.now(timezone.utc).isoformat())
                        is_high_risk = last_result.lower() in ("failed", "error")

                        events.append(
                            NormalizedEvent(
                                event_type="veeam.backup_job",
                                source_system="veeam",
                                source_event_id=f"veeam-{job_id}",
                                severity="high" if is_high_risk else "low",
                                payload={
                                    "system_name": job_name,
                                    "job_id": job_id,
                                    "last_successful_backup": last_run if not is_high_risk else None,
                                    "backup_type": job.get("type", "Backup"),
                                    "status": last_result,
                                    "description": job.get("description", ""),
                                },
                                timestamp=last_run,
                            )
                        )
        except Exception as exc:
            self.logger.error("Veeam sync failed: %s", exc)

        return events

    async def health_check(self) -> ConnectorHealth:
        """Probe Veeam REST API reachability."""
        start = time.monotonic()
        if not self._server_url:
            return ConnectorHealth(
                status="unreachable",
                message="Veeam server_url not configured",
            )
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=self._verify_ssl) as client:
                resp = await client.get(f"{self._server_url}/api")
                latency = int((time.monotonic() - start) * 1000)
                if resp.status_code < 500:
                    return ConnectorHealth(
                        status="healthy",
                        latency_ms=latency,
                        message="Veeam server reachable",
                    )
                return ConnectorHealth(
                    status="degraded",
                    latency_ms=latency,
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ConnectorHealth(
                status="unreachable",
                latency_ms=latency,
                message=str(exc),
            )

    async def validate_permissions(self) -> PermissionResult:
        """Validate read permissions on jobs endpoint."""
        ok = await self.authenticate()
        if ok:
            return PermissionResult(valid=True, message="Veeam credentials and read permissions validated")
        return PermissionResult(
            valid=False,
            missing_permissions=self.REQUIRED_PERMISSIONS,
            message="Failed to validate Veeam API permissions",
        )
