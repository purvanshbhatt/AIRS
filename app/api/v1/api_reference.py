"""
In-app API reference.

Exposes:
  GET /api/v1/reference/openapi  — customer-safe OpenAPI document for the
                                   in-product API explorer
  GET /api/v1/reference/status   — small live status used by the explorer's
                                   "Live check"

Both require a signed-in user (the same ``require_auth`` dependency the other
v1 routes use). The operator-only Swagger pages (``/docs``, ``/redoc``,
``/openapi.json``) keep their HTTP Basic guard in ``app/main.py``; this module
does not touch them and never serves the unfiltered schema.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel

from app.core.auth import User, require_auth
from app.core.config import settings
from app.core.product import get_product_info

logger = logging.getLogger("airs.api_reference")

router = APIRouter(prefix="/reference")


# ── What a customer may see ─────────────────────────────────────────────────
#
# The explorer only documents the versioned customer API plus the public
# liveness probes. Everything else is dropped, and the lists below remove the
# parts of /api/v1 that are not for customers:
#
#   * webhook receivers  - called by other systems with their own shared
#                          secrets, not by a signed-in person
#   * pilot-lead intake  - the marketing sign-up form and its admin views
#   * observability      - operator metrics and service-level numbers
#   * admin / debug / internal / demo seeding / billing webhooks - operator
#                          tooling; listed here even where no such v1 route
#                          exists today, so one added later stays hidden
#   * /health/cors, /health/llm - configuration diagnostics (allowed origins,
#                          model names); only the plain probes are public
#
# Routes declared with ``include_in_schema=False`` never reach this filter:
# FastAPI leaves them out of the generated document already.
#
# This is the single place to change what the explorer shows.

ALLOWED_PATH_PREFIX = "/api/v1/"

PUBLIC_PROBE_PATHS = frozenset({"/health", "/health/system"})

DENIED_PATH_PREFIXES = (
    "/api/v1/admin",
    "/api/v1/internal",
    "/api/v1/debug",
    "/api/v1/demo",
    "/api/v1/pilot-leads",
    "/api/v1/observability",
    "/api/v1/billing/webhook",
    "/api/v1/connectors/webhook",
    "/api/v1/integrations/siem",
    "/api/v1/telemetry/webhook",
)

# A path is also dropped when any one of its segments is in this set, wherever
# it sits in the path (for example /api/v1/orgs/{org_id}/admin/...).
DENIED_PATH_SEGMENTS = frozenset(
    {"admin", "debug", "internal", "webhook", "webhooks", "seed", "demo-seed"}
)

DENIED_TAGS = frozenset({"admin", "internal", "debug", "pilot", "observability"})

_HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options", "trace")


def is_customer_safe_path(path: str) -> bool:
    """True when ``path`` may appear in the customer-facing reference."""
    if path in PUBLIC_PROBE_PATHS:
        return True
    if not path.startswith(ALLOWED_PATH_PREFIX):
        return False
    if any(path == p or path.startswith(p + "/") for p in DENIED_PATH_PREFIXES):
        return False
    segments = {segment.lower() for segment in path.split("/") if segment}
    return not (segments & DENIED_PATH_SEGMENTS)


def _dedupe(values: Iterable[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for value in values:
        key = value.lower()
        if key not in seen:
            seen.add(key)
            out.append(value)
    return out


def _collect_refs(node: Any, found: Set[str]) -> None:
    """Collect every ``#/components/schemas/<name>`` reference under ``node``."""
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            found.add(ref.rsplit("/", 1)[-1])
        for value in node.values():
            _collect_refs(value, found)
    elif isinstance(node, list):
        for value in node:
            _collect_refs(value, found)


