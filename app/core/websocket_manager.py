import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("airs.websocket_manager")

class TelemetryConnectionManager:
    def __init__(self):
        # Maps org_id -> list of active WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, org_id: str, websocket: WebSocket):
        await websocket.accept()
        if org_id not in self.active_connections:
            self.active_connections[org_id] = []
        self.active_connections[org_id].append(websocket)
        logger.info(f"WebSocket client connected to org_id: {org_id}. Active connection count: {len(self.active_connections[org_id])}")

    def disconnect(self, org_id: str, websocket: WebSocket):
        if org_id in self.active_connections:
            if websocket in self.active_connections[org_id]:
                self.active_connections[org_id].remove(websocket)
            if not self.active_connections[org_id]:
                del self.active_connections[org_id]
        logger.info(f"WebSocket client disconnected from org_id: {org_id}")

    async def broadcast_org_update(self, org_id: str, db_session=None):
        """Fetches the latest GHI and connector health for the org and broadcasts it to all connected sockets."""
        if org_id not in self.active_connections or not self.active_connections[org_id]:
            return

        logger.info(f"Broadcasting event-driven GHI update for org: {org_id}")
        
        # Dynamically import inside to avoid circular dependencies
        from app.db.database import SessionLocal
        from app.models.organization import Organization
        from app.models.wazuh_config import WazuhConfig
        from app.models.connector import Connector, ConnectorType
        from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
        from app.services.governance.validation_engine import validate_organization
        from datetime import datetime, timezone

        db = db_session or SessionLocal()
        try:
            org = db.query(Organization).filter(Organization.id == org_id).first()
            if org:
                # Calculate GHI index
                result = validate_organization(db, org)

                # Get connector statuses
                wazuh_status = "not_configured"
                cfg = db.query(WazuhConfig).filter(WazuhConfig.org_id == org.id).first()
                if cfg:
                    wazuh_status = "configured"

                splunk_status = "not_configured"
                conn = db.query(Connector).filter(
                    Connector.org_id == org.id,
                    Connector.connector_type == ConnectorType.splunk
                ).first()
                if conn and conn.status == "active":
                    splunk_status = "configured"

                wazuh_agent_status = None
                cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org.id).first()
                if cache and cache.agent_status:
                    try:
                        wazuh_agent_status = json.loads(cache.agent_status)
                    except Exception:
                        pass

                # Calculate dynamic ROI metrics
                from app.services.telemetry import TelemetryVerificationService
                telemetry_service = TelemetryVerificationService(db)
                try:
                    roi_metrics = telemetry_service.calculate_roi_metrics(org.id)
                except Exception as roi_err:
                    logger.error(f"Error calculating ROI metrics during WebSocket broadcast: {roi_err}")
                    roi_metrics = {
                        "base_manual_hours": 100,
                        "automated_hours": 0,
                        "hours_saved": 0,
                        "revenue_protected": 250000,
                        "total_controls": 25,
                        "automated_controls": 0
                    }

                payload = {
                    "org_id": org.id,
                    "ghi": result.governance_health_index.ghi,
                    "grade": result.governance_health_index.grade,
                    "dimensions": result.governance_health_index.dimensions,
                    "weights": result.governance_health_index.weights,
                    "audit_readiness": result.audit_readiness.to_dict(),
                    "lifecycle": result.lifecycle.to_dict(),
                    "sla": result.sla.to_dict(),
                    "compliance": result.compliance.to_dict(),
                    "wazuh_status": wazuh_status,
                    "splunk_status": splunk_status,
                    "wazuh_agent_status": wazuh_agent_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "passed": result.passed,
                    "issues": result.issues,
                    "roi_metrics": roi_metrics,
                }
                
                # Broadcast
                for connection in list(self.active_connections[org_id]):
                    try:
                        await connection.send_text(json.dumps(payload))
                    except Exception as send_err:
                        logger.error(f"Failed to send websocket message to connection: {send_err}")
                        self.disconnect(org_id, connection)
        except Exception as err:
            logger.error(f"Error in broadcast_org_update: {err}")
        finally:
            if not db_session:
                db.close()

    async def broadcast_connector_progress(
        self,
        org_id: str,
        connector_type: str,
        state: str,
        status_message: str,
        details: dict = None,
    ):
        """Broadcasts a connector progress event to all connected clients for the organization."""
        if org_id not in self.active_connections or not self.active_connections[org_id]:
            return

        from datetime import datetime, timezone
        from app.schemas.connector_progress import ConnectorProgressEvent, ConnectorProgressState

        clean_details = details or {}

        event = ConnectorProgressEvent(
            type="connector_progress",
            org_id=org_id,
            connector_type=connector_type,
            state=ConnectorProgressState(state),
            status_message=status_message,
            details=clean_details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Broadcasting connector progress [{state}] to org_id: {org_id}: {status_message}"
        )
        
        event_json = event.model_dump_json()

        for connection in list(self.active_connections[org_id]):
            try:
                await connection.send_text(event_json)
            except Exception as send_err:
                logger.error(f"Failed to send websocket progress message: {send_err}")
                self.disconnect(org_id, connection)

# Global singleton manager
telemetry_ws_manager = TelemetryConnectionManager()
