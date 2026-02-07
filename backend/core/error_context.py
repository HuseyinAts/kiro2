"""
Error Context and Tracing Utilities
Advanced error context management, distributed tracing, and debugging support
"""

import asyncio
import inspect
import logging
import threading
import traceback
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from .exceptions import EnhancedServiceError
from .unified_config import get_unified_config

logger = logging.getLogger(__name__)

# ==================== CONTEXT VARIABLES ====================

# Context variables for distributed tracing
request_id_var: ContextVar[str] = ContextVar("request_id")
correlation_id_var: ContextVar[str] = ContextVar("correlation_id")
trace_id_var: ContextVar[str] = ContextVar("trace_id")
span_id_var: ContextVar[str] = ContextVar("span_id")
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
user_role_var: ContextVar[str | None] = ContextVar("user_role", default=None)
operation_name_var: ContextVar[str | None] = ContextVar("operation_name", default=None)
error_context_var: ContextVar[Optional["ErrorContext"]] = ContextVar(
    "error_context", default=None
)


# ==================== TRACE MODELS ====================


class SpanKind(str, Enum):
    """Types of spans in distributed tracing"""

    SERVER = "server"
    CLIENT = "client"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class SpanStatus(str, Enum):
    """Span status types"""

    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SpanEvent:
    """Event within a span"""

    name: str
    timestamp: datetime
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class Span:
    """Distributed tracing span"""

    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation_name: str
    kind: SpanKind
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float | None = None
    status: SpanStatus = SpanStatus.OK
    tags: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)
    events: list[SpanEvent] = field(default_factory=list)
    baggage: dict[str, str] = field(default_factory=dict)

    def finish(self, status: SpanStatus = SpanStatus.OK):
        """Finish the span"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status

    def add_event(self, name: str, attributes: dict[str, Any] | None = None):
        """Add event to span"""
        self.events.append(
            SpanEvent(name=name, timestamp=datetime.now(), attributes=attributes or {})
        )

    def add_log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        self.logs.append(
            {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                **kwargs,
            }
        )

    def set_tag(self, key: str, value: Any):
        """Set span tag"""
        self.tags[key] = value

    def set_error(self, exception: Exception):
        """Mark span with error"""
        self.status = SpanStatus.ERROR
        self.set_tag("error", True)
        self.set_tag("error.type", type(exception).__name__)
        self.set_tag("error.message", str(exception))

        if hasattr(exception, "error_code"):
            self.set_tag("error.code", exception.error_code)

        # Add stack trace
        self.add_log(
            "Exception occurred",
            level="error",
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            stack_trace=traceback.format_exc(),
        )


@dataclass
class TraceContext:
    """Distributed trace context"""

    trace_id: str
    current_span: Span | None = None
    spans: list[Span] = field(default_factory=list)
    baggage: dict[str, str] = field(default_factory=dict)

    def add_span(self, span: Span):
        """Add span to trace"""
        self.spans.append(span)

    def get_active_span(self) -> Span | None:
        """Get currently active span"""
        return self.current_span

    def set_active_span(self, span: Span):
        """Set active span"""
        self.current_span = span


# ==================== ERROR CONTEXT ====================


@dataclass
class ErrorContext:
    """Comprehensive error context for debugging and monitoring"""

    # Basic identification
    error_id: str
    timestamp: datetime
    correlation_id: str
    request_id: str | None = None

    # User context
    user_id: str | None = None
    user_role: str | None = None
    session_id: str | None = None

    # Request context
    method: str | None = None
    url: str | None = None
    endpoint: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, Any] = field(default_factory=dict)
    body: str | None = None

    # System context
    host_name: str | None = None
    process_id: int | None = None
    thread_id: int | None = None
    memory_usage_mb: float | None = None
    cpu_usage_percent: float | None = None

    # Code execution context
    function_name: str | None = None
    file_name: str | None = None
    line_number: int | None = None
    local_variables: dict[str, Any] = field(default_factory=dict)
    call_stack: list[dict[str, Any]] = field(default_factory=list)

    # Business context
    business_operation: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None

    # Performance context
    operation_start_time: datetime | None = None
    processing_time_ms: float | None = None
    database_queries: list[dict[str, Any]] = field(default_factory=list)
    external_calls: list[dict[str, Any]] = field(default_factory=list)

    # Tracing context
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    # Additional metadata
    tags: dict[str, str] = field(default_factory=dict)
    annotations: list[str] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_from_current_context(cls) -> "ErrorContext":
        """Create error context from current execution context"""

        # Get current frame info
        frame = inspect.currentframe()
        caller_frame = frame.f_back if frame else None

        function_name = None
        file_name = None
        line_number = None
        local_vars = {}

        if caller_frame:
            function_name = caller_frame.f_code.co_name
            file_name = caller_frame.f_code.co_filename
            line_number = caller_frame.f_lineno

            # Capture local variables (be careful about sensitive data)
            try:
                local_vars = {
                    k: v
                    for k, v in caller_frame.f_locals.items()
                    if not k.startswith("_")
                    and isinstance(v, (str, int, float, bool, list, dict))
                }
            except (AttributeError, TypeError) as e:
                logger.debug(f"Failed to extract local vars: {e}")
                pass

        # Get context variables
        try:
            request_id = request_id_var.get()
        except LookupError:
            request_id = None

        try:
            correlation_id = correlation_id_var.get()
        except LookupError:
            correlation_id = str(uuid.uuid4())

        try:
            user_id = user_id_var.get()
        except LookupError:
            user_id = None

        try:
            user_role = user_role_var.get()
        except LookupError:
            user_role = None

        try:
            trace_id = trace_id_var.get()
        except LookupError:
            trace_id = None

        try:
            span_id = span_id_var.get()
        except LookupError:
            span_id = None

        return cls(
            error_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            request_id=request_id,
            user_id=user_id,
            user_role=user_role,
            function_name=function_name,
            file_name=file_name,
            line_number=line_number,
            local_variables=local_vars,
            call_stack=cls._get_call_stack(),
            process_id=threading.get_ident(),
            thread_id=threading.current_thread().ident,
            trace_id=trace_id,
            span_id=span_id,
        )

    @staticmethod
    def _get_call_stack() -> list[dict[str, Any]]:
        """Get call stack information"""
        stack = []

        try:
            for frame_info in inspect.stack()[3:8]:  # Skip first few frames
                stack.append(
                    {
                        "function": frame_info.function,
                        "filename": frame_info.filename,
                        "lineno": frame_info.lineno,
                        "code": frame_info.code_context[0].strip()
                        if frame_info.code_context
                        else None,
                    }
                )
        except (AttributeError, IndexError, TypeError) as e:
            logger.debug(f"Failed to extract stack trace: {e}")
            pass

        return stack

    def add_annotation(self, annotation: str):
        """Add annotation to error context"""
        self.annotations.append(f"[{datetime.now().isoformat()}] {annotation}")

    def add_database_query(self, query: str, duration_ms: float, **kwargs):
        """Add database query information"""
        self.database_queries.append(
            {
                "query": query,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }
        )

    def add_external_call(
        self, service: str, endpoint: str, duration_ms: float, **kwargs
    ):
        """Add external service call information"""
        self.external_calls.append(
            {
                "service": service,
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
                **kwargs,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "user_context": {
                "user_id": self.user_id,
                "user_role": self.user_role,
                "session_id": self.session_id,
            },
            "request_context": {
                "method": self.method,
                "url": self.url,
                "endpoint": self.endpoint,
                "headers": self.headers,
                "query_params": self.query_params,
                "body": self.body,
            },
            "system_context": {
                "host_name": self.host_name,
                "process_id": self.process_id,
                "thread_id": self.thread_id,
                "memory_usage_mb": self.memory_usage_mb,
                "cpu_usage_percent": self.cpu_usage_percent,
            },
            "code_context": {
                "function_name": self.function_name,
                "file_name": self.file_name,
                "line_number": self.line_number,
                "local_variables": self.local_variables,
                "call_stack": self.call_stack,
            },
            "business_context": {
                "business_operation": self.business_operation,
                "entity_type": self.entity_type,
                "entity_id": self.entity_id,
            },
            "performance_context": {
                "operation_start_time": self.operation_start_time.isoformat()
                if self.operation_start_time
                else None,
                "processing_time_ms": self.processing_time_ms,
                "database_queries": self.database_queries,
                "external_calls": self.external_calls,
            },
            "tracing_context": {
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "parent_span_id": self.parent_span_id,
            },
            "metadata": {
                "tags": self.tags,
                "annotations": self.annotations,
                "custom_fields": self.custom_fields,
            },
        }


# ==================== TRACING MANAGER ====================


class TracingManager:
    """Manage distributed tracing and error context"""

    def __init__(self):
        self.active_traces: dict[str, TraceContext] = {}
        self.span_processors: list[Callable] = []
        self.config = get_unified_config()
        self.lock = threading.Lock()

    def add_span_processor(self, processor: Callable):
        """Add span processor for custom handling"""
        self.span_processors.append(processor)

    def create_trace(self, trace_id: str | None = None) -> TraceContext:
        """Create new trace context"""
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        trace_context = TraceContext(trace_id=trace_id)

        with self.lock:
            self.active_traces[trace_id] = trace_context

        return trace_context

    def get_trace(self, trace_id: str) -> TraceContext | None:
        """Get trace context by ID"""
        return self.active_traces.get(trace_id)

    def start_span(
        self,
        operation_name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> Span:
        """Start new span"""

        if trace_id is None:
            try:
                trace_id = trace_id_var.get()
            except LookupError:
                trace_id = str(uuid.uuid4())

        span_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            kind=kind,
            start_time=datetime.now(),
        )

        # Get or create trace context
        trace_context = self.get_trace(trace_id)
        if trace_context is None:
            trace_context = self.create_trace(trace_id)

        trace_context.add_span(span)
        trace_context.set_active_span(span)

        return span

    def finish_span(self, span: Span, status: SpanStatus = SpanStatus.OK):
        """Finish span and process it"""
        span.finish(status)

        # Process span through all processors
        for processor in self.span_processors:
            try:
                if asyncio.iscoroutinefunction(processor):
                    # Schedule async processor
                    asyncio.create_task(processor(span))
                else:
                    processor(span)
            except Exception as e:
                # Don't let processor failures affect the main flow
                print(f"Span processor failed: {e}")

    def cleanup_trace(self, trace_id: str):
        """Clean up completed trace"""
        with self.lock:
            self.active_traces.pop(trace_id, None)


# ==================== CONTEXT MANAGERS ====================


@contextmanager
def error_context(
    operation_name: str | None = None,
    user_id: str | None = None,
    correlation_id: str | None = None,
    **kwargs,
):
    """Context manager for error tracking and debugging"""

    # Generate IDs
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    # Set context variables
    correlation_token = correlation_id_var.set(correlation_id)
    user_token = user_id_var.set(user_id) if user_id else None
    operation_token = operation_name_var.set(operation_name) if operation_name else None

    # Create error context
    ctx = ErrorContext.create_from_current_context()
    ctx.business_operation = operation_name
    ctx.operation_start_time = datetime.now()

    # Update with additional kwargs
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            ctx.custom_fields[key] = value

    error_context_token = error_context_var.set(ctx)

    try:
        yield ctx

        # Update processing time
        if ctx.operation_start_time:
            ctx.processing_time_ms = (
                datetime.now() - ctx.operation_start_time
            ).total_seconds() * 1000

    except Exception as e:
        # Enhance exception with context
        if isinstance(e, EnhancedServiceError):
            e.correlation_id = correlation_id
            if not hasattr(e, "source_location") or not e.source_location:
                e.source_location = {
                    "function": ctx.function_name,
                    "file": ctx.file_name,
                    "line": ctx.line_number,
                }

        # Re-raise with context
        raise e

    finally:
        # Reset context variables
        correlation_id_var.reset(correlation_token)
        if user_token:
            user_id_var.reset(user_token)
        if operation_token:
            operation_name_var.reset(operation_token)
        error_context_var.reset(error_context_token)


@asynccontextmanager
async def async_error_context(
    operation_name: str | None = None,
    user_id: str | None = None,
    correlation_id: str | None = None,
    **kwargs,
):
    """Async context manager for error tracking and debugging"""

    # Generate IDs
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    # Set context variables
    correlation_token = correlation_id_var.set(correlation_id)
    user_token = user_id_var.set(user_id) if user_id else None
    operation_token = operation_name_var.set(operation_name) if operation_name else None

    # Create error context
    ctx = ErrorContext.create_from_current_context()
    ctx.business_operation = operation_name
    ctx.operation_start_time = datetime.now()

    # Update with additional kwargs
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            ctx.custom_fields[key] = value

    error_context_token = error_context_var.set(ctx)

    try:
        yield ctx

        # Update processing time
        if ctx.operation_start_time:
            ctx.processing_time_ms = (
                datetime.now() - ctx.operation_start_time
            ).total_seconds() * 1000

    except Exception as e:
        # Enhance exception with context
        if isinstance(e, EnhancedServiceError):
            e.correlation_id = correlation_id
            if not hasattr(e, "source_location") or not e.source_location:
                e.source_location = {
                    "function": ctx.function_name,
                    "file": ctx.file_name,
                    "line": ctx.line_number,
                }

        # Re-raise with context
        raise e

    finally:
        # Reset context variables
        correlation_id_var.reset(correlation_token)
        if user_token:
            user_id_var.reset(user_token)
        if operation_token:
            operation_name_var.reset(operation_token)
        error_context_var.reset(error_context_token)


@contextmanager
def tracing_span(
    operation_name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    tags: dict[str, Any] | None = None,
):
    """Context manager for distributed tracing spans"""

    tracer = get_tracer()

    # Get parent span context
    try:
        trace_id = trace_id_var.get()
    except LookupError:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)

    try:
        parent_span_id = span_id_var.get()
    except LookupError:
        parent_span_id = None

    # Start span
    span = tracer.start_span(operation_name, kind, trace_id, parent_span_id)

    # Set tags
    if tags:
        for key, value in tags.items():
            span.set_tag(key, value)

    # Set context variables
    span_token = span_id_var.set(span.span_id)
    trace_token = trace_id_var.set(trace_id)

    try:
        yield span
        tracer.finish_span(span, SpanStatus.OK)

    except Exception as e:
        span.set_error(e)
        tracer.finish_span(span, SpanStatus.ERROR)
        raise e

    finally:
        span_id_var.reset(span_token)
        trace_id_var.reset(trace_token)


# ==================== GLOBAL INSTANCES ====================

_global_tracer: TracingManager | None = None


def get_tracer() -> TracingManager:
    """Get global tracing manager instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = TracingManager()
    return _global_tracer