def filter_openapi_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``document`` holding only customer-safe operations.

    Schemas that are only used by removed operations are removed too, so the
    shape of an internal payload cannot be read from ``components``.
    """
    kept_paths: Dict[str, Any] = {}
    for path, item in (document.get("paths") or {}).items():
        if not is_customer_safe_path(path):
            continue
        kept_item: Dict[str, Any] = {}
        for key, operation in item.items():
            if key not in _HTTP_METHODS:
                kept_item[key] = operation
                continue
            tags = _dedupe(operation.get("tags") or [])
            if {tag.lower() for tag in tags} & DENIED_TAGS:
                continue
            kept_operation = dict(operation)
            if tags:
                kept_operation["tags"] = tags
            kept_item[key] = kept_operation
        if any(key in _HTTP_METHODS for key in kept_item):
            kept_paths[path] = kept_item

    all_schemas: Dict[str, Any] = (document.get("components") or {}).get("schemas") or {}
    reachable: Set[str] = set()
    _collect_refs(kept_paths, reachable)
    pending = list(reachable)
    while pending:
        name = pending.pop()
        nested: Set[str] = set()
        _collect_refs(all_schemas.get(name), nested)
        for other in nested - reachable:
            reachable.add(other)
            pending.append(other)

    components = dict(document.get("components") or {})
    components["schemas"] = {
        name: schema for name, schema in all_schemas.items() if name in reachable
    }

    filtered = dict(document)
    filtered["paths"] = kept_paths
    filtered["components"] = components
    return filtered


def build_reference_document() -> Dict[str, Any]:
    """Generate the customer-safe OpenAPI document from the app's routers.

    The live app mounts the API with ``include_in_schema=False`` (the operator
    Swagger page hides it), so the document is generated from the same router
    objects mounted on a throwaway app. Each route keeps its own
    ``include_in_schema`` flag there, so routes hidden by their authors stay
    hidden.
    """
    from app.api.routes.health import router as health_router
    from app.api.v1 import router as v1_router

    scratch = FastAPI(title=settings.APP_NAME, version="1.0.0")
    scratch.include_router(health_router)
    scratch.include_router(v1_router, prefix="/api/v1")

    document = get_openapi(
        title=f"{settings.APP_NAME} API",
        version="1.0.0",
        description=(
            "The endpoints your organisation can call with its own sign-in. "
            "Operator-only and system-to-system endpoints are not listed."
        ),
        routes=scratch.routes,
    )
    return filter_openapi_document(document)


_document_lock = threading.Lock()
_cached_document: Optional[Dict[str, Any]] = None


def get_reference_document() -> Dict[str, Any]:
    """Return the cached document, building it on first use.

    Routes are fixed once the process has started, so the document is built
    once and kept in memory.
    """
    global _cached_document
    if _cached_document is None:
        with _document_lock:
            if _cached_document is None:
                _cached_document = build_reference_document()
    return _cached_document


def reset_reference_cache() -> None:
    """Drop the cached document (used by tests)."""
    global _cached_document
    with _document_lock:
        _cached_document = None


@router.get(
    "/openapi",
    summary="API reference document",
    description=(
        "The OpenAPI description of the endpoints available to your "
        "organisation. Used by the API explorer inside the product."
    ),
)
async def get_reference_openapi(user: User = Depends(require_auth)) -> Dict[str, Any]:
    return get_reference_document()


# ── Live status ─────────────────────────────────────────────────────────────


class DependencyCheck(BaseModel):
    id: str
    label: str
    ok: bool
    detail: str


class ReferenceStatus(BaseModel):
    api_version: str
    build: Optional[str] = None
    environment: str
    server_time: str
    demo_mode: bool
    read_only: bool
    endpoint_count: int
    checks: List[DependencyCheck]


async def _check_api() -> bool:
    from app.api.routes.health import health_check

    return (await health_check()).status == "ok"


async def _check_data_store() -> bool:
    from app.db import firestore as firestore_layer

    return bool(firestore_layer.is_firestore_available())


async def _check_narratives() -> bool:
    from app.api.routes.health import llm_health

    return bool((await llm_health()).runtime_check.get("client_configured"))


async def _check_connectors() -> bool:
    from app.api.routes.health import system_health

    return bool((await system_health()).integrations_enabled)


# Each entry reuses a check the service already runs for its own health pages.
# (id, label, check, text when ok, text when not ok). The texts are fixed so a
# failure can never carry a hostname, a secret or an error trace.
_STATUS_CHECKS = (
    ("api", "API service", _check_api, "Answering requests.", "Not answering normally."),
    (
        "data_store",
        "Data storage",
        _check_data_store,
        "Connected.",
        "Not connected. Saved changes may not be kept.",
    ),
    (
        "narratives",
        "Report narrative service",
        _check_narratives,
        "Configured.",
        "Not configured. Reports use standard wording.",
    ),
    (
        "connectors",
        "Connectors",
        _check_connectors,
        "Switched on.",
        "Switched off for this deployment.",
    ),
)


async def _environment_name() -> str:
    from app.api.routes.health import health_check

    try:
        return (await health_check()).environment or settings.ENV.value
    except Exception:
        return settings.ENV.value


@router.get(
    "/status",
    response_model=ReferenceStatus,
    summary="Live API status",
    description=(
        "Whether the API and the services it depends on are working right "
        "now. Contains no secrets and no internal addresses."
    ),
)
async def get_reference_status(
    request: Request, user: User = Depends(require_auth)
) -> ReferenceStatus:
    checks: List[DependencyCheck] = []
    for check_id, label, check, ok_text, failed_text in _STATUS_CHECKS:
        try:
            ok = bool(await check())
        except Exception:
            logger.warning("Reference status check '%s' could not run", check_id, exc_info=True)
            ok = False
        checks.append(
            DependencyCheck(id=check_id, label=label, ok=ok, detail=ok_text if ok else failed_text)
        )

    try:
        endpoint_count = sum(
            1
            for item in get_reference_document().get("paths", {}).values()
            for method in item
            if method in _HTTP_METHODS
        )
    except Exception:
        logger.warning("Reference document could not be built for status", exc_info=True)
        endpoint_count = 0

    return ReferenceStatus(
        api_version=str(getattr(request.app, "version", "") or "1.0.0"),
        build=get_product_info().get("version"),
        environment=await _environment_name(),
        server_time=datetime.now(timezone.utc).isoformat(),
        demo_mode=bool(settings.is_demo_mode),
        read_only=bool(settings.is_read_only),
        endpoint_count=endpoint_count,
        checks=checks,
    )
