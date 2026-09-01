"""
GitHub Connector — Security telemetry ingestion from GitHub.

Fetches: security advisories, Dependabot alerts, code scanning alerts,
and secret scanning alerts. Supports PAT and GitHub App authentication.

Webhook ingestion validates X-Hub-Signature-256 for enterprise pen-test
compliance.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    RawEvent,
    PermissionResult,
)
from app.services.clinic_engine.v2.schema import ConnectorCapability
from app.connectors.registry import register_connector

logger = logging.getLogger("airs.connectors.github")

_GITHUB_API = "https://api.github.com"


@register_connector
class GitHubConnector(Connector):
    """GitHub security telemetry connector.

    Supports:
      - Personal Access Token (PAT) authentication
      - GitHub App JWT authentication (future)
      - Webhook payload signature verification (X-Hub-Signature-256)
    """

    CONNECTOR_TYPE = "github"
    REQUIRED_PERMISSIONS = ["repo", "security_events"]
    CAPABILITIES = [ConnectorCapability.CLOUD_ASSETS]

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        token = self._credentials.get("token", "")
        if not token:
            self.logger.error("No GitHub token provided")
            return False

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{_GITHUB_API}/user",
                    headers=self._auth_headers(token),
                )
                if resp.status_code == 200:
                    self._authenticated = True
                    self.logger.info("GitHub authentication successful")
                    return True
                self.logger.warning("GitHub auth failed: %d", resp.status_code)
                return False
        except Exception as exc:
            self.logger.error("GitHub auth error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> List[RawEvent]:
        token = self._credentials.get("token", "")
        repos = self._config.get("repositories", [])
        events: List[RawEvent] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = self._auth_headers(token)

            # If specific repos configured, fetch per-repo; otherwise org-level
            if repos:
                for repo in repos:
                    events.extend(
                        await self._fetch_repo_alerts(client, headers, repo)
                    )
            else:
                # Fetch from user's accessible repos
                resp = await client.get(
                    f"{_GITHUB_API}/user/repos",
                    headers=headers,
                    params={"per_page": 50, "sort": "updated"},
                )
                if resp.status_code == 200:
                    for repo_data in resp.json():
                        full_name = repo_data.get("full_name", "")
                        if full_name:
                            events.extend(
                                await self._fetch_repo_alerts(
                                    client, headers, full_name
                                )
                            )

        self.logger.info("GitHub sync: %d events collected", len(events))
        return events

    async def _fetch_repo_alerts(
        self,
        client: httpx.AsyncClient,
        headers: Dict[str, str],
        repo: str,
    ) -> List[RawEvent]:
        """Fetch all security alert types for a single repository."""
        events: List[RawEvent] = []

        # Dependabot alerts
        try:
            resp = await client.get(
                f"{_GITHUB_API}/repos/{repo}/dependabot/alerts",
                headers=headers,
                params={"state": "open", "per_page": 100},
            )
            if resp.status_code == 200:
                for alert in resp.json():
                    events.append(RawEvent(
                        event_type="github.dependabot_alert",
                        source_system="github",
                        source_event_id=f"dependabot-{repo}-{alert.get('number', '')}",
                        severity=self._map_severity(
                            alert.get("security_advisory", {}).get("severity", "")
                        ),
                        payload={
                            "repo": repo,
                            "number": alert.get("number"),
                            "package": alert.get("dependency", {}).get("package", {}).get("name"),
                            "advisory": alert.get("security_advisory", {}).get("summary", ""),
                            "state": alert.get("state"),
                        },
                    ))
        except Exception as exc:
            self.logger.debug("Dependabot fetch failed for %s: %s", repo, exc)

        # Code scanning alerts
        try:
            resp = await client.get(
                f"{_GITHUB_API}/repos/{repo}/code-scanning/alerts",
                headers=headers,
                params={"state": "open", "per_page": 100},
            )
            if resp.status_code == 200:
                for alert in resp.json():
                    events.append(RawEvent(
                        event_type="github.code_scanning_alert",
                        source_system="github",
                        source_event_id=f"codescan-{repo}-{alert.get('number', '')}",
                        severity=self._map_severity(
                            alert.get("rule", {}).get("severity", "")
                        ),
                        payload={
                            "repo": repo,
                            "number": alert.get("number"),
                            "rule_id": alert.get("rule", {}).get("id"),
                            "description": alert.get("rule", {}).get("description", ""),
                            "tool": alert.get("tool", {}).get("name"),
                        },
                    ))
        except Exception as exc:
            self.logger.debug("Code scanning fetch failed for %s: %s", repo, exc)

        # Secret scanning alerts
        try:
            resp = await client.get(
                f"{_GITHUB_API}/repos/{repo}/secret-scanning/alerts",
                headers=headers,
                params={"state": "open", "per_page": 100},
            )
            if resp.status_code == 200:
                for alert in resp.json():
                    events.append(RawEvent(
                        event_type="github.secret_scanning_alert",
                        source_system="github",
                        source_event_id=f"secret-{repo}-{alert.get('number', '')}",
                        severity="critical",
                        payload={
                            "repo": repo,
                            "number": alert.get("number"),
                            "secret_type": alert.get("secret_type"),
                            "state": alert.get("state"),
                        },
                    ))
        except Exception as exc:
            self.logger.debug("Secret scanning fetch failed for %s: %s", repo, exc)

        return events

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def health_check(self) -> ConnectorHealth:
        token = self._credentials.get("token", "")
        import time
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_GITHUB_API}/rate_limit",
                    headers=self._auth_headers(token),
                )
                latency = int((time.monotonic() - start) * 1000)
                if resp.status_code == 200:
                    rate_data = resp.json().get("rate", {})
                    remaining = rate_data.get("remaining", 0)
                    status = "healthy" if remaining > 100 else "degraded"
                    return ConnectorHealth(
                        status=status,
                        latency_ms=latency,
                        message=f"Rate limit remaining: {remaining}",
                    )
                return ConnectorHealth(
                    status="unreachable",
                    latency_ms=latency,
                    message=f"HTTP {resp.status_code}",
                )
        except Exception as exc:
            return ConnectorHealth(status="unreachable", message=str(exc))

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        token = self._credentials.get("token", "")
        missing = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{_GITHUB_API}/user",
                    headers=self._auth_headers(token),
                )
                if resp.status_code != 200:
                    return PermissionResult(
                        valid=False, message="Token authentication failed"
                    )
                scopes = resp.headers.get("x-oauth-scopes", "")
                scope_set = {s.strip() for s in scopes.split(",")} if scopes else set()
                for perm in self.REQUIRED_PERMISSIONS:
                    if perm not in scope_set:
                        missing.append(perm)
        except Exception as exc:
            return PermissionResult(valid=False, message=str(exc))

        if missing:
            return PermissionResult(
                valid=False,
                missing_permissions=missing,
                message=f"Missing scopes: {', '.join(missing)}",
            )
        return PermissionResult(valid=True, message="All required scopes present")

    # ------------------------------------------------------------------
    # Webhook Signature Verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_webhook_signature(
        payload_body: bytes,
        signature_header: str,
        webhook_secret: str,
    ) -> bool:
        """Verify X-Hub-Signature-256 from GitHub webhook.

        Enterprise requirement: all webhook endpoints MUST validate this
        signature or they will fail penetration testing.

        Args:
            payload_body: Raw request body bytes.
            signature_header: Value of X-Hub-Signature-256 header.
            webhook_secret: Shared secret configured in GitHub.

        Returns:
            True if signature is valid.
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        expected = hmac.new(
            webhook_secret.encode(),
            payload_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature_header)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _auth_headers(token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    @staticmethod
    def _map_severity(github_severity: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "moderate": "medium",
            "low": "low",
            "warning": "low",
            "note": "info",
            "error": "high",
        }
        return mapping.get(github_severity.lower(), "medium")
