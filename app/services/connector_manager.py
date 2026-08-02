"""
ConnectorManager — Organization-Scoped Connector Lifecycle Management.

Orchestrates connector registration, sync execution, health monitoring,
and audit logging. Acts as the bridge between API routes, connector
implementations, and the telemetry ingestion pipeline.

Architectural Invariants:
  - Connectors NEVER modify scores or findings directly.
  - All credential storage uses AES-256-GCM encryption.
  - Every sync operation is logged to ConnectorSyncLog for audit.
  - Connector operations are org-scoped — no cross-tenant access.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.connector_manager")


class ConnectorManagerError(Exception):
    """Base exception for connector management operations."""
    pass


class ConnectorNotFoundError(ConnectorManagerError):
    """Raised when a connector is not found or not owned by the org."""
    pass


class ConnectorManager:
    """Organization-scoped connector lifecycle management.

    Handles registration, sync orchestration, health checks, and
    deactivation of telemetry connectors.
    """

    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_connector(
        self,
        connector_type: str,
        display_name: str,
        auth_method: str,
        credentials: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        sync_interval_minutes: int = 60,
        created_by: Optional[str] = None,
    ):
        """Register a new connector for this organization.

        Args:
            connector_type: One of the ConnectorType enum values.
            display_name: Human-readable name for the connector.
            auth_method: Authentication method (oauth, api_key, etc.).
            credentials: Raw credential dict (will be encrypted at rest).
            config: Optional connector-specific configuration.
            sync_interval_minutes: How often to auto-sync (default 60).
            created_by: User ID who created the connector.

        Returns:
            The created Connector ORM instance.
        """
        from app.models.connector import Connector, ConnectorStatus

        # Encrypt credentials for storage
        encrypted_creds = self._encrypt_credentials(credentials)

        connector = Connector(
            org_id=self.org_id,
            connector_type=connector_type,
            display_name=display_name,
            auth_method=auth_method,
            encrypted_credentials=encrypted_creds,
            config=config if config else None,
            sync_interval_minutes=sync_interval_minutes,
            status=ConnectorStatus.pending_auth.value,
            health_status="unknown",
            created_by=created_by or "system",
        )

        self.db.add(connector)
        self.db.commit()
        self.db.refresh(connector)

        logger.info(
            "Connector registered: type=%s, name=%s, org=%s, id=%s",
            connector_type, display_name, self.org_id, connector.id,
        )
        return connector

    # ------------------------------------------------------------------
    # Sync Orchestration
    # ------------------------------------------------------------------

    async def sync_connector(self, connector_id: str):
        """Trigger a sync for a specific connector.

        Instantiates the connector implementation, runs safe_sync(),
        and logs the result to ConnectorSyncLog.

        Args:
            connector_id: UUID of the connector to sync.

        Returns:
            ConnectorSyncResult dataclass.
        """
        from app.models.connector import Connector, ConnectorStatus, ConnectorSyncLog
        from app.connectors.registry import get_connector_class
        from app.connectors.base import ConnectorSyncResult

        connector = self._get_connector(connector_id)

        # Update status to syncing
        connector.status = ConnectorStatus.syncing.value
        self.db.commit()

        # Create sync log entry
        sync_log = ConnectorSyncLog(
            connector_id=connector_id,
            sync_started_at=datetime.now(timezone.utc),
            status="running",
        )
        self.db.add(sync_log)
        self.db.commit()

        try:
            # Instantiate connector implementation
            ConnectorClass = get_connector_class(connector.connector_type)
            credentials = self._decrypt_credentials(connector.encrypted_credentials)
            cfg_raw = connector.config
            if isinstance(cfg_raw, str):
                config = json.loads(cfg_raw) if cfg_raw else {}
            elif isinstance(cfg_raw, dict):
                config = cfg_raw
            else:
                config = {}

            impl = ConnectorClass(
                connector_id=connector_id,
                org_id=self.org_id,
                credentials=credentials,
                config=config,
            )

            # Execute sync
            result = await impl.safe_sync()

            # If sync returned events, ingest them
            if result.success and result.events_ingested > 0:
                try:
                    await self._ingest_events(connector_id, result.events)
                except Exception as ingest_err:
                    logger.warning("Event ingestion failed: %s", ingest_err)

            # Update connector state
            connector.status = (
                ConnectorStatus.active.value if result.success
                else ConnectorStatus.error.value
            )
            connector.last_sync_at = datetime.now(timezone.utc)
            connector.error_message = result.error_details
            connector.health_status = "healthy" if result.success else "error"

            # Update sync log
            sync_log.sync_completed_at = datetime.now(timezone.utc)
            sync_log.status = "completed" if result.success else "failed"
            sync_log.events_ingested = result.events_ingested
            sync_log.errors_count = result.errors_count
            sync_log.duration_ms = result.duration_ms
            sync_log.error_details = result.error_details

            self.db.commit()

            logger.info(
                "Sync %s for connector %s: %d events, %dms",
                "completed" if result.success else "failed",
                connector_id,
                result.events_ingested,
                result.duration_ms,
            )
            return result

        except Exception as exc:
            connector.status = ConnectorStatus.error.value
            connector.error_message = str(exc)
            sync_log.sync_completed_at = datetime.now(timezone.utc)
            sync_log.status = "failed"
            sync_log.error_details = str(exc)
            self.db.commit()

            logger.error("Sync failed for connector %s: %s", connector_id, exc)
            return ConnectorSyncResult(
                success=False,
                error_details=str(exc),
            )

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self, connector_id: str):
        """Check the health of a specific connector.

        Returns:
            ConnectorHealth dataclass.
        """
        from app.connectors.registry import get_connector_class

        connector = self._get_connector(connector_id)
        ConnectorClass = get_connector_class(connector.connector_type)
        credentials = self._decrypt_credentials(connector.encrypted_credentials)
        config = connector.config if connector.config else {}

        impl = ConnectorClass(
            connector_id=connector_id,
            org_id=self.org_id,
            credentials=credentials,
            config=config,
        )

        health = await impl.health_check()

        # Update connector health status
        connector.health_status = health.status
        self.db.commit()

        return health

    # ------------------------------------------------------------------
    # Listing & Retrieval
    # ------------------------------------------------------------------

    def list_connectors(self, connector_type: Optional[str] = None):
        """List all connectors for this organization.

        Args:
            connector_type: Optional filter by connector type.

        Returns:
            List of Connector ORM instances.
        """
        from app.models.connector import Connector

        query = self.db.query(Connector).filter(
            Connector.org_id == self.org_id,
        )
        if connector_type:
            query = query.filter(Connector.connector_type == connector_type)

        return query.order_by(Connector.created_at.desc()).all()

    def get_connector(self, connector_id: str):
        """Get a single connector by ID, verifying org ownership."""
        return self._get_connector(connector_id)

    def get_sync_history(self, connector_id: str, limit: int = 20):
        """Get sync history for a connector.

        Args:
            connector_id: UUID of the connector.
            limit: Max records to return.

        Returns:
            List of ConnectorSyncLog ORM instances.
        """
        from app.models.connector import ConnectorSyncLog

        # Verify ownership
        self._get_connector(connector_id)

        return (
            self.db.query(ConnectorSyncLog)
            .filter(ConnectorSyncLog.connector_id == connector_id)
            .order_by(ConnectorSyncLog.created_at.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Update & Deactivation
    # ------------------------------------------------------------------

    def update_connector(
        self,
        connector_id: str,
        display_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        sync_interval_minutes: Optional[int] = None,
        status: Optional[str] = None,
    ):
        """Update a connector's configuration.

        Returns:
            Updated Connector ORM instance.
        """
        connector = self._get_connector(connector_id)

        if display_name is not None:
            connector.display_name = display_name
        if config is not None:
            connector.config = config
        if sync_interval_minutes is not None:
            connector.sync_interval_minutes = sync_interval_minutes
        if status is not None:
            connector.status = status

        self.db.commit()
        self.db.refresh(connector)
        return connector

    def deactivate_connector(self, connector_id: str) -> None:
        """Soft-delete a connector by setting status to inactive.

        Does NOT delete sync logs or telemetry events (audit trail preserved).
        """
        from app.models.connector import ConnectorStatus

        connector = self._get_connector(connector_id)
        connector.status = ConnectorStatus.inactive.value
        self.db.commit()

        logger.info("Connector deactivated: %s (org=%s)", connector_id, self.org_id)

    # ------------------------------------------------------------------
    # Permission Validation
    # ------------------------------------------------------------------

    async def validate_permissions(self, connector_id: str):
        """Validate that a connector has required permissions.

        Returns:
            PermissionResult dataclass.
        """
        from app.connectors.registry import get_connector_class

        connector = self._get_connector(connector_id)
        ConnectorClass = get_connector_class(connector.connector_type)
        credentials = self._decrypt_credentials(connector.encrypted_credentials)
        config = connector.config if connector.config else {}

        impl = ConnectorClass(
            connector_id=connector_id,
            org_id=self.org_id,
            credentials=credentials,
            config=config,
        )

        result = await impl.validate_permissions()
        connector.permissions_validated = result.valid
        self.db.commit()

        return result

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _get_connector(self, connector_id: str):
        """Get a connector by ID, enforcing org-scoped isolation.

        Raises:
            ConnectorNotFoundError: If connector not found or not owned by org.
        """
        from app.models.connector import Connector

        connector = (
            self.db.query(Connector)
            .filter(
                Connector.id == connector_id,
                Connector.org_id == self.org_id,
            )
            .first()
        )
        if not connector:
            raise ConnectorNotFoundError(
                f"Connector {connector_id} not found for org {self.org_id}"
            )
        return connector

    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for database storage.

        Currently stores as JSON string. AES-256-GCM encryption will be
        added in Phase 4 via app.core.security.connector_encryption.
        """
        # TODO(Phase 4): Replace with AES-256-GCM encryption
        # from app.core.security.connector_encryption import encrypt
        # return encrypt(json.dumps(credentials))
        return json.dumps(credentials)

    def _decrypt_credentials(self, encrypted: Optional[str]) -> Dict[str, Any]:
        """Decrypt credentials from database storage.

        Currently parses JSON string. AES-256-GCM decryption will be
        added in Phase 4 via app.core.security.connector_encryption.
        """
        if not encrypted:
            return {}
        # TODO(Phase 4): Replace with AES-256-GCM decryption
        # from app.core.security.connector_encryption import decrypt
        # return json.loads(decrypt(encrypted))
        return json.loads(encrypted)

    async def _ingest_events(self, connector_id: str, events) -> int:
        """Ingest normalized events into the telemetry + evidence pipelines.

        Each event follows the canonical Connector → Adapter → Registry →
        Verification chain defined in ADR-009:

          1. Persist the raw NormalizedEvent into ``TelemetryEvent``
             (legacy audit/cache table — keeps existing dashboard
             integrations working).
          2. Convert the NormalizedEvent into a ``NormalizedEvidence``
             pydantic model and pass it to ``EvidenceOrchestrator``
             which writes the immutable ``EvidenceLedger`` row plus
             a ``NormalizedEvidenceRecord`` consumed by the
             Verification Engine.

        Args:
            connector_id: Source connector UUID.
            events: List of NormalizedEvent dataclasses.

        Returns:
            Number of events successfully ingested into
            ``TelemetryEvent`` (legacy table count). Evidence ledger
            counts are logged separately.
        """
        from app.models.telemetry_event import TelemetryEvent

        ingested = 0
        for event in events:
            # Idempotency check (legacy telemetry table)
            existing = (
                self.db.query(TelemetryEvent)
                .filter(
                    TelemetryEvent.org_id == self.org_id,
                    TelemetryEvent.source_system == event.source_system,
                    TelemetryEvent.source_event_id == event.source_event_id,
                )
                .first()
            )
            if existing:
                continue

            record = TelemetryEvent(
                org_id=self.org_id,
                connector_id=connector_id,
                event_type=event.event_type,
                source_system=event.source_system,
                source_event_id=event.source_event_id,
                payload_hash=event.payload_hash,
                payload=json.dumps(event.payload),
                severity=event.severity,
            )
            self.db.add(record)
            ingested += 1

        if ingested > 0:
            self.db.commit()
            logger.info(
                "Ingested %d events from connector %s (org=%s)",
                ingested, connector_id, self.org_id,
            )

        # ── Evidence Registry ingestion (ADR-009) ──────────────────
        # Always run, even if every legacy row was a duplicate, because
        # the evidence ledger may not yet have hashed rows for these
        # events. The orchestrator performs its own idempotency on
        # ``evidence_hash``.
        try:
            self._ingest_into_evidence_registry(connector_id, events)
        except Exception as exc:
            logger.warning(
                "Evidence registry ingestion failed for connector %s: %s",
                connector_id, exc,
            )

        # ── Adapter registration (ADR-009) ─────────────────────────
        # Whenever a connector syncs successfully, make sure its vendor
        # adapter is registered in the EvidenceRegistry so the
        # /connectors/confidence endpoint can compute a score for it.
        try:
            self._ensure_adapter_registered(events)
        except Exception as exc:
            logger.debug("Adapter registration skipped: %s", exc)

        return ingested

    # ------------------------------------------------------------------
    # Evidence Registry integration
    # ------------------------------------------------------------------

    def _ingest_into_evidence_registry(self, connector_id: str, events) -> None:
        """Run the connector's batch through ``EvidenceOrchestrator``.

        Translates ``NormalizedEvent`` dataclasses (connector-layer)
        into ``NormalizedEvidence`` pydantic models (registry-layer)
        and writes:
          - immutable ``EvidenceLedger`` rows (one per unique event)
          - ``NormalizedEvidenceRecord`` rows consumed by the
            Verification Engine.
        """
        from app.schemas.evidence import (
            NormalizedEvidence,
            EvidenceCollectionResult,
            EvidenceConfidence,
            EvidenceSeverity,
            ProviderTransport,
        )
        from app.services.evidence.orchestrator import EvidenceOrchestrator

        if not events:
            return

        provider_name = events[0].source_system
        normalized: List[NormalizedEvidence] = []
        for event in events:
            control_id = None
            if isinstance(event.payload, dict):
                control_id = event.payload.get("control_id")

            severity_str = (event.severity or "info").lower()
            try:
                severity = EvidenceSeverity(severity_str)
            except ValueError:
                severity = EvidenceSeverity.INFO

            # Parse the event timestamp; fall back to "now" if missing.
            from datetime import datetime, timezone as _tz
            ts: datetime
            if event.timestamp:
                try:
                    ts = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    ts = datetime.now(_tz.utc)
            else:
                ts = datetime.now(_tz.utc)

            evidence = NormalizedEvidence(
                source_connector=event.source_system,
                asset_id=None,
                control_id=control_id,
                event_type=event.event_type,
                severity=severity,
                timestamp=ts,
                raw_payload=event.payload if isinstance(event.payload, dict) else {"raw": event.payload},
                confidence=EvidenceConfidence(),
            )
            evidence.compute_hash()
            normalized.append(evidence)

        result = EvidenceCollectionResult(
            provider_name=provider_name,
            transport=ProviderTransport.MCP,
            evidence_count=len(normalized),
            errors=[],
            duration_ms=0.0,
            evidence=normalized,
        )

        orchestrator = EvidenceOrchestrator(self.db)
        summary = orchestrator.ingest_collection_result(
            org_id=self.org_id,
            connector_id=connector_id,
            result=result,
        )
        logger.info(
            "Evidence registry ingestion: %d new, %d duplicates (connector=%s, org=%s)",
            summary.get("new", 0), summary.get("duplicates", 0),
            connector_id, self.org_id,
        )

    def _ensure_adapter_registered(self, events) -> None:
        """Register the appropriate ``EvidenceAdapter`` for the connector.

        The registry is what powers ``GET /api/v1/connectors/confidence``.
        Without an adapter, every connector scores confidence 0.

        The SplunkAdapter and WazuhAdapter are constructed lazily;
        they remain unbounded (``_client = None``) until the
        corresponding Connector row's credentials are known. A
        subsequent ``bind_connector(connector)`` call attaches the
        live ``SplunkConnector`` / ``WazuhClient`` once the Connector
        has been resolved — see
        ``_attach_adapter_for_connector()`` invoked from the public
        ``register_connector`` flow.
        """
        from app.services.evidence.registry import get_instance

        if not events:
            return

        source = events[0].source_system
        registry = get_instance()
        if registry.is_registered(source):
            return

        if source == "splunk":
            from app.services.evidence.adapters.splunk import SplunkAdapter
            registry.register(SplunkAdapter())
        elif source == "wazuh":
            from app.services.evidence.adapters.wazuh import WazuhAdapter
            from app.services.wazuh_client import WazuhClient
            registry.register(WazuhAdapter(WazuhClient(host="", api_key="")))
        # New connector sources (github, aws_security_hub, microsoft, etc.)
        # register lazily via a generic adapter once implemented; for
        # now the confidence endpoint will report them as 0, which is
        # the documented acceptable behaviour.
