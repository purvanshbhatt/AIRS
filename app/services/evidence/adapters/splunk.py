from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.services.evidence.base_adapter import EvidenceAdapter, EvidenceRecord, AdapterHealth

if TYPE_CHECKING:
    from app.connectors.splunk import SplunkConnector

logger = logging.getLogger("airs.adapters.splunk")


class SplunkAdapter(EvidenceAdapter):
    """EvidenceAdapter implementation for Splunk.

    The adapter delegates to a ``SplunkConnector`` instance bound at
    registration time. ``health()`` is the path used by the
    ``/api/v1/connectors/confidence`` endpoint — the endpoint only
    invokes ``health()``. ``fetch_evidence()`` and ``normalize()``
    remain policy-thin shims; the canonical telemetry path is the
    EvidenceOrchestrator writing ``NormalizedEvidenceRecord`` rows on
    every successful SplunkConnector.sync() (see
    ``ConnectorManager._ingest_events``).

    The Splunk Adapter is intentionally lazy: it can be constructed
    without a SplunkConnector and waits for ``bind_connector()`` to
    be called after the Splunk connector row has been registered.
    """

    def __init__(self, client: Optional["SplunkConnector"] = None):
        self._client: Optional["SplunkConnector"] = client

    def bind_connector(self, connector: "SplunkConnector") -> None:
        """Bind the SplunkConnector that owns this adapter's telemetry."""
        self._client = connector

    @property
    def connector_name(self) -> str:
        return "splunk"

    async def fetch_evidence(self, *, since: Optional[datetime] = None) -> List[EvidenceRecord]:
        """Fetch all evidence checks from Splunk.

        This is a thin shim — production code paths read from the
        canonical ``NormalizedEvidenceRecord`` table populated by the
        SplunkConnector sync. The method is kept so the ABC contract
        is satisfied and historic callers do not break.
        """
        if self._client is None:
            return []
        try:
            await self._client.sync()
        except Exception as exc:
            logger.error("SplunkAdapter fetch_evidence failed: %s", exc)
        return []

    def normalize(self, vendor_payload: Any) -> List[EvidenceRecord]:
        """Splunk payloads have already been normalised by the
        ``SplunkConnector`` + ``EvidenceOrchestrator`` pipeline.
        Return an empty list — the upstream adapter layer is the
        source of truth.
        """
        return []

    async def health(self) -> AdapterHealth:
        """Report live adapter health via the bound SplunkConnector.

        Returns a clean ``failure_count=1`` when no connector is
        bound so the confidence gauge never fabricates success.
        """
        now = datetime.now(timezone.utc)
        if self._client is None:
            return AdapterHealth(
                healthy=False,
                last_failure_at=now,
                success_count=0,
                failure_count=1,
                detail="SplunkAdapter not bound to a SplunkConnector yet",
            )
        try:
            connector_health = await self._client.health_check()
            is_healthy = connector_health.status == "healthy"
            return AdapterHealth(
                healthy=is_healthy,
                last_success_at=now if is_healthy else None,
                last_failure_at=now if not is_healthy else None,
                success_count=1 if is_healthy else 0,
                failure_count=0 if is_healthy else 1,
                detail=connector_health.message,
            )
        except Exception as exc:
            return AdapterHealth(
                healthy=False,
                last_failure_at=now,
                success_count=0,
                failure_count=1,
                detail=str(exc),
            )
