"""
Unified technology inventory for one organization.

Merges, without duplicating, everything already collected elsewhere:

  * ``HostAsset`` / ``InstalledProduct``  latest discovery snapshot (AWS SSM / RDS,
                                          Microsoft Intune, Wazuh)
  * ``DiscoveredAsset``                   connector-fed software list
  * ``WebAsset.last_scan``                versions read from the org's own websites
  * ``TechStackItem``                     manual tech-stack entries

Items are de-duplicated by canonical product + version + asset.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit

from sqlalchemy.orm import Session

from app.models.discovered_asset import DiscoveredAsset
from app.models.discovery import HostAsset, InstalledProduct, TechnologyInventory
from app.models.tech_stack import TechStackItem
from app.models.vuln_intel import WebAsset
from app.services.vuln_intel.catalog import OSInfo, ProductInfo, parse_os, resolve_product
from app.services.vuln_intel.versions import clean_upstream_version

logger = logging.getLogger("airs.vuln_intel.inventory")

WEB_SCAN_SOURCE = "web_scan"
MANUAL_SOURCE = "manual"
AUTO_NOTE_PREFIX = "Auto-discovered"

# installation_source values that mean "the OS package manager told us".
HOST_PACKAGE_SOURCES = ("aws_systems_manager", "wazuh_syscollector", "wazuh")
_LINUX_FAMILIES = ("ubuntu", "debian", "alpine", "amazon", "rhel")
_DISTRO_MARKERS = ("ubuntu", "deb", "amzn", ".el", "~", "alpine", "fc")

_OS_NAME_PREFIXES = (
    "windows", "microsoft windows", "macos", "mac os", "ubuntu", "debian", "amazon linux",
    "alpine", "red hat", "rhel", "centos", "rocky", "almalinux", "fedora",
)


@dataclass
class StackItem:
    """One piece of software (or operating system) on one asset."""
    name: str
    version: Optional[str]
    source: str
    product: ProductInfo
    asset: Optional[str] = None
    vendor: Optional[str] = None
    category: str = "application"
    last_seen: Optional[datetime] = None
    raw_name: str = ""
    os: Optional[OSInfo] = None            # host operating system (the OS itself for OS items)
    is_os: bool = False
    platform: Optional[str] = None         # apt | dnf | yum | apk | windows_update | macos_update | rds | lambda | web
    version_explicit: bool = True          # False when the version was inferred, not stated
    distro_hint: bool = False              # the source said this is a distribution package
    id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.id:
            basis = "|".join([self.dedupe_key[0], self.dedupe_key[1], self.dedupe_key[2], self.source])
            self.id = hashlib.sha1(basis.encode()).hexdigest()[:16]

    @property
    def product_key(self) -> str:
        return self.os.key if (self.is_os and self.os) else self.product.key

    @property
    def dedupe_key(self) -> Tuple[str, str, str]:
        return (self.product_key, (self.version or "").strip().lower(), (self.asset or "").strip().lower())

    @property
    def lookup_version(self) -> Optional[str]:
        """Upstream release number used for NVD / end-of-life comparison."""
        return clean_upstream_version(self.version)

    @property
    def is_distro_package(self) -> bool:
        """True when this is a Linux distribution package (backported fixes are likely,
        so comparing the upstream version number proves nothing)."""
        if self.is_os or self.platform in ("rds", "lambda"):
            return False
        version = (self.version or "").lower()
        marked = self.distro_hint or any(m in version for m in _DISTRO_MARKERS)
        if self.platform == "web":
            return marked
        linux_host = bool(self.os and self.os.family in _LINUX_FAMILIES)
        from_pkg_manager = any(s in (self.source or "").lower() for s in HOST_PACKAGE_SOURCES)
        return marked or (linux_host and from_pkg_manager)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def platform_for(source: Optional[str], host_os: Optional[OSInfo]) -> Optional[str]:
    src = (source or "").lower()
    if src.endswith("aws_rds"):
        return "rds"
    if "lambda" in src:
        return "lambda"
    if src.endswith(WEB_SCAN_SOURCE):
        return "web"
    if host_os and host_os.package_manager:
        return host_os.package_manager
    if "intune" in src or "defender" in src:
        return "windows_update"
    return None


def _clean_version(version: Any) -> Optional[str]:
    if version is None:
        return None
    text = str(version).strip()
    if not text or text.lower() in ("unknown", "none", "n/a", "-"):
        return None
    return text


def _looks_like_os(name: str) -> bool:
    low = (name or "").strip().lower()
    return any(low == p or low.startswith(p + " ") for p in _OS_NAME_PREFIXES)


def make_item(
    name: str,
    version: Any,
    source: str,
    *,
    asset: Optional[str] = None,
    vendor: Optional[str] = None,
    host_os: Optional[OSInfo] = None,
    last_seen: Optional[datetime] = None,
    legacy_category: Optional[str] = None,
    version_explicit: bool = True,
    distro_hint: bool = False,
) -> Optional[StackItem]:
    """Build a StackItem from a raw (name, version) pair, recognising OS rows."""
    name = str(name or "").strip()
    if not name:
        return None
    version = _clean_version(version)
    product = resolve_product(name, vendor=vendor, source=source, legacy_category=legacy_category)

    if not product.known and _looks_like_os(name):
        os_info = parse_os(name, version)
        if os_info is not None:
            return os_item(os_info, source, asset=asset, last_seen=last_seen)

    return StackItem(
        name=product.name if product.known else name,
        version=version,
        source=source,
        product=product,
        asset=asset,
        vendor=product.vendor or vendor,
        category=product.category,
        last_seen=_aware(last_seen),
        raw_name=name,
        os=host_os,
        platform=platform_for(source, host_os),
        version_explicit=version_explicit,
        distro_hint=distro_hint,
    )


def os_item(os_info: OSInfo, source: str, *, asset: Optional[str] = None,
            last_seen: Optional[datetime] = None) -> StackItem:
    vendor = {
        "windows": "Microsoft Corporation", "macos": "Apple Inc.", "ubuntu": "Canonical",
        "amazon": "Amazon Web Services", "debian": "Debian Project",
    }.get(os_info.family)
    return StackItem(
        name=os_info.name,
        version=os_info.version,
        source=source,
        product=ProductInfo(key=os_info.key, name=os_info.name, vendor=vendor, category="os", eol=os_info.eol),
        asset=asset,
        vendor=vendor,
        category="os",
        last_seen=_aware(last_seen),
        raw_name=os_info.name,
        os=os_info,
        is_os=True,
        platform=os_info.package_manager,
    )


class _Merger:
    def __init__(self) -> None:
        self.items: Dict[Tuple[str, str, str], StackItem] = {}
        self._by_product_version: Dict[Tuple[str, str], int] = {}

    def add(self, item: Optional[StackItem], *, only_if_new_product_version: bool = False) -> None:
        if item is None:
            return
        key = item.dedupe_key
        pv = (key[0], key[1])
        if only_if_new_product_version and pv in self._by_product_version:
            return
        existing = self.items.get(key)
        if existing is not None:
            if item.last_seen and (existing.last_seen is None or item.last_seen > existing.last_seen):
                existing.last_seen = item.last_seen
            return
        self.items[key] = item
        self._by_product_version[pv] = self._by_product_version.get(pv, 0) + 1


def web_detections(db: Session, org_id: str) -> List[Dict[str, Any]]:
    """Explicit-version detections from the org's scanned web assets."""
    out: List[Dict[str, Any]] = []
    try:
        rows = db.query(WebAsset).filter(WebAsset.org_id == org_id).all()
    except Exception as exc:
        logger.debug("web_assets unavailable: %s", exc)
        db.rollback()
        return out
    for row in rows:
        if not row.last_scan:
            continue
        try:
            scan = json.loads(row.last_scan)
        except (TypeError, ValueError):
            continue
        host = urlsplit(scan.get("final_url") or row.url).hostname or row.url
        for det in scan.get("detected") or []:
            if not det.get("name") or not det.get("version"):
                continue
            if det.get("confidence") == "unverified":
                continue  # inferred versions are shown on the scan, not matched against CVEs
            out.append({"name": det["name"], "version": det["version"], "asset": host,
                        "last_seen": row.last_scan_at, "distro_package": bool(det.get("distro_package"))})
    return out


