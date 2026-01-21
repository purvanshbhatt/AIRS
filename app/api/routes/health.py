"""
Health check endpoint for Cloud Run and load balancer probes.
"""

from typing import Optional, List

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core.cors import get_allowed_origins, is_localhost_origin


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


class LLMHealthResponse(BaseModel):
    """LLM status response for verification and demo confidence."""
    llm_enabled: bool
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    demo_mode: bool


class CORSHealthResponse(BaseModel):
    """CORS configuration diagnostic response."""
    env: str
    localhost_allowed: bool
    allowed_origins: List[str]
    request_origin: Optional[str] = None
    origin_allowed: bool


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
    return HealthResponse(status="ok")


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
    
    return LLMHealthResponse(
        llm_enabled=llm_enabled,
        llm_provider=settings.LLM_PROVIDER if llm_enabled else None,
        llm_model=settings.LLM_MODEL if llm_enabled else None,
        demo_mode=settings.is_demo_mode
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
    env_name = "prod" if is_production else "local"
    
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
