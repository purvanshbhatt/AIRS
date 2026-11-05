from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.services.evidence.base_adapter import EvidenceAdapter, EvidenceRecord, AdapterHealth

if TYPE_CHECKING:
    from app.connectors.aws_security_hub import AWSSecurityHubConnector

logger = logging.getLogger("airs.adapters.aws_security_hub")


class AWSSecurityHubAdapter(EvidenceAdapter):
    """EvidenceAdapter implementation for AWS Security Hub.

    The adapter delegates to a ``AWSSecurityHubConnector`` instance bound at
    registration time. ``health()`` is the path used by the
    ``/api/v1/connectors/confidence`` endpoint — the endpoint only
    invokes ``health()``. ``fetch_evidence()`` and ``normalize()``
    remain policy-thin shims; the canonical telemetry path is the
    EvidenceOrchestrator writing ``NormalizedEvidenceRecord`` rows on
    every successful AWSSecurityHubConnector.sync() (see
    ``ConnectorManager._ingest_events``).

    The AWS Security Hub Adapter is intentionally lazy: it can be constructed
    without a AWSSecurityHubConnector and waits for ``bind_connector()`` to
    be called after the AWS Security Hub connector row has been registered.
    """

    def __init__(self, client: Optional["AWSSecurityHubConnector"] = None):
        self._client: Optional["AWSSecurityHubConnector"] = client

    def bind_connector(self, connector: "AWSSecurityHubConnector") -> None:
        """Bind the AWSSecurityHubConnector that owns this adapter's telemetry."""
        self._client = connector

    @property
    def connector_name(self) -> str:
        return "aws_security_hub"

    async def fetch_evidence(self, *, since: Optional[datetime] = None) -> List[EvidenceRecord]:
        """Fetch all evidence checks from AWS Security Hub.

        This is a thin shim — production code paths read from the
        canonical ``NormalizedEvidenceRecord`` table populated by the
        AWSSecurityHubConnector sync. The method is kept so the ABC contract
        is satisfied and historic callers do not break.
        """
        if self._client is None:
            return []
        try:
            await self._client.sync()
        except Exception as exc:
            logger.error("AWSSecurityHubAdapter fetch_evidence failed: %s", exc)
        return []

    def normalize(self, vendor_payload: Any) -> List[EvidenceRecord]:
        """AWS Security Hub payloads have already been normalised by the
        ``AWSSecurityHubConnector`` + ``EvidenceOrchestrator`` pipeline.
        Return an empty list — the upstream adapter layer is the
        source of truth.
        """
        return []

    async def health(self) -> AdapterHealth:
        """Report live adapter health via the bound AWSSecurityHubConnector.

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
                detail="AWSSecurityHubAdapter not bound to a AWSSecurityHubConnector yet",
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
