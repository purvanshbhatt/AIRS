"""
Technology stack vulnerability intelligence.

Every HTTP call is mocked with ``httpx.MockTransport``; the website scanner
gets a fake resolver / fetcher and AWS a fake boto3 session. Nothing here
touches the network.

Covers:
  * version comparison, OSV range match / non-match, NVD CPE version ranges
  * CISA KEV flag, end-of-life status, status precedence
  * trust tiers: "confirmed" only for KEV + version-aware fix, or past end of life
  * explicit product alias table (golden fixtures), no fuzzy matching
  * coverage honesty and feed freshness (stale cache is never silent)
  * remediation text, top actions
  * website scanner SSRF guards and fingerprinting
  * cloud deployment collector
  * API contract: stack, refresh, advisories, web assets, deployments
"""
import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone

import httpx
import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.core.auth import User, get_optional_user
from app.models.discovered_asset import DiscoveredAsset
from app.models.discovery import AssetType, HostAsset, InstalledProduct, TechnologyInventory
from app.models.organization import Organization
from app.models.tech_stack import TechStackItem
from app.models.vuln_intel import VulnIntelCache, WebAsset
from app.services.vuln_intel import clients as intel_clients
from app.services.vuln_intel import remediation as rem
from app.services.vuln_intel.catalog import canonical_slug, parse_os, resolve_product
from app.services.vuln_intel.clients import IntelHTTP, NVDClient, OSVClient, RollingWindowLimiter
from app.services.vuln_intel.inventory import collect_inventory, make_item, os_item
from app.services.vuln_intel.matcher import (
    cvss3_base_score,
    match_nvd,
    match_osv,
    osv_range_match,
    reduce_nvd_cve,
    reduce_osv_vuln,
)
from app.services.vuln_intel.service import (
    IntelClients,
    VulnIntelService,
    advisories_payload,
    build_advisories,
    build_coverage,
    build_top_actions,
    stack_payload,
)
from app.services.vuln_intel.versions import compare_versions, dpkg_compare
from app.services.vuln_intel.web_scanner import (
    FetchResult,
    UrlNotAllowed,
    WebScanner,
    fingerprint,
    is_public_ip,
    normalize_url,
)

NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fake public feeds
# ---------------------------------------------------------------------------

def osv_vuln(vid, package, ecosystem, introduced="0", fixed=None, last_affected=None, aliases=(),
             severity="HIGH", vector=None, published="2024-03-01T00:00:00Z", summary=None):
    events = [{"introduced": introduced}]
    if fixed:
        events.append({"fixed": fixed})
    if last_affected:
        events.append({"last_affected": last_affected})
    raw = {
        "id": vid,
        "aliases": list(aliases),
        "summary": summary or f"{vid} in {package}",
        "published": published,
        "database_specific": {"severity": severity},
        "affected": [{"package": {"name": package, "ecosystem": ecosystem},
                      "ranges": [{"type": "ECOSYSTEM", "events": events}]}],
        "references": [{"type": "ADVISORY", "url": f"https://example.test/{vid}"}],
    }
    if vector:
        raw["severity"] = [{"type": "CVSS_V3", "score": vector}]
    return raw


def nvd_cve(cve_id, vendor, product, start_incl=None, end_excl=None, end_incl=None, exact="*",
            score=9.8, severity="CRITICAL", published="2024-05-01T10:00:00.000", os_only=None):
    match = {"vulnerable": True, "criteria": f"cpe:2.3:a:{vendor}:{product}:{exact}:*:*:*:*:*:*:*"}
    if start_incl:
        match["versionStartIncluding"] = start_incl
    if end_excl:
        match["versionEndExcluding"] = end_excl
    if end_incl:
        match["versionEndIncluding"] = end_incl
    config = {"nodes": [{"operator": "OR", "negate": False, "cpeMatch": [match]}]}
    if os_only:
        config["operator"] = "AND"
        config["nodes"].append({"operator": "OR", "negate": False, "cpeMatch": [
            {"vulnerable": False, "criteria": f"cpe:2.3:o:{os_only}:*:*:*:*:*:*:*:*"}]})
    return {"cve": {
        "id": cve_id,
        "published": published,
        "vulnStatus": "Analyzed",
        "descriptions": [{"lang": "en", "value": f"{cve_id} affects {product}."}],
        "metrics": {"cvssMetricV31": [{"type": "Primary", "cvssData": {"baseScore": score, "baseSeverity": severity}}]},
        "references": [{"url": f"https://vendor.test/{cve_id}"}],
        "configurations": [config],
    }}


class FakeFeeds:
    """In-memory OSV / NVD / KEV / endoflife.date behind an httpx.MockTransport."""

    def __init__(self):
        self.osv = {}       # (ecosystem, package) -> [raw vuln]
        self.nvd = {}       # (vendor, product) -> [raw cve item]
        self.kev = []       # CVE ids
        self.eol = {}       # slug -> cycles
        self.fail = set()   # feed names answering HTTP 503
        self.calls = Counter()

    def _handler(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host
        if host == "api.osv.dev":
            self.calls["osv"] += 1
            if "osv" in self.fail:
                return httpx.Response(503)
            body = json.loads(request.content)
            key = (body["package"]["ecosystem"], body["package"]["name"])
            return httpx.Response(200, json={"vulns": self.osv.get(key, [])})
        if host == "services.nvd.nist.gov":
            self.calls["nvd"] += 1
            if "nvd" in self.fail:
                return httpx.Response(503)
            cpe = request.url.params["virtualMatchString"].split(":")
            items = self.nvd.get((cpe[3], cpe[4]), [])
            return httpx.Response(200, json={"totalResults": len(items), "resultsPerPage": len(items),
                                             "vulnerabilities": items})
        if host == "www.cisa.gov":
            self.calls["cisa_kev"] += 1
            if "cisa_kev" in self.fail:
                return httpx.Response(503)
            return httpx.Response(200, json={
                "catalogVersion": "2026.11.09", "dateReleased": "2026-11-09T00:00:00Z",
                "vulnerabilities": [{"cveID": c, "dateAdded": "2026-01-01", "dueDate": "2026-01-22",
                                     "knownRansomwareCampaignUse": "Unknown"} for c in self.kev],
            })
        if host == "endoflife.date":
            self.calls["endoflife"] += 1
            if "endoflife" in self.fail:
                return httpx.Response(503)
            slug = request.url.path.rsplit("/", 1)[-1].replace(".json", "")
            if slug not in self.eol:
                return httpx.Response(404)
            return httpx.Response(200, json=self.eol[slug])
        raise AssertionError(f"unexpected outbound request to {request.url}")

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handler)

    def clients(self) -> IntelClients:
        def http():
            return IntelHTTP(transport=self.transport, retries=0)
        return IntelClients(
            osv=OSVClient(http()),
            nvd=NVDClient(http(), limiter=RollingWindowLimiter(50, 30)),
            kev=intel_clients.KEVClient(http()),
            eol=intel_clients.EOLClient(http()),
        )


PHP_CYCLES = [
    {"cycle": "8.4", "eol": "2028-12-31", "latest": "8.4.27"},
    {"cycle": "8.3", "eol": "2027-12-31", "latest": "8.3.36"},
    {"cycle": "8.1", "eol": "2025-12-31", "latest": "8.1.34"},
]
NGINX_CYCLES = [
    {"cycle": "1.30", "eol": False, "latest": "1.30.6"},
    {"cycle": "1.18", "eol": "2021-04-20", "latest": "1.18.0"},
]
WINDOWS_CYCLES = [
    {"cycle": "11-25h2-w", "eol": "2027-10-12", "latest": "10.0.26200", "releaseLabel": "11 25H2 (W)"},
    {"cycle": "10-22h2", "eol": "2025-10-14", "latest": "10.0.19045", "releaseLabel": "10 22H2"},
]
CHROME_CYCLES = [
    {"cycle": "157", "eol": "2026-11-17"},
    {"cycle": "126", "eol": "2024-07-23"},
]
DJANGO_CYCLES = [
    {"cycle": "5.2", "eol": "2028-04-30", "latest": "5.2.9"},
    {"cycle": "4.2", "eol": "2026-04-07", "latest": "4.2.26"},
]


@pytest.fixture
def feeds():
    intel_clients.reset_rate_limiters()
    f = FakeFeeds()
    f.eol.update({"php": PHP_CYCLES, "nginx": NGINX_CYCLES, "windows": WINDOWS_CYCLES,
                  "chrome": CHROME_CYCLES, "django": DJANGO_CYCLES})
    return f


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """Any client built without an explicit transport fails loudly instead of going online."""
    def _refuse(request):
        raise AssertionError(f"real network call attempted: {request.url}")
    monkeypatch.setattr(intel_clients, "DEFAULT_TRANSPORT", httpx.MockTransport(_refuse))


def _service(db, feeds, now=NOW):
    return VulnIntelService(db, clients=feeds.clients(), now=lambda: now)


# ---------------------------------------------------------------------------
# Versions and matching
# ---------------------------------------------------------------------------

class TestVersions:
    def test_generic_ordering(self):
        assert compare_versions("8.1.2", "8.1.27") < 0
        assert compare_versions("1.0", "1.0.0") == 0
        assert compare_versions("2.0.0-rc1", "2.0.0") < 0
        assert compare_versions("1.0.2k", "1.0.2") > 0
        assert compare_versions("v18.19.0", "18.19.0") == 0

    def test_dpkg_ordering(self):
        assert dpkg_compare("1.18.0-6ubuntu14.4", "1.18.0-6ubuntu14.5") < 0
        assert dpkg_compare("1:1.0", "2.0") > 0
        assert dpkg_compare("1.0~rc1", "1.0") < 0


