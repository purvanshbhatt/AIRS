"""
Passive check of a website the organization registered itself.

One ordinary GET of the page (plus up to three same-site redirects): status,
TLS certificate, security headers and any software versions the site
announces about itself. No crawling, no probing of paths, no payloads.

SSRF protection:
  * only ``http`` / ``https``, only ports 80, 443, 8080, 8443, no credentials in the URL
  * the host is resolved first and every address must be public: private,
    loopback, link-local (incl. the 169.254.169.254 metadata address), CGNAT,
    multicast, reserved and unspecified ranges are refused
  * the connection is made to the address that was validated (no second DNS
    lookup, so DNS rebinding cannot swap it)
  * every redirect target is validated the same way; redirects that leave the
    registered site are reported, not followed
  * 8 s timeout, 1 MB body cap
"""
from __future__ import annotations

import http.client
import ipaddress
import logging
import re
import socket
import ssl
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

from sqlalchemy.orm import Session

from app.services.vuln_intel.catalog import resolve_product

logger = logging.getLogger("airs.vuln_intel.web_scanner")

ALLOWED_SCHEMES = ("http", "https")
ALLOWED_PORTS = (80, 443, 8080, 8443)
MAX_REDIRECTS = 3
TIMEOUT_SECONDS = 8.0
SCAN_BUDGET_SECONDS = 15.0   # whole scan, redirects included
MAX_BODY_BYTES = 1_000_000
CERT_WARN_DAYS = 21
USER_AGENT = "ResilAI-WebCheck/1.0 (+https://resilai.org; passive header check requested by the site owner)"

EXPLICIT = "confirmed"      # the site states the version itself (header / generator tag)
INFERRED = "unverified"     # guessed from asset URLs; shown, never matched against CVEs


class UrlNotAllowed(ValueError):
    """The URL (or a redirect target) may not be fetched."""


@dataclass
class FetchResult:
    status_code: int
    headers: Dict[str, str]
    body: bytes = b""
    tls: Optional[Dict[str, Any]] = None


Resolver = Callable[[str, int], List[str]]
Fetcher = Callable[[str, str], FetchResult]


# ---------------------------------------------------------------------------
# URL / address validation
# ---------------------------------------------------------------------------

def is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address.split("%", 1)[0])
    except ValueError:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
            or ip.is_reserved or ip.is_unspecified):
        return False
    return bool(ip.is_global)


