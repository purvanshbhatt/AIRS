"""
Health check endpoint for Cloud Run and load balancer probes.
"""

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


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