def setup_tracing(processors: list[Callable] | None = None) -> TracingManager:
    """Setup global tracing"""
    global _global_tracer
    _global_tracer = TracingManager()

    if processors:
        for processor in processors:
            _global_tracer.add_span_processor(processor)

    return _global_tracer


# ==================== UTILITY FUNCTIONS ====================


def get_current_error_context() -> ErrorContext | None:
    """Get current error context"""
    try:
        return error_context_var.get()
    except LookupError:
        return None


def get_current_correlation_id() -> str | None:
    """Get current correlation ID"""
    try:
        return correlation_id_var.get()
    except LookupError:
        return None


def get_current_trace_id() -> str | None:
    """Get current trace ID"""
    try:
        return trace_id_var.get()
    except LookupError:
        return None


def get_current_span_id() -> str | None:
    """Get current span ID"""
    try:
        return span_id_var.get()
    except LookupError:
        return None


def annotate_error_context(annotation: str):
    """Add annotation to current error context"""
    ctx = get_current_error_context()
    if ctx:
        ctx.add_annotation(annotation)


def set_error_context_tag(key: str, value: str):
    """Set tag in current error context"""
    ctx = get_current_error_context()
    if ctx:
        ctx.tags[key] = value


def add_database_query_to_context(query: str, duration_ms: float, **kwargs):
    """Add database query to current error context"""
    ctx = get_current_error_context()
    if ctx:
        ctx.add_database_query(query, duration_ms, **kwargs)


