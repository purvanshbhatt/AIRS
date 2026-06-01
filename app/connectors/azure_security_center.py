"""
Azure Security Center Connector — Stub/Mock Microsoft Connector.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    BaseConnector,
    ConnectorHealth,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import register_connector

logger = logging.getLogger("airs.connectors.azure_security_center")


@register_connector
class AzureSecurityCenterConnector(BaseConnector):
    """Mock Microsoft Connector for Azure Security Center.

    Simulates pulling software inventory and configuration details for drift assessment.
    """

    CONNECTOR_TYPE = "azure_security_center"
    REQUIRED_PERMISSIONS = ["securityContacts:read", "assessments:read"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._authenticated = False

    async def authenticate(self) -> bool:
        """Simulate authentication validation."""
        self._authenticated = True
        self.logger.info("Azure Security Center authentication successful")
        return True

    async def sync(self) -> List[NormalizedEvent]:
        """Return simulated client software inventory events."""
        self.logger.info("Azure Security Center sync triggered")
        return [
            NormalizedEvent(
                event_type="azure_security_center.software_inventory",
                source_system="azure_security_center",
                source_event_id="software-inv-python",
                severity="low",
                payload={
                    "product": "python",
                    "vendor": "Python Software Foundation",
                    "version": "3.8.0",
                },
            ),
            NormalizedEvent(
                event_type="azure_security_center.software_inventory",
                source_system="azure_security_center",
                source_event_id="software-inv-kubernetes",
                severity="low",
                payload={
                    "product": "kubernetes",
                    "vendor": "CNCF",
                    "version": "1.22.0",
                },
            ),
            NormalizedEvent(
                event_type="azure_security_center.software_inventory",
                source_system="azure_security_center",
                source_event_id="software-inv-postgresql",
                severity="low",
                payload={
                    "product": "postgresql",
                    "vendor": "PostgreSQL",
                    "version": "12.0",
                },
            ),
        ]

    async def health_check(self) -> ConnectorHealth:
        """Return connectivity health status."""
        return ConnectorHealth(
            status="healthy",
            message="Connected to Azure Security Center APIs",
        )

    async def validate_permissions(self) -> PermissionResult:
        """Validate API permissions/scopes."""
        return PermissionResult(
            valid=True,
            message="Permissions validated successfully.",
        )