def collect_inventory(db: Session, org_id: str) -> List[StackItem]:
    """All software the organization is known to run, de-duplicated."""
    merger = _Merger()

    # A. latest discovery snapshot (hosts, devices, cloud databases)
    inventory = (
        db.query(TechnologyInventory)
        .filter(TechnologyInventory.org_id == org_id)
        .order_by(TechnologyInventory.last_discovered_at.desc(), TechnologyInventory.id.desc())
        .first()
    )
    if inventory is not None:
        assets = db.query(HostAsset).filter(HostAsset.inventory_id == inventory.id).all()
        products_by_asset: Dict[str, List[InstalledProduct]] = {}
        if assets:
            rows = (
                db.query(InstalledProduct)
                .filter(InstalledProduct.asset_id.in_([a.id for a in assets]))
                .all()
            )
            for row in rows:
                products_by_asset.setdefault(row.asset_id, []).append(row)
        for asset in assets:
            asset_name = asset.hostname or asset.ip_address or asset.id
            host_os = parse_os(asset.operating_system)
            products = products_by_asset.get(asset.id, [])
            default_source = next((p.installation_source for p in products if p.installation_source), None)
            if not default_source:
                default_source = "aws" if (asset.cloud_provider or "").upper() == "AWS" else "discovery"
            if host_os is not None:
                merger.add(os_item(host_os, default_source, asset=asset_name, last_seen=asset.last_seen))
            for p in products:
                merger.add(make_item(
                    p.product_name, p.version, p.installation_source or default_source,
                    asset=asset_name, vendor=p.vendor, host_os=host_os,
                    last_seen=p.last_seen or asset.last_seen,
                ))

    # B. connector-fed software list (no asset attached)
    for row in db.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == org_id).all():
        if (row.source or "") == WEB_SCAN_SOURCE:
            continue  # covered, with its asset, by C
        merger.add(
            make_item(row.product, row.version, row.source or "discovery", vendor=row.vendor,
                      last_seen=row.last_seen),
            only_if_new_product_version=True,
        )

    # C. versions read from the organization's own websites
    for det in web_detections(db, org_id):
        merger.add(make_item(det["name"], det["version"], WEB_SCAN_SOURCE, asset=det["asset"],
                             last_seen=det.get("last_seen"), distro_hint=det.get("distro_package", False)))

    # D. tech-stack registry: manual entries, plus anything discovery synced that we have not seen
    for row in db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all():
        auto = (row.notes or "").startswith(AUTO_NOTE_PREFIX)
        merger.add(
            make_item(row.component_name, row.version, "discovery" if auto else MANUAL_SOURCE,
                      legacy_category=row.category, last_seen=row.updated_at or row.created_at),
            only_if_new_product_version=True,
        )

    return list(merger.items.values())


