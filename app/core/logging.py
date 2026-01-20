"""
AIRS Production Logging Module

Provides structured logging with request ID correlation, event tracking,
and safe error handling for production environments.
"""

import logging
import sys
import uuid
import traceback
from contextvars import ContextVar
from typing import Optional, Any, Dict
from datetime import datetime

from app.core.config import settings

# Context variable for request ID (thread-safe)
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID in context."""
    request_id_var.set(request_id)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid.uuid4())[:12]


class RequestIdFilter(logging.Filter):
    """Logging filter that adds request_id to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


class SafeJsonFormatter(logging.Formatter):
    """
    JSON-style log formatter that's safe for production.
    Does not include sensitive data in logs.
    """
    
    SENSITIVE_KEYS = {"password", "token", "api_key", "secret", "authorization", "cookie"}
    
    def format(self, record: logging.LogRecord) -> str:
        # Build structured log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "request_id": getattr(record, "request_id", "-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present (excluding sensitive ones)
        if hasattr(record, "extra_data"):
            safe_extra = self._sanitize_data(record.extra_data)
            log_entry["data"] = safe_extra
        
        # Format as single line for log aggregators
        parts = [f"{k}={self._format_value(v)}" for k, v in log_entry.items()]
        return " | ".join(parts)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for logging."""
        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 500:
                return f'"{value[:500]}..."'
            return f'"{value}"'
        return str(value)
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive keys from data."""
        if not isinstance(data, dict):
            return data
        return {
            k: "***REDACTED***" if k.lower() in self.SENSITIVE_KEYS else v
            for k, v in data.items()
        }


def setup_logging() -> None:
    """Configure application logging."""
    # Determine log level
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    
    # Create formatter
    if settings.ENV.value == "prod":
        formatter = SafeJsonFormatter()
    else:
        # Human-readable format for local development
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    root_logger.addHandler(console_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


# Event logger for business events
class EventLogger:
    """
    Structured event logger for key business events.
    All events are logged with request ID correlation.
    """
    
    def __init__(self, name: str = "airs.events"):
        self.logger = logging.getLogger(name)
    
    def _log_event(self, level: int, event: str, **kwargs) -> None:
        """Log an event with structured data."""
        request_id = get_request_id() or "-"
        extra_data = {"event": event, **kwargs}
        
        # Create log record with extra data
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(event)",
            0,
            f"[{event}] {self._format_message(kwargs)}",
            (),
            None
        )
        record.extra_data = extra_data
        record.request_id = request_id
        self.logger.handle(record)
    
    def _format_message(self, data: Dict[str, Any]) -> str:
        """Format event data as readable message."""
        parts = [f"{k}={v}" for k, v in data.items() if k != "event"]
        return " ".join(parts) if parts else ""
    
    # ----- Business Events -----
    
    def assessment_created(self, assessment_id: str, organization_id: str, title: str) -> None:
        """Log assessment creation."""
        self._log_event(
            logging.INFO,
            "assessment.created",
            assessment_id=assessment_id,
            organization_id=organization_id,
            title=title
        )
    
    def answers_submitted(self, assessment_id: str, answer_count: int) -> None:
        """Log answers submission."""
        self._log_event(
            logging.INFO,
            "answers.submitted",
            assessment_id=assessment_id,
            answer_count=answer_count
        )
    
    def scoring_executed(self, assessment_id: str, overall_score: float, findings_count: int) -> None:
        """Log scoring execution."""
        self._log_event(
            logging.INFO,
            "scoring.executed",
            assessment_id=assessment_id,
            overall_score=round(overall_score, 2),
            findings_count=findings_count
        )
    
    def report_generated(self, assessment_id: str, format: str = "pdf") -> None:
        """Log report generation."""
        self._log_event(
            logging.INFO,
            "report.generated",
            assessment_id=assessment_id,
            format=format
        )
    
    def summary_fetched(self, assessment_id: str, llm_used: bool = False) -> None:
        """Log summary fetch."""
        self._log_event(
            logging.INFO,
            "summary.fetched",
            assessment_id=assessment_id,
            llm_used=llm_used
        )
    
    def organization_created(self, organization_id: str, name: str) -> None:
        """Log organization creation."""
        self._log_event(
            logging.INFO,
            "organization.created",
            organization_id=organization_id,
            name=name
        )
    
    def error_occurred(self, error_type: str, message: str, **kwargs) -> None:
        """Log an error event."""
        self._log_event(
            logging.ERROR,
            "error.occurred",
            error_type=error_type,
            message=message,
            **kwargs
        )


# Global event logger instance
event_logger = EventLogger()


def get_safe_error_response(exc: Exception) -> Dict[str, Any]:
    """
    Create a safe error response that doesn't expose internal details.
    Logs the full stack trace server-side.
    """
    request_id = get_request_id() or "-"
    
    # Log full error details server-side
    logger = logging.getLogger("airs.errors")
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    
    # Return safe response to client with consistent error format
    return {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": request_id,
        }
    }
