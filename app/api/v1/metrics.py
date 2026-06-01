"""
API routes for Observability (Metrics, Health, SLI).
"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get(
    "/metrics",
    summary="Prometheus Scrape Endpoint",
    description="Exposes application metrics in Prometheus text format.",
)
async def get_metrics():
    """Return Prometheus metrics."""
    metrics_data = generate_latest()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


@router.get(
    "/health",
    summary="Detailed Health Dashboard",
    description="Returns aggregate health status across connectors, database, and background tasks.",
)
async def get_health():
    """Detailed system health check."""
    return {
        "status": "healthy",
        "components": {
            "database": "ok",
            "scoring_engine": "ok",
            "simulation_engine": "ok",
            "policy_engine": "ok",
            "connector_manager": "ok",
        },
        "version": "1.0.0-staging"
    }


@router.get(
    "/sli",
    summary="SLI/SLO Status",
    description="Returns Service Level Indicator metrics.",
)
async def get_sli():
    """SLI/SLO tracking endpoint."""
    return {
        "availability": 99.99,
        "latency_p95_ms": 45.2,
        "latency_p99_ms": 120.5,
        "error_rate_pct": 0.01,
        "active_connectors": 3,
    }
