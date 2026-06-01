"""
OpenTelemetry Tracing Integration.

Configures OTLP/GCP trace exporter and automatic instrumentation.
"""
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

from app.core.config import settings

logger = logging.getLogger("airs.tracing")


def setup_tracing(service_name: str = "airs-api-staging") -> None:
    """Initialize OpenTelemetry tracing.
    
    In production/staging, exports to Google Cloud Trace.
    In local development, exports to console if enabled.
    """
    try:
        # Define the service resource
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "environment": "staging" if not settings.is_prod else "prod",
        })
        
        provider = TracerProvider(resource=resource)
        
        # Determine exporter based on environment
        if settings.is_prod:
            try:
                from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
                exporter = CloudTraceSpanExporter()
                logger.info("Configured Google Cloud Trace exporter")
            except ImportError:
                logger.warning("CloudTraceSpanExporter not found, falling back to Console")
                exporter = ConsoleSpanExporter()
        else:
            # Local dev uses console if configured, otherwise no-op
            # For less noise, we only use console in debug mode
            exporter = ConsoleSpanExporter() if settings.log_level == "DEBUG" else None
            
        if exporter:
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            
        # Set global provider
        trace.set_tracer_provider(provider)
        logger.info(f"OpenTelemetry tracing initialized for service: {service_name}")
        
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")


def get_tracer(module_name: str) -> trace.Tracer:
    """Get a tracer instance for a specific module."""
    return trace.get_tracer(module_name)
