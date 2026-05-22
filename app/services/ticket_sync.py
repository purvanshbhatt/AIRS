"""Remediation Ticket Sync Service.

Handles automated export of compliance findings to:
1. Jira (REST API v2)
2. ServiceNow (Table API / Incident)
3. Custom Webhook
"""

import json
import logging
import secrets
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.services.integrations import _validate_webhook_url, _sign_payload

logger = logging.getLogger("airs.ticket_sync")


class TicketSyncService:
    """Manages ticket creation and webhook synchronization for findings."""

    def __init__(self, db_session: Optional[Any] = None):
        self.db = db_session
        self.timeout = 5.0

    async def sync_finding_to_target(
        self,
        finding_id: str,
        title: str,
        description: str,
        severity: str,
        recommendation: str,
        rule_id: str,
        target: str,  # "jira" | "servicenow" | "webhook"
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Syncs the finding to the external tracking system."""
        t = str(target).lower().strip()
        
        logger.info("Ticketing Sync Called for finding_id=%s, target=%s", finding_id, t)
        
        # Prepare payload
        payload = {
            "finding_id": finding_id,
            "rule_id": rule_id,
            "title": f"ResilAI Audit Finding: {title}",
            "description": (
                f"Compliance Finding identified by ResilAI Deterministic Governance Engine.\n\n"
                f"Rule ID: {rule_id}\n"
                f"Severity: {severity.upper()}\n"
                f"Description: {description}\n\n"
                f"Technical Recommendation:\n{recommendation}\n\n"
                f"Link to Audit: {getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')}/remediations"
            ),
            "severity": severity,
            "status": "open",
            "source": "resilai"
        }
        
        # Run demo mode checks
        is_demo = settings.is_demo_mode
        
        if t == "jira":
            return await self._sync_to_jira(payload, config, is_demo)
        elif t == "servicenow":
            return await self._sync_to_servicenow(payload, config, is_demo)
        elif t == "webhook":
            return await self._sync_to_webhook(payload, config, is_demo)
        else:
            raise ValueError(f"Unknown sync target: {target}")

    async def _sync_to_jira(
        self,
        payload: Dict[str, Any],
        config: Dict[str, Any],
        is_demo: bool
    ) -> Dict[str, Any]:
        url = config.get("url", "").rstrip("/") or "https://jira.company.com"
        project_key = config.get("project_key", "RESIL").upper()
        
        # Format Jira payload
        jira_payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": payload["title"],
                "description": payload["description"],
                "issuetype": {"name": "Task"},
                "priority": {"name": self._map_severity_to_jira_priority(payload["severity"])}
            }
        }
        
        if is_demo or not config.get("url"):
            # Return demo/mock ticket
            ticket_id = f"{project_key}-{secrets.randbelow(9000) + 1000}"
            return {
                "success": True,
                "target": "jira",
                "ticket_key": ticket_id,
                "ticket_url": f"{url}/browse/{ticket_id}",
                "message": "Demo: Simulated Jira ticket successfully created.",
                "payload_sent": jira_payload,
            }
            
        # Real HTTP call
        username = config.get("username")
        api_token = config.get("api_token")
        headers = {"Content-Type": "application/json"}
        auth = (username, api_token) if username and api_token else None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{url}/rest/api/2/issue",
                    json=jira_payload,
                    headers=headers,
                    auth=auth
                )
                
            if resp.status_code in (200, 201):
                data = resp.json()
                key = data.get("key", f"{project_key}-UNKNOWN")
                return {
                    "success": True,
                    "target": "jira",
                    "ticket_key": key,
                    "ticket_url": f"{url}/browse/{key}",
                    "message": "Jira ticket created successfully.",
                    "payload_sent": jira_payload,
                }
            else:
                raise httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}: {resp.text}",
                    request=resp.request,
                    response=resp
                )
        except Exception as e:
            logger.error("Failed to sync to Jira: %s", e)
            return {
                "success": False,
                "target": "jira",
                "error": str(e),
                "message": "Failed to connect to Jira instance."
            }

    async def _sync_to_servicenow(
        self,
        payload: Dict[str, Any],
        config: Dict[str, Any],
        is_demo: bool
    ) -> Dict[str, Any]:
        url = config.get("url", "").rstrip("/") or "https://company.service-now.com"
        
        snow_payload = {
            "short_description": payload["title"],
            "description": payload["description"],
            "urgency": self._map_severity_to_snow_urgency(payload["severity"]),
            "impact": "2",  # Medium
            "comments": "Automatically generated by ResilAI Deterministic Governance Engine."
        }
        
        if is_demo or not config.get("url"):
            inc_number = f"INC{secrets.randbelow(9000000) + 1000000}"
            return {
                "success": True,
                "target": "servicenow",
                "ticket_key": inc_number,
                "ticket_url": f"{url}/nav_to.do?uri=incident.do?sysparm_query=number={inc_number}",
                "message": "Demo: Simulated ServiceNow incident successfully created.",
                "payload_sent": snow_payload,
            }
            
        username = config.get("username")
        password = config.get("password")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        auth = (username, password) if username and password else None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{url}/api/now/table/incident",
                    json=snow_payload,
                    headers=headers,
                    auth=auth
                )
                
            if resp.status_code in (200, 201):
                data = resp.json().get("result", {})
                num = data.get("number", "INC-UNKNOWN")
                sys_id = data.get("sys_id", "")
                return {
                    "success": True,
                    "target": "servicenow",
                    "ticket_key": num,
                    "ticket_url": f"{url}/nav_to.do?uri=incident.do?sys_id={sys_id}",
                    "message": "ServiceNow incident created successfully.",
                    "payload_sent": snow_payload,
                }
            else:
                raise httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}: {resp.text}",
                    request=resp.request,
                    response=resp
                )
        except Exception as e:
            logger.error("Failed to sync to ServiceNow: %s", e)
            return {
                "success": False,
                "target": "servicenow",
                "error": str(e),
                "message": "Failed to connect to ServiceNow instance."
            }

    async def _sync_to_webhook(
        self,
        payload: Dict[str, Any],
        config: Dict[str, Any],
        is_demo: bool
    ) -> Dict[str, Any]:
        webhook_url = config.get("url", "")
        if not webhook_url:
            return {
                "success": False,
                "target": "webhook",
                "error": "Missing webhook URL",
                "message": "A target URL must be configured for webhook delivery."
            }
            
        # Security: SSRF Protection
        try:
            validated_url = _validate_webhook_url(webhook_url)
        except ValueError as exc:
            # For demo, allow bypass or return error
            if is_demo:
                validated_url = webhook_url
            else:
                return {
                    "success": False,
                    "target": "webhook",
                    "error": f"SSRF Check Blocked URL: {exc}",
                    "message": "Outbound webhook URL resolves to a prohibited internal network address."
                }
                
        body = json.dumps(payload)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "resilai-ticket-sync/1.0",
            "X-ResilAI-Event": "finding.remediation_sync",
        }
        
        secret = config.get("secret")
        signature = _sign_payload(secret, body)
        if signature:
            headers["X-ResilAI-Signature"] = signature
            
        if is_demo and "requestbin" not in webhook_url and "webhook.site" not in webhook_url:
            # Simulation response for internal demo endpoints
            return {
                "success": True,
                "target": "webhook",
                "ticket_key": "webhook-delivered",
                "ticket_url": validated_url,
                "message": "Demo: Webhook payload dispatch simulated.",
                "payload_sent": payload,
            }
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(validated_url, content=body, headers=headers)
                
            if 200 <= resp.status_code < 300:
                return {
                    "success": True,
                    "target": "webhook",
                    "ticket_key": "webhook-delivered",
                    "ticket_url": validated_url,
                    "message": f"Webhook delivered (HTTP {resp.status_code}).",
                    "payload_sent": payload,
                }
            else:
                return {
                    "success": False,
                    "target": "webhook",
                    "error": f"HTTP {resp.status_code}: {resp.text[:100]}",
                    "message": "Webhook receiver returned a non-success status code."
                }
        except Exception as e:
            logger.error("Failed to deliver sync webhook: %s", e)
            return {
                "success": False,
                "target": "webhook",
                "error": str(e),
                "message": "Failed to connect to the configured webhook endpoint."
            }

    def _map_severity_to_jira_priority(self, severity: str) -> str:
        s = severity.lower()
        if s == "critical":
            return "Highest"
        elif s == "high":
            return "High"
        elif s == "medium":
            return "Medium"
        return "Low"

    def _map_severity_to_snow_urgency(self, severity: str) -> str:
        s = severity.lower()
        if s == "critical":
            return "1"  # High
        elif s == "high":
            return "2"  # Medium
        return "3"  # Low
