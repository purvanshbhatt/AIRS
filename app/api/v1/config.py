"""
Environment Config Endpoint — GET /api/v1/config

Exposes a public, unauthenticated read-only endpoint that returns the
current environment configuration. This decouples frontend env-var
management from hardcoded configuration sheets and eliminates the
URL mismatch vulnerability described in Module 3 of the architecture blueprint.

Security Design:
  - No authentication required (public metadata only).
  - Returns only safe, non-sensitive configuration fields.
  - Never exposes secrets, API keys, or database URLs.
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/config")


class EnvironmentConfigResponse(BaseModel):
    """Public environment configuration shape.

    Used by frontend clients to dynamically resolve the correct API base
    URL without relying on build-time environment variable injection.
    """

    environment: str
    api_base_url: str
    analytics_enabled: bool
    auth_provider: str
    app_name: str
    app_version: Optional[str] = None


# ---------------------------------------------------------------------------
# GET /api/v1/config
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=EnvironmentConfigResponse,
    summary="Environment Configuration",
    description=(
        "Returns the current deployment environment metadata. "
        "Public endpoint — no authentication required. "
        "Safe fields only: environment name, API base URL, feature flags, auth provider."
    ),
    tags=["config"],
)
async def get_environment_config() -> EnvironmentConfigResponse:
    """Return the current environment configuration for frontend clients."""

    env_value = settings.ENV.value if hasattr(settings.ENV, "value") else str(settings.ENV)

    # Derive the canonical API base URL for this environment
    # Priority: explicit CLOUD_RUN_SERVICE_URL env var → infer from ENV
    api_base_url = (
        os.environ.get("CLOUD_RUN_SERVICE_URL")
        or os.environ.get("API_BASE_URL")
        or _infer_api_base_url(env_value)
    )

    return EnvironmentConfigResponse(
        environment=env_value,
        api_base_url=api_base_url,
        analytics_enabled=getattr(settings, "analytics_enabled", True),
        auth_provider="firebase",
        app_name=settings.APP_NAME,
        app_version=getattr(settings, "APP_VERSION", None),
    )


def _infer_api_base_url(env: str) -> str:
    """Infer the canonical API base URL from the environment name."""
    urls = {
        "staging": "https://api-staging.resilai.org",
        "prod":    "https://api.resilai.org",
        "demo":    "https://api-demo.resilai.org",
        "local":   "http://localhost:8000",
    }
    return urls.get(env, "http://localhost:8000")