class TestOsvMatching:
    def test_version_inside_range_matches_with_fixed_version(self):
        events = [{"introduced": "3.2"}, {"fixed": "3.2.13"}]
        assert osv_range_match(events, "3.2.5") == {"fixed": "3.2.13"}

    def test_version_at_or_after_fix_does_not_match(self):
        events = [{"introduced": "3.2"}, {"fixed": "3.2.13"}]
        assert osv_range_match(events, "3.2.13") is None
        assert osv_range_match(events, "4.0.1") is None

    def test_version_before_introduced_does_not_match(self):
        assert osv_range_match([{"introduced": "3.2"}, {"fixed": "3.2.13"}], "2.2.28") is None

    def test_last_affected_boundary(self):
        events = [{"introduced": "0"}, {"last_affected": "1.4.0"}]
        assert osv_range_match(events, "1.4.0") == {"fixed": None}
        assert osv_range_match(events, "1.4.1") is None

    def test_client_reduces_and_matches(self, feeds):
        feeds.osv[("PyPI", "django")] = [
            osv_vuln("GHSA-aaaa", "django", "PyPI", "3.2", "3.2.13", aliases=["CVE-2022-28346"],
                     vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
            osv_vuln("GHSA-bbbb", "django", "PyPI", "4.0", "4.0.4", aliases=["CVE-2022-99999"]),
        ]
        records = feeds.clients().osv.query("PyPI", "django", "3.2.5")
        vulns = match_osv(records, "3.2.5", "PyPI")
        assert [v["id"] for v in vulns] == ["CVE-2022-28346"]        # the 4.0 range does not apply
        assert vulns[0]["fixed_version"] == "3.2.13"
        assert vulns[0]["cvss"] == 9.8 and vulns[0]["severity"] == "critical"

    def test_other_package_in_same_record_is_ignored(self):
        raw = osv_vuln("GHSA-cccc", "not-django", "PyPI", "0", "9.9")
        reduced = reduce_osv_vuln(raw, "PyPI", "django", "3.2.5")
        assert match_osv([reduced], "3.2.5", "PyPI") == []

    def test_cvss_vector_scoring(self):
        assert cvss3_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:L") == 8.2
        assert cvss3_base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N") == 6.1
        assert cvss3_base_score("not a vector") is None


class TestNvdMatching:
    def _records(self, *items):
        return [r for r in (reduce_nvd_cve(i, "php", "php") for i in items) if r]

    def test_version_inside_cpe_range_matches(self):
        records = self._records(nvd_cve("CVE-2024-0001", "php", "php", start_incl="8.1.0", end_excl="8.1.29"))
        vulns = match_nvd(records, "8.1.2")
        assert len(vulns) == 1
        assert vulns[0]["id"] == "CVE-2024-0001"
        assert vulns[0]["fixed_version"] == "8.1.29"
        assert vulns[0]["severity"] == "critical" and vulns[0]["cvss"] == 9.8
        assert vulns[0]["published"].endswith("Z")

    def test_version_outside_cpe_range_does_not_match(self):
        records = self._records(nvd_cve("CVE-2024-0001", "php", "php", start_incl="8.1.0", end_excl="8.1.29"))
        assert match_nvd(records, "8.1.29") == []
        assert match_nvd(records, "8.0.30") == []
        assert match_nvd(records, "8.3.1") == []

    def test_end_including_has_no_fixed_version(self):
        records = self._records(nvd_cve("CVE-2024-0002", "php", "php", end_incl="8.1.10"))
        vulns = match_nvd(records, "8.1.10")
        assert len(vulns) == 1 and vulns[0]["fixed_version"] is None
        assert match_nvd(records, "8.1.11") == []

    def test_exact_version_criteria(self):
        records = self._records(nvd_cve("CVE-2024-0003", "php", "php", exact="8.1.2"))
        assert len(match_nvd(records, "8.1.2")) == 1
        assert match_nvd(records, "8.1.3") == []

    def test_other_vendor_product_is_ignored(self):
        assert reduce_nvd_cve(nvd_cve("CVE-2024-0004", "apache", "http_server", end_excl="2.4.60"), "php", "php") is None

    def test_platform_condition_is_respected(self):
        records = self._records(nvd_cve("CVE-2024-0005", "php", "php", end_excl="8.1.29",
                                        os_only="microsoft:windows"))
        assert match_nvd(records, "8.1.2", os_family="ubuntu") == []
        assert len(match_nvd(records, "8.1.2", os_family="windows")) == 1
        assert len(match_nvd(records, "8.1.2")) == 1   # host OS unknown: keep it

    def test_client_queries_cpe_virtual_match_string(self, feeds):
        seen = {}
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-0001", "php", "php", start_incl="8.1.0", end_excl="8.1.29")]
        original = feeds._handler

        def spy(request):
            if request.url.host == "services.nvd.nist.gov":
                seen["url"] = str(request.url)
            return original(request)

        client = NVDClient(IntelHTTP(transport=httpx.MockTransport(spy), retries=0),
                           limiter=RollingWindowLimiter(5, 30))
        records = client.query("php", "php", "8.1.2")
        assert "virtualMatchString=cpe:2.3:a:php:php:8.1.2" in seen["url"]
        assert len(match_nvd(records, "8.1.2")) == 1

    def test_rate_limit_queues_instead_of_calling(self, feeds):
        client = NVDClient(IntelHTTP(transport=feeds.transport, retries=0), limiter=RollingWindowLimiter(1, 30))
        client.query("php", "php", "8.1.2")
        with pytest.raises(intel_clients.RateLimited):
            client.query("php", "php", "8.1.3")
        assert feeds.calls["nvd"] == 1


# ---------------------------------------------------------------------------
# Product alias table (golden fixtures): no fuzzy matching
# ---------------------------------------------------------------------------

GOLDEN_ALIASES = [
    # Intune / Defender display names
    ("Google Chrome", "chrome"),
    ("Mozilla Firefox (x64 en-US)", "firefox"),
    ("Microsoft Edge", "edge"),
    ("7-Zip 23.01 (x64)", "7-zip"),
    ("VLC media player", "vlc"),
    ("PuTTY release 0.78 (64-bit)", "putty"),
    ("WinRAR 6.23 (64-bit)", "winrar"),
    ("Adobe Acrobat Reader DC", "acrobat-reader"),
    ("Zoom Workplace (64-bit)", "zoom"),
    ("Microsoft 365 Apps for enterprise - en-us", "microsoft-365-apps"),
    ("Python 3.11.4 (64-bit)", "python"),
    ("Node.js", "nodejs"),
    ("PostgreSQL 15", "postgresql"),
    # Wazuh / SSM package names
    ("nginx", "nginx"),
    ("nginx-core", "nginx"),
    ("php8.1-fpm", "php"),
    ("postgresql15-server", "postgresql"),
    ("apache2", "apache-http-server"),
    ("httpd", "apache-http-server"),
    ("openssl-libs", "openssl"),
    ("mariadb-server", "mariadb"),
    ("redis-server", "redis"),
    ("google-chrome-stable", "chrome"),
    # RDS engine names
    ("postgres", "postgresql"),
    ("aurora-postgresql", "postgresql"),
    ("mysql", "mysql"),
    # Not in the table: must stay unmatched ("not checked"), never guessed
    ("python3-requests", None),
    ("Mozilla Firefox ESR", None),
    ("Microsoft Visual C++ 2015-2022 Redistributable (x64) - 14.38.33130", None),
    ("nginx-module-njs", None),
    ("php-mysqlnd", None),
    ("libssl3", None),
    ("Chromium Embedded Framework", None),
    ("Google Chrome Helper Tools", None),
    ("ACME Practice Manager", None),
    ("node-exporter", None),
]


class TestAliasTable:
    @pytest.mark.parametrize("display_name,expected", GOLDEN_ALIASES)
    def test_golden_aliases(self, display_name, expected):
        assert canonical_slug(display_name) == expected

    def test_unmatched_name_is_kept_but_not_routed_to_any_feed(self):
        info = resolve_product("ACME Practice Manager")
        assert info.known is False
        assert info.cpe is None and info.osv is None and info.eol is None
        assert info.name == "ACME Practice Manager"

    def test_explicit_ecosystem_prefix(self):
        info = resolve_product("pypi:cryptography")
        assert info.osv == ("PyPI", "cryptography")

    def test_os_parsing(self):
        win = parse_os("Windows 10.0.19045")
        assert (win.name, win.version, win.cycles[0]) == ("Windows 10", "22H2", "10-22h2")
        al = parse_os("Amazon Linux 2023")
        assert (al.name, al.version, al.package_manager) == ("Amazon Linux", "2023", "dnf")
        ub = parse_os("Ubuntu 22.04.3 LTS")
        assert ub.osv_ecosystem == "Ubuntu:22.04:LTS" and ub.package_manager == "apt"
        assert parse_os("Linux/UNIX") is None


# ---------------------------------------------------------------------------
# Enrichment: KEV, end of life, status precedence
# ---------------------------------------------------------------------------

class TestEnrichment:
    def test_kev_flag_and_sorting(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [
            nvd_cve("CVE-2024-1111", "php", "php", start_incl="8.1.0", end_excl="8.1.29", score=9.8),
            nvd_cve("CVE-2024-2222", "php", "php", start_incl="8.1.0", end_excl="8.1.30", score=5.3,
                    severity="MEDIUM"),
        ]
        feeds.kev = ["CVE-2024-2222"]
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.1.2", "manual")])
        vulns = result.enriched[0].vulns
        assert [v["id"] for v in vulns] == ["CVE-2024-2222", "CVE-2024-1111"]   # exploited first
        assert vulns[0]["known_exploited"] is True and vulns[1]["known_exploited"] is False

    def test_eol_status(self, db_session, feeds):
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.1.34", "manual")])
        e = result.enriched[0]
        assert e.eol["is_eol"] is True
        assert e.eol["eol_date"] == "2025-12-31"
        assert e.eol["latest_version"] == "8.4.27"       # newest supported release
        assert e.eol["source"] == "endoflife.date"
        assert e.status == "end_of_life"

    def test_status_precedence(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-1111", "php", "php", start_incl="8.1.0", end_excl="8.1.29")]
        items = [
            make_item("PHP", "8.1.2", "manual", asset="a"),      # vulnerable AND end of life -> vulnerable
            make_item("PHP", "8.1.34", "manual", asset="b"),     # end of life only
            make_item("PHP", "8.3.1", "manual", asset="c"),      # supported, newer patch exists
            make_item("PHP", "8.4.27", "manual", asset="d"),     # current
            make_item("PHP", None, "manual", asset="e"),         # version missing
            make_item("ACME Practice Manager", "4.2", "manual"),  # nothing covers it
        ]
        result = _service(db_session, feeds).enrich(items)
        status = {(e.item.name, e.item.asset): e.status for e in result.enriched}
        assert status[("PHP", "a")] == "vulnerable"
        assert status[("PHP", "b")] == "end_of_life"
        assert status[("PHP", "c")] == "update_available"
        assert status[("PHP", "d")] == "ok"
        assert status[("PHP", "e")] == "unknown"
        assert status[("ACME Practice Manager", None)] == "unknown"
        unknown = next(e for e in result.enriched if e.item.name == "ACME Practice Manager")
        assert unknown.checked is False and "alias table" in unknown.reason

    def test_second_run_is_served_from_the_cache(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-1111", "php", "php", end_excl="8.1.29")]
        item = [make_item("PHP", "8.1.2", "manual")]
        first = _service(db_session, feeds).enrich(item)
        calls = dict(feeds.calls)
        second = _service(db_session, feeds, now=NOW + timedelta(hours=2)).enrich(item)
        assert first.looked_up == 3 and second.looked_up == 0
        assert dict(feeds.calls) == calls
        assert [v["id"] for v in second.enriched[0].vulns] == ["CVE-2024-1111"]
        assert db_session.query(VulnIntelCache).count() == 3   # nvd, kev, eol

    def test_nvd_lookups_beyond_the_rate_limit_are_queued(self, db_session, feeds):
        clients = feeds.clients()
        clients.nvd = NVDClient(IntelHTTP(transport=feeds.transport, retries=0),
                                limiter=RollingWindowLimiter(1, 30))
        items = [make_item("PHP", "8.1.2", "manual"), make_item("nginx", "1.18.0", "manual")]
        result = VulnIntelService(db_session, clients=clients, now=lambda: NOW).enrich(items)
        assert result.feeds["nvd"]["status"] == "partial"
        assert result.queued == 1
        assert sum(1 for e in result.enriched if not e.checked) == 1
        pending = next(e for e in result.enriched if not e.checked)
        assert pending.status != "ok" and "queued" in pending.reason.lower()

    def test_distro_package_uses_distro_advisories(self, db_session, feeds):
        ubuntu = parse_os("Ubuntu 22.04.3 LTS")
        feeds.osv[("Ubuntu:22.04:LTS", "nginx")] = [
            osv_vuln("UBUNTU-CVE-2024-7347", "nginx", "Ubuntu:22.04:LTS", "0", "1.18.0-6ubuntu14.5",
                     aliases=["CVE-2024-7347"], severity="medium"),
        ]
        patched = make_item("nginx", "1.18.0-6ubuntu14.5", "aws_systems_manager", asset="web-1", host_os=ubuntu)
        behind = make_item("nginx", "1.18.0-6ubuntu14.4", "aws_systems_manager", asset="web-2", host_os=ubuntu)
        result = _service(db_session, feeds).enrich([patched, behind])
        by_asset = {e.item.asset: e for e in result.enriched}
        assert by_asset["web-1"].vulns == []                       # backported fix installed
        assert [v["id"] for v in by_asset["web-2"].vulns] == ["CVE-2024-7347"]
        assert feeds.calls["nvd"] == 0                              # upstream CPE matching not used


# ---------------------------------------------------------------------------
# Trust tiers
# ---------------------------------------------------------------------------

class TestConfidence:
    def _advisories(self, db, feeds, items):
        result = _service(db, feeds).enrich(items)
        return result, {a["id"]: a for a in build_advisories(result)}

    def test_kev_plus_osv_fixed_version_is_confirmed(self, db_session, feeds):
        feeds.osv[("PyPI", "django")] = [osv_vuln("GHSA-k", "django", "PyPI", "5.2", "5.2.8",
                                                  aliases=["CVE-2025-64459"], severity="CRITICAL")]
        feeds.kev = ["CVE-2025-64459"]
        _, adv = self._advisories(db_session, feeds, [make_item("Django", "5.2.1", "pip", asset="portal")])
        assert adv["CVE-2025-64459"]["confidence"] == "confirmed"
        assert adv["CVE-2025-64459"]["known_exploited"] is True
        assert adv["CVE-2025-64459"]["fixed_version"] == "5.2.8"

    def test_kev_without_version_proof_is_unverified(self, db_session, feeds):
        # On KEV, affected, but the feed gives no fixed version: KEV alone is not version-aware.
        feeds.osv[("PyPI", "django")] = [osv_vuln("GHSA-n", "django", "PyPI", "0", last_affected="5.2.9",
                                                  aliases=["CVE-2025-00001"])]
        feeds.kev = ["CVE-2025-00001"]
        _, adv = self._advisories(db_session, feeds, [make_item("Django", "5.2.1", "pip")])
        assert adv["CVE-2025-00001"]["known_exploited"] is True
        assert adv["CVE-2025-00001"]["confidence"] == "unverified"

    def test_nvd_cpe_match_is_never_confirmed_even_on_kev(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.3.0", end_excl="8.3.8")]
        feeds.kev = ["CVE-2024-4577"]
        _, adv = self._advisories(db_session, feeds, [make_item("PHP", "8.3.1", "manual")])
        assert adv["CVE-2024-4577"]["known_exploited"] is True
        assert adv["CVE-2024-4577"]["source"] == "nvd"
        assert adv["CVE-2024-4577"]["confidence"] == "unverified"

    def test_osv_match_not_on_kev_is_unverified(self, db_session, feeds):
        feeds.osv[("PyPI", "django")] = [osv_vuln("GHSA-q", "django", "PyPI", "5.2", "5.2.8",
                                                  aliases=["CVE-2025-11111"])]
        _, adv = self._advisories(db_session, feeds, [make_item("Django", "5.2.1", "pip")])
        assert adv["CVE-2025-11111"]["confidence"] == "unverified"

    def test_distro_package_is_never_confirmed_from_upstream_version(self, db_session, feeds):
        # rpm "python3-django"-style case: an OS package on Amazon Linux compared by upstream number.
        amazon = parse_os("Amazon Linux 2023")
        feeds.osv[("PyPI", "django")] = [osv_vuln("GHSA-k", "django", "PyPI", "4.2", "4.2.26",
                                                  aliases=["CVE-2025-64459"])]
        feeds.kev = ["CVE-2025-64459"]
        item = make_item("django", "4.2.7", "aws_systems_manager", asset="app-1", host_os=amazon)
        assert item.is_distro_package is True
        _, adv = self._advisories(db_session, feeds, [item])
        assert adv["CVE-2025-64459"]["known_exploited"] is True
        assert adv["CVE-2025-64459"]["confidence"] == "unverified"
        # ... and its upstream end-of-life date proves nothing either.
        assert adv["EOL-django-4.2"]["confidence"] == "unverified"

    def test_past_end_of_life_is_confirmed(self, db_session, feeds):
        items = [
            os_item(parse_os("Windows 10 22H2"), "microsoft_intune", asset="PC-1"),
            make_item("Google Chrome", "126.0.6478.127", "microsoft_intune", asset="PC-1"),
            make_item("PHP", "8.3.1", "manual"),
        ]
        result, adv = self._advisories(db_session, feeds, items)
        assert adv["EOL-windows-10-22h2"]["confidence"] == "confirmed"
        assert adv["EOL-windows-10-22h2"]["kind"] == "end_of_life"
        assert adv["EOL-chrome-126"]["confidence"] == "confirmed"
        assert not any(a.startswith("EOL-php") for a in adv)   # 8.3 is still supported

    def test_top_actions_are_confirmed_only_kev_first_then_eol_by_date(self, db_session, feeds):
        feeds.osv[("PyPI", "django")] = [osv_vuln("GHSA-k", "django", "PyPI", "5.2", "5.2.8",
                                                  aliases=["CVE-2025-64459"], severity="CRITICAL")]
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.3.0", end_excl="8.3.8")]
        feeds.kev = ["CVE-2025-64459", "CVE-2024-4577"]
        items = [
            make_item("PHP", "8.3.1", "manual"),                                   # KEV via NVD: unverified
            os_item(parse_os("Windows 10 22H2"), "microsoft_intune", asset="PC-1"),
            os_item(parse_os("Windows 10 22H2"), "microsoft_intune", asset="PC-2"),
            make_item("Google Chrome", "126.0.6478.127", "microsoft_intune", asset="PC-1",
                      host_os=parse_os("Windows 10 22H2")),
            make_item("Google Chrome", "126.0.6478.127", "microsoft_intune", asset="PC-2",
                      host_os=parse_os("Windows 10 22H2")),
            make_item("Django", "5.2.1", "pip", asset="portal"),
        ]
        result = _service(db_session, feeds).enrich(items)
        actions = build_top_actions(build_advisories(result))
        assert [a["id"] for a in actions] == ["CVE-2025-64459", "EOL-chrome-126", "EOL-windows-10-22h2"]
        assert all(a["confidence"] == "confirmed" for a in actions)
        assert len(actions) <= 5
        chrome = actions[1]
        assert chrome["title"] == "Update Google Chrome 126 on 2 computers"
        assert chrome["where"] == {"count": 2, "label": "2 computers", "names": ["PC-1", "PC-2"]}
        assert chrome["source_url"] == "https://endoflife.date/chrome"
        assert "PC-1, PC-2" in chrome["send_to_it_text"]
        assert chrome["fix"] in chrome["send_to_it_text"]
        kev = actions[0]
        assert kev["kind"] == "known_exploited"
        assert "5.2.8" in kev["fix"]
        assert "48 hours" in kev["send_to_it_text"]

    def test_top_actions_are_capped_at_five(self, db_session, feeds):
        feeds.eol["chrome"] = [{"cycle": str(n), "eol": f"2024-0{n - 119}-01"} for n in range(120, 128)]
        items = [make_item("Google Chrome", f"{n}.0.1", "microsoft_intune", asset=f"PC-{n}")
                 for n in range(120, 128)]
        result = _service(db_session, feeds).enrich(items)
        actions = build_top_actions(build_advisories(result))
        assert len(actions) == 5
        assert [a["eol_date"] for a in actions] == sorted(a["eol_date"] for a in actions)   # oldest first


# ---------------------------------------------------------------------------
# Coverage honesty
# ---------------------------------------------------------------------------

class TestCoverage:
    EMPTY_SOURCES = {"aws": "not_connected", "ms_graph": "not_connected", "wazuh": "not_connected",
                     "web_scan": "not_configured"}

    def test_nothing_connected_does_not_read_as_safe(self, db_session, feeds):
        result = _service(db_session, feeds).enrich([])
        coverage = build_coverage(result, self.EMPTY_SOURCES)
        assert coverage["level"] == "none"
        assert coverage["products_total"] == 0 and coverage["products_checked"] == 0
        assert coverage["sources_seen"] == []
        assert "Website not added" in coverage["not_seen"]
        assert any("No device inventory connected" in s for s in coverage["not_seen"])
        assert any("No server inventory connected" in s for s in coverage["not_seen"])
        assert "does not mean you are safe" in coverage["message"]
        payload = advisories_payload(result, self.EMPTY_SOURCES, demo=False)
        assert payload["advisories"] == [] and payload["top_actions"] == []
        assert payload["coverage"]["level"] == "none"

    def test_poor_coverage_with_no_advisories_warns(self, db_session, feeds):
        items = [make_item(f"ACME Tool {n}", "1.0", "microsoft_intune", asset="PC-1") for n in "ABCDEFG"]
        items.append(make_item("PHP", "8.4.27", "manual"))
        result = _service(db_session, feeds).enrich(items)
        coverage = build_coverage(result, dict(self.EMPTY_SOURCES, ms_graph="ok"))
        assert build_advisories(result) == []
        assert coverage["products_total"] == 8
        assert coverage["products_checked"] == 1
        assert coverage["products_not_checked"] == 7
        assert coverage["level"] == "poor"
        assert "Only 1 of 8" in coverage["message"]
        assert "does not mean you are safe" in coverage["message"]
        assert coverage["sources_seen"] == ["manual", "microsoft"]
        assert not any("device inventory" in s for s in coverage["not_seen"])   # Intune did report
        assert "Website not added" in coverage["not_seen"]

    def test_checked_and_not_checked_counts_in_stack(self, db_session, feeds):
        items = [make_item("PHP", "8.4.27", "manual"), make_item("ACME Practice Manager", "4.2", "manual")]
        payload = stack_payload(_service(db_session, feeds).enrich(items), self.EMPTY_SOURCES, demo=False)
        assert payload["summary"]["checked"] == 1 and payload["summary"]["not_checked"] == 1
        by_name = {i["name"]: i for i in payload["items"]}
        assert by_name["PHP"]["checked"] is True and by_name["PHP"]["canonical"] == "php"
        acme = by_name["ACME Practice Manager"]
        assert acme["checked"] is False and acme["status"] == "unknown" and acme["canonical"] is None
        assert acme["not_checked_reason"]


# ---------------------------------------------------------------------------
# Feed freshness
# ---------------------------------------------------------------------------

class TestFeedFreshness:
    def test_every_feed_result_carries_as_of(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-1111", "php", "php", end_excl="8.1.29")]
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.1.2", "manual")])
        for name in ("nvd", "cisa_kev", "endoflife"):
            assert result.feeds[name]["status"] == "ok"
            assert result.feeds[name]["as_of"] == "2026-11-09T12:00:00Z"
            assert result.feeds[name]["stale"] is False
        assert result.feeds["osv"]["status"] == "not_used" and result.feeds["osv"]["as_of"] is None
        assert result.stale is False and result.failing_feeds == []
        adv = build_advisories(result)
        assert all(a["as_of"] == "2026-11-09T12:00:00Z" for a in adv)

    def test_failed_feed_serves_last_cache_and_says_so(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-1111", "php", "php", end_excl="8.1.29")]
        item = [make_item("PHP", "8.1.2", "manual")]
        _service(db_session, feeds).enrich(item)

        feeds.fail = {"nvd"}
        later = NOW + timedelta(hours=30)   # cache expired, refetch attempted and fails
        result = _service(db_session, feeds, now=later).enrich(item)

        assert result.feeds["nvd"]["status"] == "stale"
        assert result.feeds["nvd"]["stale"] is True
        assert result.feeds["nvd"]["as_of"] == "2026-11-09T12:00:00Z"     # the old copy, honestly dated
        assert "503" in result.feeds["nvd"]["error"]
        assert result.stale is True
        assert result.failing_feeds == ["nvd"]
        assert any(e.startswith("nvd:") for e in result.errors)
        # The last known answer is still shown, not dropped.
        assert [v["id"] for v in result.enriched[0].vulns] == ["CVE-2024-1111"]
        # The feeds that did refresh are current.
        assert result.feeds["cisa_kev"]["stale"] is False
        assert result.feeds["cisa_kev"]["as_of"] == "2026-11-10T18:00:00Z"

        payload = stack_payload(result, TestCoverage.EMPTY_SOURCES, demo=False)
        assert payload["stale"] is True and payload["failing_feeds"] == ["nvd"]
        assert payload["sources"]["nvd"] == "stale"
        assert payload["feeds"]["nvd"]["stale"] is True
        assert "nvd" in payload["coverage"]["message"]

    def test_failed_feed_without_cache_is_not_a_clean_result(self, db_session, feeds):
        feeds.fail = {"nvd"}
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.4.27", "manual")])
        e = result.enriched[0]
        assert result.feeds["nvd"]["status"] == "unavailable"
        assert result.failing_feeds == ["nvd"]
        assert e.vulns == []
        assert e.checked is False                 # never "ok" when the feed did not answer
        assert e.status != "ok"
        assert "unavailable" in e.reason.lower()
        payload = stack_payload(result, TestCoverage.EMPTY_SOURCES, demo=False)
        assert payload["failing_feeds"] == ["nvd"]
        assert payload["coverage"]["products_not_checked"] == 1

    def test_kev_failure_is_named(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-1111", "php", "php", end_excl="8.1.29")]
        feeds.kev = ["CVE-2024-1111"]
        feeds.fail = {"cisa_kev"}
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.1.2", "manual")])
        assert "cisa_kev" in result.failing_feeds
        assert result.feeds["cisa_kev"]["status"] == "unavailable"
        assert result.enriched[0].vulns[0]["known_exploited"] is False   # unknown, and flagged as such above

    def test_all_feeds_offline_returns_inventory_without_vulnerabilities(self, db_session, feeds):
        feeds.fail = {"osv", "nvd", "cisa_kev", "endoflife"}
        result = _service(db_session, feeds).enrich([make_item("PHP", "8.1.2", "manual")])
        assert result.enriched[0].vulns == []
        assert sorted(result.failing_feeds) == ["cisa_kev", "endoflife", "nvd"]


# ---------------------------------------------------------------------------
# Remediation text
# ---------------------------------------------------------------------------

class TestRemediation:
    def test_known_exploited_urgency_and_fixed_version(self, db_session, feeds):
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.1.0", end_excl="8.1.29")]
        feeds.kev = ["CVE-2024-4577"]
        ubuntu = parse_os("Ubuntu 22.04.3 LTS")
        item = make_item("PHP", "8.1.2", "manual", asset="web-1", host_os=ubuntu)
        result = _service(db_session, feeds).enrich([item])
        text = result.enriched[0].vulns[0]["remediation"]
        assert "Being exploited in the wild: patch within 48 hours" in text
        assert "8.1.29" in text
        assert "sudo apt update && sudo apt install --only-upgrade php" in text
        assert "IT provider or MSP" in text

        advisory = build_advisories(result)[0]
        assert advisory["steps"][0] == rem.KEV_URGENCY
        assert any("8.1.29" in s for s in advisory["steps"])
        assert advisory["fixed_version"] == "8.1.29"

    def test_urgency_follows_severity(self):
        assert "7 days" in rem.urgency_line("critical", False)
        assert "14 days" in rem.urgency_line("high", False)
        assert "30 days" in rem.urgency_line("medium", False)
        assert rem.urgency_line("low", True) == rem.KEV_URGENCY

    def test_platform_specific_how(self):
        rds = rem.RemediationContext(name="PostgreSQL", version="15.4", asset="clinic-db", platform="rds")
        assert "Amazon RDS" in rem.how_line(rds, "15.9") and "15.9" in rem.how_line(rds, "15.9")
        win = rem.RemediationContext(name="Google Chrome", version="126", asset="PC-1", platform="windows_update")
        assert "Windows Update" in rem.how_line(win, None) and "Intune" in rem.how_line(win, None)
        al = rem.RemediationContext(name="nginx", version="1.24.0", asset="app-1", platform="dnf",
                                    package="nginx", os_name="Amazon Linux 2023")
        assert "sudo dnf upgrade --releasever=latest nginx" in rem.how_line(al, "1.26.3")
        fn = rem.RemediationContext(name="python3.8", version=None, asset="reminders", platform="lambda")
        assert "Runtime settings" in rem.how_line(fn, None)
        lib = rem.RemediationContext(name="Django", version="4.2.7", ecosystem="PyPI", package="django")
        assert 'pip install --upgrade "django>=4.2.26"' in rem.how_line(lib, "4.2.26")

    def test_no_fixed_version_points_to_latest_supported(self):
        ctx = rem.RemediationContext(name="PHP", version="8.1.2", latest_version="8.4.27")
        steps = rem.build_steps("high", False, [ctx])
        assert any("latest supported release (8.4.27)" in s for s in steps)


# ---------------------------------------------------------------------------
# Website scanner
# ---------------------------------------------------------------------------

def _resolver(mapping):
    def resolve(host, port):
        return mapping[host]
    return resolve


def _html(generator=None, extra=""):
    meta = f'<meta name="generator" content="{generator}">' if generator else ""
    return f"<html><head>{meta}</head><body>{extra}</body></html>".encode()


GOOD_TLS = {"valid": True, "expires_at": "2027-03-01T00:00:00Z", "days_left": 112, "issuer": "Let's Encrypt"}


class TestWebScannerSsrf:
    @pytest.mark.parametrize("url", [
        "http://127.0.0.1",
        "http://127.0.0.1:8080/admin",
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5",
        "http://192.168.1.1",
        "http://[::1]/",
        "http://[::ffff:10.0.0.1]/",
        "http://localhost",
        "http://0.0.0.0",
        "http://100.64.0.1",
    ])
    def test_non_public_addresses_are_refused(self, url):
        with pytest.raises(UrlNotAllowed):
            WebScanner(resolver=_resolver({}), fetcher=None).scan(url)

    @pytest.mark.parametrize("url", [
        "ftp://example.com/file",
        "file:///etc/passwd",
        "gopher://example.com",
        "javascript:alert(1)",
        "http://user:pass@example.com/",
        "http://example.com:22/",
    ])
    def test_non_http_schemes_credentials_and_ports_are_refused(self, url):
        with pytest.raises(UrlNotAllowed):
            normalize_url(url)

    def test_hostname_resolving_to_private_address_is_refused(self):
        called = []
        scanner = WebScanner(resolver=_resolver({"intranet.example.com": ["10.1.2.3"]}),
                             fetcher=lambda url, ip: called.append(url))
        with pytest.raises(UrlNotAllowed):
            scanner.scan("http://intranet.example.com")
        assert called == []

    def test_one_private_answer_among_public_ones_is_refused(self):
        scanner = WebScanner(resolver=_resolver({"mixed.example.com": ["93.184.216.34", "10.0.0.9"]}),
                             fetcher=lambda url, ip: pytest.fail("must not fetch"))
        with pytest.raises(UrlNotAllowed):
            scanner.scan("https://mixed.example.com")

    def test_redirect_to_private_address_is_not_followed(self):
        fetched = []

        def fetcher(url, ip):
            fetched.append((url, ip))
            return FetchResult(302, {"location": "http://internal.example.com/secret"}, b"", GOOD_TLS)

        scanner = WebScanner(
            resolver=_resolver({"example.com": ["93.184.216.34"], "internal.example.com": ["169.254.169.254"]}),
            fetcher=fetcher,
        )
        result = scanner.scan("https://example.com")
        assert fetched == [("https://example.com/", "93.184.216.34")]
        assert any("cannot be checked" in i["title"] for i in result["issues"])

    def test_redirect_to_another_site_is_reported_not_scanned(self):
        fetched = []

        def fetcher(url, ip):
            fetched.append(url)
            return FetchResult(301, {"location": "https://other-company.test/"}, b"", GOOD_TLS)

        scanner = WebScanner(
            resolver=_resolver({"example.com": ["93.184.216.34"], "other-company.test": ["93.184.216.35"]}),
            fetcher=fetcher,
        )
        result = scanner.scan("https://example.com")
        assert fetched == ["https://example.com/"]
        assert any("another site" in i["title"] for i in result["issues"])

    def test_redirect_limit(self):
        hops = []

        def fetcher(url, ip):
            hops.append(url)
            return FetchResult(302, {"location": f"/hop{len(hops)}"}, b"", GOOD_TLS)

        scanner = WebScanner(resolver=_resolver({"example.com": ["93.184.216.34"]}), fetcher=fetcher)
        result = scanner.scan("https://example.com")
        assert len(hops) == 4                       # the first request plus three redirects
        assert any(i["title"] == "Too many redirects" for i in result["issues"])

    def test_connection_goes_to_the_validated_address(self):
        seen = {}

        def fetcher(url, ip):
            seen["ip"] = ip
            return FetchResult(200, {}, b"", GOOD_TLS)

        WebScanner(resolver=_resolver({"example.com": ["93.184.216.34"]}), fetcher=fetcher).scan("https://example.com")
        assert seen["ip"] == "93.184.216.34"

    def test_second_validated_address_is_tried_when_the_first_refuses(self):
        tried = []

        def fetcher(url, ip):
            tried.append(ip)
            if ip == "93.184.216.34":
                raise ConnectionRefusedError("refused")
            return FetchResult(200, {}, b"", GOOD_TLS)

        scanner = WebScanner(resolver=_resolver({"example.com": ["2606:4700::1", "93.184.216.34", "93.184.216.35"]}),
                             fetcher=fetcher)
        result = scanner.scan("https://example.com")
        assert tried == ["93.184.216.34", "93.184.216.35"]       # IPv4 first, two attempts at most
        assert result["reachable"] is True

    def test_is_public_ip(self):
        assert is_public_ip("93.184.216.34")
        assert not is_public_ip("169.254.169.254")
        assert not is_public_ip("fd00::1")
        assert not is_public_ip("not-an-ip")


class TestWebScannerFingerprint:
    def _scan(self, headers, body=b"", tls=GOOD_TLS, url="https://clinic.example.com", status=200):
        scanner = WebScanner(
            resolver=_resolver({"clinic.example.com": ["93.184.216.34"]}),
            fetcher=lambda u, ip: FetchResult(status, headers, body, tls if u.startswith("https") else None),
            now=lambda: NOW,
        )
        return scanner.scan(url)

    def test_server_and_x_powered_by_banners(self):
        result = self._scan({"server": "nginx/1.18.0", "x-powered-by": "PHP/8.1.2"})
        detected = {d["name"]: d for d in result["detected"]}
        assert detected["nginx"]["version"] == "1.18.0"
        assert detected["nginx"]["evidence"] == "Server: nginx/1.18.0"
        assert detected["PHP"]["version"] == "8.1.2"
        assert detected["PHP"]["evidence"] == "X-Powered-By: PHP/8.1.2"
        assert all(d["confidence"] == "confirmed" for d in result["detected"])
        titles = [i["title"] for i in result["issues"]]
        assert "Software version visible to visitors (nginx 1.18.0)" in titles
        assert "Software version visible to visitors (PHP 8.1.2)" in titles

    def test_multi_product_server_header_and_distro_hint(self):
        detected = {d["name"]: d for d in fingerprint(
            {"Server": "Apache/2.4.52 (Ubuntu) OpenSSL/3.0.2", "X-Powered-By": "PHP/8.1.2-1ubuntu2.14"}, b"")}
        assert detected["Apache HTTP Server"]["version"] == "2.4.52"
        assert detected["Apache HTTP Server"]["distro_package"] is True
        assert detected["OpenSSL"]["version"] == "3.0.2"
        assert detected["PHP"]["version"] == "8.1.2-1ubuntu2.14"

    def test_generators(self):
        detected = {d["name"]: d for d in fingerprint(
            {"x-generator": "Drupal 10 (https://www.drupal.org)"}, _html("WordPress 6.4.2"))}
        assert detected["Drupal"]["version"] == "10"
        assert detected["WordPress"]["version"] == "6.4.2"
        assert detected["WordPress"]["confidence"] == "confirmed"
        assert detected["WordPress"]["evidence"] == 'meta generator: "WordPress 6.4.2"'

    def test_wordpress_inferred_from_asset_urls_is_unverified(self):
        body = _html(extra=(
            '<script src="/wp-includes/js/jquery/jquery.min.js?ver=6.4.2"></script>'
            '<link href="/wp-includes/css/dist/block-library/style.min.css?ver=6.4.2">'
            '<script src="/wp-content/plugins/contact-form-7/includes/js/index.js?ver=5.8.4"></script>'
            '<img src="/wp-content/plugins/elementor/assets/logo.png">'
        ))
        detected = {d["name"]: d for d in fingerprint({}, body)}
        assert detected["WordPress"]["version"] == "6.4.2"
        assert detected["WordPress"]["confidence"] == "unverified"
        plugin = detected["WordPress plugin: contact-form-7"]
        assert plugin["version"] == "5.8.4" and plugin["confidence"] == "unverified"
        assert detected["WordPress plugin: elementor"]["version"] is None

    def test_explicit_generator_wins_over_inferred_version(self):
        body = _html("WordPress 6.5.1", extra='<script src="/wp-includes/js/a.js?ver=6.4.2"></script>')
        detected = {d["name"]: d for d in fingerprint({}, body)}
        assert detected["WordPress"]["version"] == "6.5.1"
        assert detected["WordPress"]["confidence"] == "confirmed"

    def test_headers_tls_and_issues(self):
        result = self._scan(
            {"strict-transport-security": "max-age=31536000", "x-frame-options": "DENY"},
            tls={"valid": True, "expires_at": "2026-11-19T12:00:00Z", "days_left": 10, "issuer": "Let's Encrypt"},
        )
        assert result["reachable"] is True and result["status_code"] == 200
        assert result["final_url"] == "https://clinic.example.com/"
        assert result["headers"] == {"hsts": True, "csp": False, "x_frame_options": True,
                                     "x_content_type_options": False, "referrer_policy": False}
        assert result["tls"]["days_left"] == 10 and result["tls"]["issuer"] == "Let's Encrypt"
        titles = [i["title"] for i in result["issues"]]
        assert "Certificate expires in 10 days" in titles
        assert "No Content-Security-Policy header" in titles
        assert "No X-Content-Type-Options header" in titles
        assert not any("HSTS" in t for t in titles)
        assert all(set(i) == {"title", "severity", "fix"} for i in result["issues"])
        assert result["scanned_at"] == "2026-11-09T12:00:00Z"

    def test_plain_http_site(self):
        result = self._scan({}, url="http://clinic.example.com")
        assert result["tls"] is None
        assert any(i["title"] == "Site does not use HTTPS" and i["severity"] == "high" for i in result["issues"])

    def test_invalid_certificate(self):
        result = self._scan({}, tls={"valid": False, "expires_at": "2026-10-01T00:00:00Z", "days_left": -39,
                                     "issuer": "Let's Encrypt", "error": "certificate has expired"})
        issue = next(i for i in result["issues"] if "certificate" in i["title"].lower())
        assert issue["title"] == "TLS certificate has expired" and issue["severity"] == "critical"

    def test_unreachable_site(self):
        def fetcher(url, ip):
            raise ConnectionRefusedError("refused")
        scanner = WebScanner(resolver=_resolver({"clinic.example.com": ["93.184.216.34"]}), fetcher=fetcher)
        result = scanner.scan("https://clinic.example.com")
        assert result["reachable"] is False and result["status_code"] is None
        assert result["issues"][0]["title"] == "Site could not be reached"


# ---------------------------------------------------------------------------
# Inventory unification
# ---------------------------------------------------------------------------

@pytest.fixture
def real_org(db_session):
    org = Organization(id="vi-org-1", name="Riverside Dental", owner_uid="vi-owner",
                       subscription_plan="starter", subscription_status="active")
    db_session.add(org)
    db_session.commit()
    return org


class TestInventory:
    def test_sources_are_merged_and_deduplicated(self, db_session, real_org):
        inv = TechnologyInventory(org_id=real_org.id, discovery_source="orchestrator;aws=ok;ms_graph=ok")
        db_session.add(inv)
        db_session.commit()
        web = HostAsset(org_id=real_org.id, inventory_id=inv.id, hostname="web-1",
                        asset_type=AssetType.CLOUD_SERVICE, operating_system="Ubuntu 22.04.3 LTS", cloud_provider="AWS")
        pc = HostAsset(org_id=real_org.id, inventory_id=inv.id, hostname="FRONT-PC",
                       asset_type=AssetType.HOST, operating_system="Windows 10.0.19045")
        rds = HostAsset(org_id=real_org.id, inventory_id=inv.id, hostname="clinic-db",
                        asset_type=AssetType.CLOUD_SERVICE, cloud_provider="AWS")
        db_session.add_all([web, pc, rds])
        db_session.commit()
        db_session.add_all([
            InstalledProduct(asset_id=web.id, product_name="nginx", version="1.18.0-6ubuntu14.4",
                             installation_source="aws_systems_manager"),
            InstalledProduct(asset_id=pc.id, product_name="windows", version="10.0.19045",
                             installation_source="microsoft_intune"),
            InstalledProduct(asset_id=pc.id, product_name="Google Chrome", version="126.0.6478.127",
                             installation_source="microsoft_intune"),
            InstalledProduct(asset_id=rds.id, product_name="postgres", version="15.4",
                             installation_source="aws_rds"),
            # same product+version as the host row: already represented
            DiscoveredAsset(org_id=real_org.id, product="nginx", version="1.18.0-6ubuntu14.4",
                            source="aws_systems_manager"),
            DiscoveredAsset(org_id=real_org.id, product="redis", version="7.2.4", source="aws_systems_manager"),
            TechStackItem(org_id=real_org.id, component_name="WordPress", version="6.4.2", category="Other"),
            TechStackItem(org_id=real_org.id, component_name="postgres", version="15.4", category="Database",
                          notes="Auto-discovered from aws_rds"),
        ])
        db_session.commit()

        items = collect_inventory(db_session, real_org.id)
        rows = sorted((i.name, i.version, i.asset, i.source, i.category) for i in items)
        assert rows == sorted([
            ("Ubuntu", "22.04.3", "web-1", "aws_systems_manager", "os"),
            ("nginx", "1.18.0-6ubuntu14.4", "web-1", "aws_systems_manager", "web_server"),
            ("Windows 10", "22H2", "FRONT-PC", "microsoft_intune", "os"),
            ("Google Chrome", "126.0.6478.127", "FRONT-PC", "microsoft_intune", "application"),
            ("PostgreSQL", "15.4", "clinic-db", "aws_rds", "database"),
            ("Redis", "7.2.4", None, "aws_systems_manager", "database"),
            ("WordPress", "6.4.2", None, "manual", "application"),
        ])
        by_name = {i.name: i for i in items}
        assert by_name["PostgreSQL"].platform == "rds"
        assert by_name["nginx"].platform == "apt" and by_name["nginx"].is_distro_package
        assert by_name["Google Chrome"].platform == "windows_update"
        assert len({i.id for i in items}) == len(items)


# ---------------------------------------------------------------------------
# Cloud deployments
# ---------------------------------------------------------------------------

class _Denied(Exception):
    response = {"Error": {"Code": "AccessDeniedException", "Message": "not authorized"}}


class _FakeAwsClient:
    def __init__(self, name):
        self._name = name

    def __getattr__(self, method):
        table = _AWS_RESPONSES.get(self._name, {})
        if method not in table:
            raise AttributeError(method)

        def call(**kwargs):
            value = table[method]
            if isinstance(value, Exception):
                raise value
            return value(**kwargs) if callable(value) else value
        return call


class _FakeAwsSession:
    region_name = "eu-west-1"

    def client(self, name, **kwargs):
        return _FakeAwsClient(name)


_AWS_RESPONSES = {
    "lambda": {"list_functions": {"Functions": [
        {"FunctionName": "reminders", "Runtime": "python3.8", "Version": "$LATEST"},
        {"FunctionName": "intake", "Runtime": "python3.13", "Version": "$LATEST"},
    ]}},
    "rds": {"describe_db_instances": {"DBInstances": [
        {"DBInstanceIdentifier": "clinic-db", "Engine": "postgres", "EngineVersion": "15.4",
         "PubliclyAccessible": True, "StorageEncrypted": False, "AutoMinorVersionUpgrade": True},
    ]}},
    "ec2": {"describe_instances": {"Reservations": [{"Instances": [
        {"InstanceId": "i-1", "State": {"Name": "running"}, "InstanceType": "t3.micro",
         "PlatformDetails": "Linux/UNIX", "PublicIpAddress": "3.3.3.3",
         "Tags": [{"Key": "Name", "Value": "web-1"}], "MetadataOptions": {"HttpTokens": "required"}},
    ]}]}},
    "elbv2": {
        "describe_load_balancers": {"LoadBalancers": [
            {"LoadBalancerName": "portal-alb", "LoadBalancerArn": "arn:alb", "Scheme": "internet-facing",
             "Type": "application"}]},
        "describe_listeners": {"Listeners": [
            {"Port": 80, "Protocol": "HTTP", "DefaultActions": [{"Type": "forward"}]},
            {"Port": 443, "Protocol": "HTTPS", "SslPolicy": "ELBSecurityPolicy-TLS13-1-2-2021-06",
             "DefaultActions": [{"Type": "forward"}]}]},
    },
    "cloudfront": {"list_distributions": _Denied()},
    "apigateway": {"get_rest_apis": {"items": [
        {"id": "a1", "name": "booking-api", "endpointConfiguration": {"types": ["REGIONAL"]}}]}},
    "apigatewayv2": {"get_apis": {"Items": [{"ApiId": "h1", "Name": "portal-http", "ProtocolType": "HTTP"}]}},
    "s3": {
        "list_buckets": {"Buckets": [{"Name": "clinic-site"}, {"Name": "clinic-backups"}]},
        "get_bucket_website": lambda Bucket: ({"IndexDocument": {"Suffix": "index.html"}}
                                              if Bucket == "clinic-site" else (_ for _ in ()).throw(
                                                  type("NoSite", (Exception,), {"response": {"Error": {
                                                      "Code": "NoSuchWebsiteConfiguration"}}})())),
    },
    "ecs": {
        "list_clusters": {"clusterArns": ["arn:cluster/main"]},
        "list_services": {"serviceArns": ["arn:svc/portal"]},
        "describe_services": {"services": [
            {"serviceName": "portal", "launchType": "FARGATE", "platformVersion": "1.4.0",
             "networkConfiguration": {"awsvpcConfiguration": {"assignPublicIp": "ENABLED"}}}]},
    },
    "apprunner": {"list_services": {"ServiceSummaryList": [{"ServiceName": "intake-web"}]}},
    "elasticbeanstalk": {"describe_environments": {"Environments": [
        {"EnvironmentName": "legacy-env", "SolutionStackName": "64bit Amazon Linux 2 v3.5.0 running PHP 8.1",
         "VersionLabel": "v12", "CNAME": "legacy.eu-west-1.elasticbeanstalk.com", "Tier": {"Name": "WebServer"}}]}},
}

LAMBDA_CYCLES = [
    {"cycle": "python3.13", "eol": "2029-08-31", "support": "2029-06-30"},
    {"cycle": "python3.8", "eol": "2027-08-31", "support": "2024-10-14"},
]


class TestCloudDeployments:
    def test_no_connector_means_not_connected(self, db_session, real_org):
        from app.services.vuln_intel.cloud_deployments import CloudDeploymentCollector
        payload = CloudDeploymentCollector(db_session, real_org.id).collect()
        assert payload["deployments"] == []
        assert payload["sources"] == {"aws": "not_connected"}
        assert payload["collected_at"].endswith("Z")

    def test_collects_every_service_and_records_access_denied(self, db_session, real_org):
        from app.services.connector_manager import ConnectorManager
        from app.services.vuln_intel.cloud_deployments import CloudDeploymentCollector
        ConnectorManager(db_session, real_org.id).register_connector(
            connector_type="aws_security_hub", display_name="AWS", auth_method="api_key",
            credentials={"aws_access_key_id": "AKIATEST", "aws_secret_access_key": "secret",
                         "aws_region": "eu-west-1"},
            created_by="test",
        )
        collector = CloudDeploymentCollector(
            db_session, real_org.id, session_factory=lambda creds, cfg, cid: _FakeAwsSession(),
            lambda_cycles=LAMBDA_CYCLES, today=NOW.date(),
        )
        payload = collector.collect()
        deployments = {(d["type"], d["name"]): d for d in payload["deployments"]}

        assert {t for t, _ in deployments} == {
            "lambda", "rds", "ec2", "load_balancer", "api_gateway", "s3_website",
            "ecs_service", "app_runner", "elastic_beanstalk",
        }
        for d in payload["deployments"]:
            assert set(d) == {"id", "type", "name", "provider", "region", "runtime", "version", "public", "issues"}
            assert d["provider"] == "aws"

        old = deployments[("lambda", "reminders")]
        assert old["runtime"] == "python3.8"
        assert "deprecated" in old["issues"][0]["title"] and "2024-10-14" in old["issues"][0]["title"]
        assert deployments[("lambda", "intake")]["issues"] == []

        db = deployments[("rds", "clinic-db")]
        assert db["runtime"] == "postgres" and db["version"] == "15.4" and db["public"] is True
        titles = [i["title"] for i in db["issues"]]
        assert "Database is reachable from the internet" in titles
        assert "Database storage is not encrypted" in titles

        alb = deployments[("load_balancer", "portal-alb")]
        assert alb["public"] is True
        assert any("plain HTTP" in i["title"] for i in alb["issues"])
        assert deployments[("ecs_service", "portal")]["public"] is True
        assert deployments[("s3_website", "clinic-site")]["issues"]
        assert ("s3_website", "clinic-backups") not in deployments
        assert deployments[("api_gateway", "booking-api")]["public"] is True

        assert payload["sources"]["cloudfront:ListDistributions"] == "permission_missing"
        assert payload["sources"]["lambda:ListFunctions"] == "ok"
        assert payload["sources"]["aws"] == "partial"

    def test_runtime_fallback_when_lifecycle_feed_is_unavailable(self):
        from app.services.vuln_intel.cloud_deployments import lambda_runtime_issue
        assert lambda_runtime_issue("nodejs12.x", None, NOW.date())["severity"] == "medium"
        assert lambda_runtime_issue("python3.13", None, NOW.date()) is None
        assert lambda_runtime_issue(None, LAMBDA_CYCLES, NOW.date()) is None


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

OWNER = User(uid="vi-owner", email="owner@example.com", name="Owner")
STRANGER = User(uid="vi-stranger", email="stranger@example.com", name="Stranger")
STACK = "/api/v1/technology/stack"
ADVISORIES = "/api/v1/technology/advisories"
WEB_ASSETS = "/api/v1/technology/web-assets"
DEPLOYMENTS = "/api/v1/technology/deployments"


def _as(client, user):
    async def override():
        return user
    client.app.dependency_overrides[get_optional_user] = override


@pytest.fixture
def api(client, feeds):
    """Test client whose intelligence feeds are the in-memory fakes."""
    from app.api.v1.technology import get_intel_clients
    feeds.eol.update({
        "amazon-linux": [{"cycle": "2023", "eol": "2029-06-30", "latest": "2023.12.20261102.0"}],
        "postgresql": [{"cycle": "15", "eol": "2027-11-11", "latest": "15.19"}],
        "openssl": [{"cycle": "3.5", "eol": "2030-04-08", "latest": "3.5.9"},
                    {"cycle": "3.0", "eol": "2026-09-07", "latest": "3.0.21"}],
        "wordpress": [{"cycle": "6.4", "eol": False, "latest": "6.4.14"}],
        "aws-lambda": LAMBDA_CYCLES,
    })
    feeds.nvd[("php", "php")] = [
        nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.1.0", end_excl="8.1.29", score=9.8),
        nvd_cve("CVE-2025-1217", "php", "php", start_incl="8.1.0", end_excl="8.1.32", score=5.3,
                severity="MEDIUM", published="2025-03-29T06:15:00.000"),
    ]
    feeds.nvd[("f5", "nginx")] = [
        nvd_cve("CVE-2025-23419", "f5", "nginx", start_incl="1.11.4", end_excl="1.26.3", score=7.5,
                severity="HIGH", published="2025-02-05T18:15:00.000"),
        nvd_cve("CVE-2024-7347", "f5", "nginx", start_incl="1.5.13", end_excl="1.26.2", score=4.7,
                severity="MEDIUM", published="2024-08-14T15:15:00.000"),
    ]
    feeds.nvd[("wordpress", "wordpress")] = [
        nvd_cve("CVE-2024-31210", "wordpress", "wordpress", start_incl="6.4.0", end_excl="6.4.3", score=7.6,
                severity="HIGH", published="2024-04-04T23:15:00.000"),
    ]
    feeds.kev = ["CVE-2024-4577"]
    client.app.dependency_overrides[get_intel_clients] = feeds.clients
    return client


class TestStackApi:
    def test_demo_org_returns_items_without_a_token(self, api, feeds):
        resp = api.get(f"{STACK}/demo-northstar-health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo"] is True
        assert set(body) >= {"items", "summary", "sources", "demo", "coverage", "feeds", "stale", "failing_feeds"}
        names = {(i["name"], i["version"]) for i in body["items"]}
        assert {("Amazon Linux", "2023"), ("nginx", "1.24.0"), ("PostgreSQL", "15.4"), ("PHP", "8.1.27"),
                ("WordPress", "6.4.2"), ("OpenSSL", "3.0.8"), ("Windows 10", "22H2")} <= names
        assert any("metro-health" in (i["asset"] or "") for i in body["items"])

        item_keys = {"id", "name", "vendor", "version", "category", "source", "asset", "last_seen", "eol",
                     "vulnerabilities", "status"}
        for item in body["items"]:
            assert item_keys <= set(item)
            assert item["category"] in {"os", "runtime", "database", "web_server", "framework", "application",
                                        "cloud_service", "library"}
            assert item["status"] in {"ok", "update_available", "vulnerable", "end_of_life", "unknown"}

        # Vulnerabilities come from the same lookup path as real organizations (the mocked feeds).
        php = next(i for i in body["items"] if i["name"] == "PHP")
        assert php["status"] == "vulnerable"
        assert [v["id"] for v in php["vulnerabilities"]] == ["CVE-2024-4577", "CVE-2025-1217"]
        vuln = php["vulnerabilities"][0]
        assert {"id", "severity", "cvss", "summary", "fixed_version", "published", "known_exploited",
                "references", "remediation"} <= set(vuln)
        assert vuln["known_exploited"] is True and vuln["fixed_version"] == "8.1.29"
        assert vuln["confidence"] == "unverified"            # NVD match on a distribution package
        assert "48 hours" in vuln["remediation"]
        assert php["eol"] == {"is_eol": True, "eol_date": "2025-12-31", "latest_version": "8.4.27",
                              "source": "endoflife.date"}

        windows = next(i for i in body["items"] if i["name"] == "Windows 10")
        assert windows["status"] == "end_of_life"
        office = next(i for i in body["items"] if i["name"] == "Microsoft 365 Apps")
        assert office["status"] == "unknown" and office["checked"] is False

        summary = body["summary"]
        assert set(summary) >= {"total", "vulnerable", "critical", "known_exploited", "end_of_life",
                                "last_intel_refresh"}
        assert summary["total"] == len(body["items"])
        assert summary["vulnerable"] >= 2 and summary["known_exploited"] == 1 and summary["critical"] == 1
        assert summary["last_intel_refresh"] is not None
        assert body["sources"]["nvd"] == "ok" and body["sources"]["cisa_kev"] == "ok"
        assert body["sources"]["aws"] == "demo"
        assert body["stale"] is False and body["failing_feeds"] == []

    def test_demo_legal_org_uses_its_own_servers(self, api):
        body = api.get(f"{STACK}/demo-northstar-cole").json()
        assets = {i["asset"] for i in body["items"] if i["asset"]}
        assert any("northstar-cole" in a for a in assets)
        assert not any("metro-health" in a for a in assets)
        assert any(i["name"] == "Express" for i in body["items"])

    def test_demo_offline_returns_stack_with_empty_vulnerabilities(self, api, feeds):
        feeds.fail = {"osv", "nvd", "cisa_kev", "endoflife"}
        body = api.get(f"{STACK}/demo-northstar-health").json()
        assert body["demo"] is True and len(body["items"]) >= 10
        assert all(i["vulnerabilities"] == [] for i in body["items"])
        assert body["sources"]["nvd"] == "unavailable"
        assert body["sources"]["endoflife"] == "unavailable"
        assert sorted(body["failing_feeds"]) == ["cisa_kev", "endoflife", "nvd", "osv"]
        assert body["summary"]["vulnerable"] == 0
        assert all(i["status"] != "ok" for i in body["items"])     # nothing reads as clean

    def test_real_org_with_nothing_is_empty_with_sources(self, api, real_org, feeds):
        _as(api, OWNER)
        resp = api.get(f"{STACK}/{real_org.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo"] is False
        assert body["items"] == []
        assert body["summary"]["total"] == 0 and body["summary"]["last_intel_refresh"] is None
        assert body["sources"]["aws"] == "not_connected"
        assert body["sources"]["ms_graph"] == "not_connected"
        assert body["sources"]["web_scan"] == "not_configured"
        assert body["sources"]["nvd"] == "not_used"
        assert body["coverage"]["level"] == "none"
        assert "Website not added" in body["coverage"]["not_seen"]
        assert sum(feeds.calls.values()) == 0

    def test_foreign_org_is_not_found(self, api, real_org):
        _as(api, STRANGER)
        for url in (f"{STACK}/{real_org.id}", f"{ADVISORIES}/{real_org.id}", f"{WEB_ASSETS}/{real_org.id}",
                    f"{DEPLOYMENTS}/{real_org.id}"):
            resp = api.get(url)
            assert resp.status_code == 404, url
            body = resp.json()
            assert (body.get("error") or body.get("detail") or {}).get("code") == "ORGANIZATION_NOT_FOUND"
        assert api.post(f"{STACK}/{real_org.id}/refresh").status_code == 404
        assert api.post(f"{WEB_ASSETS}/{real_org.id}", json={"url": "https://example.com"}).status_code == 404

    def test_real_org_inventory_is_matched(self, api, real_org, db_session):
        db_session.add(TechStackItem(org_id=real_org.id, component_name="PHP", version="8.1.2", category="Runtime"))
        db_session.commit()
        _as(api, OWNER)
        body = api.get(f"{STACK}/{real_org.id}").json()
        assert [(i["name"], i["version"], i["source"], i["status"]) for i in body["items"]] == [
            ("PHP", "8.1.2", "manual", "vulnerable")]
        assert body["coverage"]["sources_seen"] == ["manual"]

    def test_existing_routes_still_work(self, client):
        for path in ("inventory", "lifecycle", "exposure"):
            assert client.get(f"/api/v1/technology/{path}/test_org").status_code == 200


class TestRefreshApi:
    def test_demo_refresh(self, api):
        resp = api.post(f"{STACK}/demo-northstar-health/refresh")
        assert resp.status_code == 200
        body = resp.json()
        assert body["looked_up"] > 0 and isinstance(body["errors"], list)
        assert body["summary"]["known_exploited"] == 1
        again = api.post(f"{STACK}/demo-northstar-health/refresh").json()
        assert again["looked_up"] == 0                      # fresh cache, nothing re-fetched

    def test_real_org_refresh_runs_the_lookup(self, api, real_org, db_session):
        db_session.add(TechStackItem(org_id=real_org.id, component_name="nginx", version="1.24.0",
                                     category="Web Server"))
        db_session.commit()
        _as(api, OWNER)
        resp = api.post(f"{STACK}/{real_org.id}/refresh")
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["total"] == 1 and body["summary"]["vulnerable"] == 1
        assert body["looked_up"] == 3
        assert body["discovery"] == {"discovery": "not_connected"}
        # Manual entries survive a refresh.
        assert db_session.query(TechStackItem).filter(TechStackItem.org_id == real_org.id).count() == 1

    def test_real_org_refresh_requires_the_readiness_entitlement(self, api, db_session):
        org = Organization(id="vi-free-org", name="Free Org", owner_uid=OWNER.uid)
        db_session.add(org)
        db_session.commit()
        _as(api, OWNER)
        assert api.post(f"{STACK}/{org.id}/refresh").status_code == 402
        assert api.get(f"{STACK}/{org.id}").status_code == 200   # reading stays open to the owner


class TestAdvisoriesApi:
    def test_ordering_known_exploited_then_severity_then_newest(self, api, real_org, db_session):
        db_session.add_all([
            TechStackItem(org_id=real_org.id, component_name="PHP", version="8.1.2", category="Runtime"),
            TechStackItem(org_id=real_org.id, component_name="nginx", version="1.24.0", category="Web Server"),
            TechStackItem(org_id=real_org.id, component_name="WordPress", version="6.4.2", category="Other"),
        ])
        db_session.commit()
        _as(api, OWNER)
        body = api.get(f"{ADVISORIES}/{real_org.id}").json()
        ids = [a["id"] for a in body["advisories"]]
        assert ids == [
            "CVE-2024-4577",     # known exploited
            "EOL-php-8.1",       # high, 2025-12-31
            "CVE-2025-23419",    # high, 2025-02-05
            "CVE-2024-31210",    # high, 2024-04-04
            "CVE-2025-1217",     # medium, 2025-03
            "CVE-2024-7347",     # medium, 2024-08
        ]
        first = body["advisories"][0]
        assert set(first) >= {"id", "severity", "cvss", "summary", "published", "known_exploited", "affected",
                              "fixed_version", "steps", "references", "confidence"}
        assert first["known_exploited"] is True and first["severity"] == "critical"
        assert first["affected"] == [{"name": "PHP", "version": "8.1.2", "asset": None}]
        assert first["fixed_version"] == "8.1.29"
        assert first["steps"][0] == "Being exploited in the wild: patch within 48 hours."
        assert first["confidence"] == "unverified"          # NVD: never confirmed
        assert first["references"][0] == "https://nvd.nist.gov/vuln/detail/CVE-2024-4577"
        assert body["generated_at"].endswith("Z")
        eol = body["advisories"][1]
        assert eol["kind"] == "end_of_life" and eol["confidence"] == "confirmed"
        assert [a["id"] for a in body["top_actions"]] == ["EOL-php-8.1"]
        action = body["top_actions"][0]
        assert set(action) >= {"title", "where", "fix", "send_to_it_text", "source_url"}
        assert body["summary"]["confirmed_advisories"] == 1
        assert body["summary"]["unverified_advisories"] == 5
        assert "coverage" in body and "feeds" in body and body["stale"] is False

    def test_demo_advisories(self, api):
        body = api.get(f"{ADVISORIES}/demo-northstar-health").json()
        assert body["demo"] is True
        assert body["advisories"][0]["id"] == "CVE-2024-4577"
        titles = [a["title"] for a in body["top_actions"]]
        assert "Update Google Chrome 126 on 2 computers" in titles
        assert "Replace or upgrade Windows 10 22H2 on 2 computers" in titles
        assert all(a["confidence"] == "confirmed" for a in body["top_actions"])
        assert len(body["top_actions"]) <= 5


class TestWebAssetsApi:
    def _fake_scanner(self, api, headers, body=b""):
        from app.api.v1.technology import get_web_scanner
        scanner = WebScanner(
            resolver=_resolver({"clinic.example.com": ["93.184.216.34"]}),
            fetcher=lambda url, ip: FetchResult(200, headers, body, GOOD_TLS),
        )
        api.app.dependency_overrides[get_web_scanner] = lambda: scanner

    def test_crud_scan_and_inventory_upsert(self, api, real_org, db_session):
        _as(api, OWNER)
        assert api.get(f"{WEB_ASSETS}/{real_org.id}").json()["assets"] == []

        created = api.post(f"{WEB_ASSETS}/{real_org.id}", json={"url": "clinic.example.com", "label": "Main site"})
        assert created.status_code == 201
        asset = created.json()
        assert asset["url"] == "https://clinic.example.com/" and asset["label"] == "Main site"
        assert asset["last_scan"] is None and asset["id"]

        # Same URL again returns the existing asset instead of a duplicate.
        again = api.post(f"{WEB_ASSETS}/{real_org.id}", json={"url": "https://clinic.example.com/"})
        assert again.json()["id"] == asset["id"]
        assert len(api.get(f"{WEB_ASSETS}/{real_org.id}").json()["assets"]) == 1

        self._fake_scanner(api, {"server": "nginx/1.24.0", "x-powered-by": "PHP/8.1.2"},
                           _html(extra='<script src="/wp-content/plugins/akismet/a.js?ver=5.3"></script>'))
        scan = api.post(f"{WEB_ASSETS}/{real_org.id}/{asset['id']}/scan")
        assert scan.status_code == 200
        result = scan.json()
        assert set(result) >= {"url", "reachable", "status_code", "final_url", "tls", "headers", "detected",
                               "issues", "scanned_at"}
        assert result["reachable"] is True
        assert {"name": "nginx", "version": "1.24.0", "evidence": "Server: nginx/1.24.0",
                "confidence": "confirmed"} in result["detected"]

        listed = api.get(f"{WEB_ASSETS}/{real_org.id}").json()["assets"][0]
        assert listed["last_scan"]["scanned_at"] == result["scanned_at"]

        # Explicit versions are upserted into the inventory (source web_scan) and CVE-matched;
        # the plugin version guessed from an asset URL is not.
        rows = db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == real_org.id).all()
        assert sorted((r.product, r.version, r.source) for r in rows) == [
            ("PHP", "8.1.2", "web_scan"), ("nginx", "1.24.0", "web_scan")]
        stack = api.get(f"{STACK}/{real_org.id}").json()
        items = {i["name"]: i for i in stack["items"]}
        assert set(items) == {"nginx", "PHP"}
        assert items["nginx"]["source"] == "web_scan" and items["nginx"]["asset"] == "clinic.example.com"
        assert items["PHP"]["status"] == "vulnerable"
        assert "clinic.example.com" in items["PHP"]["vulnerabilities"][0]["remediation"]
        assert stack["sources"]["web_scan"] == "ok"
        assert "web_scan" in stack["coverage"]["sources_seen"]

        deleted = api.delete(f"{WEB_ASSETS}/{real_org.id}/{asset['id']}")
        assert deleted.status_code == 200 and deleted.json()["deleted"] is True
        assert api.get(f"{WEB_ASSETS}/{real_org.id}").json()["assets"] == []
        assert db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == real_org.id).count() == 0
        assert api.delete(f"{WEB_ASSETS}/{real_org.id}/{asset['id']}").status_code == 404

    @pytest.mark.parametrize("url", ["http://127.0.0.1", "http://169.254.169.254/latest/meta-data/",
                                     "ftp://example.com", "http://10.0.0.8/"])
    def test_create_refuses_urls_that_may_not_be_scanned(self, api, real_org, url):
        _as(api, OWNER)
        resp = api.post(f"{WEB_ASSETS}/{real_org.id}", json={"url": url})
        assert resp.status_code == 400
        assert api.get(f"{WEB_ASSETS}/{real_org.id}").json()["assets"] == []

    def test_scan_refuses_a_site_that_resolves_to_a_private_address(self, api, real_org):
        from app.api.v1.technology import get_web_scanner
        _as(api, OWNER)
        asset = api.post(f"{WEB_ASSETS}/{real_org.id}", json={"url": "https://rebind.example.com"}).json()
        api.app.dependency_overrides[get_web_scanner] = lambda: WebScanner(
            resolver=_resolver({"rebind.example.com": ["10.0.0.7"]}),
            fetcher=lambda url, ip: pytest.fail("must not fetch"),
        )
        resp = api.post(f"{WEB_ASSETS}/{real_org.id}/{asset['id']}/scan")
        assert resp.status_code == 400

    def test_only_the_organizations_own_assets_can_be_scanned(self, api, real_org, db_session):
        other = Organization(id="vi-org-2", name="Other", owner_uid=OWNER.uid)
        db_session.add(other)
        db_session.add(WebAsset(id="foreign-asset", org_id="vi-org-2", url="https://other.example.com/"))
        db_session.commit()
        _as(api, OWNER)
        assert api.post(f"{WEB_ASSETS}/{real_org.id}/foreign-asset/scan").status_code == 404

    def test_demo_assets_are_read_only_samples(self, api):
        body = api.get(f"{WEB_ASSETS}/demo-northstar-health").json()
        assert body["demo"] is True and len(body["assets"]) == 1
        asset = body["assets"][0]
        assert asset["url"].endswith(".example/") and asset["last_scan"]["reachable"] is True
        assert api.post(f"{WEB_ASSETS}/demo-northstar-health", json={"url": "https://example.com"}).status_code == 403
        assert api.delete(f"{WEB_ASSETS}/demo-northstar-health/{asset['id']}").status_code == 403
        scan = api.post(f"{WEB_ASSETS}/demo-northstar-health/{asset['id']}/scan")
        assert scan.status_code == 200 and scan.json()["sample"] is True


class TestDeploymentsApi:
    def test_real_org_without_connector(self, api, real_org, feeds):
        _as(api, OWNER)
        body = api.get(f"{DEPLOYMENTS}/{real_org.id}").json()
        assert body["deployments"] == []
        assert body["sources"] == {"aws": "not_connected"}
        assert body["collected_at"]
        assert sum(feeds.calls.values()) == 0     # nothing to look up when nothing is connected

    def test_demo_deployments(self, api):
        body = api.get(f"{DEPLOYMENTS}/demo-northstar-health").json()
        assert body["sources"] == {"aws": "demo"} and body["demo"] is True
        types = {d["type"] for d in body["deployments"]}
        assert {"ec2", "lambda"} <= types
        assert any("metro-health" in d["name"] for d in body["deployments"])
        fn = next(d for d in body["deployments"] if d["type"] == "lambda")
        assert fn["runtime"] == "python3.8" and "deprecated" in fn["issues"][0]["title"]


# ---------------------------------------------------------------------------
# Daily job
# ---------------------------------------------------------------------------

class TestDailyJob:
    def test_refreshes_orgs_with_inventory_and_reports_counts(self, db_session, real_org, feeds):
        from app.services.vuln_intel.jobs import orgs_with_inventory, run_daily_refresh
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.1.0", end_excl="8.1.29")]
        db_session.add(Organization(id="vi-empty-org", name="Empty", owner_uid="x"))
        db_session.add(TechStackItem(org_id=real_org.id, component_name="PHP", version="8.1.2"))
        db_session.commit()
        assert orgs_with_inventory(db_session) == [real_org.id]

        totals = run_daily_refresh(db=db_session, clients=feeds.clients(), now=NOW)
        assert totals["orgs"] == 1 and totals["failed"] == 0
        assert totals["vulnerable_items"] == 1
        assert totals["looked_up"] > 0
        assert db_session.query(VulnIntelCache).filter(VulnIntelCache.cache_key == "nvd:php:php:8.1.2").count() == 1

    def test_waits_for_the_nvd_rate_limit_window_instead_of_leaving_work_undone(self, db_session, real_org, feeds):
        from app.services.vuln_intel.jobs import run_daily_refresh
        feeds.nvd[("php", "php")] = [nvd_cve("CVE-2024-4577", "php", "php", start_incl="8.1.0", end_excl="8.1.29")]
        db_session.add_all([
            TechStackItem(org_id=real_org.id, component_name="PHP", version="8.1.2"),
            TechStackItem(org_id=real_org.id, component_name="nginx", version="1.30.6"),
        ])
        db_session.commit()

        clock = {"t": 0.0}
        clients = feeds.clients()
        clients.nvd = NVDClient(IntelHTTP(transport=feeds.transport, retries=0),
                                limiter=RollingWindowLimiter(1, 30, clock=lambda: clock["t"]))
        sleeps = []

        def fake_sleep(seconds):
            sleeps.append(seconds)
            clock["t"] += seconds

        totals = run_daily_refresh(db=db_session, clients=clients, now=NOW, sleep=fake_sleep)
        assert sleeps and all(s > 30 for s in sleeps)       # waited out the 30 s window, never hammered
        assert totals["orgs"] == 1 and totals["queued"] == 0
        assert totals["vulnerable_items"] == 1

    def test_scheduler_registers_the_daily_job(self):
        from app.tasks.scheduler import TaskScheduler
        assert hasattr(TaskScheduler, "_refresh_vuln_intel")
