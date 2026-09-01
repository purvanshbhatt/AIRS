"""
Splunk MCP telemetry ingestion service.

Provides ``ingest_splunk_telemetry`` — a convenience wrapper that runs
the canonical ``SplunkConnector`` sync for an organization through
``ConnectorManager`` and returns the number of newly ingested events.

Single Backend Path invariant (2026-07-15 audit):
  This module is the only externally callable Splunk ingestion helper.
  The deleted ``app.integrations.sentinel_splunk`` package had a
  parallel HEC implementation — that path is gone. All Splunk queries
  flow through ``SplunkMCPClient`` behind ``SplunkConnector``.
"""
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger("airs.splunk_service")


async def ingest_splunk_telemetry(db: Session, org_id: str) -> int:
    """Run the canonical SplunkConnector sync for an org.

    Looks up the active Splunk connector in the org, invokes
    ``ConnectorManager.sync_connector``, and returns the number of
    events recorded in the sync result. The legacy
    ``TelemetryEvent`` rows plus the immutable ``EvidenceLedger`` and
    ``NormalizedEvidenceRecord`` rows are written by
    ``ConnectorManager._ingest_events``.

    Returns 0 if no Splunk connector is configured or the sync fails.
    """
    from app.models.connector import Connector, ConnectorType, ConnectorStatus
    from app.services.connector_manager import ConnectorManager

    active_value = (
        ConnectorStatus.active.value
        if hasattr(ConnectorStatus, "active")
        else "active"
    )
    connector = (
        db.query(Connector)
        .filter(
            Connector.org_id == org_id,
            Connector.connector_type == ConnectorType.splunk,
            Connector.status == active_value,
        )
        .first()
    )
    if not connector:
        logger.warning("No active Splunk connector for org %s", org_id)
        return 0

    mgr = ConnectorManager(db, org_id)
    try:
        result = await mgr.sync_connector(connector.id)
        if not result.success:
            connector.health_status = "error"
            connector.error_message = result.error_details
            db.commit()
            return 0
        return result.events_ingested
    except Exception as exc:
        logger.error("Splunk sync failed for org %s: %s", org_id, exc)
        try:
            connector.health_status = "error"
            connector.error_message = str(exc)
            db.commit()
        except Exception:
            pass
        return 0
