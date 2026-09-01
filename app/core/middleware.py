"""
AIRS Middleware

Production-grade middleware for request tracking, logging, security headers,
and error handling.
"""

import time
import logging
from typing import Callable, List

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    generate_request_id,
    set_request_id,
    get_request_id,
    get_safe_error_response,
)
from app.core.cors import is_trusted_origin

logger = logging.getLogger("airs.middleware")


# ---- CORS Error Safety Net Middleware ----

class CORSErrorSafetyMiddleware(BaseHTTPMiddleware):
    """
    Safety-net middleware that guarantees CORS headers are present on EVERY
    response, including error responses (5xx, timeouts, unhandled exceptions).

    WHY THIS EXISTS:
    When Cloud Run's reverse proxy returns a 504 (timeout) or the app crashes,
    CORS headers from FastAPI's CORSMiddleware get stripped because that
    middleware never ran its response-path. The browser then reports a misleading
    "CORS error" instead of the real error. This middleware sits OUTSIDE the
    CORS middleware and catches those cases.
    """

    def __init__(self, app, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []

    def _get_cors_origin(self, request: Request) -> str:
        """Return the request Origin if it's in our allowed list or matches trusted pattern, else empty."""
        origin = request.headers.get("origin", "")
        if not origin:
            return ""
        origin = origin.strip().rstrip("/")
        if origin in self.allowed_origins or is_trusted_origin(origin):
            return origin
        return ""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = self._get_cors_origin(request)
        raw_origin = request.headers.get("origin", "")

        # Fast-path: handle preflight OPTIONS explicitly so Cloud Run
        # never has a chance to timeout or strip headers on them.
        if request.method == "OPTIONS":
            req_headers = request.headers.get("access-control-request-headers")
            req_method = request.headers.get("access-control-request-method")
            
            response = Response(status_code=204)
            # Only use the validated 'origin'. If not trusted, don't allow CORS.
            if origin:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Methods"] = req_method if req_method else "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD"
                response.headers["Access-Control-Allow-Headers"] = req_headers if req_headers else "*"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Max-Age"] = "86400"
            return response

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "Unhandled exception in middleware chain: %s", exc, exc_info=True
            )
            if "/readiness/" in request.url.path:
                import uuid
                from datetime import datetime, timezone
                org_id = request.url.path.split("/")[-1]
                fallback = {
                    "report_id": str(uuid.uuid4()),
                    "org_id": org_id,
                    "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": "unknown",
                    "clinic_health_pct": 0,
                    "connector_health_pct": 0,
                    "greeting": "System Degraded",
                    "summary": "We are unable to load your clinic's data at this time. Please check back later.",
                    "business_continuity": {
                        "operational_readiness": {
                            "can_operate_today": False,
                            "can_recover": False,
                            "current_blockers": ["System unavailable"],
                            "estimated_downtime_minutes": 0,
                            "critical_systems_verified": [],
                            "critical_systems_assumed": []
                        }
                    },
                    "passed_checks": [],
                    "failed_checks": [],
                    "warnings": [],
                    "unknowns": [],
                    "immediate_actions": [],
                    "coverage": {
                        "coverage_pct": 0,
                        "monitored": [],
                        "not_monitored": []
                    },
                    "connectors": [],
                    "verification": {
                        "verification_source": "System",
                        "last_verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "connector_health": "unreachable",
                        "confidence_pct": 0,
                        "verification_status": "unverified",
                        "data_age_description": "Data unavailable",
                        "can_reverify": False,
                        "verification_method": "System check"
                    },
                    "audit_snapshot_id": str(uuid.uuid4()),
                    "checks_performed": 0,
                    "devices_checked": 0,
                    "accounts_checked": 0,
                    "backups_verified": 0
                }
                response = JSONResponse(status_code=200, content=fallback)
            else:
                response = JSONResponse(
                    status_code=500,
                    content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
                )

        # Ensure CORS headers are always present for valid origins only
        if origin:
            if "access-control-allow-origin" not in response.headers:
                response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = "*"

        return response


