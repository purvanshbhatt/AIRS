"""
SplunkService — Evidence-Based Security Verification.

Queries a customer's Splunk instance via HEC (HTTP Event Collector) REST API
to pull *live log evidence* for security controls:
  - MFA Enforcement (index=main sourcetype=mfa_logs)
  - EDR Coverage   (index=main sourcetype=edr_telemetry)

This lets ResilAI move beyond self-reported questionnaire answers
and verify controls with real telemetry data.

Usage:
    svc = SplunkService(base_url="https://splunk.customer.com:8089",
                        hec_token="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    result = await svc.verify_mfa_enforcement()
    result = await svc.verify_edr_coverage()
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

import httpx

logger = logging.getLogger("airs.splunk")


class EvidenceStatus(str, Enum):
    """Status of an evidence verification check."""
    VERIFIED = "verified"           # Live logs confirm the control
    PARTIAL = "partial"             # Some evidence found, gaps exist
    NOT_VERIFIED = "not_verified"   # No evidence found
    ERROR = "error"                 # Could not query Splunk
    NOT_CONFIGURED = "not_configured"  # No Splunk credentials


class EvidenceResult:
    """Result of a single evidence verification check."""

    def __init__(
        self,
        control: str,
        status: EvidenceStatus,
        event_count: int = 0,
        sample_events: Optional[List[Dict[str, Any]]] = None,
        message: str = "",
        query_used: str = "",
        verified_at: Optional[str] = None,
    ):
        self.control = control
        self.status = status
        self.event_count = event_count
        self.sample_events = sample_events or []
        self.message = message
        self.query_used = query_used
        self.verified_at = verified_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "control": self.control,
            "status": self.status.value,
            "event_count": self.event_count,
            "sample_events": self.sample_events[:5],  # Cap at 5 samples
            "message": self.message,
            "query_used": self.query_used,
            "verified_at": self.verified_at,
        }


class LoggingHealthResult(EvidenceResult):
    """Structured logging-health result used by the integrations UI and tests."""

    def __init__(
        self,
        logging_enabled: bool,
        last_event_time: Optional[str],
        event_count_24h: int,
        event_count_7d: int,
        sourcetypes_active: Optional[List[str]] = None,
        indexes_active: Optional[List[str]] = None,
        message: str = "",
        query_used: str = "",
        verified_at: Optional[str] = None,
    ):
        super().__init__(
            control="Centralized Logging",
            status=EvidenceStatus.VERIFIED if logging_enabled else EvidenceStatus.NOT_VERIFIED,
            event_count=event_count_24h,
            sample_events=[],
            message=message,
            query_used=query_used,
            verified_at=verified_at,
        )
        self.logging_enabled = logging_enabled
        self.last_event_time = last_event_time
        self.event_count_24h = event_count_24h
        self.event_count_7d = event_count_7d
        self.sourcetypes_active = sourcetypes_active or []
        self.indexes_active = indexes_active or []

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "logging_enabled": self.logging_enabled,
                "last_event_time": self.last_event_time,
                "event_count_24h": self.event_count_24h,
                "event_count_7d": self.event_count_7d,
                "sourcetypes_active": self.sourcetypes_active,
                "indexes_active": self.indexes_active,
            }
        )
        return base


class SplunkService:
    """
    Client for querying a Splunk instance via REST API.

    Requires:
      - base_url: Splunk management URL (e.g. https://splunk.example.com:8089)
      - hec_token: HTTP Event Collector token for authentication
    """

    # Default search time range: last 30 days
    DEFAULT_EARLIEST = "-30d"
    DEFAULT_LATEST = "now"
    TIMEOUT_SECONDS = 30

    def __init__(self, base_url: Optional[str] = None, hec_token: str = "", host: Optional[str] = None, port: int = 8089, verify_ssl: bool = False):
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif host:
            self.base_url = f"https://{host}:{port}"
        else:
            raise TypeError("SplunkService requires either base_url or host")
        self.hec_token = hec_token
        self.verify_ssl = verify_ssl
        self._headers = {
            "Authorization": f"Bearer {hec_token}",
            "Content-Type": "application/json",
        }

    async def _run_search(
        self,
        query: str,
        earliest: str = DEFAULT_EARLIEST,
        latest: str = DEFAULT_LATEST,
        max_results: int = 100,
    ) -> Dict[str, Any]:
        """
        Execute a Splunk search via the REST API (oneshot mode).

        Returns: {"results": [...], "total_count": int}
        """
        search_url = f"{self.base_url}/services/search/jobs/export"
        params = {
            "search": f"search {query}",
            "earliest_time": earliest,
            "latest_time": latest,
            "output_mode": "json",
            "count": max_results,
        }

        try:
            async with httpx.AsyncClient(
                verify=self.verify_ssl is True,
                timeout=self.TIMEOUT_SECONDS,
            ) as client:
                resp = await client.get(
                    search_url,
                    params=params,
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()

                results = data.get("results", [])
                return {
                    "results": results,
                    "total_count": len(results),
                }
        except httpx.TimeoutException:
            logger.warning("Splunk search timed out: %s", query)
            raise
        except Exception as exc:
            logger.error("Splunk search failed: %s — %s", query, exc)
            raise

    async def verify_mfa_enforcement(self) -> EvidenceResult:
        """
        Query Splunk for MFA enforcement evidence.
        Looks for mfa_logs indicating MFA challenges.
        """
        query = 'index=main sourcetype=mfa_logs action="challenge" | stats count by user, result'
        try:
            data = await self._run_search(query)
            count = data["total_count"]
            if count > 0:
                # Check for failures
                failures = [
                    r for r in data["results"]
                    if r.get("result", "").lower() in ("failure", "failed", "denied")
                ]
                if failures and len(failures) / count > 0.2:
                    return EvidenceResult(
                        control="MFA Enforcement",
                        status=EvidenceStatus.PARTIAL,
                        event_count=count,
                        sample_events=data["results"][:5],
                        message=f"MFA logs found ({count} events) but {len(failures)} failures detected (>{20}% failure rate).",
                        query_used=query,
                    )
                return EvidenceResult(
                    control="MFA Enforcement",
                    status=EvidenceStatus.VERIFIED,
                    event_count=count,
                    sample_events=data["results"][:5],
                    message=f"MFA enforcement verified: {count} challenge events in last 30 days.",
                    query_used=query,
                )
            else:
                return EvidenceResult(
                    control="MFA Enforcement",
                    status=EvidenceStatus.NOT_VERIFIED,
                    event_count=0,
                    message="No MFA logs found in the last 30 days. MFA enforcement cannot be verified.",
                    query_used=query,
                )
        except Exception as exc:
            return EvidenceResult(
                control="MFA Enforcement",
                status=EvidenceStatus.ERROR,
                message=f"Failed to query Splunk: {str(exc)}",
                query_used=query,
            )

    async def verify_edr_coverage(self) -> EvidenceResult:
        """
        Query Splunk for EDR telemetry evidence.
        Looks for endpoint detection & response data.
        """
        query = 'index=main sourcetype=edr_telemetry | stats count by host, action | head 100'
        try:
            data = await self._run_search(query)
            count = data["total_count"]
            if count > 0:
                # Count unique hosts
                hosts = set()
                for r in data["results"]:
                    if "host" in r:
                        hosts.add(r["host"])

                if len(hosts) < 5:
                    return EvidenceResult(
                        control="EDR Coverage",
                        status=EvidenceStatus.PARTIAL,
                        event_count=count,
                        sample_events=data["results"][:5],
                        message=f"EDR telemetry found but only {len(hosts)} unique hosts reporting. Coverage may be incomplete.",
                        query_used=query,
                    )
                return EvidenceResult(
                    control="EDR Coverage",
                    status=EvidenceStatus.VERIFIED,
                    event_count=count,
                    sample_events=data["results"][:5],
                    message=f"EDR coverage verified: {len(hosts)} hosts reporting telemetry.",
                    query_used=query,
                )
            else:
                return EvidenceResult(
                    control="EDR Coverage",
                    status=EvidenceStatus.NOT_VERIFIED,
                    event_count=0,
                    message="No EDR telemetry found in the last 30 days.",
                    query_used=query,
                )
        except Exception as exc:
            return EvidenceResult(
                control="EDR Coverage",
                status=EvidenceStatus.ERROR,
                message=f"Failed to query Splunk: {str(exc)}",
                query_used=query,
            )

    async def verify_logging_health(
        self,
        sourcetype: str = "resilai_drift",
        index: str = "security_alerts",
    ) -> LoggingHealthResult:
        """
        Verify that ResilAI logs are being received in Splunk (heartbeat check).
        
        This control checks the "Centralized Logging Enabled" requirement in the
        Telemetry & Logging domain. A successful heartbeat from Splunk confirms
        logs are persisting and searchable.
        
        Args:
            sourcetype: Splunk sourcetype to check (default: resilai_drift)
            index: Splunk index to check (default: security_alerts)
        
        Returns:
            EvidenceResult with logging health status
        """
        query = f'index={index} sourcetype={sourcetype} | stats latest(_time) as last_event, count as event_count'
        try:
            data = await self._run_search(
                query,
                earliest="-24h",
                latest="now",
                max_results=10
            )
            count = data["total_count"]
            
            if count > 0:
                # Extract event count from results
                event_count_24h = int(data["results"][0].get("event_count", 0))
                last_event = data["results"][0].get("last_event")
                
                return LoggingHealthResult(
                    logging_enabled=True,
                    last_event_time=last_event,
                    event_count_24h=event_count_24h,
                    event_count_7d=event_count_24h,
                    sourcetypes_active=[sourcetype],
                    indexes_active=[index],
                    message=f"Logging verified: {event_count_24h} events received in last 24 hours. "
                            f"Last event at {last_event}.",
                    query_used=query,
                )
            else:
                return LoggingHealthResult(
                    logging_enabled=False,
                    last_event_time=None,
                    event_count_24h=0,
                    event_count_7d=0,
                    sourcetypes_active=[],
                    indexes_active=[],
                    message=f"No logs found in {index}/{sourcetype} in the last 24 hours. "
                            "Centralized logging may not be enabled or configured correctly.",
                    query_used=query,
                )
        except Exception as exc:
            return LoggingHealthResult(
                logging_enabled=False,
                last_event_time=None,
                event_count_24h=0,
                event_count_7d=0,
                message=f"Failed to verify logging health: {str(exc)}",
                query_used=query,
            )

    async def verify_heartbeat(
        self,
        sourcetype: str = "resilai_drift",
        index: str = "security_alerts",
    ) -> Dict[str, Any]:
        """Higher-level heartbeat check returning structured health fields

        Returns a dict compatible with the integrations router:
          - logging_enabled: bool
          - last_event_time: ISO timestamp or None
          - event_count_24h: int
          - event_count_7d: int
          - sourcetypes_active: List[str]
          - indexes_active: List[str]
          - verified_at: ISO timestamp
        """
        try:
            res_24h = await self.verify_logging_health(sourcetype=sourcetype, index=index)

            # 7d count
            query_7d = f'index={index} sourcetype={sourcetype} | stats count as event_count'
            data_7d = await self._run_search(query_7d, earliest="-7d", latest="now", max_results=1)
            event_count_7d = int(data_7d.get("total_count", 0))

            # sourcetypes active list (sample)
            query_sourcetypes = f'index={index} | stats count by sourcetype | sort -count | head 10'
            st_data = await self._run_search(query_sourcetypes, earliest="-7d", latest="now", max_results=10)
            sourcetypes_active = [r.get("sourcetype") for r in st_data.get("results", []) if r.get("sourcetype")]

            # indexes_active sample (Splunk events include index field)
            query_indexes = f'| metadata type=sources index={index} | head 10'
            idx_data = await self._run_search(query_indexes, earliest="-7d", latest="now", max_results=10)
            indexes_active = [r.get("source") for r in idx_data.get("results", []) if r.get("source")]

            return {
                "logging_enabled": getattr(res_24h, "logging_enabled", False),
                "last_event_time": getattr(res_24h, "last_event_time", None),
                "event_count_24h": getattr(res_24h, "event_count_24h", 0),
                "event_count_7d": event_count_7d,
                "sourcetypes_active": sourcetypes_active,
                "indexes_active": indexes_active,
                "verified_at": getattr(res_24h, "verified_at", None),
            }
        except Exception as exc:
            logger.error("verify_heartbeat failed: %s", exc)
            return {
                "logging_enabled": False,
                "last_event_time": None,
                "event_count_24h": 0,
                "event_count_7d": 0,
                "sourcetypes_active": [],
                "indexes_active": [],
                "verified_at": None,
            }
    
    async def run_custom_query(
        self,
        query: str,
        earliest: str = "-24h",
        latest: str = "now",
        max_results: int = 1000,
    ) -> Dict[str, Any]:
        """
        Execute a custom SPL (Search Processing Language) query against Splunk.
        
        This endpoint allows ad-hoc queries for security drift verification,
        custom compliance checks, or incident investigation.
        
        Args:
            query: SPL query string
            earliest: Start time (e.g., "-7d", "2026-05-01T00:00:00")
            latest: End time (e.g., "now", "2026-05-08T23:59:59")
            max_results: Maximum events to return
        
        Returns:
            Dict with query results: {"results": [...], "total_count": int}
        
        Raises:
            Exception: If query fails or times out
        """
        return await self._run_search(
            query,
            earliest=earliest,
            latest=latest,
            max_results=max_results,
        )

    async def pull_all_evidence(self) -> List[Dict[str, Any]]:
        """Run all evidence checks and return combined results."""
        mfa = await self.verify_mfa_enforcement()
        edr = await self.verify_edr_coverage()
        logging_health = await self.verify_logging_health()
        return [mfa.to_dict(), edr.to_dict(), logging_health.to_dict()]
