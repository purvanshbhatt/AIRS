"""
Vulnerability intelligence service.

Takes the unified inventory, looks every product up in the public feeds
(cache first, 24 h TTL, bounded time budget), keeps only vulnerabilities
whose affected range contains the installed version, and produces the API
payloads for the stack, the advisories and the refresh endpoints.

Trust rules (deterministic):
  * ``confidence == "confirmed"`` only when
      (a) the CVE is on CISA KEV AND the installed version is provably below
          a fixed version published by OSV (version-aware), or
      (b) endoflife.date says the installed release cycle is past end of life.
    NVD/CPE matches are always ``unverified``. Linux distribution packages
    are never confirmed from an upstream version comparison (backports).
  * A feed that could not be fetched is never silent: the last cached answer
    is served with ``stale: true`` and the feed is named in ``failing_feeds``.
  * Nothing here feeds the readiness score. Counts only.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.services.vuln_intel import remediation as rem
from app.services.vuln_intel.cache import CacheEntry, IntelCache
from app.services.vuln_intel.clients import (
    Deadline,
    DeadlineExceeded,
    EOLClient,
    IntelHTTP,
    KEVClient,
    NVDClient,
    OSVClient,
    RateLimited,
)
from app.services.vuln_intel.inventory import (
    HOST_PACKAGE_SOURCES,
    StackItem,
    collect_inventory,
    inventory_sources,
)
from app.services.vuln_intel.matcher import (
    SEVERITY_RANK,
    match_nvd,
    match_osv,
    sort_vulnerabilities,
)
from app.services.vuln_intel.versions import max_version, newer_than

logger = logging.getLogger("airs.vuln_intel")

FEEDS = ("osv", "nvd", "cisa_kev", "endoflife")
KEV_KEY = "kev:catalog"
MAX_ITEMS = 500
MAX_VULNS_PER_ITEM = 100
MAX_TOP_ACTIONS = 5
MAX_ADVISORIES = 200

CONFIRMED = "confirmed"
UNVERIFIED = "unverified"

_STATUS_ORDER = {"vulnerable": 0, "end_of_life": 1, "update_available": 2, "ok": 3, "unknown": 4}


@dataclass
class IntelClients:
    osv: OSVClient
    nvd: NVDClient
    kev: KEVClient
    eol: EOLClient

    @classmethod
    def default(cls, transport: Any = None) -> "IntelClients":
        from app.core.config import settings
        api_key = getattr(settings, "NVD_API_KEY", None)
        return cls(
            osv=OSVClient(IntelHTTP(transport=transport)),
            nvd=NVDClient(IntelHTTP(transport=transport, timeout=8.0), api_key=api_key),
            kev=KEVClient(IntelHTTP(transport=transport, timeout=8.0)),
            eol=EOLClient(IntelHTTP(transport=transport)),
        )


@dataclass(frozen=True)
class Lookup:
    feed: str                      # osv | nvd | cisa_kev | endoflife
    key: str                       # cache key
    args: Tuple[str, ...] = ()
    priority: int = 5
    distro_aware: bool = False     # OSV distro ecosystem: compares the distro's own package version


@dataclass
class Enriched:
    item: StackItem
    vulns: List[Dict[str, Any]] = field(default_factory=list)
    eol: Optional[Dict[str, Any]] = None
    status: str = "unknown"
    checked: bool = False
    reason: Optional[str] = None
    ctx: Optional[rem.RemediationContext] = None


@dataclass
class IntelResult:
    enriched: List[Enriched]
    feeds: Dict[str, Dict[str, Any]]
    errors: List[str]
    looked_up: int
    queued: int
    last_refresh: Optional[datetime]
    generated_at: datetime

    @property
    def stale(self) -> bool:
        return any(f.get("stale") for f in self.feeds.values())

    @property
    def failing_feeds(self) -> List[str]:
        return [name for name, f in self.feeds.items() if f.get("error")]


def _iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_date(value: Any) -> Optional[date]:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Lookup planning
# ---------------------------------------------------------------------------

def plan_vuln_lookup(item: StackItem) -> Optional[Lookup]:
    """Which feed can answer 'is this version vulnerable?' for an item (or None)."""
    if item.is_os or not item.version:
        return None
    product = item.product
    host_eco = item.os.osv_ecosystem if item.os else None
    from_pkg_manager = any(s in (item.source or "").lower() for s in HOST_PACKAGE_SOURCES)
    if host_eco and from_pkg_manager and item.platform in ("apt", "apk"):
        # Distribution package on a distro OSV tracks: ask for the distro's own advisories,
        # which already account for backported fixes.
        package = (item.raw_name or item.name).strip().lower()
        return Lookup("osv", f"osv:{host_eco}:{package}:{item.version}",
                      (host_eco, package, item.version), 2 if product.known else 4, True)
    if product.osv:
        ecosystem, package = product.osv
        version = item.version.strip()
        if version[:1] in ("v", "V") and version[1:2].isdigit():
            version = version[1:]
        return Lookup("osv", f"osv:{ecosystem}:{package}:{version}", (ecosystem, package, version), 2)
    if product.cpe:
        version = item.lookup_version
        if not version:
            return None
        vendor, name = product.cpe
        return Lookup("nvd", f"nvd:{vendor}:{name}:{version}", (vendor, name, version), 3)
    return None


def plan_eol_lookup(item: StackItem) -> Optional[Lookup]:
    slug = item.os.eol if (item.is_os and item.os) else item.product.eol
    if not slug:
        return None
    return Lookup("endoflife", f"eol:{slug}", (slug,), 1)


def _cycle_candidates(item: StackItem) -> List[str]:
    if item.is_os and item.os:
        return [c.lower() for c in item.os.cycles]
    version = item.lookup_version
    if not version:
        return []
    parts = version.split(".")
    return [".".join(parts[:n]) for n in range(len(parts), 0, -1)]


def resolve_eol(item: StackItem, cycles: List[Dict[str, Any]], today: date) -> Optional[Dict[str, Any]]:
    """End-of-life facts for the item's release cycle, or None when the cycle is not listed."""
    if not cycles:
        return None
    by_cycle = {str(c.get("cycle", "")).lower(): c for c in cycles}
    cycle = next((by_cycle[c] for c in _cycle_candidates(item) if c in by_cycle), None)
    if cycle is None:
        return None

    def _is_eol(c: Dict[str, Any]) -> bool:
        raw = c.get("eol")
        if raw is True:
            return True
        d = _parse_date(raw)
        return bool(d and d <= today)

    is_eol = _is_eol(cycle)
    eol_date = cycle.get("eol") if isinstance(cycle.get("eol"), str) else None
    build_numbered = bool(item.is_os and item.os and item.os.family in ("windows", "amazon"))
    latest: Optional[str] = None
    if is_eol:
        newest = next((c for c in cycles if not _is_eol(c)), None)
        if newest is not None:
            if item.is_os:
                label = str(newest.get("label") or newest.get("cycle") or "")
                latest = label.replace(" (E)", "").replace(" (W)", "") or None
            else:
                latest = newest.get("latest") or str(newest.get("cycle"))
    elif not build_numbered:
        latest = cycle.get("latest")
    return {
        "is_eol": is_eol,
        "eol_date": eol_date,
        "latest_version": str(latest) if latest else None,
        "source": "endoflife.date",
        "_cycle": str(cycle.get("cycle")),
        "_slug": item.os.eol if (item.is_os and item.os) else item.product.eol,
    }


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def vulnerability_confidence(vuln: Dict[str, Any], item: StackItem, lookup: Optional[Lookup]) -> str:
    """``confirmed`` needs KEV + a version-aware proof; everything else is ``unverified``."""
    if not vuln.get("known_exploited"):
        return UNVERIFIED
    if vuln.get("source") != "osv":
        return UNVERIFIED                      # NVD/CPE matching is never a proof
    fixed = vuln.get("fixed_version")
    if not fixed or not item.version or not item.version_explicit:
        return UNVERIFIED                      # KEV alone carries no version information
    distro_aware = bool(lookup and lookup.distro_aware)
    if item.is_distro_package and not distro_aware:
        return UNVERIFIED                      # backports: upstream numbers prove nothing
    return CONFIRMED


