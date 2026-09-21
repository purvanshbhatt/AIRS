"""
Cisco Duo Security Connector — MFA and Access Hygiene Telemetry.

Ingests authentication logs, bypass tracking, and device posture telemetry
from Cisco Duo Admin API.
"""
from __future__ import annotations

import email.utils
import hashlib
import hmac
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector
from app.services.clinic_engine.v2.schema import ConnectorCapability

logger = logging.getLogger("airs.connectors.duo")


@register_connector
class DuoConnector(Connector):
    """Cisco Duo Admin API telemetry connector for MFA verification.

    Credentials:
      - integration_key: Duo ikey (e.g. DIXXXXXXXXXXXXXXXXXX)
      - secret_key: Duo skey (HMAC secret)
      - api_hostname: Duo API hostname (e.g. api-XXXXXXXX.duosecurity.com)
    """

    CONNECTOR_TYPE = "duo"
    CAPABILITIES = [ConnectorCapability.IDENTITY]
    REQUIRED_PERMISSIONS = ["admin:read", "auth_logs:read"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ikey = (
            self._credentials.get("integration_key", "")
            or self._credentials.get("ikey", "")
            or self._config.get("integration_key", "")
        )
        self._skey = (
            self._credentials.get("secret_key", "")
            or self._credentials.get("skey", "")
            or self._config.get("secret_key", "")
        )
        self._hostname = (
            self._credentials.get("api_hostname", "")
            or self._credentials.get("host", "")
            or self._config.get("api_hostname", "")
        ).replace("https://", "").replace("http://", "").rstrip("/")

    def _sign(self, method: str, path: str, params: Dict[str, Any], date_str: str) -> str:
        """Generate Duo API HMAC-SHA1 signature."""
        canon = [
            date_str,
            method.upper(),
            self._hostname.lower(),
            path,
            urlencode(sorted(params.items())),
        ]
        canon_str = "\n".join(canon)
        sig = hmac.new(
            self._skey.encode("utf-8"),
            canon_str.encode("utf-8"),
            hashlib.sha1,
        ).hexdigest()
        import base64
        auth = f"{self._ikey}:{sig}"
        return "Basic " + base64.b64encode(auth.encode("utf-8")).decode("utf-8")

    async def authenticate(self) -> bool:
        """Validate Duo API credentials via /admin/v1/ping."""
        if not self._hostname or not self._ikey or not self._skey:
            self.logger.warning("Missing Duo hostname, integration key, or secret key")
            return False

        path = "/admin/v1/ping"
        date_str = email.utils.formatdate(usegmt=True)
        headers = {
            "Date": date_str,
            "Authorization": self._sign("GET", path, {}, date_str),
            "Host": self._hostname,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"https://{self._hostname}{path}", headers=headers)
                if resp.status_code == 200:
                    self._authenticated = True
                    return True
                self.logger.warning("Duo auth check returned HTTP %d", resp.status_code)
                return False
        except Exception as exc:
            self.logger.error("Duo authentication failed: %s", exc)
            return False

    async def sync(self) -> List[NormalizedEvent]:
        """Fetch MFA authentication logs from Duo Admin API."""
        if not self._authenticated:
            ok = await self.authenticate()
            if not ok:
                return []

        path = "/admin/v2/logs/authentication"
        now_ts = int(time.time())
        mintime = now_ts - (86400 * 7)  # Last 7 days
        params = {"mintime": str(mintime), "limit": "100"}
        date_str = email.utils.formatdate(usegmt=True)
        headers = {
            "Date": date_str,
            "Authorization": self._sign("GET", path, params, date_str),
            "Host": self._hostname,
        }

        events: List[NormalizedEvent] = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"https://{self._hostname}{path}",
                    headers=headers,
                    params=params,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    auth_logs = data.get("response", {}).get("authlogs", [])
                    for entry in auth_logs:
                        txid = entry.get("txid", f"tx-{int(time.time())}")
                        result = entry.get("result", "SUCCESS").upper()
                        is_failure = result in ("FAILURE", "DENIED", "FRAUD")
                        events.append(
                            NormalizedEvent(
                                event_type="duo.auth_log",
                                source_system="duo",
                                source_event_id=f"duo-{txid}",
                                severity="high" if is_failure else "low",
                                payload={
                                    "user": entry.get("user", {}).get("name", "unknown"),
                                    "factor": entry.get("factor", "unknown"),
                                    "result": result,
                                    "reason": entry.get("reason", ""),
                                    "ip": entry.get("access_device", {}).get("ip", ""),
                                    "timestamp": entry.get("isotimestamp", datetime.now(timezone.utc).isoformat()),
                                },
                                timestamp=entry.get("isotimestamp"),
                            )
                        )
        except Exception as exc:
            self.logger.error("Duo sync failed: %s", exc)

        return events

    async def health_check(self) -> ConnectorHealth:
        """Probe Duo API hostname reachability."""
        start = time.monotonic()
        if not self._hostname:
            return ConnectorHealth(
                status="unreachable",
                message="Duo api_hostname not configured",
            )
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"https://{self._hostname}/auth/v2/ping")
                latency = int((time.monotonic() - start) * 1000)
                if resp.status_code == 200:
                    return ConnectorHealth(
                        status="healthy",
                        latency_ms=latency,
                        message="Duo API reachable",
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
        """Validate Duo Admin credentials."""
        ok = await self.authenticate()
        if ok:
            return PermissionResult(valid=True, message="Duo Admin credentials verified")
        return PermissionResult(
            valid=False,
            missing_permissions=self.REQUIRED_PERMISSIONS,
            message="Failed to validate Duo Admin API credentials",
        )
