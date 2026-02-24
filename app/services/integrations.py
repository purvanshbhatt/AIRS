"""Integration service for API keys, webhooks, and external data contracts."""

import hashlib
import hmac
import ipaddress
import json
import secrets
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.frameworks import get_framework_refs
from app.core.logging import event_logger
from app.db.database import SessionLocal
from app.models.api_key import ApiKey
from app.models.assessment import Assessment, AssessmentStatus
from app.models.external_finding import ExternalFinding
from app.models.finding import Finding
from app.models.organization import Organization
from app.models.webhook import Webhook
from app.services.audit import record_audit_event
from app.services.assessment import AssessmentService

DEFAULT_SCOPE = "scores:read"
EVENT_ASSESSMENT_SCORED = "assessment.scored"

MOCK_SPLUNK_FINDINGS = [
    ("Missing EDR coverage on AI training nodes", "critical"),
    ("No AI model access logging in production environment", "high"),
    ("No incident playbook for prompt injection response", "high"),
    ("Unapproved model artifact downloaded to unmanaged endpoint", "high"),
    ("Privileged model registry token used from atypical location", "medium"),
    ("Sensitive prompt dataset exported to external storage", "critical"),
    ("Inference API experiencing sustained authentication failures", "medium"),
    ("LLM gateway requests bypassing content safety controls", "high"),
    ("Service account granted admin role outside change window", "high"),
    ("Telemetry gap detected for model-serving audit events", "medium"),
]


def _json_load_list(raw: Optional[str], fallback: Optional[List[str]] = None) -> List[str]:
    if not raw:
        return fallback or []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return fallback or []


def _json_dump_list(values: List[str]) -> str:
    return json.dumps(values or [])


def hash_api_key(plaintext_key: str) -> str:
    return hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()


def generate_api_key_plaintext() -> str:
    return f"airs_live_{secrets.token_urlsafe(32)}"