def eol_confidence(eol: Optional[Dict[str, Any]], item: StackItem) -> str:
    if not eol or not eol.get("is_eol"):
        return UNVERIFIED
    if item.is_distro_package or not item.version_explicit:
        return UNVERIFIED                      # the distribution may still maintain it
    return CONFIRMED


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class VulnIntelService:
    def __init__(
        self,
        db: Session,
        clients: Optional[IntelClients] = None,
        now: Optional[Callable[[], datetime]] = None,
    ):
        self.db = db
        self.clients = clients or IntelClients.default()
        self.cache = IntelCache(db)
        self._now = now or (lambda: datetime.now(timezone.utc))

    # -- feed access -------------------------------------------------------

    def _fetch(self, lookup: Lookup, deadline: Deadline) -> Any:
        if lookup.feed == "osv":
            return self.clients.osv.query(*lookup.args, deadline=deadline)
        if lookup.feed == "nvd":
            return self.clients.nvd.query(*lookup.args, deadline=deadline)
        if lookup.feed == "cisa_kev":
            return self.clients.kev.fetch(deadline=deadline)
        if lookup.feed == "endoflife":
            return self.clients.eol.fetch(*lookup.args, deadline=deadline)
        raise ValueError(f"unknown feed {lookup.feed}")

    def enrich(
        self,
        items: List[StackItem],
        *,
        network: bool = True,
        max_age: Optional[timedelta] = None,
        budget_seconds: float = 8.0,
        max_lookups: int = 60,
    ) -> IntelResult:
        now = self._now()
        deadline = Deadline(budget_seconds)

        plans: Dict[str, Tuple[Optional[Lookup], Optional[Lookup]]] = {}
        needed: Dict[str, Lookup] = {}
        for item in items:
            vuln_lk, eol_lk = plan_vuln_lookup(item), plan_eol_lookup(item)
            plans[item.id] = (vuln_lk, eol_lk)
            for lk in (vuln_lk, eol_lk):
                if lk is not None and (lk.key not in needed or lk.priority < needed[lk.key].priority):
                    needed[lk.key] = lk
        if any(lk.feed in ("osv", "nvd") for lk in needed.values()):
            needed[KEV_KEY] = Lookup("cisa_kev", KEV_KEY, (), 0)

        entries: Dict[str, CacheEntry] = {}
        outcome: Dict[str, Dict[str, Any]] = {}
        to_fetch: List[Lookup] = []
        for lk in needed.values():
            entry = self.cache.get(lk.key)
            if entry is not None:
                entries[lk.key] = entry
            if entry is not None and entry.is_fresh(now, max_age):
                outcome[lk.key] = {"state": "fresh"}
            else:
                outcome[lk.key] = {"state": "stale" if entry is not None else "missing", "queued": True}
                to_fetch.append(lk)

        looked_up = 0
        errors: List[str] = []
        if network and to_fetch:
            to_fetch.sort(key=lambda l: (l.priority, l.key))
            nvd_budget = self.clients.nvd.max_lookups_per_refresh
            batch: List[Lookup] = []
            for lk in to_fetch:
                if len(batch) >= max_lookups:
                    break
                if lk.feed == "nvd":
                    if nvd_budget <= 0:
                        continue
                    nvd_budget -= 1
                batch.append(lk)

            executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="vuln-intel")
            try:
                futures = {executor.submit(self._fetch, lk, deadline): lk for lk in batch}
                done, _pending = wait(list(futures), timeout=max(0.1, deadline.remaining() + 0.5))
                for future, lk in futures.items():
                    if future not in done:
                        future.cancel()
                        continue  # stays queued
                    try:
                        payload = future.result()
                    except (RateLimited, DeadlineExceeded) as exc:
                        outcome[lk.key]["note"] = str(exc)
                        continue  # queued for the next refresh, not a feed failure
                    except Exception as exc:  # IntelError and anything unexpected
                        outcome[lk.key].update({"queued": False, "error": str(exc) or type(exc).__name__})
                        logger.warning("Intel lookup %s failed: %s", lk.key, exc)
                        continue
                    stored = self.cache.set(lk.key, lk.feed, payload, now=now)
                    entries[lk.key] = stored or CacheEntry(lk.key, payload, now, now + self.cache.ttl)
                    outcome[lk.key] = {"state": "fetched"}
                    looked_up += 1
            finally:
                executor.shutdown(wait=False, cancel_futures=True)

        # -- per-feed freshness ------------------------------------------------
        feeds: Dict[str, Dict[str, Any]] = {}
        for feed in FEEDS:
            lks = [lk for lk in needed.values() if lk.feed == feed]
            if not lks:
                feeds[feed] = {"status": "not_used", "as_of": None, "stale": False, "error": None, "queued": 0}
                continue
            failed = [lk for lk in lks if outcome[lk.key].get("error")]
            queued = [lk for lk in lks if outcome[lk.key].get("queued")]
            unanswered = failed + queued
            have = [entries[lk.key] for lk in lks if lk.key in entries]
            as_of = min((e.fetched_at for e in have), default=None)
            stale = any(lk.key in entries for lk in unanswered)
            if failed:
                if not have:
                    status = "unavailable"
                elif all(lk.key in entries for lk in failed) and not queued:
                    status = "stale"
                else:
                    status = "partial"
                error = outcome[failed[0].key]["error"]
                errors.append(f"{feed}: {error}" + (f" ({len(failed)} lookups failed)" if len(failed) > 1 else ""))
            elif queued:
                status, error = "partial", None
                errors.append(f"{feed}: {len(queued)} lookup{'s' if len(queued) != 1 else ''} queued "
                              f"for the next refresh (rate limit or time budget)")
            else:
                status, error = "ok", None
            feeds[feed] = {"status": status, "as_of": _iso(as_of), "stale": stale, "error": error,
                           "queued": len(queued)}

        kev_entry = entries.get(KEV_KEY)
        kev_cves: Dict[str, Any] = (kev_entry.payload or {}).get("cves", {}) if kev_entry else {}

        # -- per item ------------------------------------------------------------
        today = now.date()
        enriched: List[Enriched] = []
        used: List[datetime] = [e.fetched_at for k, e in entries.items() if k in needed]
        for item in items:
            vuln_lk, eol_lk = plans[item.id]
            result = Enriched(item=item)

            eol_entry = entries.get(eol_lk.key) if eol_lk else None
            if eol_entry is not None:
                result.eol = resolve_eol(item, eol_entry.payload or [], today)
                if result.eol is not None:
                    result.eol["_as_of"] = _iso(eol_entry.fetched_at)

            vuln_entry = entries.get(vuln_lk.key) if vuln_lk else None
            vulns: List[Dict[str, Any]] = []
            if vuln_lk is not None and vuln_entry is not None:
                records = vuln_entry.payload or []
                if vuln_lk.feed == "osv":
                    vulns = match_osv(records, vuln_lk.args[2], vuln_lk.args[0])
                else:
                    family = item.os.family if item.os else None
                    vulns = match_nvd(records, vuln_lk.args[2], os_family=family)
                for v in vulns:
                    v["source"] = vuln_lk.feed
                    v["as_of"] = _iso(vuln_entry.fetched_at)
                    v["known_exploited"] = any(a in kev_cves for a in (v.get("aliases") or [v["id"]]))
                    v["confidence"] = vulnerability_confidence(v, item, vuln_lk)
                vulns = sort_vulnerabilities(vulns)
            result.vulns = vulns

            # "Checked" means every feed that can speak about this product answered.
            vuln_checked = vuln_lk is not None and vuln_entry is not None
            vuln_pending = vuln_lk is not None and vuln_entry is None
            result.checked = vuln_checked if vuln_lk is not None else result.eol is not None
            latest = result.eol.get("latest_version") if result.eol else None
            if not item.version:
                result.status, result.reason = "unknown", "Version not reported"
                result.checked = False
            elif vulns:
                result.status = "vulnerable"
            elif result.eol and result.eol["is_eol"]:
                result.status = "end_of_life"
            elif latest and newer_than(latest, item.lookup_version):
                result.status = "update_available"
            elif result.checked:
                result.status = "ok"
            else:
                result.status = "unknown"
            if item.version and not result.checked:
                if vuln_pending:
                    state = outcome.get(vuln_lk.key, {})
                    result.reason = ("Vulnerability feed unavailable" if state.get("error")
                                     else "Lookup queued for the next refresh")
                elif item.product.known or item.is_os:
                    result.reason = "No version-aware public feed covers this product"
                else:
                    result.reason = "Product name not in the alias table"

            result.ctx = self._context(item, latest)
            for v in result.vulns:
                ctx = rem.RemediationContext(**{**result.ctx.__dict__, "fixed_version": v.get("fixed_version")})
                v["remediation"] = rem.remediation_text(
                    rem.build_steps(v.get("severity"), bool(v.get("known_exploited")), [ctx])
                )
            enriched.append(result)

        return IntelResult(
            enriched=enriched,
            feeds=feeds,
            errors=errors,
            looked_up=looked_up,
            queued=sum(f.get("queued", 0) for f in feeds.values()),
            last_refresh=max(used) if used else None,
            generated_at=now,
        )

    @staticmethod
    def _context(item: StackItem, latest: Optional[str]) -> rem.RemediationContext:
        package: Optional[str] = None
        if item.platform == "apt":
            package = item.product.apt
        elif item.platform in ("dnf", "yum"):
            package = item.product.rpm
        if not package and any(s in (item.source or "").lower() for s in HOST_PACKAGE_SOURCES):
            package = (item.raw_name or "").lower() or None
        if not package and item.product.osv:
            package = item.product.osv[1]
        return rem.RemediationContext(
            name=item.name,
            version=item.version,
            asset=item.asset,
            platform=item.platform,
            package=package,
            ecosystem=item.product.osv[0] if item.product.osv else None,
            product_key=item.product_key,
            os_name=(f"{item.os.name} {item.os.version}".strip() if item.os and item.os.version
                     else (item.os.name if item.os else None)),
            latest_version=latest,
        )


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------

