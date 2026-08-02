from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.evidence.base_adapter import EvidenceAdapter, EvidenceRecord, AdapterHealth
from app.services.wazuh_client import WazuhClient

logger = logging.getLogger("airs.adapters.wazuh")


class WazuhAdapter(EvidenceAdapter):
    """EvidenceAdapter implementation for Wazuh."""

    def __init__(self, client: WazuhClient):
        self._client = client

    @property
    def connector_name(self) -> str:
        return "wazuh"

    async def fetch_evidence(self, *, since: Optional[datetime] = None) -> List[EvidenceRecord]:
        """Fetch all evidence checks from Wazuh."""
        try:
            status = await self._client.get_agent_status()
            status_dict = status.to_dict() if hasattr(status, "to_dict") else {}
        except Exception as e:
            logger.error("WazuhAdapter get_agent_status failed: %s", e)
            status_dict = {}

        try:
            vulns = await self._client.get_vulnerabilities()
            vulns_dict = vulns.to_dict() if hasattr(vulns, "to_dict") else {}
        except Exception as e:
            logger.error("WazuhAdapter get_vulnerabilities failed: %s", e)
            vulns_dict = {}

        return self.normalize({"status": status_dict, "vulnerabilities": vulns_dict})

    def normalize(self, vendor_payload: Any) -> List[EvidenceRecord]:
        """Convert Wazuh dictionaries to canonical EvidenceRecords."""
        records = []
        now = datetime.now(timezone.utc)
        
        if not isinstance(vendor_payload, dict):
            return records

        status_payload = vendor_payload.get("status", {})
        vuln_payload = vendor_payload.get("vulnerabilities", {})
        
        if status_payload:
            records.append(EvidenceRecord(
                connector_name=self.connector_name,
                external_id=f"wazuh-agents-{int(now.timestamp())}",
                control_id="DC-001",  # Matches EDR check fallback
                finding_kind="telemetry",
                raw_payload=status_payload,
                observed_at=now,
                metadata={
                    "total_agents": status_payload.get("total_agents", 0),
                    "active_agents": status_payload.get("active_agents", 0)
                }
            ))
            
        if vuln_payload:
            records.append(EvidenceRecord(
                connector_name=self.connector_name,
                external_id=f"wazuh-vulns-{int(now.timestamp())}",
                control_id="TL-001",
                finding_kind="telemetry",
                raw_payload=vuln_payload,
                observed_at=now,
                metadata={
                    "total_vulnerabilities": vuln_payload.get("total_vulnerabilities", 0),
                    "critical_count": vuln_payload.get("critical_count", 0)
                }
            ))
            
        return records

    async def health(self) -> AdapterHealth:
        """Report live adapter health."""
        try:
            res = await self._client.get_agent_status()
            is_healthy = res.total_agents > 0 if hasattr(res, "total_agents") else False
            return AdapterHealth(
                healthy=is_healthy,
                last_success_at=datetime.now(timezone.utc) if is_healthy else None,
                success_count=1 if is_healthy else 0,
                failure_count=0 if is_healthy else 1,
                detail=f"Active agents: {res.active_agents}" if hasattr(res, "active_agents") else "OK"
            )
        except Exception as e:
            return AdapterHealth(
                healthy=False,
                last_failure_at=datetime.now(timezone.utc),
                success_count=0,
                failure_count=1,
                detail=str(e),
            )
