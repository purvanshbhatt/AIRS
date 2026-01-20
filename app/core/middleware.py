"""
AIRS Middleware

Production-grade middleware for request tracking, logging, and error handling.
"""

import time
import logging
from typing import Callable

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

logger = logging.getLogger("airs.middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique request ID for each request.
    
    - Generates or uses existing X-Request-ID header
    - Sets request ID in context for logging correlation
    - Adds X-Request-ID to response headers
    - Logs request timing
    """
    
    # Paths to skip detailed logging (health checks, etc.)
    SKIP_LOGGING_PATHS = {"/health", "/", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()
        set_request_id(request_id)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Skip logging for health checks
        skip_logging = request.url.path in self.SKIP_LOGGING_PATHS
        
        if not skip_logging:
            logger.info(
                f"Request started: {request.method} {request.url.path}"
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            if not skip_logging:
                logger.info(
                    f"Request completed: {request.method} {request.url.path} "
                    f"status={response.status_code} duration={duration_ms:.2f}ms"
                )
            
            return response
            
        except Exception as exc:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log error with full context
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={type(exc).__name__} duration={duration_ms:.2f}ms"
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
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": exc.detail,
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
