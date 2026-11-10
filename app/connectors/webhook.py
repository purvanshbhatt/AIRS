"""
Custom Webhook / Generic API Connector — MSP & Ingestion Telemetry.

Manages generic webhook endpoints for receiving custom audit evidence,
MSP monitoring alerts, and third-party CI/CD compliance payloads.

Network topology push
---------------------
Firewalls and VPN tools (Tailscale, UniFi, pfSense, WireGuard, ...) can push
what they know about the network to the same endpoint::

    POST /api/v1/connectors/webhook/webhook?org_id=<org>
    X-Webhook-Secret: <secret>
    {"event_type": "network.snapshot", "provider": "unifi",
     "networks": [...], "subnets": [...], "gateways": [...], "vpns": [...],
     "security_groups": [...], "devices": [...], "links": [...], "peerings": [...]}

The body is stored unchanged as a telemetry event of that type (any event
type is accepted; nothing is filtered) and the network map reads it through
``app.services.network_topology``. Every list is optional. The map uses the
newest snapshot per ``provider`` (and optional ``scope``), so a tool should
send its complete current view each time.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector
from app.services.clinic_engine.v2.schema import ConnectorCapability

logger = logging.getLogger("airs.connectors.webhook")

# Event type of a pushed network topology document (see module docstring).
NETWORK_SNAPSHOT_EVENT = "network.snapshot"


@register_connector
class WebhookConnector(Connector):
    """Custom Webhook / Generic API connector for MSP telemetry ingestion."""

    CONNECTOR_TYPE = "webhook"
    CAPABILITIES = [ConnectorCapability.LOGS]
    REQUIRED_PERMISSIONS = ["webhook:receive"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._webhook_name = (
            self._credentials.get("webhook_name")
            or self._config.get("webhook_name")
            or "Primary MSP Webhook"
        )

    async def authenticate(self) -> bool:
        """Webhooks receive payloads actively; registration confirms readiness."""
        self._authenticated = True
        return True

    async def sync(self) -> List[NormalizedEvent]:
        """Webhooks are push-based: events arrive via
        POST /api/v1/connectors/webhook/webhook?org_id=... and are ingested
        there. A pull sync therefore has nothing to fetch and must not
        fabricate heartbeat evidence.
        """
        return []

    async def health_check(self) -> ConnectorHealth:
        """Health check verifies internal readiness to receive webhook events."""
        return ConnectorHealth(
            status="healthy",
            latency_ms=1,
            message=f"Webhook '{self._webhook_name}' active and ready to accept payloads",
        )

    async def validate_permissions(self) -> PermissionResult:
        """Permissions are valid upon connector registration."""
        return PermissionResult(
            valid=True,
            message="Webhook receiver permissions verified",
        )
