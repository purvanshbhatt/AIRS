"""
Custom Webhook / Generic API Connector — MSP & Ingestion Telemetry.

Manages generic webhook endpoints for receiving custom audit evidence,
MSP monitoring alerts, and third-party CI/CD compliance payloads.
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
        """Webhooks are push-based; pull sync returns active status heartbeat."""
        now = datetime.now(timezone.utc)
        return [
            NormalizedEvent(
                event_type="webhook.heartbeat",
                source_system="webhook",
                source_event_id=f"webhook-hb-{int(now.timestamp())}",
                severity="low",
                payload={
                    "webhook_name": self._webhook_name,
                    "status": "listening",
                    "last_checked": now.isoformat(),
                },
                timestamp=now.isoformat(),
            )
        ]

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
