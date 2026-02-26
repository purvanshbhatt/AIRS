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

    def __init__(self, base_url: str, hec_token: str):
        self.base_url = base_url.rstrip("/")
        self.hec_token = hec_token
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
                verify=False,  # Many Splunk instances use self-signed certs
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

    async def pull_all_evidence(self) -> List[Dict[str, Any]]:
        """Run all evidence checks and return combined results."""
        mfa = await self.verify_mfa_enforcement()
        edr = await self.verify_edr_coverage()
        return [mfa.to_dict(), edr.to_dict()]