# ---- Security Headers Middleware ----

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security response headers on every response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        # HSTS: 1 year, include subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request ID for each request.
    
    - Generates or uses existing X-Request-ID header
    - Sets request ID in context for logging correlation
    - Adds X-Request-ID to response headers
    - Logs request timing
    - Records Prometheus metrics
    - Adds tracing attributes
    """
    
    # Paths to skip detailed logging (health checks, etc.)
    SKIP_LOGGING_PATHS = {"/health", "/", "/favicon.ico", "/api/v1/observability/metrics"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from opentelemetry import trace
        from app.observability.metrics import API_REQUEST_DURATION
        
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Skip logging for health checks
        skip_logging = request.url.path in self.SKIP_LOGGING_PATHS
        
        # Get active span
        tracer = trace.get_tracer(__name__)
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("http.request_id", request_id)
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.url", str(request.url))
            
        if not skip_logging:
            org_id = request.path_params.get("org_id") or request.query_params.get("org_id")
            if span.is_recording() and org_id:
                span.set_attribute("app.org_id", org_id)
                
            logger.info(
                "request_start request_id=%s method=%s path=%s org_id=%s",
                request_id,
                request.method,
                request.url.path,
                org_id or "-",
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Record metric
            API_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).observe(duration)
            
            if span.is_recording():
                span.set_attribute("http.status_code", response.status_code)
            
            if not skip_logging:
                org_id = request.path_params.get("org_id") or request.query_params.get("org_id")
                logger.info(
                    "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%.2f org_id=%s",
                    request_id,
                    request.method,
                    request.url.path,
                    response.status_code,
                    duration_ms,
                    org_id or "-",
                )
            
            return response
            
        except Exception as exc:
            # Calculate duration even on error
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            # Record metric
            API_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).observe(duration)
            
            if span.is_recording():
                span.record_exception(exc)
                span.set_status(trace.status.Status(trace.status.StatusCode.ERROR))
            
            # Log error with full context
            logger.error(
                "request_failed request_id=%s method=%s path=%s error=%s duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                type(exc).__name__,
                duration_ms,
            )
            
            # Re-raise to let exception handler deal with it
            raise


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that returns safe JSON errors.
    
    - Logs full stack trace server-side
    - Returns safe error response to client (no internal details)
    - Includes request ID for support correlation
    """
    # 1. Product Feature: Return Graceful Unknowns for Readiness endpoint
    if "/readiness/" in request.url.path:
        import uuid
        from datetime import datetime, timezone
        org_id = request.url.path.split("/")[-1]
        
        fallback = {
            "report_id": str(uuid.uuid4()),
            "org_id": org_id,
            "report_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": "unknown",
            "clinic_health_pct": 0,
            "connector_health_pct": 0,
            "greeting": "System Degraded",
            "summary": "We are unable to load your clinic's data at this time. Please check back later.",
            "business_continuity": {
                "operational_readiness": {
                    "can_operate_today": False,
                    "can_recover": False,
                    "current_blockers": ["System unavailable"],
                    "estimated_downtime_minutes": 0,
                    "critical_systems_verified": [],
                    "critical_systems_assumed": []
                }
            },
            "passed_checks": [],
            "failed_checks": [],
            "warnings": [],
            "unknowns": [],
            "immediate_actions": [],
            "coverage": {
                "coverage_pct": 0,
                "monitored": [],
                "not_monitored": []
            },
            "connectors": [],
            "verification": {
                "verification_source": "System",
                "last_verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "connector_health": "unreachable",
                "confidence_pct": 0,
                "verification_status": "unverified",
                "data_age_description": "Data unavailable",
                "can_reverify": False,
                "verification_method": "System check"
            },
            "audit_snapshot_id": str(uuid.uuid4()),
            "checks_performed": 0,
            "devices_checked": 0,
            "accounts_checked": 0,
            "backups_verified": 0
        }
        response = JSONResponse(status_code=200, content=fallback)
        response.headers["X-Request-ID"] = get_request_id() or "-"
        return response

    # Get safe error response (logs internally)
    error_response = get_safe_error_response(exc)
    
    # Create JSON response with request ID header
    response = JSONResponse(
        status_code=500,
        content=error_response
    )
    response.headers["X-Request-ID"] = get_request_id() or "-"
    
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for HTTP exceptions with consistent error format.

    Produces structured error responses that let the frontend distinguish:
    - ORGANIZATION_NOT_FOUND (specific 404 from org lookup)
    - NOT_FOUND (generic route not found)
    - ORG_ID_REQUIRED (missing/empty org identifier)
    - UNAUTHORIZED / FORBIDDEN / etc.
    """
    request_id = get_request_id() or "-"

    # Map status codes to error codes
    error_codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
    }

    error_code = error_codes.get(exc.status_code, f"HTTP_{exc.status_code}")

    # Extract message from detail, handling both string and dict formats
    detail = exc.detail
    if isinstance(detail, dict):
        message = detail.get("message", str(detail))
    elif isinstance(detail, str):
        message = detail
    else:
        message = str(detail) if detail else "Unknown error"

    # Refine error code based on detail content for better frontend disambiguation
    if exc.status_code == 404 and isinstance(detail, str):
        if "Organization not found" in detail:
            error_code = "ORGANIZATION_NOT_FOUND"
        elif "Issue not found" in detail:
            error_code = "RESOURCE_NOT_FOUND"
    elif exc.status_code == 422 and isinstance(detail, str):
        if "Organization ID is required" in detail:
            error_code = "ORG_ID_REQUIRED"

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "request_id": request_id
            }
        }
    )
    response.headers["X-Request-ID"] = request_id

    return response


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler for request validation errors with consistent format.
    """
    request_id = get_request_id() or "-"
    
    # Extract validation error details
    errors = exc.errors()
    if errors:
        # Get first error for main message
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error.get("loc", []))
        message = f"Validation error: {field} - {first_error.get('msg', 'Invalid value')}"
    else:
        message = "Request validation failed"
        
    try:
        body_bytes = await request.body()
        logger.warning(f"Validation Error Payload [path={request.url.path}]: {body_bytes.decode('utf-8')} || Errors: {errors}")
    except Exception as e:
        logger.warning(f"Failed to read validation error payload: {e}")
    
    response = JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": message,
                "request_id": request_id
            }
        }
    )
    response.headers["X-Request-ID"] = request_id
    
    return response
