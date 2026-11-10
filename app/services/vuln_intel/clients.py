"""
HTTP clients for the public intelligence sources.

    OSVClient   POST https://api.osv.dev/v1/query
    NVDClient   GET  https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:<vendor>:<product>:<version>
    KEVClient   GET  https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
    EOLClient   GET  https://endoflife.date/api/<product>.json

Every client goes through ``IntelHTTP`` (timeouts, bounded retries with
backoff, a shared deadline). The transport is injectable so tests never
touch the network: pass ``transport=httpx.MockTransport(handler)`` or set
``clients.DEFAULT_TRANSPORT``.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional
from urllib.parse import quote

import httpx

from app.services.vuln_intel.matcher import reduce_nvd_cve, reduce_osv_vuln

logger = logging.getLogger("airs.vuln_intel.clients")

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
NVD_CVE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
EOL_URL = "https://endoflife.date/api/{slug}.json"

USER_AGENT = "ResilAI-VulnIntel/1.0 (+https://resilai.org)"

# Tests set this to an ``httpx.MockTransport``; production leaves it None (real network).
DEFAULT_TRANSPORT: Optional[httpx.BaseTransport] = None

# NVD public rate limits (rolling 30 s window).
NVD_WINDOW_SECONDS = 30.0
NVD_LIMIT_NO_KEY = 5
NVD_LIMIT_WITH_KEY = 50


class IntelError(Exception):
    """A source could not be reached or answered with an error."""


class RateLimited(IntelError):
    """The source's rate limit was reached; the lookup should be queued."""


class DeadlineExceeded(IntelError):
    """The request-level time budget ran out before this lookup started."""


class Deadline:
    """Wall-clock budget shared by every lookup of one request."""

    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic):
        self._clock = clock
        self._end = clock() + max(0.0, seconds)

    def remaining(self) -> float:
        return self._end - self._clock()

    def expired(self) -> bool:
        return self.remaining() <= 0


class RollingWindowLimiter:
    """At most ``max_calls`` per ``window`` seconds (thread-safe, non-blocking)."""

    def __init__(self, max_calls: int, window: float, clock: Callable[[], float] = time.monotonic):
        self.max_calls = max_calls
        self.window = window
        self._clock = clock
        self._calls: Deque[float] = deque()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self._lock:
            now = self._clock()
            while self._calls and now - self._calls[0] >= self.window:
                self._calls.popleft()
            if len(self._calls) >= self.max_calls:
                return False
            self._calls.append(now)
            return True

    def available(self) -> int:
        with self._lock:
            now = self._clock()
            while self._calls and now - self._calls[0] >= self.window:
                self._calls.popleft()
            return max(0, self.max_calls - len(self._calls))