def source_family(source: Optional[str]) -> str:
    src = (source or "").lower()
    if src.startswith("demo_"):
        src = src[len("demo_"):]
    if src.startswith("aws"):
        return "aws"
    if "intune" in src or "defender" in src or src in ("ms_graph", "microsoft"):
        return "microsoft"
    if "wazuh" in src:
        return "wazuh"
    if src.endswith("web_scan"):
        return "web_scan"
    return src or "unknown"


def build_coverage(result: IntelResult, inv_sources: Dict[str, str]) -> Dict[str, Any]:
    """What was looked at and, just as important, what was not."""
    seen = sorted({source_family(e.item.source) for e in result.enriched})
    distinct: Dict[Tuple[str, str], bool] = {}
    for e in result.enriched:
        key = (e.item.product_key, (e.item.version or "").lower())
        distinct[key] = distinct.get(key, False) or e.checked
    total = len(distinct)
    checked = sum(1 for ok in distinct.values() if ok)

    not_seen: List[str] = []
    if "microsoft" not in seen:
        connected = inv_sources.get("ms_graph", "not_connected") not in ("not_connected",)
        not_seen.append(
            "Device inventory connected but it reported no software (Microsoft Intune)" if connected
            else "No device inventory connected (Microsoft Intune): laptops and PCs are not checked"
        )
    if "aws" not in seen and "wazuh" not in seen:
        connected = any(inv_sources.get(k, "not_connected") != "not_connected" for k in ("aws", "wazuh"))
        not_seen.append(
            "Server inventory connected but it reported no software (AWS / Wazuh)" if connected
            else "No server inventory connected (AWS or Wazuh): servers are not checked"
        )
    web = inv_sources.get("web_scan", "not_configured")
    if "web_scan" not in seen:
        if web == "not_configured":
            not_seen.append("Website not added")
        elif web == "not_scanned":
            not_seen.append("Website added but not scanned yet")
        else:
            not_seen.append("Website scanned but it does not reveal software versions")

    failing = result.failing_feeds
    if total == 0:
        level = "none"
        message = ("Nothing has been checked yet. Connect a system or add your website: "
                   "an empty list does not mean you are safe.")
    else:
        ratio = checked / total
        if ratio < 0.34:
            level = "poor"
            message = (f"Only {checked} of {total} products could be checked against public vulnerability "
                       f"feeds. An empty list here does not mean you are safe.")
        elif ratio < 0.8 or not_seen:
            level = "partial"
            message = f"{checked} of {total} products checked. {total - checked} could not be checked."
            if not_seen:
                message += " Some parts of your environment are not connected yet."
        else:
            level = "good"
            message = f"{checked} of {total} products checked against public vulnerability feeds."
    if failing:
        if level == "good":
            level = "partial"
        message += f" Feed problem: {', '.join(failing)} could not be refreshed, results may be out of date."
    elif result.stale:
        message += " Some results come from an older cached copy."

    return {
        "sources_seen": seen,
        "not_seen": not_seen,
        "products_total": total,
        "products_checked": checked,
        "products_not_checked": total - checked,
        "level": level,
        "message": message,
    }