def add_external_call_to_context(
    service: str, endpoint: str, duration_ms: float, **kwargs
):
    """Add external call to current error context"""
    ctx = get_current_error_context()
    if ctx:
        ctx.add_external_call(service, endpoint, duration_ms, **kwargs)


# ==================== DECORATORS ====================


def trace_operation(
    operation_name: str | None = None, kind: SpanKind = SpanKind.INTERNAL
):
    """Decorator for tracing operations"""

    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                with tracing_span(name, kind):
                    return await func(*args, **kwargs)

            return async_wrapper

        def wrapper(*args, **kwargs):
            with tracing_span(name, kind):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def error_context_decorator(
    operation_name: str | None = None,
    capture_args: bool = False,
    capture_result: bool = False,
):
    """Decorator for error context management"""

    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                context_kwargs = {"operation_name": name}

                if capture_args:
                    context_kwargs["function_args"] = {
                        "args": [str(arg) for arg in args],
                        "kwargs": {k: str(v) for k, v in kwargs.items()},
                    }

                async with async_error_context(**context_kwargs) as ctx:
                    result = await func(*args, **kwargs)

                    if capture_result:
                        ctx.custom_fields["function_result"] = str(result)[
                            :1000
                        ]  # Limit size

                    return result

            return async_wrapper

        def wrapper(*args, **kwargs):
            context_kwargs = {"operation_name": name}

            if capture_args:
                context_kwargs["function_args"] = {
                    "args": [str(arg) for arg in args],
                    "kwargs": {k: str(v) for k, v in kwargs.items()},
                }

            with error_context(**context_kwargs) as ctx:
                result = func(*args, **kwargs)

                if capture_result:
                    ctx.custom_fields["function_result"] = str(result)[
                        :1000
                    ]  # Limit size

                return result

        return wrapper

    return decorator