def normalize_url(url: str) -> str:
    """Validate and normalise a user-supplied URL. Raises ``UrlNotAllowed``."""
    text = str(url or "").strip()
    if not text:
        raise UrlNotAllowed("URL is required")
    if "://" not in text:
        text = "https://" + text
    try:
        parts = urlsplit(text)
        port = parts.port
    except ValueError as exc:
        raise UrlNotAllowed(f"URL is not valid: {exc}") from exc
    scheme = (parts.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UrlNotAllowed("Only http and https URLs can be checked")
    if parts.username or parts.password:
        raise UrlNotAllowed("URLs with a username or password are not allowed")
    host = (parts.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise UrlNotAllowed("URL has no host name")
    if port is not None and port not in ALLOWED_PORTS:
        raise UrlNotAllowed(f"Port {port} is not allowed (use 80, 443, 8080 or 8443)")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise UrlNotAllowed("Internal host names cannot be checked")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and not is_public_ip(host):
        raise UrlNotAllowed("Private, loopback and link-local addresses cannot be checked")
    netloc = f"[{host}]" if literal is not None and literal.version == 6 else host
    default_port = 443 if scheme == "https" else 80
    if port is not None and port != default_port:
        netloc += f":{port}"
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


def default_resolver(host: str, port: int) -> List[str]:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    seen: List[str] = []
    for info in infos:
        address = info[4][0]
        if address not in seen:
            seen.append(address)
    return seen


def same_site(host_a: str, host_b: str) -> bool:
    a = (host_a or "").lower().rstrip(".")
    b = (host_b or "").lower().rstrip(".")
    a0 = a[4:] if a.startswith("www.") else a
    b0 = b[4:] if b.startswith("www.") else b
    return a0 == b0 or a0.endswith("." + b0) or b0.endswith("." + a0)


# ---------------------------------------------------------------------------
# Default fetcher: connects to the validated address, reads the certificate
# ---------------------------------------------------------------------------

def _cert_info(cert: Dict[str, Any], valid: bool, now: datetime, error: Optional[str] = None) -> Dict[str, Any]:
    expires_at = None
    days_left = None
    not_after = cert.get("notAfter") if cert else None
    if not_after:
        try:
            expires = datetime.fromtimestamp(ssl.cert_time_to_seconds(not_after), tz=timezone.utc)
            expires_at = expires.isoformat().replace("+00:00", "Z")
            days_left = (expires - now).days
        except (ValueError, OverflowError):
            pass
    issuer = None
    for rdn in (cert.get("issuer") or ()) if cert else ():
        for key, value in rdn:
            if key == "organizationName":
                issuer = value
            elif key == "commonName" and issuer is None:
                issuer = value
    info: Dict[str, Any] = {"valid": valid, "expires_at": expires_at, "days_left": days_left, "issuer": issuer}
    if error:
        info["error"] = error
    return info


def _unverified_cert_info(der: Optional[bytes], now: datetime, error: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"valid": False, "expires_at": None, "days_left": None, "issuer": None, "error": error}
    if not der:
        return info
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        cert = x509.load_der_x509_certificate(der)
        expires = getattr(cert, "not_valid_after_utc", None) or cert.not_valid_after.replace(tzinfo=timezone.utc)
        info["expires_at"] = expires.isoformat().replace("+00:00", "Z")
        info["days_left"] = (expires - now).days
        for oid in (NameOID.ORGANIZATION_NAME, NameOID.COMMON_NAME):
            attrs = cert.issuer.get_attributes_for_oid(oid)
            if attrs:
                info["issuer"] = str(attrs[0].value)
                break
    except Exception as exc:  # cryptography missing or unparsable certificate
        logger.debug("Could not parse unverified certificate: %s", exc)
    return info


def default_fetcher(url: str, ip: str, timeout: float = TIMEOUT_SECONDS,
                    max_body: int = MAX_BODY_BYTES) -> FetchResult:
    """GET ``url`` by connecting to ``ip`` (already validated) with the right Host / SNI."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    https = parts.scheme == "https"
    port = parts.port or (443 if https else 80)
    deadline = time.monotonic() + timeout
    now = datetime.now(timezone.utc)

    def _connect() -> socket.socket:
        return socket.create_connection((ip, port), timeout=max(0.5, deadline - time.monotonic()))

    sock = _connect()
    tls_info: Optional[Dict[str, Any]] = None
    try:
        if https:
            context = ssl.create_default_context()
            try:
                sock = context.wrap_socket(sock, server_hostname=host)
                tls_info = _cert_info(sock.getpeercert() or {}, True, now)
            except ssl.SSLCertVerificationError as exc:
                # Invalid certificate: reconnect without verification so the owner still
                # gets the expiry date and the header report. Nothing is sent but a GET.
                try:
                    sock.close()
                except OSError:
                    pass
                reason = getattr(exc, "verify_message", None) or str(exc)
                insecure = ssl.create_default_context()
                insecure.check_hostname = False
                insecure.verify_mode = ssl.CERT_NONE
                sock = insecure.wrap_socket(_connect(), server_hostname=host)
                tls_info = _unverified_cert_info(sock.getpeercert(binary_form=True), now, reason)

        path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
        if parts.query:
            path += "?" + quote(parts.query, safe="=&%:@!$'()*+,;/?-._~")
        host_header = parts.netloc
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            f"User-Agent: {USER_AGENT}\r\n"
            "Accept: text/html,application/xhtml+xml;q=0.9,*/*;q=0.5\r\n"
            "Accept-Encoding: identity\r\n"
            "Connection: close\r\n\r\n"
        )
        sock.settimeout(max(0.5, deadline - time.monotonic()))
        sock.sendall(request.encode("ascii", "ignore"))
        response = http.client.HTTPResponse(sock, method="GET")
        response.begin()
        headers: Dict[str, str] = {}
        for key, value in response.getheaders():
            k = key.lower()
            headers[k] = f"{headers[k]}, {value}" if k in headers else value
        chunks: List[bytes] = []
        size = 0
        while size < max_body and time.monotonic() < deadline:
            sock.settimeout(max(0.5, deadline - time.monotonic()))
            chunk = response.read(min(16384, max_body - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
        return FetchResult(status_code=response.status, headers=headers, body=b"".join(chunks), tls=tls_info)
    finally:
        try:
            sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

_PRODUCT_TOKEN = re.compile(r"([A-Za-z][A-Za-z0-9_.+\- ]*?)/v?(\d[A-Za-z0-9_.+~\-]*)")
_GENERATOR = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 .!+\-]*?)\s+v?(\d[A-Za-z0-9_.\-]*)")
_META_GENERATOR = re.compile(
    r"""<meta\b(?=[^>]*\bname\s*=\s*["']generator["'])[^>]*\bcontent\s*=\s*["']([^"']{1,200})["']""",
    re.IGNORECASE,
)
_WP_CORE_VER = re.compile(r"""/wp-includes/[^"'\s>]+\?ver=(\d+\.\d+(?:\.\d+)?)""", re.IGNORECASE)
_WP_PLUGIN = re.compile(
    r"""/wp-content/plugins/([a-z0-9][a-z0-9_\-]{1,60})/[^"'\s>?]*(?:\?ver=(\d+(?:\.\d+){1,3}))?""",
    re.IGNORECASE,
)
MAX_PLUGINS = 15
_DISTRO_HINTS = ("ubuntu", "debian", "centos", "red hat", "rhel", "amazon linux", "amzn", "fedora",
                 "alpine", "almalinux", "rocky", "suse")


def _display(name: str) -> str:
    info = resolve_product(name)
    return info.name if info.known else name.strip()


def _add(detected: List[Dict[str, Any]], name: str, version: Optional[str], evidence: str,
         confidence: str = EXPLICIT) -> None:
    name = _display(name)
    for existing in detected:
        if existing["name"].lower() == name.lower():
            if existing["version"] is None and version:
                existing.update({"version": version, "evidence": evidence, "confidence": confidence})
            elif existing["confidence"] == INFERRED and confidence == EXPLICIT and version:
                existing.update({"version": version, "evidence": evidence, "confidence": confidence})
            return
    detected.append({"name": name, "version": version, "evidence": evidence[:200], "confidence": confidence})


def fingerprint(headers: Dict[str, str], body: bytes) -> List[Dict[str, Any]]:
    """Software the site announces: ``Server``, ``X-Powered-By``, ``X-Generator``, ``<meta name=generator>``."""
    detected: List[Dict[str, Any]] = []
    h = {k.lower(): v for k, v in (headers or {}).items()}

    for header in ("server", "x-powered-by"):
        value = (h.get(header) or "").strip()
        if not value:
            continue
        label = "Server" if header == "server" else "X-Powered-By"
        tokens = _PRODUCT_TOKEN.findall(value)
        if tokens:
            # "(Ubuntu)" etc. means a distribution package: fixes are backported, so the
            # upstream version number alone proves nothing.
            distro = any(d in value.lower() for d in _DISTRO_HINTS)
            for name, version in tokens:
                _add(detected, name.strip(), version, f"{label}: {value}")
                if distro:
                    for det in detected:
                        if det["version"] == version and det["evidence"].startswith(label):
                            det["distro_package"] = True
        else:
            for part in value.split(","):
                name = re.sub(r"\s*\(.*?\)\s*", "", part).strip()
                if name and len(name) <= 60:
                    _add(detected, name, None, f"{label}: {value}")

    aspnet = (h.get("x-aspnet-version") or "").strip()
    if aspnet:
        _add(detected, "ASP.NET", aspnet, f"X-AspNet-Version: {aspnet}")

    generators: List[Tuple[str, str]] = []
    if h.get("x-generator"):
        generators.append(("X-Generator", h["x-generator"]))
    text = ""
    if body:
        text = body[:MAX_BODY_BYTES].decode("utf-8", "replace")
        for content in _META_GENERATOR.findall(text)[:5]:
            generators.append(("meta generator", content))
    for label, value in generators:
        m = _GENERATOR.match(value)
        if m:
            _add(detected, m.group(1).strip(), m.group(2), f'{label}: "{value.strip()}"')
        else:
            name = re.split(r"[\-–(|]", value)[0].strip()
            if name and len(name) <= 60:
                _add(detected, name, None, f'{label}: "{value.strip()}"')

    # WordPress inferred from asset URLs: shown as unverified (the ?ver= value is often
    # the core version, a cache-buster or simply wrong).
    if text and ("/wp-content/" in text or "/wp-includes/" in text):
        versions = Counter(_WP_CORE_VER.findall(text))
        guessed = versions.most_common(1)[0][0] if versions else None
        if not any(d["name"].lower() == "wordpress" for d in detected):
            _add(detected, "WordPress", guessed,
                 f"/wp-includes/ asset URLs (?ver={guessed})" if guessed else "/wp-content/ asset URLs",
                 INFERRED if guessed else EXPLICIT)
        plugins: Dict[str, Optional[str]] = {}
        for slug, ver in _WP_PLUGIN.findall(text):
            slug = slug.lower()
            if slug not in plugins or (ver and not plugins[slug]):
                plugins[slug] = ver or None
            if len(plugins) >= MAX_PLUGINS:
                break
        for slug, ver in plugins.items():
            detected.append({
                "name": f"WordPress plugin: {slug}",
                "version": ver,
                "evidence": f"/wp-content/plugins/{slug}/" + (f"...?ver={ver}" if ver else ""),
                "confidence": INFERRED,
            })
    return detected


def security_headers(headers: Dict[str, str]) -> Dict[str, bool]:
    h = {k.lower(): v for k, v in (headers or {}).items()}
    return {
        "hsts": bool(h.get("strict-transport-security")),
        "csp": bool(h.get("content-security-policy")),
        "x_frame_options": bool(h.get("x-frame-options"))
        or "frame-ancestors" in (h.get("content-security-policy") or "").lower(),
        "x_content_type_options": "nosniff" in (h.get("x-content-type-options") or "").lower(),
        "referrer_policy": bool(h.get("referrer-policy")),
    }


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class WebScanner:
    def __init__(
        self,
        resolver: Optional[Resolver] = None,
        fetcher: Optional[Fetcher] = None,
        now: Optional[Callable[[], datetime]] = None,
    ):
        self.resolver = resolver or default_resolver
        self.fetcher = fetcher or default_fetcher
        self._now = now or (lambda: datetime.now(timezone.utc))

    def check_url(self, url: str) -> Tuple[str, List[str]]:
        """Validate a URL and resolve it. Returns (normalised url, public addresses)."""
        normalized = normalize_url(url)
        parts = urlsplit(normalized)
        host = parts.hostname or ""
        port = parts.port or (443 if parts.scheme == "https" else 80)
        try:
            ipaddress.ip_address(host)
            addresses = [host]
        except ValueError:
            try:
                addresses = list(self.resolver(host, port))
            except (socket.gaierror, OSError) as exc:
                raise LookupError(f"{host} does not resolve: {exc}") from exc
        if not addresses:
            raise LookupError(f"{host} does not resolve")
        blocked = [a for a in addresses if not is_public_ip(a)]
        if blocked:
            # One private answer is enough to refuse: do not pick the "good" one.
            raise UrlNotAllowed(f"{host} resolves to a non-public address and cannot be checked")
        addresses.sort(key=lambda a: ":" in a)   # IPv4 first: many servers have no IPv6 route
        return normalized, addresses

    def _fetch(self, url: str, addresses: List[str]) -> FetchResult:
        """Fetch from the first validated address that accepts a connection (at most two tried)."""
        last: Optional[BaseException] = None
        for address in addresses[:2]:
            try:
                return self.fetcher(url, address)
            except ssl.SSLError:
                raise
            except OSError as exc:
                last = exc
        assert last is not None
        raise last

    def scan(self, url: str) -> Dict[str, Any]:
        """Scan one registered URL. Raises ``UrlNotAllowed`` when the URL itself is refused."""
        now = self._now()
        issues: List[Dict[str, str]] = []
        result: Dict[str, Any] = {
            "url": url,
            "reachable": False,
            "status_code": None,
            "final_url": None,
            "tls": None,
            "headers": security_headers({}),
            "detected": [],
            "issues": issues,
            "scanned_at": now.isoformat().replace("+00:00", "Z"),
            "error": None,
        }

        try:
            current, addresses = self.check_url(url)
        except LookupError as exc:
            result["error"] = str(exc)
            issues.append({"title": "Site could not be reached", "severity": "high",
                           "fix": "Check the address is spelled correctly and that the site's DNS record exists."})
            return result
        result["url"] = current
        origin_host = urlsplit(current).hostname or ""

        response: Optional[FetchResult] = None
        hops = 0
        started = time.monotonic()
        while True:
            if response is not None and time.monotonic() - started > SCAN_BUDGET_SECONDS:
                issues.append({"title": "Site is very slow to respond", "severity": "low",
                               "fix": "The redirect chain took too long to follow; check the site's hosting."})
                break
            try:
                response = self._fetch(current, addresses)
            except (OSError, ssl.SSLError, http.client.HTTPException, ValueError) as exc:
                result["final_url"] = current
                result["error"] = f"{type(exc).__name__}: {exc}"[:300]
                issues.append({"title": "Site could not be reached", "severity": "high",
                               "fix": "Confirm the site is online and reachable from the internet, then scan again."})
                return result
            result["final_url"] = current
            location = response.headers.get("location")
            if response.status_code in (301, 302, 303, 307, 308) and location:
                target = urljoin(current, location)
                if hops >= MAX_REDIRECTS:
                    issues.append({"title": "Too many redirects", "severity": "medium",
                                   "fix": "Shorten the redirect chain so the site loads in one or two hops."})
                    break
                target_host = urlsplit(target).hostname or ""
                if not same_site(origin_host, target_host):
                    issues.append({
                        "title": f"Redirects to another site ({target_host}), which was not scanned",
                        "severity": "low",
                        "fix": "If that is your site too, add it as its own website so it can be checked.",
                    })
                    break
                try:
                    current, addresses = self.check_url(target)
                except (UrlNotAllowed, LookupError) as exc:
                    issues.append({"title": "Redirects to an address that cannot be checked", "severity": "medium",
                                   "fix": f"The redirect target was refused ({exc}). Point it at your public site."})
                    break
                hops += 1
                continue
            break

        result["reachable"] = True
        result["status_code"] = response.status_code
        result["tls"] = response.tls
        result["headers"] = security_headers(response.headers)
        result["detected"] = fingerprint(response.headers, response.body)
        final_https = urlsplit(result["final_url"]).scheme == "https"

        if not final_https:
            issues.append({
                "title": "Site does not use HTTPS", "severity": "high",
                "fix": "Install a TLS certificate (free with Let's Encrypt or your host) and redirect "
                       "http:// to https://.",
            })
        tls = response.tls
        if final_https and tls is not None:
            days = tls.get("days_left")
            if not tls.get("valid"):
                expired = days is not None and days < 0
                issues.append({
                    "title": "TLS certificate has expired" if expired else "TLS certificate is not valid",
                    "severity": "critical" if expired else "high",
                    "fix": "Renew or reissue the certificate for this host name; visitors see a browser warning.",
                })
            elif days is not None and days < CERT_WARN_DAYS:
                issues.append({
                    "title": f"Certificate expires in {max(days, 0)} days",
                    "severity": "high" if days < 7 else "medium",
                    "fix": "Renew the TLS certificate now, or turn on automatic renewal with your host.",
                })
        flags = result["headers"]
        if final_https and not flags["hsts"]:
            issues.append({
                "title": "No Strict-Transport-Security (HSTS) header", "severity": "medium",
                "fix": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' on the web server.",
            })
        if not flags["csp"]:
            issues.append({
                "title": "No Content-Security-Policy header", "severity": "medium",
                "fix": "Ask your web developer or host to add a Content-Security-Policy header.",
            })
        if not flags["x_content_type_options"]:
            issues.append({
                "title": "No X-Content-Type-Options header", "severity": "low",
                "fix": "Add the header 'X-Content-Type-Options: nosniff' on the web server.",
            })
        for det in result["detected"]:
            if det.get("version") and det.get("confidence") == EXPLICIT:
                issues.append({
                    "title": f"Software version visible to visitors ({det['name']} {det['version']})",
                    "severity": "low",
                    "fix": "Hide version banners (nginx: 'server_tokens off;', Apache: 'ServerTokens Prod', "
                           "PHP: 'expose_php = Off') and keep the software updated.",
                })
        return result


# ---------------------------------------------------------------------------
# Inventory sync
# ---------------------------------------------------------------------------

def sync_web_detections(db: Session, org_id: str) -> int:
    """Mirror explicit-version web detections into ``discovered_assets`` (source ``web_scan``).

    Rows for versions no longer seen on any of the org's websites are removed.
    Returns the number of web_scan rows after the sync.
    """
    from app.models.discovered_asset import DiscoveredAsset
    from app.services.vuln_intel.inventory import WEB_SCAN_SOURCE, web_detections

    wanted: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for det in web_detections(db, org_id):
        info = resolve_product(det["name"])
        wanted[(det["name"], str(det["version"])[:50])] = {"vendor": info.vendor}

    rows = (
        db.query(DiscoveredAsset)
        .filter(DiscoveredAsset.org_id == org_id, DiscoveredAsset.source == WEB_SCAN_SOURCE)
        .all()
    )
    existing = {(r.product, r.version or ""): r for r in rows}
    now = datetime.now(timezone.utc)
    for key, row in existing.items():
        if key not in wanted:
            db.delete(row)
        else:
            row.last_seen = now
    for (name, version), meta in wanted.items():
        if (name, version) not in existing:
            db.add(DiscoveredAsset(org_id=org_id, vendor=meta["vendor"], product=name,
                                   version=version, source=WEB_SCAN_SOURCE))
    db.commit()
    return len(wanted)
