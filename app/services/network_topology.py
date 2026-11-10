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
     inventory snapshots, Microsoft Intune/Entra telemetry, Veeam backup jobs,
     IAM credential reports, Wazuh agents and alerts, Splunk host inventory
     and network snapshots (``aws.network.snapshot`` from the AWS collector,
     ``network.snapshot`` pushed by a firewall / VPN tool through the webhook).

Edges describe real relationships: a connector ``monitors`` the resources it
reported, an identity provider ``authenticates`` the identities it manages,
the backup connector ``backs_up`` a protected system, and the synthetic
``internet`` node is ``exposed_to_internet`` to a resource whose security
group (or public IP) lets 0.0.0.0/0 in. The infrastructure layer adds
``member_of`` (device -> subnet / network), ``part_of`` (subnet -> network),
``vpn_tunnel`` (VPN -> the network or gateway at each end, remote device ->
client VPN), ``routes_to`` (network -> gateway, gateway -> internet, network
peering), ``protects`` (security group -> device) and ``talks_to`` (observed
device-to-device traffic).

The only inference made is the "inferred" /24 network: a device with a
private IPv4 address and no reported network is attached to a network node
named after its /24, and that node is flagged ``meta.inferred = True``.

An organization with nothing connected yields an empty graph with
``summary.empty = True`` so the UI can say so in plain English.
"""
from __future__ import annotations

import ipaddress
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger("airs.services.network_topology")

INTERNET_NODE_ID = "internet"

# Node / edge vocabulary shared with the frontend.
NODE_TYPES = (
    "connector", "server", "workstation", "database", "bucket", "identity", "security_group", "internet",
    "network", "subnet", "vpn", "gateway",
)
ZONES = ("internet", "cloud", "security", "servers", "workstations", "data", "backups", "identity", "network")
STATUSES = ("healthy", "warning", "attention", "error", "unknown")
EDGE_KINDS = (
    "monitors", "backs_up", "authenticates", "exposed_to_internet",
    "member_of", "part_of", "vpn_tunnel", "routes_to", "protects", "talks_to",
)

NETWORK_KINDS = ("vpc", "office_lan", "wifi", "vpn_pool", "inferred", "other")
VPN_KINDS = ("site_to_site", "client")
GATEWAY_KINDS = (
    "internet_gateway", "nat_gateway", "vpn_gateway", "customer_gateway", "transit_gateway", "firewall", "router",
)

# One handler serves the generic push and the AWS collector.
SNAPSHOT_EVENT_TYPES = ("network.snapshot", "aws.network.snapshot")
# Events that describe the current state of something (the newest one counts).
STATE_EVENT_TYPES = SNAPSHOT_EVENT_TYPES + ("wazuh.agent_status", "splunk.host_inventory")
_MAX_STATE_EVENTS = 500

# Devices a network can contain (also the only nodes matched by name).
_DEVICE_TYPES = ("server", "workstation", "database")

_MAX_SNAPSHOT_ITEMS = 200
_MAX_ALERT_ISSUES_PER_NODE = 5

_NETWORK_KIND_ALIASES = {
    "lan": "office_lan", "office": "office_lan", "office-lan": "office_lan", "on_prem": "office_lan",
    "wi-fi": "wifi", "wlan": "wifi", "guest_wifi": "wifi", "guest-wifi": "wifi", "wireless": "wifi",
    "vpn": "vpn_pool", "vpn-pool": "vpn_pool", "client_vpn": "vpn_pool",
    "vnet": "vpc", "cloud": "vpc",
}
_NETWORK_KIND_LABELS = {
    "vpc": "Cloud network (VPC)",
    "office_lan": "Office network",
    "wifi": "Wi-Fi network",
    "vpn_pool": "VPN address pool",
    "inferred": "Network worked out from device addresses",
    "other": "Network",
}
_GATEWAY_KIND_ALIASES = {
    "igw": "internet_gateway", "internet": "internet_gateway",
    "nat": "nat_gateway", "natgw": "nat_gateway",
    "vgw": "vpn_gateway", "virtual_private_gateway": "vpn_gateway",
    "cgw": "customer_gateway",
    "tgw": "transit_gateway",
    "fw": "firewall",
}
_GATEWAY_KIND_LABELS = {
    "internet_gateway": "Internet gateway",
    "nat_gateway": "NAT gateway (outbound internet)",
    "vpn_gateway": "VPN gateway",
    "customer_gateway": "Office end of the VPN",
    "transit_gateway": "Transit gateway",
    "firewall": "Firewall",
    "router": "Router",
}
_INTERNET_GATEWAY_KINDS = {"internet_gateway", "nat_gateway"}
_VPN_KIND_ALIASES = {
    "site-to-site": "site_to_site", "s2s": "site_to_site", "ipsec": "site_to_site", "site": "site_to_site",
    "client_vpn": "client", "client-vpn": "client", "remote_access": "client", "remote-access": "client",
}
_VPN_UP_STATES = {"up", "connected", "active", "established", "online"}
_VPN_DOWN_STATES = {"down", "disconnected", "failed", "error", "offline"}
# Peerings in these states carry no traffic.
_GONE_STATES = {
    "deleted", "deleting", "rejected", "failed", "expired",
    "pending", "pending-acceptance", "initiating-request", "provisioning",
}

_PRIVATE_V4_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)
_WORKSTATION_OS_RE = re.compile(r"windows\s*1[01]\b|mac\s*os", re.IGNORECASE)

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
        # Live-feed bookkeeping (the ``live`` block of the response).
        self._connector_last_sync: Dict[str, Optional[str]] = {}
        self._event_counts: Dict[str, int] = {}
        self._source_latest: Dict[str, Optional[str]] = {}
        self._latest_event_at: Optional[str] = None
        self._wazuh_agents: Dict[str, str] = {}
        self._alert_issue_counts: Dict[str, int] = {}

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
        self._connector_last_sync[node_id] = _iso(last_sync)
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
        """Feed telemetry into the graph.

        Events are handled in phases so matching by name sees every node that
        could be matched, whatever order the rows arrive in:

          0. inventory, findings, identity, backups (everything else)
          1. Wazuh agents and Splunk hosts (enrich a same-named node)
          2. Wazuh alerts (need the agent nodes)
          3. network snapshots (place devices on networks by id or name)

        Status feeds (phases 1 and 3) describe "now", so only the newest
        event per source is used: an hour-old "tunnel down" must not outlive
        the tunnel coming back up.
        """
        phases: Dict[int, List[Any]] = {0: [], 1: [], 2: [], 3: []}
        for event in events or []:
            phases[_event_phase(_lower(_get(event, "event_type")))].append(event)
        phases[1] = _latest_per_key(phases[1])
        phases[3] = _latest_per_key(phases[3])
        for phase in sorted(phases):
            for event in phases[phase]:
                try:
                    self._add_event(event)
                except Exception as exc:  # one bad payload must not sink the map
                    logger.debug("Skipping telemetry event for topology: %s", type(exc).__name__)

    def _add_event(self, event: Any) -> None:
        event_type = _lower(_get(event, "event_type"))
        source = _get(event, "source_system") or ""
        payload = _event_payload(event)
        seen_at = _event_seen_at(event, payload)

        cnode: Optional[str] = None
        if event_type == "aws.securityhub.finding":
            cnode = self._add_securityhub_finding(source, payload, seen_at)
        elif event_type == "aws.inventory.snapshot":
            cnode = self._add_aws_inventory(source, payload, seen_at)
        elif event_type == "microsoft.telemetry":
            cnode = self._add_microsoft(source, payload, seen_at)
        elif event_type == "veeam.backup_job":
            cnode = self._add_backup_job(source, payload, seen_at)
        elif event_type == "aws.iam.credential_report":
            cnode = self._add_iam_report(source, payload, seen_at)
        elif event_type == "wazuh.agent_status":
            cnode = self._add_wazuh_agent(source, payload, seen_at)
        elif event_type == "wazuh.alert":
            cnode = self._add_wazuh_alert(source, payload, seen_at)
        elif event_type == "splunk.host_inventory":
            cnode = self._add_splunk_hosts(source, payload, seen_at)
        elif event_type in SNAPSHOT_EVENT_TYPES:
            cnode = self._add_network_snapshot(source, payload, seen_at, event_type)

        if cnode:
            # The event contributed to the map: count it for the live block.
            self._event_counts[cnode] = self._event_counts.get(cnode, 0) + 1
            self._source_latest[cnode] = _newest(self._source_latest.get(cnode), seen_at)
            self._latest_event_at = _newest(self._latest_event_at, seen_at)

    def _add_securityhub_finding(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> str:
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
        return cnode

    def _add_aws_inventory(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> str:
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
                    "network_id": res.get("vpc_id"),
                    "subnet_id": res.get("subnet_id"),
                    "availability_zone": res.get("availability_zone"),
                    "last_seen": seen_at,
                    "seen_by": [connector_label(source or "aws")],
                },
            )
            self.add_edge(cnode, node_id, "monitors")
            self._place_aws_resource(node_id, res, seen_at)
            if res.get("public_ip"):
                self._ensure_internet()
                self.add_edge(INTERNET_NODE_ID, node_id, "exposed_to_internet", "public IP")
                self.nodes[node_id]["meta"]["internet_exposed"] = True
            # A backup-role server is the thing the backups land on.
            if zone == "backups":
                veeam = self._connector_by_type.get("veeam")
                if veeam:
                    self.add_edge(veeam, node_id, "backs_up", "stores backups")
        return cnode

    def _place_aws_resource(self, node_id: str, res: Dict[str, Any], seen_at: Optional[str]) -> None:
        """Attach an inventory resource to the VPC / subnet / security groups AWS reported for it.

        The network snapshot may not have been seen (or may be denied), so the
        network, subnet and security-group nodes are created bare here and
        upgraded with names and CIDRs when the snapshot arrives.
        """
        vpc_id = _sid(res.get("vpc_id"))
        subnet_id = _sid(res.get("subnet_id"))
        net_node = self._bare_network("aws", vpc_id, seen_at) if vpc_id else None
        subnet_node = self._bare_subnet("aws", subnet_id, seen_at) if subnet_id else None
        if subnet_node and net_node:
            self.add_edge(subnet_node, net_node, "part_of")
        if subnet_node or net_node:
            self.add_edge(node_id, subnet_node or net_node, "member_of")
        for sg_id in _as_list(res.get("security_group_ids"))[:_MAX_SNAPSHOT_ITEMS]:
            sg_node = self._bare_security_group("aws", _sid(sg_id), seen_at)
            if sg_node:
                self.add_edge(sg_node, node_id, "protects")

    def _add_microsoft(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> str:
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
        return cnode

    def _add_iam_report(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> str:
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
        return cnode

    def _add_backup_job(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> str:
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
        return cnode

    # -- Wazuh / Splunk ------------------------------------------------------

    def _add_wazuh_agent(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> Optional[str]:
        """One Wazuh agent = one machine that reports (or has stopped reporting)."""
        agent_id = _sid(payload.get("agent_id") or payload.get("id"))
        if not agent_id or agent_id == "000":  # 000 is the Wazuh manager itself
            return None
        cnode = self.connector_for_source(source or "wazuh")
        name = _sid(payload.get("name")) or f"agent-{agent_id}"
        os_name = payload.get("os")
        if isinstance(os_name, dict):
            os_name = os_name.get("name")
        os_name = _sid(os_name) or None
        agent_status = _lower(payload.get("status"))
        if agent_status == "active":
            status = "healthy"
        elif agent_status in ("disconnected", "never_connected"):
            status = "warning"
        else:
            status = "unknown"
        meta = {
            "agent_id": agent_id,
            "agent_status": payload.get("status"),
            "ip_address": _ip_or_none(payload.get("ip")),
            "operating_system": os_name,
            "agent_version": payload.get("version"),
            "agent_group": payload.get("group"),
            "last_seen": _iso_or_none(payload.get("last_keep_alive")) or seen_at,
            "seen_by": [connector_label(source or "wazuh")],
        }
        node_id = self._find_node_by_label(name, _DEVICE_TYPES)
        if node_id:
            self._enrich_node(node_id, status=status, meta=meta)
        else:
            node_id = f"wazuh:agent:{agent_id}"
            ntype, zone = _device_type_zone(name, os_name)
            self.add_node(
                node_id,
                type=ntype,
                label=name,
                sublabel=" · ".join(x for x in ("Wazuh agent", os_name) if x),
                zone=zone,
                status=status,
                meta=meta,
            )
        if status == "warning":
            self.mark_issue(node_id, "Security agent is not reporting", "medium")
        self.add_edge(cnode, node_id, "monitors")
        self._wazuh_agents[agent_id] = node_id
        return cnode

    def _add_wazuh_alert(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> Optional[str]:
        """High (level >= 10) and medium (>= 7) alerts become issues on the agent's node."""
        try:
            level = int(payload.get("rule_level") or 0)
        except (TypeError, ValueError):
            return None
        if level < 7:
            return None
        agent_id = _sid(payload.get("agent_id"))
        node_id = self._wazuh_agents.get(agent_id) if agent_id else None
        if not node_id and payload.get("agent_name"):
            node_id = self._find_node_by_label(payload.get("agent_name"), _DEVICE_TYPES)
        if not node_id or node_id not in self.nodes:
            return None
        if self._alert_issue_counts.get(node_id, 0) >= _MAX_ALERT_ISSUES_PER_NODE:
            return None
        issues = self.nodes[node_id]["meta"]["issues"]
        before = len(issues)
        title = (_sid(payload.get("rule_description")) or "Security alert")[:160]
        self.mark_issue(
            node_id,
            title,
            "high" if level >= 10 else "medium",
            _iso_or_none(payload.get("timestamp")) or seen_at,
        )
        if len(issues) > before:
            self._alert_issue_counts[node_id] = self._alert_issue_counts.get(node_id, 0) + 1
        return self.connector_for_source(source or "wazuh")

    def _add_splunk_hosts(self, source: str, payload: Dict[str, Any], seen_at: Optional[str]) -> Optional[str]:
        """Hosts that send logs to Splunk, and the ones that went quiet."""
        hosts = [
            h for h in _as_list(payload.get("hosts"))
            if isinstance(h, dict) and _sid(h.get("host"))
        ][:_MAX_SNAPSHOT_ITEMS]
        if not hosts:
            return None
        cnode = self.connector_for_source(source or "splunk")
        now = datetime.now(timezone.utc)
        for host in hosts:
            name = _sid(host.get("host"))
            last_seen = _iso_or_none(host.get("last_seen"))
            seen_dt = _parse_dt(last_seen)
            if seen_dt is None:
                status = "unknown"
            elif now - seen_dt > timedelta(hours=24):
                status = "warning"
            else:
                status = "healthy"
            meta = {
                "last_seen": last_seen,
                "log_event_count": host.get("event_count"),
                "seen_by": [connector_label(source or "splunk")],
            }
            node_id = self._find_node_by_label(name, _DEVICE_TYPES)
            if node_id:
                self._enrich_node(node_id, status=status, meta=meta)
            else:
                node_id = f"splunk:host:{name}"
                ntype, zone = _device_type_zone(name)
                self.add_node(
                    node_id,
                    type=ntype,
                    label=name,
                    sublabel="Sends logs to Splunk",
                    zone=zone,
                    status=status,
                    meta=meta,
                )
            if status == "warning":
                self.mark_issue(node_id, "Stopped sending logs", "medium")
            self.add_edge(cnode, node_id, "monitors")
        return cnode

    # -- network snapshots ---------------------------------------------------

    def _add_network_snapshot(
        self, source: str, payload: Dict[str, Any], seen_at: Optional[str], event_type: str
    ) -> Optional[str]:
        """Networks, subnets, gateways, VPNs, security groups, devices and links.

        Serves ``aws.network.snapshot`` (AWS collector) and ``network.snapshot``
        (pushed by a firewall / VPN tool, or the scripted demo). Every list is
        optional. References between items use the ids of the same snapshot; a
        referenced item that was not described becomes a bare placeholder node.
        An item may carry its own ``provider`` when one feed describes several
        environments (an office firewall that also knows the cloud VPC).
        """
        snap = _unwrap_snapshot(payload)
        if not any(_items(snap, key) for key in _SNAPSHOT_LISTS):
            return None
        provider = _provider(snap.get("provider")) or ("aws" if event_type.startswith("aws.") else "manual")
        sample = bool(snap.get("sample"))
        cnode = self.connector_for_source(source or provider)
        seen_by = [connector_label(source or provider)]
        index: Dict[str, Dict[str, str]] = {"net": {}, "subnet": {}, "gw": {}, "vpn": {}, "sg": {}, "device": {}}

        def prov_of(item: Dict[str, Any]) -> str:
            return _provider(item.get("provider")) or provider

        def put(node_id: str, *, meta: Optional[Dict[str, Any]] = None, **fields: Any) -> bool:
            """Add / upgrade a node described by this snapshot. True when it is new."""
            is_new = node_id not in self.nodes
            merged = dict(meta or {})
            merged["seen_by"] = seen_by
            merged.setdefault("last_seen", seen_at)
            if sample and is_new:
                merged["sample"] = True
            self.add_node(node_id, meta=merged, **fields)
            return is_new

        def ref(kind: str, raw: Any, prov: str) -> Optional[str]:
            """Node id for a referenced item; a bare placeholder when it was not described."""
            raw_id = _sid(raw)
            if not raw_id:
                return None
            known = index[kind].get(raw_id)
            if known:
                return known
            maker = {
                "net": self._bare_network,
                "subnet": self._bare_subnet,
                "gw": self._bare_gateway,
                "vpn": self._bare_vpn,
                "sg": self._bare_security_group,
            }[kind]
            node_id = maker(prov, raw_id, seen_at, sample=sample, seen_by=seen_by)
            if node_id:
                index[kind][raw_id] = node_id
            return node_id

        def internet() -> str:
            is_new = INTERNET_NODE_ID not in self.nodes
            self._ensure_internet()
            if is_new and sample:
                self.nodes[INTERNET_NODE_ID]["meta"]["sample"] = True
            return INTERNET_NODE_ID

        # 1. Networks -------------------------------------------------------
        for net in _items(snap, "networks"):
            raw_id = _sid(net.get("id"))
            if not raw_id:
                continue
            prov = prov_of(net)
            node_id = f"net:{prov}:{raw_id}"
            kind = _network_kind(net.get("kind"), prov)
            cidr = _sid(net.get("cidr")) or None
            put(
                node_id,
                type="network",
                label=_sid(net.get("name")) or raw_id,
                sublabel=" · ".join(x for x in (_NETWORK_KIND_LABELS[kind], cidr) if x),
                zone="network",
                status="healthy",
                meta={"cidr": cidr, "network_kind": kind, "location": net.get("location")},
            )
            index["net"][raw_id] = node_id
            self.add_edge(cnode, node_id, "monitors")

        # 2. Subnets --------------------------------------------------------
        for subnet in _items(snap, "subnets"):
            raw_id = _sid(subnet.get("id"))
            if not raw_id:
                continue
            prov = prov_of(subnet)
            node_id = f"subnet:{prov}:{raw_id}"
            cidr = _sid(subnet.get("cidr")) or None
            public = subnet.get("public") if isinstance(subnet.get("public"), bool) else None
            kind_label = "Subnet" if public is None else ("Public subnet" if public else "Private subnet")
            put(
                node_id,
                type="subnet",
                label=_sid(subnet.get("name")) or cidr or raw_id,
                sublabel=" · ".join(x for x in (kind_label, cidr) if x),
                zone="network",
                status="healthy",
                meta={
                    "cidr": cidr,
                    "network_id": _sid(subnet.get("network_id")) or None,
                    "public": public,
                    "availability_zone": subnet.get("availability_zone"),
                },
            )
            index["subnet"][raw_id] = node_id
            self.add_edge(node_id, ref("net", subnet.get("network_id"), prov), "part_of")

        # 3. Gateways -------------------------------------------------------
        for gateway in _items(snap, "gateways"):
            raw_id = _sid(gateway.get("id"))
            if not raw_id:
                continue
            prov = prov_of(gateway)
            node_id = f"gw:{prov}:{raw_id}"
            kind = _gateway_kind(gateway.get("kind"))
            put(
                node_id,
                type="gateway",
                label=_sid(gateway.get("name")) or raw_id,
                sublabel=_GATEWAY_KIND_LABELS.get(kind or "", "Gateway"),
                zone="network",
                status="healthy",
                meta={
                    "gateway_kind": kind,
                    "network_id": _sid(gateway.get("network_id")) or None,
                    "public_ip": gateway.get("public_ip"),
                    "location": gateway.get("location"),
                },
            )
            index["gw"][raw_id] = node_id
            # ``network_ids`` covers a firewall / router that serves several networks.
            for network_id in [gateway.get("network_id")] + _as_list(gateway.get("network_ids"))[:_MAX_SNAPSHOT_ITEMS]:
                self.add_edge(ref("net", network_id, prov), node_id, "routes_to")
            if gateway.get("to_internet") is True or (kind in _INTERNET_GATEWAY_KINDS and gateway.get("to_internet") is not False):
                self.add_edge(node_id, internet(), "routes_to", "to the internet")

        # 4. VPNs -----------------------------------------------------------
        for vpn in _items(snap, "vpns"):
            raw_id = _sid(vpn.get("id"))
            state = _lower(vpn.get("state"))
            if not raw_id or state in ("deleted", "deleting"):
                continue
            prov = prov_of(vpn)
            node_id = f"vpn:{prov}:{raw_id}"
            kind = _vpn_kind(vpn.get("kind"))
            tunnels = [t for t in _as_list(vpn.get("tunnels")) if isinstance(t, dict)]
            total = len(tunnels)
            up = sum(1 for t in tunnels if _lower(t.get("status")) == "up")
            down = sum(1 for t in tunnels if _lower(t.get("status")) == "down")
            status, issue = _vpn_status(kind, state, up, down, total)
            tunnels_known = total > 0 and up + down == total
            tunnel_label = f"{up} of {total} tunnels up" if tunnels_known else None
            kind_label = {"site_to_site": "Site-to-site VPN", "client": "Remote access VPN"}.get(kind or "", "VPN")
            put(
                node_id,
                type="vpn",
                label=_sid(vpn.get("name")) or raw_id,
                sublabel=" · ".join(x for x in (kind_label, tunnel_label) if x),
                zone="network",
                status=status,
                meta={
                    "vpn_kind": kind,
                    "tunnels_up": up if tunnels_known else None,
                    "tunnels_total": total if total else None,
                    "active_connections": _int_or_none(vpn.get("active_connections")),
                    "state": vpn.get("state"),
                    "network_id": _sid(vpn.get("network_id")) or None,
                },
            )
            index["vpn"][raw_id] = node_id
            if issue:
                self.mark_issue(node_id, issue[0], issue[1], seen_at)
            # Each end of the VPN: the gateway when one is named, else the network.
            for gw_key, net_key in (("gateway_id", "network_id"), ("remote_gateway_id", "remote_network_id")):
                gw_node = ref("gw", vpn.get(gw_key), prov)
                net_node = ref("net", vpn.get(net_key), prov)
                if gw_node:
                    self.add_edge(node_id, gw_node, "vpn_tunnel", tunnel_label)
                    self.add_edge(net_node, gw_node, "routes_to")
                elif net_node:
                    self.add_edge(node_id, net_node, "vpn_tunnel", tunnel_label)

        # 5. Security groups ------------------------------------------------
        for group in _items(snap, "security_groups"):
            raw_id = _sid(group.get("id"))
            if not raw_id:
                continue
            prov = prov_of(group)
            node_id = _sg_node_id(prov, raw_id)
            open_ports = [str(p) for p in _as_list(group.get("open_ports")) if p not in (None, "")]
            put(
                node_id,
                type="security_group",
                label=_sid(group.get("name")) or raw_id,
                sublabel="Security group (firewall rules)",
                zone="cloud",
                status="healthy",
                meta={
                    "network_id": _sid(group.get("network_id")) or None,
                    "open_ports": open_ports or None,
                    "internet_exposed": True if open_ports else None,
                },
            )
            index["sg"][raw_id] = node_id
            if open_ports:
                self.add_edge(internet(), node_id, "exposed_to_internet", "open to the internet")

        # 6. Devices --------------------------------------------------------
        for device in _items(snap, "devices"):
            raw_id = (
                _sid(device.get("id")) or _sid(device.get("instance_id"))
                or _sid(device.get("device_id")) or _sid(device.get("name"))
            )
            if not raw_id:
                continue
            prov = prov_of(device)
            node_id, created = self._resolve_snapshot_device(device, prov, raw_id, put)
            index["device"][raw_id] = node_id
            self._enrich_node(node_id, meta={
                "ip_address": _ip_or_none(device.get("ip")),
                "network_id": _sid(device.get("network_id")) or None,
                "subnet_id": _sid(device.get("subnet_id")) or None,
                "operating_system": device.get("os"),
                "last_seen": _iso_or_none(device.get("last_seen")) or seen_at,
                "seen_by": seen_by,
            })
            if created:
                self.add_edge(cnode, node_id, "monitors")
            subnet_node = ref("subnet", device.get("subnet_id"), prov)
            net_node = ref("net", device.get("network_id"), prov)
            if subnet_node and net_node:
                self.add_edge(subnet_node, net_node, "part_of")
            self.add_edge(node_id, subnet_node or net_node, "member_of")
            for sg_id in _as_list(device.get("security_group_ids"))[:_MAX_SNAPSHOT_ITEMS]:
                self.add_edge(ref("sg", sg_id, prov), node_id, "protects")
            self.add_edge(node_id, ref("vpn", device.get("via_vpn_id"), prov), "vpn_tunnel", "remote access")

        # 7. Observed traffic -----------------------------------------------
        for link in _items(snap, "links"):
            src = self._resolve_link_end(link.get("source"), index["device"])
            dst = self._resolve_link_end(link.get("target"), index["device"])
            self.add_edge(src, dst, "talks_to", _sid(link.get("label")) or None)

        # 8. Peerings -------------------------------------------------------
        for peering in _items(snap, "peerings"):
            if _lower(peering.get("state")) in _GONE_STATES:
                continue
            prov = prov_of(peering)
            self.add_edge(
                ref("net", peering.get("a_network_id"), prov),
                ref("net", peering.get("b_network_id"), prov),
                "routes_to",
                "peering",
            )
        return cnode

    def _resolve_snapshot_device(
        self, device: Dict[str, Any], provider: str, raw_id: str, put: Any
    ) -> tuple:
        """Find the node a snapshot device refers to, or create a bare one.

        Order: AWS instance id, Microsoft device id, a device with the same
        name, else a new ``net:device:<provider>:<id>`` node. Returns
        (node_id, created).
        """
        name = _sid(device.get("name"))
        instance_id = _sid(device.get("instance_id"))
        device_id = _sid(device.get("device_id"))
        ntype, zone = _device_type_zone(name, device.get("os"), device.get("kind"))
        # When the device itself was last seen, not when the snapshot was taken.
        meta = {"last_seen": _iso_or_none(device.get("last_seen"))}
        meta = {key: value for key, value in meta.items() if value}

        if instance_id:
            node_id = f"aws:instance:{instance_id}"
            if node_id in self.nodes:
                return node_id, False
            put(node_id, type=ntype, label=name or instance_id, sublabel="EC2 instance", zone=zone,
                status="unknown", bare=True, meta=meta)
            return node_id, True
        if device_id and provider == "microsoft":
            node_id = f"ms:device:{device_id}"
            if node_id in self.nodes:
                return node_id, False
            put(
                node_id,
                type="workstation" if ntype == "server" else ntype,
                label=name or device_id,
                sublabel="Intune managed device",
                zone="workstations" if ntype == "server" else zone,
                status="unknown",
                bare=True,
                meta=meta,
            )
            return node_id, True
        existing = self._find_node_by_label(name, _DEVICE_TYPES) if name else None
        if existing:
            return existing, False
        node_id = f"net:device:{provider}:{raw_id}"
        if node_id in self.nodes:
            return node_id, False
        put(
            node_id,
            type=ntype,
            label=name or raw_id,
            sublabel=_sid(device.get("os")) or "Seen on the network",
            zone=zone,
            status="unknown",
            bare=True,
            meta=meta,
        )
        return node_id, True

    def _resolve_link_end(self, raw: Any, devices: Dict[str, str]) -> Optional[str]:
        """A link end is a device id of the same snapshot, a node id, or a device name."""
        raw_id = _sid(raw)
        if not raw_id:
            return None
        if raw_id in devices:
            return devices[raw_id]
        if raw_id in self.nodes:
            return raw_id
        return self._find_node_by_label(raw_id, _DEVICE_TYPES)

    # -- placeholder nodes ---------------------------------------------------

    def _placeholder(self, node_id: str, seen_at: Optional[str], sample: bool, seen_by: Optional[List[str]], **fields: Any) -> str:
        """Create a placeholder for something referenced but not described yet."""
        if node_id not in self.nodes:
            meta = dict(fields.pop("meta", None) or {})
            meta["last_seen"] = seen_at
            meta["seen_by"] = seen_by or []
            if sample:
                meta["sample"] = True
            self.add_node(node_id, status="unknown", meta=meta, bare=True, **fields)
        return node_id

    def _bare_network(self, provider: str, raw_id: str, seen_at: Optional[str], *, sample: bool = False,
                      seen_by: Optional[List[str]] = None) -> Optional[str]:
        if not raw_id:
            return None
        is_aws = provider == "aws"
        return self._placeholder(
            f"net:{provider}:{raw_id}", seen_at, sample, seen_by,
            type="network", label=raw_id, zone="network",
            sublabel=_NETWORK_KIND_LABELS["vpc" if is_aws else "other"],
            meta={"network_kind": "vpc" if is_aws else None},
        )

    def _bare_subnet(self, provider: str, raw_id: str, seen_at: Optional[str], *, sample: bool = False,
                     seen_by: Optional[List[str]] = None) -> Optional[str]:
        if not raw_id:
            return None
        return self._placeholder(
            f"subnet:{provider}:{raw_id}", seen_at, sample, seen_by,
            type="subnet", label=raw_id, zone="network", sublabel="Subnet",
        )

    def _bare_gateway(self, provider: str, raw_id: str, seen_at: Optional[str], *, sample: bool = False,
                      seen_by: Optional[List[str]] = None) -> Optional[str]:
        if not raw_id:
            return None
        return self._placeholder(
            f"gw:{provider}:{raw_id}", seen_at, sample, seen_by,
            type="gateway", label=raw_id, zone="network", sublabel="Gateway",
        )

    def _bare_vpn(self, provider: str, raw_id: str, seen_at: Optional[str], *, sample: bool = False,
                  seen_by: Optional[List[str]] = None) -> Optional[str]:
        if not raw_id:
            return None
        return self._placeholder(
            f"vpn:{provider}:{raw_id}", seen_at, sample, seen_by,
            type="vpn", label=raw_id, zone="network", sublabel="VPN",
        )

    def _bare_security_group(self, provider: str, raw_id: str, seen_at: Optional[str], *, sample: bool = False,
                             seen_by: Optional[List[str]] = None) -> Optional[str]:
        if not raw_id:
            return None
        return self._placeholder(
            _sg_node_id(provider, raw_id), seen_at, sample, seen_by,
            type="security_group", label=raw_id, zone="cloud", sublabel="Security group (firewall rules)",
        )

    def _enrich_node(self, node_id: str, *, status: str = "unknown", meta: Optional[Dict[str, Any]] = None) -> None:
        """Add facts to an existing node without overwriting what its own source said."""
        node = self.nodes.get(node_id)
        if not node:
            return
        node["status"] = _worse(node["status"], status)
        for key, value in (meta or {}).items():
            if key in ("issues", "seen_by"):
                for item in value or []:
                    if item not in node["meta"][key]:
                        node["meta"][key].append(item)
            elif key == "last_seen":
                node["meta"]["last_seen"] = _newest(node["meta"].get("last_seen"), value)
            elif value is not None and node["meta"].get(key) is None:
                node["meta"][key] = value

    # -- inferred networks ---------------------------------------------------

    def finalize(self) -> None:
        """Attach devices with a private address and no reported network to an inferred /24.

        This is the one place the map reasons beyond what a source said, so the
        network node is flagged ``meta.inferred``. A network is only created
        when at least one device lands on it. Safe to call more than once.
        """
        placed = {edge["source"] for edge in self.edges.values() if edge["kind"] == "member_of"}
        for node_id, node in list(self.nodes.items()):
            if node["type"] not in _DEVICE_TYPES or node_id in placed:
                continue
            cidr = _private_slash24(node["meta"].get("private_ip")) or _private_slash24(node["meta"].get("ip_address"))
            if not cidr:
                continue
            net_id = f"net:inferred:{cidr}"
            self.add_node(
                net_id,
                type="network",
                label=cidr,
                sublabel=_NETWORK_KIND_LABELS["inferred"],
                zone="network",
                status="unknown",
                meta={"cidr": cidr, "network_kind": "inferred", "inferred": True},
            )
            self.add_edge(node_id, net_id, "member_of", "worked out from address")

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

    def _find_node_by_label(self, label: str, types: Optional[Iterable[str]] = None) -> Optional[str]:
        """Case-insensitive match on a node's label, optionally limited to node types."""
        target = _lower(label).strip()
        if not target:
            return None
        allowed = tuple(types) if types else None
        for node_id, node in self.nodes.items():
            if allowed and node["type"] not in allowed:
                continue
            if _lower(node["label"]).strip() == target:
                return node_id
        return None

    # -- output --------------------------------------------------------------

    def build(self) -> Dict[str, Any]:
        self.finalize()
        nodes = list(self.nodes.values())
        edges = list(self.edges.values())
        summary = self._summary(nodes, edges)
        return {
            "nodes": nodes,
            "edges": edges,
            "summary": summary,
            "live": self._live(nodes),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _live(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Which feeds the map was built from and how fresh they are.

        ``last_sync_at`` is the connector row's last sync; a source without a
        connector row (demo, manually injected events) reports the time of the
        newest event it contributed instead.
        """
        sources = []
        for node in nodes:
            if node["type"] != "connector":
                continue
            node_id = node["id"]
            sources.append({
                "id": node_id,
                "type": node["meta"].get("connector_type"),
                "label": node["label"],
                "status": node["status"],
                "last_sync_at": _utc_iso(self._connector_last_sync.get(node_id) or self._source_latest.get(node_id)),
                "event_count": self._event_counts.get(node_id, 0),
            })
        return {
            "mode": "live" if nodes else "empty",
            "latest_event_at": _utc_iso(self._latest_event_at),
            "sources": sources,
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
                "networks": 0,
                "vpns": 0,
                "vpn_down": 0,
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
            "networks": sum(1 for n in nodes if n["type"] == "network"),
            "vpns": sum(1 for n in nodes if n["type"] == "vpn"),
            "vpn_down": sum(1 for n in nodes if n["type"] == "vpn" and n["status"] == "attention"),
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
            # State feeds (network snapshots, agents, log sources) arrive rarely
            # compared with findings and alerts. Load them on their own so a
            # burst of alerts cannot push the network layout out of the window.
            loaded = {row.id for row in events}
            state_rows = (
                db.query(TelemetryEvent)
                .filter(
                    TelemetryEvent.org_id == org_id,
                    TelemetryEvent.created_at >= cutoff,
                    TelemetryEvent.event_type.in_(STATE_EVENT_TYPES),
                )
                .order_by(TelemetryEvent.created_at.desc())
                .limit(_MAX_STATE_EVENTS)
                .all()
            )
            events.extend(row for row in state_rows if row.id not in loaded)
        except Exception as exc:
            logger.warning("Topology: could not load telemetry for %s: %s", org_id, exc)

    topology = build_topology(org_id, connectors=connectors, assets=assets, events=events)
    if demo:
        topology["live"]["mode"] = "demo"
    return topology


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


# ---------------------------------------------------------------------------
# Event ordering
# ---------------------------------------------------------------------------

_SNAPSHOT_LISTS = ("networks", "subnets", "gateways", "vpns", "security_groups", "devices", "links", "peerings")
_PC_RE = re.compile(r"(?<![a-z])pc(?![a-z])")


def _event_payload(event: Any) -> Dict[str, Any]:
    """Payload as a dict. Raises on malformed JSON so the caller skips the event."""
    payload = _get(event, "payload") or {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise ValueError("telemetry payload is not an object")
    return payload


def _event_seen_at(event: Any, payload: Dict[str, Any]) -> Optional[str]:
    return _iso(
        _get(event, "timestamp") or _get(event, "created_at")
        or payload.get("updated_at") or payload.get("created_at")
    )


def _event_phase(event_type: str) -> int:
    if event_type in SNAPSHOT_EVENT_TYPES:
        return 3
    if event_type == "wazuh.alert":
        return 2
    if event_type in ("wazuh.agent_status", "splunk.host_inventory"):
        return 1
    return 0


def _unwrap_snapshot(payload: Dict[str, Any]) -> Dict[str, Any]:
    """A pushed snapshot may sit at the top level or under snapshot / payload / data."""
    if any(key in payload for key in _SNAPSHOT_LISTS):
        return payload
    for wrapper in ("snapshot", "payload", "data"):
        inner = payload.get(wrapper)
        if isinstance(inner, dict) and any(key in inner for key in _SNAPSHOT_LISTS):
            return inner
    return payload


def _status_feed_key(event: Any, payload: Dict[str, Any]) -> tuple:
    """Identity of a "current state" feed: later events replace earlier ones."""
    event_type = _lower(_get(event, "event_type"))
    base = (event_type, _lower(_get(event, "source_system")), str(_get(event, "connector_id") or ""))
    if event_type == "wazuh.agent_status":
        return base + (str(payload.get("agent_id") or payload.get("id") or ""),)
    if event_type in SNAPSHOT_EVENT_TYPES:
        snap = _unwrap_snapshot(payload)
        # ``scope`` lets one tool push separate partial documents (devices, tunnels).
        return base + tuple(
            _lower(snap.get(field)) for field in ("provider", "account_id", "region", "scope")
        )
    return base


def _latest_per_key(events: List[Any]) -> List[Any]:
    """Keep the newest event of each status feed, preserving first-seen order."""
    chosen: Dict[tuple, tuple] = {}
    unreadable: List[Any] = []
    for event in events:
        try:
            payload = _event_payload(event)
            key = _status_feed_key(event, payload)
            when = _parse_dt(_event_seen_at(event, payload))
        except Exception:
            unreadable.append(event)  # _add_event reports and skips it
            continue
        current = chosen.get(key)
        if current is None or (when is not None and (current[0] is None or when > current[0])):
            chosen[key] = (when, event)
    return [event for _, event in chosen.values()] + unreadable


# ---------------------------------------------------------------------------
# Normalisation helpers for network data
# ---------------------------------------------------------------------------

def _sid(value: Any) -> str:
    """Identifier / name as a trimmed string ("" when missing)."""
    if value is None or isinstance(value, (dict, list)):
        return ""
    return str(value).strip()


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _items(snapshot: Dict[str, Any], key: str) -> List[Dict[str, Any]]:
    return [item for item in _as_list(snapshot.get(key)) if isinstance(item, dict)][:_MAX_SNAPSHOT_ITEMS]


def _provider(value: Any) -> str:
    """Provider name safe to embed in a node id."""
    return "".join(ch if (ch.isalnum() or ch in "-_") else "-" for ch in _lower(value).strip()).strip("-")


def _sg_node_id(provider: str, raw_id: str) -> str:
    """AWS security groups keep the id findings already use."""
    if provider == "aws" or raw_id.startswith("sg-"):
        return f"aws:sg:{raw_id}"
    return f"sg:{provider}:{raw_id}"


def _network_kind(value: Any, provider: str) -> str:
    kind = _lower(value).strip().replace(" ", "_")
    kind = _NETWORK_KIND_ALIASES.get(kind, kind)
    if kind in NETWORK_KINDS and kind != "inferred":
        return kind
    return "vpc" if (not kind and provider == "aws") else "other"


def _gateway_kind(value: Any) -> Optional[str]:
    kind = _lower(value).strip().replace(" ", "_").replace("-", "_")
    kind = _GATEWAY_KIND_ALIASES.get(kind, kind)
    return kind if kind in GATEWAY_KINDS else None


def _vpn_kind(value: Any) -> Optional[str]:
    kind = _lower(value).strip().replace(" ", "_")
    kind = _VPN_KIND_ALIASES.get(kind, kind)
    return kind if kind in VPN_KINDS else None


def _vpn_status(kind: Optional[str], state: str, up: int, down: int, total: int) -> tuple:
    """(status, issue) for a VPN. ``issue`` is (title, severity) or None.

    Tunnel telemetry decides when present: all up is healthy, some down is a
    warning, all down needs attention. Without it, only an explicit up / down
    state is trusted (a client VPN endpoint has no tunnels, so "available"
    counts as up for it); anything else stays unknown.
    """
    if total and up + down > 0:
        if down == 0:
            return ("healthy" if up == total else "unknown"), None
        if up == 0:
            return "attention", ("VPN is down", "high")
        title = "One VPN tunnel is down" if down == 1 else f"{down} of {total} VPN tunnels are down"
        return "warning", (title, "medium")
    if state in _VPN_UP_STATES or (kind == "client" and state == "available"):
        return "healthy", None
    if state in _VPN_DOWN_STATES:
        return "attention", ("VPN is down", "high")
    return "unknown", None


def _device_type_zone(name: Any, os_name: Any = None, kind: Any = None) -> tuple:
    """(type, zone) for a machine, always one of the device types."""
    explicit = _lower(kind).strip()
    if explicit in ("laptop", "desktop", "pc", "workstation"):
        return "workstation", "workstations"
    if explicit == "database":
        return "database", "data"
    if os_name and _WORKSTATION_OS_RE.search(str(os_name)):
        return "workstation", "workstations"
    hint = " ".join(str(part) for part in (kind, name, os_name) if part)
    ntype = type_for_hint(hint, "server")
    if ntype not in _DEVICE_TYPES:
        ntype = "server"
    if ntype == "workstation":
        return ntype, "workstations"
    if ntype == "database":
        return ntype, "data"
    zone = zone_for_hint(hint, "servers")
    if zone == "workstations":
        # zone_for_hint matches a bare "pc" anywhere; only trust it as a word.
        return ("workstation", "workstations") if _PC_RE.search(_lower(hint)) else ("server", "servers")
    if zone == "identity":
        zone = "servers"
    return ntype, zone


def _int_or_none(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _iso_or_none(value: Any) -> Optional[str]:
    """ISO timestamp from an ISO string, a datetime or epoch seconds; else None."""
    if value is None or isinstance(value, bool) or value == "":
        return None
    if isinstance(value, datetime):
        return _utc_iso(value.isoformat())
    if isinstance(value, (int, float)):
        epoch: Optional[float] = float(value)
    else:
        text = str(value).strip()
        try:
            epoch = float(text)
        except ValueError:
            epoch = None
        if epoch is None:
            return text if _parse_dt(text) else None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
    except (OverflowError, OSError, ValueError):
        return None


def _utc_iso(value: Optional[str]) -> Optional[str]:
    """Timezone-aware ISO string (naive database timestamps are UTC)."""
    parsed = _parse_dt(value)
    return parsed.isoformat() if parsed else None


def _ip_or_none(value: Any) -> Optional[str]:
    text = _sid(value).split("/")[0]
    if not text:
        return None
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return None


def _private_slash24(value: Any) -> Optional[str]:
    """The /24 of an RFC 1918 IPv4 address, e.g. 10.0.1.57 -> "10.0.1.0/24"."""
    text = _ip_or_none(value)
    if not text:
        return None
    address = ipaddress.ip_address(text)
    if address.version != 4 or not any(address in network for network in _PRIVATE_V4_NETWORKS):
        return None
    return str(ipaddress.ip_network(f"{address}/24", strict=False))
