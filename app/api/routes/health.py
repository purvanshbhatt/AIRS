"""
Health check endpoint for Cloud Run and load balancer probes.
"""

from typing import Optional, List
import importlib.util

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.cors import get_allowed_origins, is_localhost_origin
from app.core.product import get_product_info


class ProductInfo(BaseModel):
    name: str
    version: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    product: ProductInfo


class LLMHealthResponse(BaseModel):
    """LLM status response for verification and demo confidence."""
    llm_enabled: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    demo_mode: bool
    runtime_check: dict


class CORSHealthResponse(BaseModel):
    """CORS configuration diagnostic response."""
    env: str
    localhost_allowed: bool
    allowed_origins: List[str]
    request_origin: Optional[str] = None
    origin_allowed: bool


class SystemHealthResponse(BaseModel):
    version: Optional[str] = None
    environment: str
    llm_enabled: bool
    demo_mode: bool
    is_read_only: bool = False
    integrations_enabled: bool
    last_deployment_at: Optional[str] = None


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Simple health check for load balancers and orchestrators. Returns immediately with minimal processing.",
    responses={
        200: {"description": "Service is healthy and ready to receive traffic"}
    }
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns a simple status for load balancer health probes.
    Cloud Run uses this to determine if the service is ready to receive traffic.
    """
    return HealthResponse(status="ok", product=ProductInfo(**get_product_info()))


@router.get(
    "/health/llm",
    response_model=LLMHealthResponse,
    summary="LLM Status",
    description="Returns the current LLM configuration status. Does NOT call the LLM. Safe to expose publicly.",
    responses={
        200: {"description": "LLM configuration status"}
    }
)
async def llm_health() -> LLMHealthResponse:
    """
    LLM status endpoint.
    
    Returns the current LLM configuration for verification and demo confidence.
    Does NOT make any LLM API calls - just returns configuration state.
    """
    llm_enabled = settings.is_llm_enabled
    sdk_installed = importlib.util.find_spec("google.genai") is not None
    feature_flag_enabled = bool(settings.AIRS_USE_LLM)
    credentials_configured = bool(settings.GEMINI_API_KEY or settings.GCP_PROJECT_ID)
    if settings.GCP_PROJECT_ID:
        auth_mode = "vertex-adc"
    elif settings.GEMINI_API_KEY:
        auth_mode = "api-key"
    else:
        auth_mode = "none"
    runtime_check = {
        "sdk_installed": sdk_installed,
        "feature_flag_enabled": feature_flag_enabled,
        "credentials_configured": credentials_configured,
        "auth_mode": auth_mode,
        "client_configured": bool(feature_flag_enabled and sdk_installed and (credentials_configured or settings.is_demo_mode)),
    }
    
    return LLMHealthResponse(
        llm_enabled=llm_enabled,
        llm_provider=settings.LLM_PROVIDER if llm_enabled else None,
        llm_model=settings.LLM_MODEL if llm_enabled else None,
        demo_mode=settings.is_demo_mode,
        runtime_check=runtime_check,
    )


@router.get(
    "/health/cors",
    response_model=CORSHealthResponse,
    summary="CORS Verification",
    description="Returns current CORS configuration for debugging. Does NOT expose secrets. Safe to call from browser console.",
    responses={
        200: {"description": "CORS configuration status"}
    }
)
async def cors_health(request: Request) -> CORSHealthResponse:
    """
    CORS diagnostic endpoint.
    
    Returns the current CORS configuration for verification and debugging.
    Useful for demo verification and troubleshooting "Failed to fetch" errors.
    
    Does NOT expose any secrets - only shows:
    - Environment (prod/local)
    - Whether localhost is allowed
    - List of allowed origins
    - The requesting origin (if present)
    - Whether that origin would be allowed
    """
    is_production = settings.is_prod
    env_name = settings.ENV.value
    
    # Get the effective allowed origins
    allowed_origins = get_allowed_origins(
        env_var="CORS_ALLOW_ORIGINS",
        default="",
        is_production=is_production
    )
    
    # Check if localhost is allowed
    localhost_allowed = not is_production and any(
        is_localhost_origin(o) for o in allowed_origins
    )
    
    # Get the request's Origin header (if present)
    request_origin = request.headers.get("origin")
    
    # Determine if the request origin would be allowed
    origin_allowed = False
    if request_origin:
        # Normalize the origin (strip trailing slash)
        normalized_origin = request_origin.rstrip("/")
        if allowed_origins == ["*"]:
            origin_allowed = True
        else:
            origin_allowed = normalized_origin in allowed_origins
    
    return CORSHealthResponse(
        env=env_name,
        localhost_allowed=localhost_allowed,
        allowed_origins=allowed_origins,
        request_origin=request_origin,
        origin_allowed=origin_allowed
    )


@router.get(
    "/health/system",
    response_model=SystemHealthResponse,
    summary="System Status",
    description="Public system status for UI footer/build verification.",
)
async def system_health() -> SystemHealthResponse:
    product = get_product_info()
    return SystemHealthResponse(
        version=product.get("version"),
        environment=settings.ENV.value,
        llm_enabled=settings.is_llm_enabled,
        demo_mode=settings.is_demo_mode,
        is_read_only=settings.is_read_only,
        integrations_enabled=settings.INTEGRATIONS_ENABLED,
        last_deployment_at=settings.DEPLOYED_AT,
    )