class IntelHTTP:
    """Small JSON-over-HTTP helper with timeout, retries and a deadline."""

    def __init__(
        self,
        transport: Optional[httpx.BaseTransport] = None,
        timeout: float = 6.0,
        retries: int = 2,
        backoff: float = 0.4,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._transport = transport if transport is not None else DEFAULT_TRANSPORT
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._sleep = sleep

    def request_json(
        self,
        method: str,
        url: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        deadline: Optional[Deadline] = None,
        not_found_ok: bool = False,
        timeout: Optional[float] = None,
    ) -> Any:
        last_error: Optional[str] = None
        for attempt in range(self.retries + 1):
            budget = timeout or self.timeout
            if deadline is not None:
                remaining = deadline.remaining()
                if remaining <= 0.2:
                    raise DeadlineExceeded(last_error or "time budget exhausted before the lookup ran")
                budget = min(budget, remaining)
            try:
                with httpx.Client(transport=self._transport, timeout=budget, follow_redirects=True,
                                  headers={"User-Agent": USER_AGENT, "Accept": "application/json"}) as client:
                    response = client.request(method, url, json=json_body, headers=headers)
            except httpx.HTTPError as exc:
                last_error = f"{type(exc).__name__}: {exc}" if str(exc) else type(exc).__name__
            else:
                status = response.status_code
                if status == 404 and not_found_ok:
                    return None
                if status in (403, 429):
                    raise RateLimited(f"HTTP {status} from {httpx.URL(url).host} (rate limited)")
                if 200 <= status < 300:
                    try:
                        return response.json()
                    except ValueError as exc:
                        raise IntelError(f"invalid JSON from {httpx.URL(url).host}: {exc}") from exc
                last_error = f"HTTP {status} from {httpx.URL(url).host}"
                if status < 500:
                    raise IntelError(last_error)
            if attempt < self.retries:
                pause = self.backoff * (2 ** attempt)
                if deadline is not None and deadline.remaining() <= pause + 0.2:
                    break
                self._sleep(pause)
        raise IntelError(last_error or "request failed")


class OSVClient:
    name = "osv"
    MAX_PAGES = 3

    def __init__(self, http: Optional[IntelHTTP] = None):
        self.http = http or IntelHTTP()

    def query(self, ecosystem: str, package: str, version: str,
              deadline: Optional[Deadline] = None) -> List[Dict[str, Any]]:
        """Reduced OSV records for a package version (see ``matcher.reduce_osv_vuln``)."""
        body: Dict[str, Any] = {"version": version, "package": {"name": package, "ecosystem": ecosystem}}
        records: List[Dict[str, Any]] = []
        for _ in range(self.MAX_PAGES):
            data = self.http.request_json("POST", OSV_QUERY_URL, json_body=body, deadline=deadline) or {}
            for raw in data.get("vulns") or []:
                if raw.get("withdrawn"):
                    continue
                records.append(reduce_osv_vuln(raw, ecosystem, package, version))
            token = data.get("next_page_token")
            if not token:
                break
            body = dict(body, page_token=token)
        return records


class NVDClient:
    name = "nvd"
    MAX_PAGES = 3

    def __init__(self, http: Optional[IntelHTTP] = None, api_key: Optional[str] = None,
                 limiter: Optional[RollingWindowLimiter] = None):
        self.http = http or IntelHTTP(timeout=8.0)
        self.api_key = api_key or None
        self.limiter = limiter or _shared_nvd_limiter(bool(self.api_key))

    @property
    def max_lookups_per_refresh(self) -> int:
        return NVD_LIMIT_WITH_KEY - 10 if self.api_key else NVD_LIMIT_NO_KEY

    def query(self, vendor: str, product: str, version: str,
              deadline: Optional[Deadline] = None) -> List[Dict[str, Any]]:
        """Reduced NVD records whose configurations mention this CPE (see ``matcher.reduce_nvd_cve``)."""
        cpe = f"cpe:2.3:a:{vendor}:{product}:{version}"
        headers = {"apiKey": self.api_key} if self.api_key else None
        records: List[Dict[str, Any]] = []
        start = 0
        for _ in range(self.MAX_PAGES):
            if not self.limiter.try_acquire():
                raise RateLimited("NVD rate limit reached; lookup queued for the next refresh")
            url = f"{NVD_CVE_URL}?virtualMatchString={quote(cpe, safe=':*')}&noRejected"
            if start:
                url += f"&startIndex={start}"
            data = self.http.request_json("GET", url, headers=headers, deadline=deadline) or {}
            for raw in data.get("vulnerabilities") or []:
                reduced = reduce_nvd_cve(raw, vendor, product)
                if reduced:
                    records.append(reduced)
            total = int(data.get("totalResults") or 0)
            per_page = int(data.get("resultsPerPage") or 0)
            start += per_page
            if not per_page or start >= total:
                break
        return records


class KEVClient:
    name = "cisa_kev"

    def __init__(self, http: Optional[IntelHTTP] = None):
        self.http = http or IntelHTTP(timeout=8.0)

    def fetch(self, deadline: Optional[Deadline] = None) -> Dict[str, Any]:
        data = self.http.request_json("GET", KEV_URL, deadline=deadline) or {}
        cves: Dict[str, Dict[str, Any]] = {}
        for v in data.get("vulnerabilities") or []:
            cve_id = v.get("cveID")
            if not cve_id:
                continue
            cves[cve_id] = {
                "date_added": v.get("dateAdded"),
                "due_date": v.get("dueDate"),
                "ransomware": str(v.get("knownRansomwareCampaignUse") or "").lower() == "known",
            }
        return {
            "catalog_version": data.get("catalogVersion"),
            "date_released": data.get("dateReleased"),
            "cves": cves,
        }


class EOLClient:
    name = "endoflife"

    def __init__(self, http: Optional[IntelHTTP] = None):
        self.http = http or IntelHTTP()

    def fetch(self, slug: str, deadline: Optional[Deadline] = None) -> List[Dict[str, Any]]:
        """Release cycles, newest first. An unknown product returns []."""
        data = self.http.request_json("GET", EOL_URL.format(slug=quote(slug, safe="-")),
                                      deadline=deadline, not_found_ok=True)
        cycles: List[Dict[str, Any]] = []
        for c in data or []:
            if not isinstance(c, dict) or c.get("cycle") is None:
                continue
            cycles.append({
                "cycle": str(c.get("cycle")),
                "eol": c.get("eol"),
                "support": c.get("support"),
                "latest": c.get("latest"),
                "lts": c.get("lts"),
                "label": c.get("releaseLabel"),
            })
        return cycles


_limiters: Dict[bool, RollingWindowLimiter] = {}
_limiters_lock = threading.Lock()


def _shared_nvd_limiter(with_key: bool) -> RollingWindowLimiter:
    """One limiter per process so concurrent requests share NVD's budget."""
    with _limiters_lock:
        if with_key not in _limiters:
            _limiters[with_key] = RollingWindowLimiter(
                NVD_LIMIT_WITH_KEY - 5 if with_key else NVD_LIMIT_NO_KEY, NVD_WINDOW_SECONDS,
            )
        return _limiters[with_key]


def reset_rate_limiters() -> None:
    """Forget recorded NVD calls (tests)."""
    with _limiters_lock:
        _limiters.clear()
