"""
Network topology builder — turns what the connectors actually observed into a
graph the Network page can draw.

Nothing here is invented. Every node comes from one of three real sources:

  1. Connector rows (``ConnectorManager.list_connectors``) — what the org has
     plugged in.
  2. Discovered host assets (``HostAsset``) — what the discovery services
     wrote after talking to AWS / Microsoft Graph.
  3. Recent telemetry events (``TelemetryEvent`` rows, or the recorded demo
     telemetry for explicit demo organizations) — Security Hub findings, AWS
     inventory snapshots, Microsoft Intune/Entra telemetry, Veeam backup jobs
     and IAM credential reports.

Edges describe real relationships: a connector ``monitors`` the resources it
reported, an identity provider ``authenticates`` the identities it manages,
the backup connector ``backs_up`` a protected system, and the synthetic
``internet`` node is ``exposed_to_internet`` to a resource whose security
group (or public IP) lets 0.0.0.0/0 in.

An organization with nothing connected yields an empty graph with
``summary.empty = True`` so the UI can say so in plain English.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("airs.services.network_topology")

INTERNET_NODE_ID = "internet"

# Node / edge vocabulary shared with the frontend.
NODE_TYPES = ("connector", "server", "workstation", "database", "bucket", "identity", "security_group", "internet")
ZONES = ("internet", "cloud", "security", "servers", "workstations", "data", "backups", "identity")
STATUSES = ("healthy", "warning", "attention", "error", "unknown")
EDGE_KINDS = ("monitors", "backs_up", "authenticates", "exposed_to_internet")

# Connector types that are "cloud platforms" rather than security tooling.
_CLOUD_CONNECTOR_TYPES = {
    "aws", "aws_bedrock", "gcp_scc", "azure_openai", "vertex_ai", "github", "gitlab", "veeam",
}
# Connector types that manage identities (produce ``authenticates`` edges).
_IDENTITY_CONNECTOR_TYPES = {"okta", "microsoft", "duo", "aws"}

_HIGH_SEVERITIES = {"high", "critical"}

_CONNECTOR_LABELS = {
    "aws_security_hub": "AWS Security Hub",
    "aws": "Amazon Web Services",
    "microsoft": "Microsoft 365",
    "veeam": "Veeam Backup",
    "okta": "Okta",
    "duo": "Duo",
    "wazuh": "Wazuh",
    "splunk": "Splunk",
    "crowdstrike": "CrowdStrike",
    "github": "GitHub",
    "gitlab": "GitLab",
    "gcp_scc": "Google Cloud Security Command Center",
    "azure_security_center": "Microsoft Defender for Cloud",
    "webhook": "Webhook feed",
}


def _lower(value: Any) -> str:
    return str(value or "").lower()


def _severity_status(severity: str) -> str:
    sev = _lower(severity)
    if sev in _HIGH_SEVERITIES:
        return "attention"
    if sev in ("medium", "low"):
        return "warning"
    return "healthy"


_STATUS_RANK = {"unknown": 0, "healthy": 1, "warning": 2, "attention": 3, "error": 3}


def _worse(current: str, candidate: str) -> str:
    return candidate if _STATUS_RANK.get(candidate, 0) > _STATUS_RANK.get(current, 0) else current


def zone_for_hint(hint: str, default: str = "servers") -> str:
    """Map a free-text role / hostname / type hint onto a zone."""
    h = _lower(hint)
    if any(k in h for k in ("workstation", "laptop", "desktop", "front-desk", "frontdesk", "pc", "macbook", "surface")):
        return "workstations"
    if any(k in h for k in ("backup", "veeam", "vault", "recovery")):
        return "backups"
    if any(k in h for k in ("db", "database", "rds", "sql", "postgres", "mysql", "dms", "records", "s3", "bucket")):
        return "data"
    if any(k in h for k in ("user", "identity", "role", "iam", "account")):
        return "identity"
    return default


def type_for_hint(hint: str, default: str = "server") -> str:
    h = _lower(hint)
    if any(k in h for k in ("workstation", "laptop", "desktop", "front-desk", "frontdesk", "macbook", "surface")):
        return "workstation"
    if any(k in h for k in ("rds", "database", "db-", "-db", "sql", "postgres", "mysql")):
        return "database"
    if "s3" in h or "bucket" in h:
        return "bucket"
    if any(k in h for k in ("iam", "user", "role")):
        return "identity"
    return default


def connector_zone(connector_type: str) -> str:
    return "cloud" if _lower(connector_type) in _CLOUD_CONNECTOR_TYPES else "security"


def connector_label(connector_type: str) -> str:
    return _CONNECTOR_LABELS.get(_lower(connector_type), str(connector_type).replace("_", " ").title())


def _connector_status(status: str, health: str) -> str:
    s, h = _lower(status), _lower(health)
    if s == "error" or h == "down":
        return "error"
    if s in ("pending_auth", "inactive") or h == "degraded":
        return "warning"
    if s in ("active", "syncing") or h == "healthy":
        return "healthy"
    return "unknown"


def parse_arn(arn: str) -> Optional[Dict[str, str]]:
    """Return {service, resource_type, resource_id, region, account} for an AWS ARN."""
    if not isinstance(arn, str) or not arn.startswith("arn:"):
        return None
    parts = arn.split(":", 5)
    if len(parts) < 6:
        return None
    _, _, service, region, account, resource = parts
    if "/" in resource:
        rtype, rid = resource.split("/", 1)
    elif ":" in resource:
        rtype, rid = resource.split(":", 1)
    else:
        rtype, rid = ("bucket" if service == "s3" else service), resource
    return {"service": service, "resource_type": rtype, "resource_id": rid, "region": region, "account": account}


class TopologyBuilder:
    """Accumulates nodes/edges, merging duplicates and keeping the worst status."""

    def __init__(self, org_id: str):
        self.org_id = org_id
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: Dict[tuple, Dict[str, Any]] = {}
        self._connector_by_type: Dict[str, str] = {}
        self._bare: Dict[str, bool] = {}
        self._source_count = 0

    # -- nodes ---------------------------------------------------------------

    def add_node(
        self,
        node_id: str,
        *,
        type: str,
        label: str,
        zone: str,
        status: str = "unknown",
        sublabel: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        bare: bool = False,
    ) -> Dict[str, Any]:
        """``bare`` marks a node known only from an ARN in a finding; a later
        inventory record (name, role, zone) overrides its placeholder fields."""
        node = self.nodes.get(node_id)
        if node is None:
            node = {
                "id": node_id,
                "type": type,
                "label": label or node_id,
                "sublabel": sublabel,
                "status": status,
                "zone": zone,
                "meta": {"issues": [], "seen_by": [], "last_seen": None},
            }
            self._bare[node_id] = bare
            self.nodes[node_id] = node
        else:
            if self._bare.get(node_id) and not bare:
                node["label"] = label or node["label"]
                node["type"] = type
                node["zone"] = zone
                node["sublabel"] = sublabel or node.get("sublabel")
                self._bare[node_id] = False
            elif sublabel and not node.get("sublabel"):
                node["sublabel"] = sublabel
            node["status"] = _worse(node["status"], status)
        if meta:
            for key, value in meta.items():
                if key in ("issues", "seen_by"):
                    for item in value or []:
                        if item not in node["meta"][key]:
                            node["meta"][key].append(item)
                elif key == "last_seen":
                    node["meta"]["last_seen"] = _newest(node["meta"].get("last_seen"), value)
                elif value is not None:
                    node["meta"][key] = value
        return node

    def mark_issue(self, node_id: str, title: str, severity: str, seen_at: Optional[str] = None) -> None:
        node = self.nodes.get(node_id)
        if not node:
            return
        issue = {"title": title, "severity": _lower(severity) or "unknown"}
        if issue not in node["meta"]["issues"]:
            node["meta"]["issues"].append(issue)
        node["status"] = _worse(node["status"], _severity_status(severity))
        if seen_at:
            node["meta"]["last_seen"] = _newest(node["meta"].get("last_seen"), seen_at)

    # -- edges ---------------------------------------------------------------

    def add_edge(self, source: str, target: str, kind: str, label: Optional[str] = None) -> None:
        if not source or not target or source == target:
            return
        if source not in self.nodes or target not in self.nodes:
            return
        key = (source, target, kind)
        if key not in self.edges:
            self.edges[key] = {"source": source, "target": target, "kind": kind, "label": label or kind.replace("_", " ")}

    # -- connectors ----------------------------------------------------------

    def add_connector(self, connector: Any) -> str:
        """Register a real connector row (ORM object or dict)."""
        ctype = _enum_value(_get(connector, "connector_type"))
        cid = str(_get(connector, "id") or f"connector:{ctype}")
        node_id = f"connector:{cid}"
        status = _connector_status(_enum_value(_get(connector, "status")), _get(connector, "health_status"))
        last_sync = _get(connector, "last_sync_at")
        self.add_node(
            node_id,
            type="connector",
            label=_get(connector, "display_name") or connector_label(ctype),
            sublabel=connector_label(ctype),
            zone=connector_zone(ctype),
            status=status,
            meta={
                "connector_type": ctype,
                "connector_id": cid,
                "last_seen": _iso(last_sync),
                "error_message": _get(connector, "error_message"),
            },
        )
        self._connector_by_type.setdefault(ctype, node_id)
        self._source_count += 1
        return node_id

    def connector_for_source(self, source_system: str) -> str:
        """Resolve the connector node that produced a telemetry event.

        Real orgs: the registered connector of that type. Otherwise (demo orgs,
        manually injected events) a virtual connector node keyed by source.
        """
        src = _lower(source_system) or "unknown"
        aliases = {"aws_securityhub": "aws_security_hub", "securityhub": "aws_security_hub", "msgraph": "microsoft"}
        src = aliases.get(src, src)
        if src in self._connector_by_type:
            return self._connector_by_type[src]
        # AWS Security Hub findings are also produced by the plain AWS connector.
        if src == "aws_security_hub" and "aws" in self._connector_by_type:
            return self._connector_by_type["aws"]
        if src == "aws" and "aws_security_hub" in self._connector_by_type:
            return self._connector_by_type["aws_security_hub"]
        node_id = f"connector:{src}"
        self.add_node(
            node_id,
            type="connector",
            label=connector_label(src),
            sublabel="Connected system",
            zone=connector_zone(src),
            status="healthy",
            meta={"connector_type": src, "virtual": True},
        )
        self._connector_by_type[src] = node_id
        return node_id

    # -- assets --------------------------------------------------------------

    def add_host_asset(self, asset: Any) -> str:
        hostname = _get(asset, "hostname") or ""
        asset_type = _enum_value(_get(asset, "asset_type"))
        aid = str(_get(asset, "id") or hostname)
        hint = f"{hostname} {asset_type}"
        ntype = type_for_hint(hint, "identity" if asset_type == "IAM" else "server")
        zone = zone_for_hint(hint, "identity" if asset_type == "IAM" else "servers")
        node_id = f"asset:{aid}"
        provider = _get(asset, "cloud_provider")
        self.add_node(
            node_id,
            type=ntype,
            label=hostname or aid,
            sublabel=" · ".join(x for x in (provider, _get(asset, "operating_system")) if x) or asset_type,
            zone=zone,
            status="healthy",
            meta={
                "asset_type": asset_type,
                "ip_address": _get(asset, "ip_address"),
                "cloud_provider": provider,
                "operating_system": _get(asset, "operating_system"),
                "last_seen": _iso(_get(asset, "last_seen")),
                "seen_by": ["discovery"],
            },
        )
        connector_type = "aws" if _lower(provider) == "aws" else ("microsoft" if asset_type == "HOST" else None)
        if connector_type:
            cnode = self.connector_for_source(connector_type)
            self.add_edge(cnode, node_id, "monitors")
        return node_id

    # -- telemetry -----------------------------------------------------------

    def add_events(self, events: Iterable[Any]) -> None:
        for event in events or []:
            try:
                self._add_event(event)
            except Exception as exc:  # one bad payload must not sink the map
                logger.debug("Skipping telemetry event for topology: %s", exc)

    def _add_event(self, event: Any) -> None:
        event_type = _lower(_get(event, "event_type"))
        source = _get(event, "source_system") or ""
        payload = _get(event, "payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        seen_at = _iso(_get(event, "timestamp") or _get(event, "created_at") or payload.get("updated_at") or payload.get("created_at"))

        if event_type == "aws.securityhub.finding":
            self._add_securityhub_finding(source, payload, seen_at)
        elif event_type == "aws.inventory.snapshot":
            self._add_aws_inventory(source, payload, seen_at)
        elif event_type == "microsoft.telemetry":
            self._add_microsoft(source, payload, seen_at)
        elif event_type == "veeam.backup_job":
            self._add_backup_job(source, payload, seen_at)
        elif event_type == "aws.iam.credential_report":
            self._add_iam_report(source, payload, seen_at)

    def _add_securityhub_finding(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> None:
        cnode = self.connector_for_source(source or "aws_security_hub")
        title = payload.get("title") or "Security finding"
        severity = payload.get("severity_label") or payload.get("severity") or "medium"
        blob = _lower(json.dumps({"t": title, "d": payload.get("description")}))
        unrestricted = "0.0.0.0/0" in blob or "::/0" in blob or "unrestricted" in blob or "open to the internet" in blob
        for arn in payload.get("resources") or []:
            node_id = self._node_from_arn(arn, seen_at)
            if not node_id:
                continue
            self.mark_issue(node_id, title, severity, seen_at)
            self.add_edge(cnode, node_id, "monitors")
            node = self.nodes[node_id]
            node["meta"]["seen_by"] = _unique(node["meta"]["seen_by"] + [connector_label(source or "aws_security_hub")])
            if unrestricted and node["type"] in ("security_group", "server", "database", "bucket"):
                self._ensure_internet()
                self.add_edge(INTERNET_NODE_ID, node_id, "exposed_to_internet", "open to the internet")
                node["meta"]["internet_exposed"] = True

    def _add_aws_inventory(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> None:
        cnode = self.connector_for_source(source or "aws")
        for res in payload.get("resources") or []:
            kind = _lower(res.get("kind") or res.get("type"))
            name = res.get("name") or res.get("instance_id") or res.get("identifier") or res.get("bucket") or "resource"
            hint = f"{kind} {res.get('role') or ''} {name}"
            if kind in ("ec2_instance", "instance", "ec2"):
                rid = res.get("instance_id") or name
                node_id = f"aws:instance:{rid}"
                ntype = type_for_hint(hint, "server")
                zone = zone_for_hint(hint, "servers")
            elif kind in ("rds_instance", "rds", "db_instance", "database"):
                rid = res.get("identifier") or res.get("db_instance_identifier") or name
                node_id = f"aws:db:{rid}"
                ntype, zone = "database", "data"
            elif kind in ("s3_bucket", "bucket", "s3"):
                rid = res.get("bucket") or name
                node_id = f"aws:bucket:{rid}"
                ntype, zone = "bucket", "data"
            else:
                node_id = f"aws:{kind or 'resource'}:{name}"
                ntype = type_for_hint(hint, "server")
                zone = zone_for_hint(hint, "servers")
            state = res.get("state")
            sub_bits = [res.get("role"), res.get("instance_type"), res.get("platform"), res.get("engine")]
            self.add_node(
                node_id,
                type=ntype,
                label=str(name),
                sublabel=" · ".join(str(b) for b in sub_bits if b) or None,
                zone=zone,
                status="healthy" if _lower(state) in ("", "running", "available") else "warning",
                meta={
                    "resource_id": res.get("instance_id") or res.get("identifier") or res.get("bucket"),
                    "role": res.get("role"),
                    "department": res.get("department"),
                    "state": state,
                    "instance_type": res.get("instance_type"),
                    "platform": res.get("platform"),
                    "private_ip": res.get("private_ip"),
                    "public_ip": res.get("public_ip"),
                    "ssm_managed": res.get("ssm_managed"),
                    "imdsv2": res.get("imdsv2"),
                    "ebs_encrypted": res.get("ebs_encrypted"),
                    "last_seen": seen_at,
                    "seen_by": [connector_label(source or "aws")],
                },
            )
            self.add_edge(cnode, node_id, "monitors")
            if res.get("public_ip"):
                self._ensure_internet()
                self.add_edge(INTERNET_NODE_ID, node_id, "exposed_to_internet", "public IP")
                self.nodes[node_id]["meta"]["internet_exposed"] = True
            # A backup-role server is the thing the backups land on.
            if zone == "backups":
                veeam = self._connector_by_type.get("veeam")
                if veeam:
                    self.add_edge(veeam, node_id, "backs_up", "stores backups")

    def _add_microsoft(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> None:
        cnode = self.connector_for_source(source or "microsoft")
        alerts_by_device: Dict[str, List[Dict[str, Any]]] = {}
        for alert in payload.get("defender_alerts") or []:
            alerts_by_device.setdefault(str(alert.get("device_id")), []).append(alert)

        for device in payload.get("intune_devices") or []:
            did = device.get("device_id") or device.get("device_name")
            node_id = f"ms:device:{did}"
            name = device.get("device_name") or str(did)
            compliance = _lower(device.get("compliance_state"))
            status = "warning" if compliance == "noncompliant" else "healthy"
            self.add_node(
                node_id,
                type=type_for_hint(name, "workstation"),
                label=name,
                sublabel=f"Intune · {device.get('os_version')}" if device.get("os_version") else "Intune managed device",
                zone="workstations",
                status=status,
                meta={
                    "compliance_state": device.get("compliance_state"),
                    "bitlocker_status": device.get("bitlocker_status"),
                    "os_version": device.get("os_version"),
                    "last_seen": seen_at,
                    "seen_by": [connector_label(source or "microsoft")],
                },
            )
            if compliance == "noncompliant":
                self.mark_issue(node_id, "Device is not compliant with the security baseline", "medium", seen_at)
            if _lower(device.get("bitlocker_status")) in ("not_encrypted", "off", "disabled"):
                self.mark_issue(node_id, "Disk is not encrypted", "medium", seen_at)
            for alert in alerts_by_device.get(str(did), []):
                self.mark_issue(node_id, alert.get("title") or "Defender alert", alert.get("severity") or "high", seen_at)
            self.add_edge(cnode, node_id, "monitors")

        for user in payload.get("entra_users") or []:
            uid = user.get("user_id") or user.get("user_principal_name")
            node_id = f"ms:user:{uid}"
            upn = user.get("user_principal_name") or str(uid)
            self.add_node(
                node_id,
                type="identity",
                label=upn,
                sublabel="Entra ID account",
                zone="identity",
                status="healthy",
                meta={
                    "mfa_enforced": user.get("mfa_enforced"),
                    "account_enabled": user.get("account_enabled"),
                    "last_sign_in": user.get("last_sign_in"),
                    "last_seen": user.get("last_sign_in") or seen_at,
                    "seen_by": [connector_label(source or "microsoft")],
                },
            )
            if user.get("mfa_enforced") is False:
                self.mark_issue(node_id, "Multi-factor authentication is not enforced", "high", seen_at)
            if _is_stale(user.get("last_sign_in")) and user.get("account_enabled", True):
                self.mark_issue(node_id, "Account still enabled but unused for 30+ days", "medium", seen_at)
            self.add_edge(cnode, node_id, "authenticates")

    def _add_iam_report(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> None:
        cnode = self.connector_for_source(source or "aws")
        for user in payload.get("iam_users") or []:
            name = user.get("user_name") or user.get("display_name") or user.get("user_id")
            node_id = f"aws:iam:{name}"
            is_root = _lower(name) == "<root_account>"
            self.add_node(
                node_id,
                type="identity",
                label="AWS root account" if is_root else (user.get("display_name") or str(name)),
                sublabel="Account owner login" if is_root else "AWS IAM user",
                zone="identity",
                status="healthy",
                meta={
                    "mfa_enforced": user.get("mfa_enforced"),
                    "access_key_active": user.get("access_key_active"),
                    "last_sign_in": user.get("last_sign_in"),
                    "last_seen": seen_at,
                    "seen_by": [connector_label(source or "aws")],
                },
            )
            if user.get("mfa_enforced") is False:
                self.mark_issue(node_id, "No multi-factor authentication on this account", "high", seen_at)
            self.add_edge(cnode, node_id, "authenticates")

    def _add_backup_job(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> None:
        cnode = self.connector_for_source(source or "veeam")
        system = payload.get("system_name") or payload.get("vm_name") or "Protected system"
        node_id = self._find_node_by_label(system) or f"system:{_slug(system)}"
        last_ok = payload.get("last_successful_backup")
        stale = _older_than(last_ok, hours=24)
        self.add_node(
            node_id,
            type=type_for_hint(system, "server"),
            label=system,
            sublabel="Protected by backups",
            zone=zone_for_hint(system, "servers"),
            status="healthy",
            meta={
                "last_successful_backup": last_ok,
                "backup_type": payload.get("backup_type"),
                "last_seen": seen_at,
                "seen_by": [connector_label(source or "veeam")],
            },
        )
        if stale:
            self.mark_issue(node_id, "Last good backup is more than 24 hours old", "high", seen_at)
        self.add_edge(cnode, node_id, "backs_up")

    # -- helpers -------------------------------------------------------------

    def _node_from_arn(self, arn: str, seen_at: Optional[str]) -> Optional[str]:
        parsed = parse_arn(arn)
        if not parsed:
            return None
        service, rtype, rid = parsed["service"], parsed["resource_type"], parsed["resource_id"]
        if service == "ec2" and rtype == "instance":
            node_id, ntype, zone, label, sub = f"aws:instance:{rid}", "server", "servers", rid, "EC2 instance"
        elif service == "ec2" and rtype == "security-group":
            node_id, ntype, zone, label, sub = f"aws:sg:{rid}", "security_group", "cloud", rid, "Security group (firewall rules)"
        elif service == "s3":
            node_id, ntype, zone, label, sub = f"aws:bucket:{rid}", "bucket", "data", rid, "S3 bucket"
        elif service == "rds":
            node_id, ntype, zone, label, sub = f"aws:db:{rid}", "database", "data", rid, "RDS database"
        elif service == "iam":
            node_id, ntype, zone, label, sub = f"aws:iam:{rid.split('/')[-1]}", "identity", "identity", rid.split("/")[-1], f"IAM {rtype}"
        else:
            # Account-level controls (Config, CloudTrail, ...) attach to the connector, not a box on the map.
            return None
        self.add_node(node_id, type=ntype, label=label, sublabel=sub, zone=zone, status="healthy", meta={"arn": arn, "last_seen": seen_at}, bare=True)
        return node_id

    def _ensure_internet(self) -> None:
        self.add_node(
            INTERNET_NODE_ID,
            type="internet",
            label="Internet",
            sublabel="Anyone, anywhere",
            zone="internet",
            status="unknown",
        )

    def _find_node_by_label(self, label: str) -> Optional[str]:
        target = _lower(label)
        for node_id, node in self.nodes.items():
            if _lower(node["label"]) == target:
                return node_id
        return None

    # -- output --------------------------------------------------------------

    def build(self) -> Dict[str, Any]:
        nodes = list(self.nodes.values())
        edges = list(self.edges.values())
        summary = self._summary(nodes, edges)
        return {
            "nodes": nodes,
            "edges": edges,
            "summary": summary,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _summary(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not nodes:
            return {
                "empty": True,
                "hint": "connect a system",
                "node_count": 0,
                "edge_count": 0,
                "connectors": 0,
                "attention": 0,
                "internet_exposed": 0,
                "by_type": {},
                "by_zone": {},
                "by_status": {},
            }
        return {
            "empty": False,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "connectors": sum(1 for n in nodes if n["type"] == "connector"),
            "attention": sum(1 for n in nodes if n["status"] in ("attention", "error")),
            "internet_exposed": sum(1 for e in edges if e["kind"] == "exposed_to_internet"),
            "by_type": dict(Counter(n["type"] for n in nodes)),
            "by_zone": dict(Counter(n["zone"] for n in nodes)),
            "by_status": dict(Counter(n["status"] for n in nodes)),
        }


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def build_topology(
    org_id: str,
    *,
    connectors: Iterable[Any] = (),
    assets: Iterable[Any] = (),
    events: Iterable[Any] = (),
) -> Dict[str, Any]:
    """Pure builder: connectors + discovered assets + telemetry → graph dict."""
    builder = TopologyBuilder(org_id)
    for connector in connectors or []:
        builder.add_connector(connector)
    for asset in assets or []:
        builder.add_host_asset(asset)
    builder.add_events(events)
    return builder.build()


def build_topology_for_org(db, org_id: str, *, demo: bool = False, lookback_days: int = 7) -> Dict[str, Any]:
    """Load the real sources for ``org_id`` from the database and build the graph.

    Demo orgs replay the recorded demo telemetry instead of DB telemetry rows;
    they never get hardcoded node lists.
    """
    connectors: List[Any] = []
    assets: List[Any] = []
    events: List[Any] = []

    try:
        from app.services.connector_manager import ConnectorManager
        connectors = ConnectorManager(db, org_id).list_connectors()
    except Exception as exc:
        logger.warning("Topology: could not list connectors for %s: %s", org_id, exc)

    if demo:
        try:
            from app.api.clinic.router import get_demo_telemetry
            events = get_demo_telemetry(org_id)
        except Exception as exc:
            logger.warning("Topology: demo telemetry unavailable for %s: %s", org_id, exc)
    else:
        try:
            from app.models.discovery import HostAsset
            assets = db.query(HostAsset).filter(HostAsset.org_id == org_id).all()
        except Exception as exc:
            logger.warning("Topology: could not load host assets for %s: %s", org_id, exc)
        try:
            from app.models.telemetry_event import TelemetryEvent
            cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
            events = (
                db.query(TelemetryEvent)
                .filter(TelemetryEvent.org_id == org_id, TelemetryEvent.created_at >= cutoff)
                .order_by(TelemetryEvent.created_at.desc())
                .limit(1000)
                .all()
            )
        except Exception as exc:
            logger.warning("Topology: could not load telemetry for %s: %s", org_id, exc)

    return build_topology(org_id, connectors=connectors, assets=assets, events=events)


# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------

def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _enum_value(value: Any) -> str:
    if value is None:
        return ""
    return str(getattr(value, "value", value))


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _newest(a: Optional[str], b: Optional[str]) -> Optional[str]:
    da, db_ = _parse_dt(a), _parse_dt(b)
    if da and db_:
        return a if da >= db_ else b
    return a or b


def _older_than(value: Any, *, hours: int) -> bool:
    dt = _parse_dt(value)
    if dt is None:
        return bool(value) is False  # no backup ever recorded counts as stale
    return datetime.now(timezone.utc) - dt > timedelta(hours=hours)


def _is_stale(value: Any, days: int = 30) -> bool:
    dt = _parse_dt(value)
    return bool(dt) and datetime.now(timezone.utc) - dt > timedelta(days=days)


def _unique(items: List[Any]) -> List[Any]:
    out: List[Any] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in _lower(text)).strip("-")
