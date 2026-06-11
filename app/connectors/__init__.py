"""
ResilAI Connector Framework — Modular Telemetry Ingestion.

Auto-imports all connector implementations so they self-register
with the ConnectorRegistry via the @register_connector decorator.
"""

from app.connectors.base import (  # noqa: F401
    BaseConnector,
    ConnectorHealth,
    ConnectorSyncResult,
    NormalizedEvent,
    PermissionResult,
)
from app.connectors.registry import (  # noqa: F401
    ConnectorRegistry,
    ConnectorType,
    register_connector,
)

# Auto-register all built-in connectors on import
from app.connectors import github  # noqa: F401
from app.connectors import wazuh  # noqa: F401
from app.connectors import aws_security_hub  # noqa: F401
from app.connectors import azure_security_center  # noqa: F401
from app.connectors import microsoft  # noqa: F401