class IntegrationService:
    """Org-scoped integration operations."""

    def __init__(self, db: Session, owner_uid: Optional[str] = None):
        self.db = db
        self.owner_uid = owner_uid

    def _get_org_for_owner(self, org_id: str) -> Optional[Organization]:
        q = self.db.query(Organization).filter(Organization.id == org_id)
        if self.owner_uid:
            q = q.filter(Organization.owner_uid == self.owner_uid)
        return q.first()

    def assert_org_owned(self, org_id: str) -> Organization:
        org = self._get_org_for_owner(org_id)
        if not org:
            raise ValueError(f"Organization not found: {org_id}")
        return org

    def resolve_org(self, org_id: Optional[str] = None) -> Organization:
        """Resolve org by explicit id or fallback to caller's most recent org."""
        if org_id:
            return self.assert_org_owned(org_id)

        q = self.db.query(Organization)
        if self.owner_uid:
            q = q.filter(Organization.owner_uid == self.owner_uid)
        org = q.order_by(Organization.created_at.desc()).first()
        if not org:
            raise ValueError("No organization found for this user")
        return org

    def create_api_key(self, org_id: str, scopes: Optional[List[str]] = None) -> Dict[str, Any]:
        self.assert_org_owned(org_id)

        scope_list = list(dict.fromkeys(scopes or [DEFAULT_SCOPE]))
        plaintext = generate_api_key_plaintext()
        hashed = hash_api_key(plaintext)

        key = ApiKey(
            owner_org_id=org_id,
            key_hash=hashed,
            prefix=plaintext[:20],
            scopes=_json_dump_list(scope_list),
            is_active=True,
        )
        self.db.add(key)
        self.db.commit()
        self.db.refresh(key)

        return {
            "id": key.id,
            "org_id": org_id,
            "prefix": key.prefix,
            "scopes": scope_list,
            "api_key": plaintext,
            "created_at": key.created_at,
        }

    def list_api_keys(self, org_id: str) -> List[Dict[str, Any]]:
        self.assert_org_owned(org_id)
        rows = (
            self.db.query(ApiKey)
            .filter(ApiKey.owner_org_id == org_id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )
        return [
            {
                "id": row.id,
                "org_id": row.owner_org_id,
                "prefix": row.prefix,
                "scopes": _json_load_list(row.scopes, [DEFAULT_SCOPE]),
                "is_active": row.is_active,
                "created_at": row.created_at,
                "last_used_at": row.last_used_at,
            }
            for row in rows
        ]

    def deactivate_api_key(self, key_id: str) -> bool:
        row = self.db.query(ApiKey).filter(ApiKey.id == key_id).first()
        if not row:
            return False

        org = self._get_org_for_owner(row.owner_org_id)
        if not org:
            return False

        row.is_active = False
        self.db.commit()
        return True

    def create_webhook(
        self,
        org_id: str,
        url: str,
        event_types: Optional[List[str]] = None,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.assert_org_owned(org_id)

        events = list(dict.fromkeys(event_types or [EVENT_ASSESSMENT_SCORED]))
        webhook = Webhook(
            org_id=org_id,
            url=url,
            event_types=_json_dump_list(events),
            secret=secret,
            is_active=True,
        )
        self.db.add(webhook)
        self.db.commit()
        self.db.refresh(webhook)

        return {
            "id": webhook.id,
            "org_id": webhook.org_id,
            "url": webhook.url,
            "event_types": events,
            "is_active": webhook.is_active,
            "created_at": webhook.created_at,
        }

    def list_webhooks(self, org_id: str) -> List[Dict[str, Any]]:
        self.assert_org_owned(org_id)
        hooks = (
            self.db.query(Webhook)
            .filter(Webhook.org_id == org_id)
            .order_by(Webhook.created_at.desc())
            .all()
        )
        return [
            {
                "id": hook.id,
                "org_id": hook.org_id,
                "url": hook.url,
                "event_types": _json_load_list(hook.event_types, [EVENT_ASSESSMENT_SCORED]),
                "is_active": hook.is_active,
                "created_at": hook.created_at,
            }
            for hook in hooks
        ]

    def delete_webhook(self, webhook_id: str) -> bool:
        hook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not hook:
            return False
        org = self._get_org_for_owner(hook.org_id)
        if not org:
            return False
        hook.is_active = False
        self.db.commit()
        return True

    def get_webhook_for_owner(self, webhook_id: str) -> Optional[Webhook]:
        hook = self.db.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not hook:
            return None
        org = self._get_org_for_owner(hook.org_id)
        if not org:
            return None
        return hook

    def seed_mock_splunk_findings(self, org_id: Optional[str] = None) -> Dict[str, Any]:
        org = self.resolve_org(org_id)
        created = 0

        for index, (title, severity) in enumerate(MOCK_SPLUNK_FINDINGS, start=1):
            raw = {
                "vendor": "splunk",
                "alert_id": f"splunk-{index:03d}",
                "title": title,
                "severity": severity,
                "confidence": 0.78,
                "status": "new",
            }
            finding = ExternalFinding(
                org_id=org.id,
                source="splunk",
                title=title,
                severity=severity,
                raw_json=raw,
            )
            self.db.add(finding)
            created += 1

        # Mark the mock integration connected for demo visibility.
        try:
            integration_status = json.loads(org.integration_status or "{}")
        except Exception:
            integration_status = {}
        integration_status["splunk"] = {
            "connected": True,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
        org.integration_status = json.dumps(integration_status)

        self.db.commit()

        return {
            "org_id": org.id,
            "source": "splunk",
            "inserted": created,
            "connected": True,
        }

    def list_external_findings(
        self,
        source: str = "splunk",
        limit: int = 50,
        org_id: Optional[str] = None,
    ) -> List[ExternalFinding]:
        org = self.resolve_org(org_id)
        return (
            self.db.query(ExternalFinding)
            .filter(ExternalFinding.org_id == org.id, ExternalFinding.source == source)
            .order_by(ExternalFinding.created_at.desc())
            .limit(max(1, min(limit, 200)))
            .all()
        )


def validate_api_key(db: Session, plaintext_key: str, required_scopes: Optional[List[str]] = None) -> Optional[ApiKey]:
    hashed = hash_api_key(plaintext_key)
    row = db.query(ApiKey).filter(ApiKey.key_hash == hashed, ApiKey.is_active == True).first()
    if not row:
        return None

    scopes = set(_json_load_list(row.scopes, [DEFAULT_SCOPE]))
    expected = set(required_scopes or [])
    if expected and not expected.issubset(scopes):
        return None

    row.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return row


def _sign_payload(secret: Optional[str], payload: str) -> Optional[str]:
    if not secret:
        return None
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


# ---- SSRF protection ----

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private RFC-1918
    ipaddress.ip_network("172.16.0.0/12"),      # Private RFC-1918
    ipaddress.ip_network("192.168.0.0/16"),     # Private RFC-1918
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]


def _validate_webhook_url(url: str) -> str:
    """Validate a webhook URL is safe to call (anti-SSRF).
    
    Rules:
      - Must use https:// scheme (http:// blocked in production)
      - Hostname must not resolve to a private/loopback/link-local IP
      - Blocks cloud metadata endpoints (169.254.169.254)
    
    Returns the validated URL or raises ValueError.
    """
    parsed = urlparse(url)

    # Scheme check
    if parsed.scheme not in ("https",):
        raise ValueError(f"Webhook URL must use HTTPS: {url}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError(f"Webhook URL has no hostname: {url}")

    # Resolve hostname to IPs and check each
    try:
        results = socket.getaddrinfo(hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError(f"Cannot resolve webhook hostname: {hostname}")

    for _, _, _, _, sockaddr in results:
        ip = ipaddress.ip_address(sockaddr[0])
        for net in _BLOCKED_NETWORKS:
            if ip in net:
                raise ValueError(
                    f"Webhook URL resolves to blocked private/internal address ({ip})"
                )

    return url


def deliver_webhook(webhook: Webhook, event_type: str, payload: Dict[str, Any]) -> Tuple[bool, Optional[int], Optional[str]]:
    body = json.dumps(payload)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "airs-webhook/1.0",
        "X-AIRS-Event": event_type,
    }
    signature = _sign_payload(webhook.secret, body)
    if signature:
        headers["X-AIRS-Signature"] = signature

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook.url, content=body, headers=headers)
        if 200 <= response.status_code < 300:
            return True, response.status_code, None
        return False, response.status_code, f"HTTP {response.status_code}: {response.text[:180]}"
    except Exception as exc:
        return False, None, str(exc)


def deliver_webhook_url_test(
    url: str,
    event_type: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
) -> Tuple[bool, Optional[int], Optional[str]]:
    """Send a direct webhook test payload to a provided URL.
    
    Validates the URL against SSRF before making the outbound call.
    """
    try:
        url = _validate_webhook_url(url)
    except ValueError as exc:
        return False, None, f"URL validation failed: {exc}"

    temp_webhook = Webhook(url=url, secret=secret, event_types='["assessment.scored"]', org_id="test-org")
    return deliver_webhook(temp_webhook, event_type, payload)


def dispatch_assessment_scored_webhooks(org_id: str, payload: Dict[str, Any]) -> None:
    """Background task entrypoint: delivers scoring events with simple retry/backoff."""
    db = SessionLocal()
    try:
        webhooks = (
            db.query(Webhook)
            .filter(Webhook.org_id == org_id, Webhook.is_active == True)
            .all()
        )
        for hook in webhooks:
            events = set(_json_load_list(hook.event_types, [EVENT_ASSESSMENT_SCORED]))
            if EVENT_ASSESSMENT_SCORED not in events:
                continue

            success = False
            error: Optional[str] = None
            status_code: Optional[int] = None
            for attempt in range(3):
                ok, status_code, error = deliver_webhook(hook, EVENT_ASSESSMENT_SCORED, payload)
                if ok:
                    success = True
                    break
                time.sleep(2 ** attempt)

            if success:
                record_audit_event(
                    db=db,
                    org_id=org_id,
                    action="webhook.triggered",
                    actor="system:webhook-dispatch",
                )
                event_logger._log_event(
                    level=20,
                    event="webhook.delivered",
                    webhook_id=hook.id,
                    org_id=org_id,
                    assessment_id=payload.get("assessment_id"),
                    status_code=status_code,
                )
            else:
                record_audit_event(
                    db=db,
                    org_id=org_id,
                    action="webhook.trigger_failed",
                    actor="system:webhook-dispatch",
                )
                event_logger._log_event(
                    level=40,
                    event="webhook.delivery_failed",
                    webhook_id=hook.id,
                    org_id=org_id,
                    assessment_id=payload.get("assessment_id"),
                    status_code=status_code,
                    error=error,
                )
    finally:
        db.close()


def build_external_latest_score_payload(db: Session, org_id: str) -> Optional[Dict[str, Any]]:
    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.organization_id == org_id,
            Assessment.status == AssessmentStatus.COMPLETED,
            Assessment.overall_score.isnot(None),
        )
        .order_by(Assessment.completed_at.desc().nullslast(), Assessment.created_at.desc())
        .first()
    )
    if not assessment:
        return None

    summary = AssessmentService(db).get_summary(assessment.id)
    if not summary:
        return None

    top_findings = []
    for finding in summary.get("findings", [])[:5]:
        refs = finding.get("framework_refs") or get_framework_refs(finding.get("rule_id") or "")
        top_findings.append(
            {
                "id": finding.get("id"),
                "title": finding.get("title"),
                "severity": finding.get("severity"),
                "framework_refs": refs,
            }
        )

    return {
        "org_id": org_id,
        "assessment_id": assessment.id,
        "timestamp": assessment.completed_at or assessment.updated_at or assessment.created_at,
        "overall_score": float(assessment.overall_score or 0),
        "risk_summary": summary.get("analytics", {}).get("risk_summary", {}),
        "top_findings": top_findings,
    }
