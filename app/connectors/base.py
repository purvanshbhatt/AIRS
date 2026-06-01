"""
Base Connector — Abstract interface for all SIEM/XDR/Cloud connectors.

Every connector implements authenticate(), sync(), health_check(), and
validate_permissions(). The framework handles retry logic, rate limiting,
audit logging, and credential encryption.

Architectural Invariant: Connectors NEVER modify scores or findings.
They only ingest telemetry events into the TelemetryEvent table.
"""
from __future__ import annotations

import abc
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger("airs.connectors")


# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------

@dataclass
class ConnectorHealth:
    """Result of a health-check probe."""

    status: str  # healthy, degraded, unreachable
    latency_ms: Optional[int] = None
    message: str = ""
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorSyncResult:
    """Outcome of a sync() invocation."""

    success: bool
    events_ingested: int = 0
    errors_count: int = 0
    duration_ms: int = 0
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedEvent:
    """Connector-agnostic normalized telemetry event."""

    event_type: str
    source_system: str
    source_event_id: str
    severity: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    @property
    def payload_hash(self) -> str:
        """Deterministic SHA-256 hash of the payload for deduplication."""
        canonical = json.dumps(self.payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PermissionResult:
    """Outcome of a permissions validation check."""

    valid: bool
    missing_permissions: List[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Abstract base connector
# ---------------------------------------------------------------------------

class BaseConnector(abc.ABC):
    """Abstract base for all platform connectors.

    Sub-classes **must** set ``CONNECTOR_TYPE`` and implement the four
    abstract async methods.  The ``safe_sync`` wrapper provides timing,
    error handling, and structured logging around ``sync()``.
    """

    CONNECTOR_TYPE: str = "unknown"
    REQUIRED_PERMISSIONS: List[str] = []

    def __init__(
        self,
        connector_id: str,
        org_id: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.connector_id = connector_id
        self.org_id = org_id
        self._credentials = credentials
        self._config = config or {}
        self._authenticated = False
        self.logger = logging.getLogger(f"airs.connectors.{self.CONNECTOR_TYPE}")

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abc.abstractmethod
    async def authenticate(self) -> bool:
        """Validate credentials and establish connection. Returns True on success."""
        ...

    @abc.abstractmethod
    async def sync(self) -> List[NormalizedEvent]:
        """Fetch and normalize telemetry events from the source. Returns normalized events."""
        ...

    @abc.abstractmethod
    async def health_check(self) -> ConnectorHealth:
        """Check connectivity and API health. Returns health status."""
        ...

    @abc.abstractmethod
    async def validate_permissions(self) -> PermissionResult:
        """Validate that credentials have required scopes/permissions."""
        ...

    # ------------------------------------------------------------------
    # Safe wrapper
    # ------------------------------------------------------------------

    async def safe_sync(self) -> ConnectorSyncResult:
        """Sync with error handling, timing, and logging."""
        start = time.monotonic()
        try:
            if not self._authenticated:
                auth_ok = await self.authenticate()
                if not auth_ok:
                    return ConnectorSyncResult(
                        success=False, error_details="Authentication failed"
                    )

            events = await self.sync()
            duration = int((time.monotonic() - start) * 1000)
            self.logger.info(
                "Sync completed: %d events in %dms", len(events), duration
            )
            return ConnectorSyncResult(
                success=True, events_ingested=len(events), duration_ms=duration
            )
        except Exception as exc:
            duration = int((time.monotonic() - start) * 1000)
            self.logger.error("Sync failed: %s", exc)
            return ConnectorSyncResult(
                success=False, error_details=str(exc), duration_ms=duration
            )
