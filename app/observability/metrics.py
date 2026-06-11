"""
Prometheus metrics registry for AIRS.
"""
import time
from typing import Callable
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge

# Telemetry Metrics
TELEMETRY_EVENTS_INGESTED = Counter(
    "airs_telemetry_events_ingested_total",
    "Total number of telemetry events ingested",
    ["connector_type"]
)

# Connector Metrics
CONNECTOR_SYNC_DURATION = Histogram(
    "airs_connector_sync_duration_seconds",
    "Time spent syncing with external connectors",
    ["connector_type", "status"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float("inf"))
)

# Scoring Metrics
SCORING_CALCULATION_DURATION = Histogram(
    "airs_scoring_calculation_duration_seconds",
    "Time spent calculating continuous scores",
    ["org_id"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, float("inf"))
)

# Drift Metrics
DRIFT_SIGNALS_DETECTED = Counter(
    "airs_drift_signals_detected_total",
    "Total number of governance drift signals detected",
    ["signal_type", "severity"]
)

# Simulation Metrics
SIMULATION_EXECUTIONS = Counter(
    "airs_simulation_executions_total",
    "Total number of threat simulations executed",
    ["category"]
)

# Policy Metrics
POLICY_EVALUATIONS = Counter(
    "airs_policy_evaluations_total",
    "Total number of policy evaluations executed",
    ["policy_type", "result"]
)

# API Metrics
API_REQUEST_DURATION = Histogram(
    "airs_api_request_duration_seconds",
    "Time spent processing API requests",
    ["method", "endpoint", "status_code"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"))
)

# System Health
ACTIVE_CONNECTORS = Gauge(
    "airs_active_connectors",
    "Number of active connectors configured",
    ["connector_type"]
)


def track_time(histogram: Histogram, **labels):
    """Decorator to automatically track execution time of a function."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                histogram.labels(**labels).observe(time.perf_counter() - start)
                return result
            except Exception:
                histogram.labels(**labels).observe(time.perf_counter() - start)
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                histogram.labels(**labels).observe(time.perf_counter() - start)
                return result
            except Exception:
                histogram.labels(**labels).observe(time.perf_counter() - start)
                raise
                
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
