"""
SSRF-safe URL fetcher.

Provides a secure way to fetch external URLs by protecting against:
- Private/Local IP access
- Non-HTTP schemes
- Large responses
- Excessive redirects
"""

import ipaddress
import socket
import logging
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Blocked IP ranges (Private, Loopback, Link-Local, Multicast)
BLOCKED_RANGES = [
    ipaddress.ip_network("127.0.0.0/8"),  # Loopback
    ipaddress.ip_network("10.0.0.0/8"),   # Private
    ipaddress.ip_network("172.16.0.0/12"), # Private
    ipaddress.ip_network("192.168.0.0/16"), # Private
    ipaddress.ip_network("169.254.0.0/16"), # Link-Local
    ipaddress.ip_network("224.0.0.0/4"),    # Multicast
    ipaddress.ip_network("::1/128"),        # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),       # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),      # IPv6 Link-Local
]

MAX_CONTENT_SIZE = 1 * 1024 * 1024  # 1 MB
TIMEOUT_SECONDS = 5
MAX_REDIRECTS = 3
USER_AGENT = "AIRS-Bot/1.0 (+https://gen-lang-client-0384513977.web.app)"


class SSRFError(Exception):
    """Raised when a URL is deemed unsafe."""
    pass


class FetchError(Exception):
    """Raised when content fetching fails."""
    pass


def _is_safe_ip(ip_addr: str) -> bool:
    """Check if an IP address is safe (public)."""
    try:
        ip = ipaddress.ip_address(ip_addr)
        for blocked in BLOCKED_RANGES:
            if ip in blocked:
                return False
        return True
    except ValueError:
        return False


def _resolve_and_validate(hostname: str) -> None:
    """
    Resolve hostname to IP and validate against blocked ranges.
    Raises SSRFError if unsafe.
    """
    try:
        # Get address info (handles both IPv4 and IPv6)
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            ip_addr = sockaddr[0]
            if not _is_safe_ip(ip_addr):
                logger.warning(f"Blocked unsafe IP resolution: {hostname} -> {ip_addr}")
                raise SSRFError(f"Host {hostname} resolves to blocked IP: {ip_addr}")
    except socket.gaierror as e:
        logger.warning(f"DNS resolution failed for {hostname}: {e}")
        raise FetchError(f"Could not resolve host: {hostname}")


def fetch_url(url: str) -> str:
    """
    Safely fetch a URL's content (text).
    
    Args:
        url: The URL to fetch.
        
    Returns:
        The text content of the response.
        
    Raises:
        SSRFError: If the URL resolves to a protected/private IP.
        FetchError: If the request fails (timeout, 404, etc.) or is too large.
    """
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise FetchError(f"Invalid URL format: {e}")

    # 1. Scheme Validation
    if parsed.scheme not in ("http", "https"):
        raise SSRFError(f"Blocked unsafe scheme: {parsed.scheme}")
    
    hostname = parsed.hostname
    if not hostname:
        raise FetchError("Invalid URL: missing hostname")

    # 2. DNS Validation (Direct IP check)
    _resolve_and_validate(hostname)

    # 3. Request Execution
    try:
        session = requests.Session()
        retries = Retry(total=MAX_REDIRECTS, backoff_factor=0.5)
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # Stream=True to check size before downloading full content
        with session.get(url, timeout=TIMEOUT_SECONDS, stream=True, headers={"User-Agent": USER_AGENT}) as response:
            
            # Check for excessive size in header first (optimization)
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_CONTENT_SIZE:
                raise FetchError(f"Content too large ({content_length} bytes)")

            response.raise_for_status()

            # Read content with size limit
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > MAX_CONTENT_SIZE:
                    raise FetchError("Content exceeded maximum allowed size")
            
            return content.decode("utf-8", errors="replace")

    except requests.exceptions.Timeout:
        raise FetchError("Request timed out")
    except requests.exceptions.TooManyRedirects:
        raise FetchError("Too many redirects")
    except requests.exceptions.RequestException as e:
        raise FetchError(f"Request failed: {str(e)}")
    except SSRFError:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error fetching {url}")
        raise FetchError(f"Internal fetch error: {str(e)}")