def inventory_sources(db: Session, org_id: str) -> Dict[str, str]:
    """Per-source status of the inventory itself (not the intelligence feeds)."""
    sources: Dict[str, str] = {"aws": "not_connected", "ms_graph": "not_connected", "wazuh": "not_connected"}
    try:
        from app.models.connector import Connector, ConnectorStatus
        for row in db.query(Connector).filter(Connector.org_id == org_id).all():
            if row.status == ConnectorStatus.inactive.value:
                continue
            ctype = str(row.connector_type or "")
            if ctype in ("aws", "aws_security_hub"):
                sources["aws"] = "connected_not_scanned"
            elif ctype == "microsoft":
                sources["ms_graph"] = "connected_not_scanned"
            elif ctype == "wazuh":
                sources["wazuh"] = "connected_not_scanned"
        from app.models.wazuh_config import WazuhConfig
        if db.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first():
            sources["wazuh"] = "connected_not_scanned"
    except Exception as exc:
        logger.debug("connector lookup failed: %s", exc)
        db.rollback()

    inventory = (
        db.query(TechnologyInventory)
        .filter(TechnologyInventory.org_id == org_id)
        .order_by(TechnologyInventory.last_discovered_at.desc(), TechnologyInventory.id.desc())
        .first()
    )
    if inventory is not None and inventory.discovery_source:
        # "orchestrator;wazuh=not_connected;ms_graph=ok;assets=3;aws=partial;denied=..."
        for token in str(inventory.discovery_source).split(";"):
            if "=" not in token:
                continue
            name, value = token.split("=", 1)
            if name in sources:
                sources[name] = value

    try:
        web_rows = db.query(WebAsset).filter(WebAsset.org_id == org_id).all()
    except Exception:
        db.rollback()
        web_rows = []
    if not web_rows:
        sources[WEB_SCAN_SOURCE] = "not_configured"
    elif any(r.last_scan for r in web_rows):
        sources[WEB_SCAN_SOURCE] = "ok"
    else:
        sources[WEB_SCAN_SOURCE] = "not_scanned"
    return sources