# ---------------------------------------------------------------------------
# API payloads
# ---------------------------------------------------------------------------

_PUBLIC_VULN_FIELDS = ("id", "severity", "cvss", "summary", "fixed_version", "published",
                       "known_exploited", "references", "remediation", "confidence", "source")


def _public_eol(eol: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if eol is None:
        return None
    return {k: eol[k] for k in ("is_eol", "eol_date", "latest_version", "source")}


def _item_payload(e: Enriched) -> Dict[str, Any]:
    item = e.item
    return {
        "id": item.id,
        "name": item.name,
        "vendor": item.vendor,
        "version": item.version,
        "category": item.category,
        "source": item.source,
        "asset": item.asset,
        "last_seen": _iso(item.last_seen),
        "eol": _public_eol(e.eol),
        "vulnerabilities": [{k: v.get(k) for k in _PUBLIC_VULN_FIELDS} for v in e.vulns[:MAX_VULNS_PER_ITEM]],
        "vulnerability_count": len(e.vulns),
        "status": e.status,
        "checked": e.checked,
        "not_checked_reason": None if e.checked else e.reason,
        "canonical": item.product_key if (item.product.known or item.is_os) else None,
    }


def build_summary(result: IntelResult, advisories: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    critical_ids = set()
    kev_ids = set()
    for e in result.enriched:
        for v in e.vulns:
            if v.get("severity") == "critical":
                critical_ids.add(v["id"])
            if v.get("known_exploited"):
                kev_ids.add(v["id"])
    advisories = advisories if advisories is not None else build_advisories(result)
    return {
        "total": len(result.enriched),
        "vulnerable": sum(1 for e in result.enriched if e.vulns),
        "critical": len(critical_ids),
        "known_exploited": len(kev_ids),
        "end_of_life": sum(1 for e in result.enriched if e.eol and e.eol.get("is_eol")),
        "last_intel_refresh": _iso(result.last_refresh),
        "checked": sum(1 for e in result.enriched if e.checked),
        "not_checked": sum(1 for e in result.enriched if not e.checked),
        "confirmed_advisories": sum(1 for a in advisories if a["confidence"] == CONFIRMED),
        "unverified_advisories": sum(1 for a in advisories if a["confidence"] == UNVERIFIED),
    }


def _sorted_enriched(result: IntelResult) -> List[Enriched]:
    def key(e: Enriched):
        kev = sum(1 for v in e.vulns if v.get("known_exploited"))
        top = max((SEVERITY_RANK.get(v.get("severity") or "unknown", 0) for v in e.vulns), default=0)
        return (_STATUS_ORDER.get(e.status, 9), -kev, -top, e.item.name.lower(), e.item.asset or "")
    return sorted(result.enriched, key=key)


def _feeds_public(result: IntelResult) -> Dict[str, Dict[str, Any]]:
    return {name: {k: f.get(k) for k in ("status", "as_of", "stale", "error")} for name, f in result.feeds.items()}


def stack_payload(result: IntelResult, inv_sources: Dict[str, str], demo: bool) -> Dict[str, Any]:
    ordered = _sorted_enriched(result)
    sources = dict(inv_sources)
    sources.update({name: f["status"] for name, f in result.feeds.items()})
    advisories = build_advisories(result)
    return {
        "items": [_item_payload(e) for e in ordered[:MAX_ITEMS]],
        "truncated": len(ordered) > MAX_ITEMS,
        "summary": build_summary(result, advisories),
        "sources": sources,
        "demo": demo,
        "coverage": build_coverage(result, inv_sources),
        "feeds": _feeds_public(result),
        "stale": result.stale,
        "failing_feeds": result.failing_feeds,
        "generated_at": _iso(result.generated_at),
    }


# ---------------------------------------------------------------------------
# Advisories and top actions
# ---------------------------------------------------------------------------

def _affected(e: Enriched) -> Dict[str, Any]:
    return {"name": e.item.name, "version": e.item.version, "asset": e.item.asset}


def _eol_steps(e: Enriched) -> List[str]:
    item, eol = e.item, e.eol or {}
    label = f"{item.name} {eol.get('_cycle') or item.version or ''}".strip()
    if item.is_os and item.os and item.os.version:
        label = f"{item.name} {item.os.version}"
    when = f" on {eol['eol_date']}" if eol.get("eol_date") else ""
    steps = [f"End of life: {label} stopped receiving security fixes{when}. Plan the upgrade within 30 days."]
    steps.append(_eol_fix_line(e))
    ctx = e.ctx
    if ctx is not None:
        if not item.is_os:
            steps.append(rem.how_line(ctx, eol.get("latest_version")))
        steps.append(rem.who_line([ctx]))
    steps.append(rem.VERIFY_LINE)
    return steps


def _eol_fix_line(e: Enriched, generic: bool = False) -> str:
    item, eol = e.item, e.eol or {}
    latest = eol.get("latest_version")
    if item.is_os:
        where = f" on {item.asset}" if (item.asset and not generic) else ""
        target = f" (currently {latest})" if latest else ""
        if item.os and item.os.family == "windows" and item.name == "Windows 10":
            return (f"Upgrade{where or ' each PC'} to Windows 11 where the hardware supports it; otherwise "
                    f"enrol it in Extended Security Updates or replace it.")
        return f"Move{where or ' each system'} to a supported release of {item.name}{target}."
    target = f" (latest: {latest})" if latest else ""
    installed = f" from {item.version}" if item.version else ""
    return f"Upgrade {item.name}{installed} to a supported release{target}."


def build_advisories(result: IntelResult) -> List[Dict[str, Any]]:
    """One advisory per vulnerability (across every place it was found) and per end-of-life release."""
    grouped: Dict[str, Dict[str, Any]] = {}

    for e in result.enriched:
        for v in e.vulns:
            adv = grouped.get(v["id"])
            ctx = rem.RemediationContext(**{**e.ctx.__dict__, "fixed_version": v.get("fixed_version")})
            if adv is None:
                adv = grouped[v["id"]] = {
                    "id": v["id"],
                    "kind": "vulnerability",
                    "severity": v.get("severity") or "unknown",
                    "cvss": v.get("cvss"),
                    "summary": v.get("summary") or "",
                    "published": v.get("published"),
                    "known_exploited": bool(v.get("known_exploited")),
                    "affected": [],
                    "fixed_version": None,
                    "steps": [],
                    "references": list(v.get("references") or []),
                    "confidence": UNVERIFIED,
                    "source": v.get("source"),
                    "as_of": v.get("as_of"),
                    "_fixed": [],
                    "_contexts": [],
                    "_confirmed": [],
                    "_confirmed_contexts": [],
                }
            entry = _affected(e)
            if entry not in adv["affected"]:
                adv["affected"].append(entry)
                adv["_contexts"].append(ctx)
                if v.get("confidence") == CONFIRMED:
                    adv["_confirmed"].append(e)
                    adv["_confirmed_contexts"].append(ctx)
            adv["_fixed"].append(v.get("fixed_version"))
            adv["known_exploited"] = adv["known_exploited"] or bool(v.get("known_exploited"))
            if SEVERITY_RANK.get(v.get("severity") or "unknown", 0) > SEVERITY_RANK.get(adv["severity"], 0):
                adv["severity"], adv["cvss"] = v["severity"], v.get("cvss")
            if v.get("confidence") == CONFIRMED:
                adv["confidence"] = CONFIRMED

        if e.eol and e.eol.get("is_eol"):
            cycle = e.eol.get("_cycle") or (e.item.version or "")
            prefix = e.eol.get("_slug") if e.item.is_os else e.item.product_key
            adv_id = f"EOL-{prefix}-{cycle}".replace(" ", "-")
            adv = grouped.get(adv_id)
            if adv is None:
                label = f"{e.item.name} {cycle}".strip()
                if e.item.is_os and e.item.os and e.item.os.version:
                    label = f"{e.item.name} {e.item.os.version}"
                when = f" on {e.eol['eol_date']}" if e.eol.get("eol_date") else ""
                eol_date = e.eol.get("eol_date")
                adv = grouped[adv_id] = {
                    "id": adv_id,
                    "kind": "end_of_life",
                    "severity": "high",
                    "cvss": None,
                    "summary": (f"{label} reached end of life{when}. It no longer receives security fixes, "
                                f"so new vulnerabilities in it will stay open."),
                    "published": f"{eol_date}T00:00:00Z" if eol_date else None,
                    "known_exploited": False,
                    "affected": [],
                    "fixed_version": e.eol.get("latest_version"),
                    "steps": _eol_steps(e),
                    "references": [f"https://endoflife.date/{e.eol.get('_slug')}"],
                    "confidence": UNVERIFIED,
                    "source": "endoflife",
                    "as_of": e.eol.get("_as_of"),
                    "_confirmed": [],
                    "_eol_date": eol_date,
                    "_label": label,
                }
            entry = _affected(e)
            is_confirmed = eol_confidence(e.eol, e.item) == CONFIRMED
            if entry not in adv["affected"]:
                adv["affected"].append(entry)
                if is_confirmed:
                    adv["_confirmed"].append(e)
            if is_confirmed:
                adv["confidence"] = CONFIRMED

    advisories: List[Dict[str, Any]] = []
    for adv in grouped.values():
        if adv["kind"] == "vulnerability":
            adv["fixed_version"] = max_version(adv.pop("_fixed"))
            adv["steps"] = rem.build_steps(adv["severity"], adv["known_exploited"], adv["_contexts"])
        advisories.append(adv)

    advisories.sort(key=lambda a: (
        0 if a["known_exploited"] else 1,
        -SEVERITY_RANK.get(a["severity"], 0),
        _inverted_date(a.get("published")),
        a["id"],
    ))
    return advisories


def _inverted_date(value: Optional[str]) -> str:
    text = (value or "0000-00-00")[:19]
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in text)


def _public_advisory(adv: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in adv.items() if not k.startswith("_")}


_NOUNS = {
    "web": ("website", "websites"),
    "rds": ("database", "databases"),
    "lambda": ("function", "functions"),
    "windows_update": ("computer", "computers"),
    "macos_update": ("computer", "computers"),
    "apt": ("server", "servers"), "dnf": ("server", "servers"),
    "yum": ("server", "servers"), "apk": ("server", "servers"),
}


def _where(enriched: List[Enriched]) -> Dict[str, Any]:
    names: List[str] = []
    nouns = set()
    for e in enriched:
        if e.item.asset and e.item.asset not in names:
            names.append(e.item.asset)
        nouns.add(_NOUNS.get(e.item.platform or "", ("system", "systems")))
    count = len(names) if names else len(enriched)
    singular, plural = nouns.pop() if len(nouns) == 1 else ("system", "systems")
    return {"count": count, "label": f"{count} {singular if count == 1 else plural}", "names": names[:10]}


def _send_to_it(title: str, why: str, where: Dict[str, Any], fix: str, how_soon: str, url: Optional[str]) -> str:
    names = ", ".join(where["names"]) if where["names"] else where["label"]
    lines = [
        "Hi,",
        "",
        "ResilAI flagged something on our systems that needs your attention.",
        "",
        f"What: {title}.",
        f"Why: {why}",
        f"Where: {names}",
        f"What to do: {fix}",
        f"How soon: {how_soon}",
    ]
    if url:
        lines.append(f"Reference: {url}")
    lines += ["", "Please reply when it is done so we can re-check. Thank you."]
    return "\n".join(lines)


def build_top_actions(advisories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """At most five things to do now. Confirmed findings only: KEV first, then end of life by date."""
    confirmed = [a for a in advisories if a["confidence"] == CONFIRMED]
    kev = [a for a in confirmed if a["kind"] == "vulnerability" and a["known_exploited"]]
    eol = sorted((a for a in confirmed if a["kind"] == "end_of_life"),
                 key=lambda a: (a.get("_eol_date") or "9999-12-31", a["id"]))
    actions: List[Dict[str, Any]] = []
    seen_titles = set()
    for adv in kev + eol:
        enriched: List[Enriched] = adv.get("_confirmed") or []
        if not enriched:
            continue
        where = _where(enriched)
        first = enriched[0]
        url = next(iter(adv.get("references") or []), None)
        if adv["kind"] == "vulnerability":
            names = sorted({e.item.name for e in enriched})
            title = f"Update {' and '.join(names[:2])} on {where['label']}"
            ctx = adv["_confirmed_contexts"][0]
            fix = rem.target_line(ctx, ctx.fixed_version)
            why = (f"{adv['id']} is being exploited in real attacks (CISA Known Exploited Vulnerabilities list) "
                   f"and our installed version is older than the fixed release.")
            how_soon = rem.KEV_URGENCY
            action_kind = "known_exploited"
            due = None
        else:
            label = adv.get("_label") or first.item.name
            verb = "Replace or upgrade" if first.item.is_os else "Update"
            title = f"{verb} {label} on {where['label']}"
            fix = _eol_fix_line(first, generic=len(enriched) > 1)
            when = f" on {adv['_eol_date']}" if adv.get("_eol_date") else ""
            why = f"{label} reached end of life{when} and no longer receives security fixes."
            how_soon = "Plan the upgrade within 30 days."
            action_kind = "end_of_life"
            due = adv.get("_eol_date")
        if title in seen_titles:
            continue
        seen_titles.add(title)
        actions.append({
            "id": adv["id"],
            "kind": action_kind,
            "title": title,
            "where": where,
            "fix": fix,
            "send_to_it_text": _send_to_it(title, why, where, fix, how_soon, url),
            "source_url": url,
            "confidence": CONFIRMED,
            "eol_date": due,
        })
        if len(actions) >= MAX_TOP_ACTIONS:
            break
    return actions


def advisories_payload(result: IntelResult, inv_sources: Dict[str, str], demo: bool) -> Dict[str, Any]:
    advisories = build_advisories(result)
    return {
        "advisories": [_public_advisory(a) for a in advisories[:MAX_ADVISORIES]],
        "total": len(advisories),
        "truncated": len(advisories) > MAX_ADVISORIES,
        "top_actions": build_top_actions(advisories),
        "generated_at": _iso(result.generated_at),
        "summary": build_summary(result, advisories),
        "coverage": build_coverage(result, inv_sources),
        "feeds": _feeds_public(result),
        "stale": result.stale,
        "failing_feeds": result.failing_feeds,
        "demo": demo,
    }


# ---------------------------------------------------------------------------
# Entry points used by the API and the scheduler
# ---------------------------------------------------------------------------

def load_items(db: Session, org_id: str, demo: bool) -> Tuple[List[StackItem], Dict[str, str]]:
    if demo:
        from app.services.demo.demo_stack import demo_inventory_sources, demo_stack_items
        return demo_stack_items(org_id), demo_inventory_sources()
    return collect_inventory(db, org_id), inventory_sources(db, org_id)


def run_intel(
    db: Session,
    org_id: str,
    demo: bool,
    *,
    clients: Optional[IntelClients] = None,
    network: bool = True,
    max_age: Optional[timedelta] = None,
    budget_seconds: float = 8.0,
    max_lookups: int = 60,
) -> Tuple[IntelResult, Dict[str, str]]:
    items, inv_sources = load_items(db, org_id, demo)
    service = VulnIntelService(db, clients=clients)
    result = service.enrich(items, network=network, max_age=max_age,
                            budget_seconds=budget_seconds, max_lookups=max_lookups)
    return result, inv_sources


def has_inventory_source(db: Session, org_id: str) -> bool:
    """True when the org has a connector (or Wazuh config) discovery can read."""
    return any(v != "not_connected" for k, v in inventory_sources(db, org_id).items() if k != "web_scan")


def run_discovery(db: Session, org_id: str) -> Dict[str, str]:
    """Run the existing discovery orchestrator, keeping manual tech-stack entries.

    The orchestrator rebuilds ``tech_stack_registry`` from what it discovered;
    entries a person typed in are put back afterwards.
    """
    from app.models.tech_stack import LtsStatus, TechStackItem
    from app.services.discovery.orchestrator import TechnologyDiscoveryOrchestrator
    from app.services.vuln_intel.inventory import AUTO_NOTE_PREFIX

    manual = [
        {"component_name": r.component_name, "version": r.version, "lts_status": r.lts_status,
         "major_versions_behind": r.major_versions_behind, "category": r.category, "notes": r.notes}
        for r in db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
        if not (r.notes or "").startswith(AUTO_NOTE_PREFIX)
    ]
    orchestrator = TechnologyDiscoveryOrchestrator(db, org_id)
    orchestrator.run_discovery_cycle()
    if manual:
        present = {
            (r.component_name, r.version)
            for r in db.query(TechStackItem).filter(TechStackItem.org_id == org_id).all()
        }
        for row in manual:
            if (row["component_name"], row["version"]) in present:
                continue
            db.add(TechStackItem(org_id=org_id, **{**row, "lts_status": row["lts_status"] or LtsStatus.ACTIVE}))
        db.commit()
    return {name: getattr(res, "status", "error") for name, res in (orchestrator.last_results or {}).items()}


def refresh_org(
    db: Session,
    org_id: str,
    demo: bool,
    *,
    clients: Optional[IntelClients] = None,
    run_discovery_first: bool = True,
    budget_seconds: float = 10.0,
    max_lookups: int = 80,
    max_age: Optional[timedelta] = timedelta(minutes=15),
) -> Dict[str, Any]:
    """Discovery (real orgs with a connector) + a forced intelligence refresh."""
    errors: List[str] = []
    discovery: Dict[str, str] = {}
    if not demo and run_discovery_first:
        if has_inventory_source(db, org_id):
            try:
                discovery = run_discovery(db, org_id)
            except Exception as exc:
                db.rollback()
                logger.error("Discovery failed for org %s: %s", org_id, exc, exc_info=True)
                errors.append(f"discovery: {exc}")
        else:
            discovery = {"discovery": "not_connected"}
    result, inv_sources = run_intel(db, org_id, demo, clients=clients, max_age=max_age,
                                    budget_seconds=budget_seconds, max_lookups=max_lookups)
    payload = stack_payload(result, inv_sources, demo)
    return {
        "summary": payload["summary"],
        "looked_up": result.looked_up,
        "queued": result.queued,
        "errors": errors + result.errors,
        "discovery": discovery,
        "sources": payload["sources"],
        "coverage": payload["coverage"],
        "feeds": payload["feeds"],
        "stale": payload["stale"],
        "failing_feeds": payload["failing_feeds"],
        "demo": demo,
    }
