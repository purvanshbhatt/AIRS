"""
CORS Configuration Helper

Single source of truth for CORS allowed origins.
Validates, sanitizes, and logs the configured origins at startup.

Environment-aware behavior:
- ENV=prod: Only explicit HTTPS origins, localhost is NEVER allowed
- ENV=local/dev: Auto-adds localhost:3000 and localhost:5173, merges with CORS_ALLOW_ORIGINS
"""

import logging
import os
import re
from typing import List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger("airs.cors")

# Regex for valid origin: scheme://hostname[:port]
# Allows http/https schemes, valid hostnames, and optional port
ORIGIN_PATTERN = re.compile(
    r'^https?://'                           # http:// or https://
    r'('
    r'localhost|'                           # localhost
    r'127\.0\.0\.1|'                        # IPv4 loopback
    r'\[::1\]|'                             # IPv6 loopback
    r'[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?'  # hostname start
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*'  # additional hostname parts
    r')'
    r'(:\d{1,5})?$'                         # optional port
)

# Default localhost origins for development
DEV_LOCALHOST_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]


def is_localhost_origin(origin: str) -> bool:
    """Check if an origin is a localhost/loopback origin."""
    if not origin:
        return False
    try:
        parsed = urlparse(origin)
        hostname = parsed.hostname or ""
        return hostname in ("localhost", "127.0.0.1", "::1", "[::1]")
    except Exception:
        return False


def validate_origin(origin: str) -> Tuple[bool, str]:
    """
    Validate a single origin string.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not origin:
        return False, "Origin is empty"
    
    origin = origin.strip()
    
    if not origin:
        return False, "Origin is empty after trimming"
    
    # Check for wildcard
    if origin == "*":
        return True, ""  # Wildcard is technically valid but handled separately
    
    # Parse the URL to validate structure
    try:
        parsed = urlparse(origin)
    except Exception as e:
        return False, f"Failed to parse URL: {e}"
    
    # Must have a scheme
    if not parsed.scheme:
        return False, "Missing scheme (http:// or https://)"
    
    # Scheme must be http or https
    if parsed.scheme not in ("http", "https"):
        return False, f"Invalid scheme '{parsed.scheme}' (must be http or https)"
    
    # Must have a netloc (hostname)
    if not parsed.netloc:
        return False, "Missing hostname"
    
    # Should not have a path (except empty or /)
    if parsed.path and parsed.path != "/":
        return False, f"Origin should not include path: '{parsed.path}'"
    
    # Should not have query params or fragments
    if parsed.query:
        return False, "Origin should not include query parameters"
    if parsed.fragment:
        return False, "Origin should not include fragment"
    
    # Validate with regex for additional security
    if not ORIGIN_PATTERN.match(origin.rstrip("/")):
        return False, "Origin format is invalid"
    
    return True, ""


def get_allowed_origins(
    env_var: str = "CORS_ALLOW_ORIGINS",
    default: str = "",
    is_production: bool = False
) -> List[str]:
    """
    Get the list of allowed CORS origins with environment-aware behavior.
    
    Reads from environment variable, validates each origin,
    and returns a sanitized list.
    
    Environment rules:
    - ENV=prod: Only explicit HTTPS origins from CORS_ALLOW_ORIGINS
                Localhost origins are NEVER allowed
    - ENV=local/dev: Auto-adds localhost:3000 and localhost:5173
                     Merges with CORS_ALLOW_ORIGINS if provided
    
    Args:
        env_var: Environment variable name to read from
        default: Default value if env var is not set
        is_production: Whether running in production mode
        
    Returns:
        List of validated origin strings
    """
    raw_value = os.environ.get(env_var, default)
    
    # Handle wildcard
    if raw_value and raw_value.strip() == "*":
        if is_production:
            logger.error(
                "CORS wildcard '*' is NOT allowed in production! "
                "Set CORS_ALLOW_ORIGINS to specific origins. "
                "Falling back to empty list - all cross-origin requests will be rejected."
            )
            return []
        else:
            logger.warning(
                "CORS wildcard '*' detected. This allows ALL origins. "
                "Only use this in local development."
            )
            return ["*"]
    
    # Split on commas and validate each origin
    raw_origins = raw_value.split(",") if raw_value else []
    valid_origins: List[str] = []
    invalid_origins: List[Tuple[str, str]] = []
    rejected_localhost: List[str] = []
    
    for raw_origin in raw_origins:
        origin = raw_origin.strip()
        
        if not origin:
            continue
        
        # Remove trailing slash for consistency
        origin = origin.rstrip("/")
        
        is_valid, error = validate_origin(origin)
        
        if not is_valid:
            invalid_origins.append((raw_origin.strip(), error))
            continue
        
        # In production, reject localhost origins
        if is_production and is_localhost_origin(origin):
            rejected_localhost.append(origin)
            continue
        
        # In production, reject non-HTTPS origins (except for testing purposes)
        if is_production and not origin.startswith("https://"):
            logger.warning(
                f"Rejecting non-HTTPS origin in production: '{origin}'"
            )
            continue
        
        if origin not in valid_origins:  # Deduplicate
            valid_origins.append(origin)
    
    # Log warnings for invalid origins
    for origin, error in invalid_origins:
        logger.warning(
            f"Rejecting malformed CORS origin '{origin}': {error}"
        )
    
    # Log warnings for rejected localhost origins in production
    for origin in rejected_localhost:
        logger.warning(
            f"Rejecting localhost origin in production: '{origin}' "
            "(localhost is never allowed in ENV=prod)"
        )
    
    # In development mode, auto-add localhost origins
    if not is_production:
        for localhost_origin in DEV_LOCALHOST_ORIGINS:
            if localhost_origin not in valid_origins:
                valid_origins.append(localhost_origin)
    
    return valid_origins


def log_cors_config(origins: List[str], is_production: bool = False) -> None:
    """
    Log the CORS configuration at startup.
    
    Shows:
    - Current ENV (prod/dev)
    - Effective allowed origins
    - Whether localhost is enabled
    
    Args:
        origins: List of allowed origins
        is_production: Whether running in production
    """
    env_label = "PRODUCTION" if is_production else "DEVELOPMENT"
    env_value = "prod" if is_production else "local"
    
    # Check if localhost is in the origins
    localhost_enabled = any(is_localhost_origin(o) for o in origins)
    localhost_status = "DISABLED" if is_production else ("ENABLED" if localhost_enabled else "DISABLED")
    
    logger.info("=" * 60)
    logger.info("CORS Configuration")
    logger.info("=" * 60)
    logger.info(f"  ENV:              {env_value} ({env_label})")
    logger.info(f"  Localhost:        {localhost_status}")
    logger.info("-" * 60)
    
    if not origins:
        logger.error("  ❌ No origins configured - all CORS requests will fail!")
    elif origins == ["*"]:
        if is_production:
            logger.error("  ❌ Wildcard '*' - INSECURE IN PRODUCTION!")
        else:
            logger.warning("  ⚠️  Wildcard '*' - all origins allowed (dev mode)")
    else:
        logger.info(f"  Allowed Origins ({len(origins)}):")
        for origin in origins:
            if is_localhost_origin(origin):
                logger.info(f"    ✓ {origin} (localhost)")
            else:
                logger.info(f"    ✓ {origin}")
    
    logger.info("=" * 60)
    
    # Additional warnings
    if is_production and not origins:
        logger.error(
            "CRITICAL: No CORS origins configured in production! "
            "Set CORS_ALLOW_ORIGINS environment variable."
        )
    elif not is_production and localhost_enabled:
        logger.info(
            "Dev mode: localhost origins auto-added for local development."
        )
