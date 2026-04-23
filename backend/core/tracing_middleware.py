"""
Distributed Tracing Middleware for Kiro2 Platform
Sprint 11: OpenTelemetry + Jaeger

Advanced tracing middleware with:
- Request tracing with metadata
- Performance profiling
- Business context enrichment
- Error tracking
- Custom attributes
"""
import logging
import time
from collections.abc import Callable

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.trace import SpanKind, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware

from core.opentelemetry_config import get_otel_config

logger = logging.getLogger(__name__)


class DistributedTracingMiddleware(BaseHTTPMiddleware):
    """
    Advanced Distributed Tracing Middleware

    Features:
    - Automatic span creation for all requests
    - Request/response metadata
    - Performance metrics
    - Error tracking
    - Business context enrichment
    """

    def __init__(self, app, excluded_paths: list = None):
        """
        Initialize tracing middleware

        Args:
            app: FastAPI application
            excluded_paths: Paths to exclude from tracing (health checks, etc.)
        """
        super().__init__(app)
        self.otel_config = get_otel_config()
        self.tracer = self.otel_config.get_tracer()
        self.excluded_paths = excluded_paths or ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with distributed tracing

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response with tracing headers
        """
        # Skip tracing for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Start request span
        span_name = f"{request.method} {request.url.path}"

        with self.tracer.start_as_current_span(span_name, kind=SpanKind.SERVER) as span:
            # Record request start time
            start_time = time.time()

            try:
                # Add request attributes
                self._add_request_attributes(span, request)

                # Process request
                response = await call_next(request)

                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Add response attributes
                self._add_response_attributes(span, response, duration_ms)

                # Set span status based on response code
                if response.status_code >= 500 or response.status_code >= 400:
                    span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
                else:
                    span.set_status(StatusCode.OK)

                # Add trace ID to response headers for correlation
                trace_id = format(span.get_span_context().trace_id, '032x')
                response.headers["X-Trace-ID"] = trace_id

                return response

            except Exception as e:
                # Record exception
                duration_ms = (time.time() - start_time) * 1000
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))

                # Add error attributes
                span.set_attribute("error", True)
                span.set_attribute("error.type", type(e).__name__)
                span.set_attribute("error.message", str(e))
                span.set_attribute("http.request.duration_ms", duration_ms)

                logger.error(f"[ERROR] Request failed: {e}", extra={"trace_id": format(span.get_span_context().trace_id, '032x')})

                # Re-raise exception
                raise

    def _add_request_attributes(self, span: trace.Span, request: Request):
        """
        Add request attributes to span

        Args:
            span: Current span
            request: FastAPI request
        """
        # HTTP attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.target", request.url.path)
        span.set_attribute("http.host", request.url.hostname or "unknown")
        span.set_attribute("http.scheme", request.url.scheme)

        # Client attributes
        if request.client:
            span.set_attribute("http.client_ip", request.client.host)

        # User-Agent
        user_agent = request.headers.get("user-agent", "unknown")
        span.set_attribute("http.user_agent", user_agent)

        # Request ID
        request_id = request.headers.get("x-request-id", "unknown")
        span.set_attribute("request.id", request_id)

        # Authentication context
        if hasattr(request.state, "user") and request.state.user:
            span.set_attribute("user.id", str(request.state.user.id))
            span.set_attribute("user.role", request.state.user.role)
            if hasattr(request.state.user, "is_premium"):
                span.set_attribute("user.is_premium", request.state.user.is_premium)

        # Add query parameters (sanitized)
        if request.query_params:
            query_string = str(request.query_params)
            # Sanitize sensitive parameters
            for sensitive in ["password", "token", "secret", "api_key"]:
                if sensitive in query_string.lower():
                    query_string = query_string.replace(
                        request.query_params.get(sensitive, ""), "***REDACTED***"
                    )
            span.set_attribute("http.query_string", query_string[:500])  # Limit length

    def _add_response_attributes(self, span: trace.Span, response: Response, duration_ms: float):
        """
        Add response attributes to span

        Args:
            span: Current span
            response: FastAPI response
            duration_ms: Request duration in milliseconds
        """
        # HTTP response attributes
        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("http.response.duration_ms", duration_ms)

        # Response size
        if "content-length" in response.headers:
            span.set_attribute("http.response.size_bytes", int(response.headers["content-length"]))

        # Performance classification
        if duration_ms < 100:
            span.set_attribute("performance.classification", "fast")
        elif duration_ms < 500:
            span.set_attribute("performance.classification", "normal")
        elif duration_ms < 2000:
            span.set_attribute("performance.classification", "slow")
        else:
            span.set_attribute("performance.classification", "very_slow")

        # Add event for slow requests
        if duration_ms > 1000:
            span.add_event(
                "slow_request",
                {
                    "duration_ms": duration_ms,
                    "threshold_ms": 1000,
                    "url": span.attributes.get("http.url", "unknown")
                }
            )


# Business Logic Tracing Utilities

class BusinessSpanManager:
    """
    Manager for business logic spans

    Provides high-level tracing for business operations
    """

    def __init__(self):
        self.otel_config = get_otel_config()
        self.tracer = self.otel_config.get_tracer()

    def trace_exam_session(self, exam_id: str, user_id: str):
        """
        Create span for exam session

        Args:
            exam_id: Exam ID
            user_id: User ID

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            "exam.session",
            kind=SpanKind.INTERNAL,
            attributes={
                "exam.id": exam_id,
                "user.id": user_id,
                "business.operation": "exam_taking"
            }
        )

    def trace_question_answer(self, question_id: str, user_id: str, correct: bool):
        """
        Create span for question answering

        Args:
            question_id: Question ID
            user_id: User ID
            correct: Whether answer was correct

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            "question.answer",
            kind=SpanKind.INTERNAL,
            attributes={
                "question.id": question_id,
                "user.id": user_id,
                "answer.correct": correct,
                "business.operation": "question_solving"
            }
        )

    def trace_irt_calculation(self, user_id: str, algorithm: str):
        """
        Create span for IRT calculation

        Args:
            user_id: User ID
            algorithm: Algorithm name (IRT, FSRS, ZPD)

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            f"algorithm.{algorithm.lower()}",
            kind=SpanKind.INTERNAL,
            attributes={
                "user.id": user_id,
                "algorithm.name": algorithm,
                "algorithm.type": "adaptive_learning",
                "business.operation": "ability_estimation"
            }
        )

    def trace_ai_model_request(self, model: str, operation: str):
        """
        Create span for AI model request

        Args:
            model: Model name (GPT-4, BERTurk, etc.)
            operation: Operation type

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            f"ai.{model.lower()}.{operation}",
            kind=SpanKind.CLIENT,
            attributes={
                "ai.model": model,
                "ai.operation": operation,
                "business.operation": "ai_inference"
            }
        )

    def trace_recommendation_generation(self, user_id: str, recommendation_type: str):
        """
        Create span for recommendation generation

        Args:
            user_id: User ID
            recommendation_type: Type of recommendation

        Returns:
            Span context manager
        """
        return self.tracer.start_as_current_span(
            f"recommendation.{recommendation_type}",
            kind=SpanKind.INTERNAL,
            attributes={
                "user.id": user_id,
                "recommendation.type": recommendation_type,
                "business.operation": "content_recommendation"
            }
        )


# Global business span manager
_business_span_manager: BusinessSpanManager = None


def get_business_span_manager() -> BusinessSpanManager:
    """Get or create global business span manager"""
    global _business_span_manager
    if _business_span_manager is None:
        _business_span_manager = BusinessSpanManager()
    return _business_span_manager


# Performance Profiling Utilities

def profile_function_performance(func_name: str):
    """
    Decorator to profile function performance

    Args:
        func_name: Function name for span

    Example:
        @profile_function_performance("calculate_fsrs_stability")
        def calculate_stability(data):
            pass
    """
    def decorator(func):
        import functools
        import inspect

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            manager = get_business_span_manager()
            with manager.tracer.start_as_current_span(
                f"performance.{func_name}",
                kind=SpanKind.INTERNAL
            ) as span:
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.set_attribute("function.name", func_name)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.record_exception(e)
                    span.set_status(StatusCode.ERROR, str(e))
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            manager = get_business_span_manager()
            with manager.tracer.start_as_current_span(
                f"performance.{func_name}",
                kind=SpanKind.INTERNAL
            ) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.set_attribute("function.name", func_name)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("function.duration_ms", duration_ms)
                    span.record_exception(e)
                    span.set_status(StatusCode.ERROR, str(e))
                    raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


if __name__ == "__main__":
    print("=" * 80)
    print("DISTRIBUTED TRACING MIDDLEWARE TEST")
    print("=" * 80)
    print("\n[OK] Middleware module loaded successfully")
    print("Features:")
    print("  - Request/Response tracing")
    print("  - Business logic spans")
    print("  - Performance profiling")
    print("  - Error tracking")
