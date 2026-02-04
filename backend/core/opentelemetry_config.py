"""
OpenTelemetry Configuration for Kiro2 Platform
Sprint 11: Distributed Tracing & Performance Profiling

Comprehensive tracing configuration with:
- Automatic instrumentation for FastAPI, SQLAlchemy, Redis, HTTP clients
- Custom spans for business logic
- Trace context propagation
- Performance profiling
- Jaeger exporter
"""
import logging
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

logger = logging.getLogger(__name__)


class OpenTelemetryConfig:
    """
    OpenTelemetry Configuration for Distributed Tracing

    Features:
    - Automatic instrumentation for FastAPI, SQLAlchemy, Redis
    - Custom span creation for business logic
    - Trace context propagation across services
    - Jaeger exporter for visualization
    - Performance profiling
    """

    def __init__(
        self,
        service_name: str = "kiro2-backend",
        service_version: str = "1.0.0",
        environment: str = "production",
        jaeger_host: str = "localhost",
        jaeger_port: int = 6831,
        enable_console_export: bool = False
    ):
        """
        Initialize OpenTelemetry configuration

        Args:
            service_name: Name of the service
            service_version: Version of the service
            environment: Deployment environment (dev, staging, production)
            jaeger_host: Jaeger agent host
            jaeger_port: Jaeger agent port
            enable_console_export: Enable console span export for debugging
        """
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.enable_console_export = enable_console_export

        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None

    def setup(self):
        """Setup OpenTelemetry with all instrumentations"""
        try:
            # Create resource with service information
            resource = Resource.create({
                SERVICE_NAME: self.service_name,
                SERVICE_VERSION: self.service_version,
                DEPLOYMENT_ENVIRONMENT: self.environment,
                "platform": "kiro2",
                "language": "python",
                "framework": "fastapi"
            })

            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)

            # Configure Jaeger exporter
            jaeger_exporter = JaegerExporter(
                agent_host_name=self.jaeger_host,
                agent_port=self.jaeger_port,
            )

            # Add batch span processor for Jaeger
            span_processor = BatchSpanProcessor(jaeger_exporter)
            self.tracer_provider.add_span_processor(span_processor)

            # Optional: Add console exporter for debugging
            if self.enable_console_export:
                console_exporter = ConsoleSpanExporter()
                console_processor = BatchSpanProcessor(console_exporter)
                self.tracer_provider.add_span_processor(console_processor)

            # Set global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)

            logger.info(f"[ROCKET] OpenTelemetry initialized - Service: {self.service_name}, Jaeger: {self.jaeger_host}:{self.jaeger_port}")

        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize OpenTelemetry: {e}")
            raise

    def instrument_fastapi(self, app):
        """
        Instrument FastAPI application

        Args:
            app: FastAPI application instance
        """
        try:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("[OK] FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"[ERROR] FastAPI instrumentation failed: {e}")

    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine

        Args:
            engine: SQLAlchemy engine instance
        """
        try:
            SQLAlchemyInstrumentor().instrument(
                engine=engine,
                service=f"{self.service_name}-db"
            )
            logger.info("[OK] SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.error(f"[ERROR] SQLAlchemy instrumentation failed: {e}")

    def instrument_redis(self):
        """Instrument Redis client"""
        try:
            RedisInstrumentor().instrument()
            logger.info("[OK] Redis instrumentation enabled")
        except Exception as e:
            logger.error(f"[ERROR] Redis instrumentation failed: {e}")

    def instrument_requests(self):
        """Instrument requests HTTP client"""
        try:
            RequestsInstrumentor().instrument()
            logger.info("[OK] Requests HTTP client instrumentation enabled")
        except Exception as e:
            logger.error(f"[ERROR] Requests instrumentation failed: {e}")

    def instrument_logging(self):
        """Instrument Python logging"""
        try:
            LoggingInstrumentor().instrument(set_logging_format=True)
            logger.info("[OK] Logging instrumentation enabled")
        except Exception as e:
            logger.error(f"[ERROR] Logging instrumentation failed: {e}")

    def instrument_all(self, app, engine):
        """
        Enable all instrumentations

        Args:
            app: FastAPI application instance
            engine: SQLAlchemy engine instance
        """
        self.setup()
        self.instrument_fastapi(app)
        self.instrument_sqlalchemy(engine)
        self.instrument_redis()
        self.instrument_requests()
        self.instrument_logging()

        logger.info("[ROCKET] All OpenTelemetry instrumentations enabled - Distributed tracing active!")

    def get_tracer(self) -> trace.Tracer:
        """Get tracer instance"""
        if self.tracer is None:
            self.setup()
        return self.tracer

    def create_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL, attributes: dict = None):
        """
        Create a custom span

        Args:
            name: Span name
            kind: Span kind (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
            attributes: Additional span attributes

        Returns:
            Span context manager

        Example:
            with otel_config.create_span("process_exam", attributes={"exam_id": exam_id}):
                # Your code here
                pass
        """
        tracer = self.get_tracer()
        span = tracer.start_as_current_span(name, kind=kind)

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        return span

    def add_span_event(self, event_name: str, attributes: dict = None):
        """
        Add an event to the current span

        Args:
            event_name: Event name
            attributes: Event attributes
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(event_name, attributes or {})

    def set_span_status(self, status_code: StatusCode, description: str = None):
        """
        Set status of current span

        Args:
            status_code: Status code (OK, ERROR)
            description: Optional status description
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_status(Status(status_code, description))

    def record_exception(self, exception: Exception):
        """
        Record an exception in the current span

        Args:
            exception: Exception to record
        """
        current_span = trace.get_current_span()
        if current_span:
            current_span.record_exception(exception)
            current_span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global instance
_otel_config: Optional[OpenTelemetryConfig] = None


def get_otel_config() -> OpenTelemetryConfig:
    """Get or create global OpenTelemetry configuration"""
    global _otel_config
    if _otel_config is None:
        _otel_config = OpenTelemetryConfig(
            service_name=os.getenv("OTEL_SERVICE_NAME", "kiro2-backend"),
            service_version=os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
            environment=os.getenv("DEPLOYMENT_ENV", "production"),
            jaeger_host=os.getenv("JAEGER_HOST", "localhost"),
            jaeger_port=int(os.getenv("JAEGER_PORT", "6831")),
            enable_console_export=os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true"
        )
    return _otel_config


def init_tracing(app, engine):
    """
    Initialize distributed tracing

    Args:
        app: FastAPI application
        engine: SQLAlchemy engine
    """
    config = get_otel_config()
    config.instrument_all(app, engine)
    return config


# Decorators for easy span creation

def trace_function(name: str = None, attributes: dict = None):
    """
    Decorator to trace a function

    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes

    Example:
        @trace_function(name="calculate_irt_theta", attributes={"algorithm": "IRT"})
        def calculate_theta(user_id: str):
            pass
    """
    def decorator(func):
        import functools

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            config = get_otel_config()

            with config.create_span(span_name, attributes=attributes):
                try:
                    result = await func(*args, **kwargs)
                    config.set_span_status(StatusCode.OK)
                    return result
                except Exception as e:
                    config.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__
            config = get_otel_config()

            with config.create_span(span_name, attributes=attributes):
                try:
                    result = func(*args, **kwargs)
                    config.set_span_status(StatusCode.OK)
                    return result
                except Exception as e:
                    config.record_exception(e)
                    raise

        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


if __name__ == "__main__":
    # Test OpenTelemetry configuration
    print("=" * 80)
    print("OPENTELEMETRY CONFIGURATION TEST")
    print("=" * 80)

    config = OpenTelemetryConfig(
        service_name="kiro2-test",
        environment="dev",
        enable_console_export=True
    )

    config.setup()

    # Create a test span
    with config.create_span("test_span", attributes={"test": "value"}):
        config.add_span_event("test_event", {"event_data": "test"})
        print("Test span created successfully")

    print("\n[OK] OpenTelemetry configuration test passed")
