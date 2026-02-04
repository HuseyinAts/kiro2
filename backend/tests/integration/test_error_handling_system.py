"""
Comprehensive Tests for Error Handling System
Test suite for the new centralized error handling pattern consolidation
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from core.error_context import ErrorContext as ErrorContextData
from core.error_context import (
    SpanKind,
    SpanStatus,
    TracingManager,
    async_error_context,
    error_context,
    error_context_decorator,
    trace_operation,
    tracing_span,
)
from core.error_monitoring import (
    AlertManager,
    AlertRule,
    ConsoleLogProcessor,
    ErrorLogEntry,
    ErrorMetrics,
    ErrorMonitor,
    LogLevel,
)
from core.exceptions import (
    AuthorizationError,
    BusinessLogicError,
    DatabaseError,
    EnhancedServiceError,
    ErrorChain,
    ErrorFactory,
    ErrorSeverity,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from core.global_exception_handler import (
    ErrorTracker,
    ExceptionHandlerConfig,
    GlobalExceptionHandler,
    HandlerMode,
)

# ==================== EXCEPTION HIERARCHY TESTS ====================


class TestExceptionHierarchy:
    """Test the enhanced exception hierarchy"""

    def test_basic_service_error(self):
        """Test basic ServiceError functionality"""
        error = ServiceError("Test error", "TEST_ERROR", {"key": "value"})

        assert str(error) == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        assert error.message == "Test error"

    def test_enhanced_service_error(self):
        """Test EnhancedServiceError with additional features"""
        error = EnhancedServiceError(
            message="Enhanced error",
            error_code="ENHANCED_ERROR",
            severity=ErrorSeverity.HIGH,
            user_message="User-friendly message",
            retry_after=60,
            correlation_id="corr-123",
        )

        assert error.severity == ErrorSeverity.HIGH
        assert error.user_message == "User-friendly message"
        assert error.retry_after == 60
        assert error.correlation_id == "corr-123"
        assert error.timestamp is not None

        # Test string representation
        error_str = str(error)
        assert "ENHANCED_ERROR" in error_str
        assert "corr-123" in error_str
        assert "high" in error_str.lower()

    def test_validation_error(self):
        """Test ValidationError functionality"""
        error = ValidationError("Invalid email", field="email")

        assert error.field == "email"
        assert error.error_code == "VALIDATION_ERROR"
        assert str(error) == "Invalid email"

    def test_not_found_error(self):
        """Test NotFoundError functionality"""
        error = NotFoundError("User not found", resource_type="user", resource_id="123")

        assert error.details["resource_type"] == "user"
        assert error.details["resource_id"] == "123"
        assert error.error_code == "NOT_FOUND"

    def test_authorization_error(self):
        """Test AuthorizationError functionality"""
        error = AuthorizationError("Access denied")

        assert error.error_code == "AUTHORIZATION_ERROR"
        assert str(error) == "Access denied"

    def test_database_error(self):
        """Test DatabaseError functionality"""
        error = DatabaseError("Connection failed", operation="select")

        assert error.details["operation"] == "select"
        assert error.error_code == "DATABASE_ERROR"

    def test_business_logic_error(self):
        """Test BusinessLogicError functionality"""
        error = BusinessLogicError("Rule violated", rule="unique_email")

        assert error.details["rule"] == "unique_email"
        assert error.error_code == "BUSINESS_LOGIC_ERROR"


class TestErrorFactory:
    """Test error factory methods"""

    def test_validation_error_factory(self):
        """Test validation error creation"""
        error = ErrorFactory.validation_error(
            field="email",
            value="invalid-email",
            constraint="email_format",
            message="Invalid email format",
        )

        assert isinstance(error, ValidationError)
        assert error.field == "email"
        assert error.details["rejected_value"] == "invalid-email"
        assert error.details["constraint"] == "email_format"

    def test_not_found_error_factory(self):
        """Test not found error creation"""
        error = ErrorFactory.not_found_error(
            resource_type="user", resource_id="123", message="User not found"
        )

        assert isinstance(error, NotFoundError)
        assert error.details["resource_type"] == "user"
        assert error.details["resource_id"] == "123"

    def test_authorization_error_factory(self):
        """Test authorization error creation"""
        error = ErrorFactory.authorization_error(
            required_role="admin",
            user_role="user",
            resource="users",
            message="Access denied",
        )

        assert isinstance(error, AuthorizationError)
        assert error.details["required_role"] == "admin"
        assert error.details["user_role"] == "user"
        assert error.details["resource"] == "users"

    def test_database_error_factory(self):
        """Test database error creation"""
        original_error = Exception("Connection timeout")
        error = ErrorFactory.database_error(
            operation="select",
            table="users",
            original_error=original_error,
            message="Database query failed",
        )

        assert isinstance(error, DatabaseError)
        assert error.details["table"] == "users"
        assert error.details["original_error"] == str(original_error)

    def test_business_logic_error_factory(self):
        """Test business logic error creation"""
        error = ErrorFactory.business_logic_error(
            rule_name="unique_email",
            context={"email": "test@example.com", "user_id": "123"},
            message="Email already exists",
        )

        assert isinstance(error, BusinessLogicError)
        assert error.details["rule"] == "unique_email"
        assert error.details["email"] == "test@example.com"
        assert error.details["user_id"] == "123"


class TestErrorChain:
    """Test error chaining functionality"""

    def test_error_chain_creation(self):
        """Test error chain creation and management"""
        chain = ErrorChain()

        assert not chain.has_errors()
        assert chain.get_root_error() is None
        assert chain.get_latest_error() is None

    def test_error_chain_with_errors(self):
        """Test error chain with multiple errors"""
        chain = ErrorChain()

        error1 = ValueError("First error")
        error2 = TypeError("Second error")
        error3 = RuntimeError("Third error")

        chain.add_error(error1).add_error(error2).add_error(error3)

        assert chain.has_errors()
        assert chain.get_root_error() == error1
        assert chain.get_latest_error() == error3

        summary = chain.get_error_summary()
        assert summary["total_errors"] == 3
        assert summary["error_types"] == ["ValueError", "TypeError", "RuntimeError"]
        assert summary["error_messages"] == [
            "First error",
            "Second error",
            "Third error",
        ]

    def test_error_chain_aggregated_raise(self):
        """Test aggregated error raising"""
        chain = ErrorChain()

        error1 = ValueError("First error")
        error2 = TypeError("Second error")

        chain.add_error(error1).add_error(error2)

        with pytest.raises(EnhancedServiceError) as exc_info:
            chain.raise_aggregated("Multiple errors occurred")

        assert exc_info.value.error_code == "AGGREGATED_ERROR"
        assert exc_info.value.details["error_count"] == 2
        assert "error_chain" in exc_info.value.details

    def test_single_error_chain_reraise(self):
        """Test that single error chains re-raise the original error"""
        chain = ErrorChain()
        original_error = ValueError("Single error")
        chain.add_error(original_error)

        with pytest.raises(ValueError) as exc_info:
            chain.raise_aggregated("Should not see this message")

        assert exc_info.value == original_error


# ==================== GLOBAL EXCEPTION HANDLER TESTS ====================


class TestGlobalExceptionHandler:
    """Test global exception handler functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.config = ExceptionHandlerConfig(
            mode=HandlerMode.STRICT,
            enable_error_recovery=True,
            enable_detailed_logging=True,
        )
        self.handler = GlobalExceptionHandler(self.config)

    def test_handler_initialization(self):
        """Test handler initialization"""
        assert self.handler.config.mode == HandlerMode.STRICT
        assert self.handler.config.enable_error_recovery is True
        assert self.handler.error_tracker is not None
        assert len(self.handler.recovery_functions) > 0

    def test_exception_classification(self):
        """Test exception classification"""
        # Test validation error
        validation_error = ValidationError("Invalid input")
        classification = self.handler._classify_exception(validation_error)

        assert classification["type"] == "ValidationError"
        assert classification["error_code"] == "VALIDATION_ERROR"
        assert classification["expose_details"] is True

        # Test enhanced service error
        enhanced_error = EnhancedServiceError(
            "Test error", severity=ErrorSeverity.CRITICAL
        )
        classification = self.handler._classify_exception(enhanced_error)

        assert classification["severity"] == ErrorSeverity.CRITICAL
        assert classification["expose_details"] is True

        # Test Python built-in error
        value_error = ValueError("Invalid value")
        classification = self.handler._classify_exception(value_error)

        assert classification["type"] == "ValueError"
        assert classification["error_code"] == "VALUE_ERROR"
        assert classification["severity"] == ErrorSeverity.LOW

    def test_error_tracker(self):
        """Test error tracking functionality"""
        tracker = ErrorTracker()

        # Record some errors
        context = Mock()
        context.user_role = "user"

        tracker.record_error(
            "ValidationError", "/api/users", ErrorSeverity.LOW, context
        )
        tracker.record_error("DatabaseError", "/api/users", ErrorSeverity.HIGH, context)
        tracker.record_error(
            "ValidationError", "/api/posts", ErrorSeverity.LOW, context
        )

        # Test error counting
        assert tracker.error_counts["ValidationError:/api/users"] == 1
        assert tracker.error_counts["DatabaseError:/api/users"] == 1
        assert tracker.error_counts["ValidationError:/api/posts"] == 1

        # Test error rate calculation
        rate = tracker.get_error_rate("ValidationError", "/api/users", 60)
        assert rate >= 0

        # Test statistics
        stats = tracker.get_error_statistics()
        assert stats["total_error_types"] == 3
        assert "top_errors" in stats


# ==================== ERROR MONITORING TESTS ====================


class TestErrorMonitoring:
    """Test error monitoring system"""

    def setup_method(self):
        """Setup test environment"""
        self.monitor = ErrorMonitor()

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.metrics is not None
        assert len(self.monitor.processors) > 0  # Should have default processors
        assert self.monitor.alert_manager is not None

    def test_error_log_entry(self):
        """Test error log entry creation"""
        entry = ErrorLogEntry(
            id="test-id",
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            error_code="TEST_ERROR",
            error_type="TestError",
            message="Test error message",
            user_message="User friendly message",
            severity=ErrorSeverity.MEDIUM,
        )

        assert entry.id == "test-id"
        assert entry.level == LogLevel.ERROR
        assert entry.error_code == "TEST_ERROR"
        assert entry.severity == ErrorSeverity.MEDIUM

        # Test serialization
        data = entry.to_dict()
        assert data["id"] == "test-id"
        assert data["level"] == "ERROR"
        assert data["severity"] == "medium"

    def test_error_metrics_update(self):
        """Test error metrics updating"""
        metrics = ErrorMetrics()

        entry = ErrorLogEntry(
            id="test-id",
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            error_code="TEST_ERROR",
            error_type="TestError",
            message="Test message",
            user_message="User message",
            severity=ErrorSeverity.HIGH,
            endpoint="/api/test",
            user_id="user123",
        )

        metrics.update_metrics(entry)

        assert metrics.total_errors == 1
        assert metrics.errors_by_type["TestError"] == 1
        assert metrics.errors_by_severity["high"] == 1
        assert metrics.errors_by_endpoint["/api/test"] == 1
        assert metrics.errors_by_user["user123"] == 1
        assert len(metrics.errors_per_minute) == 1
        assert len(metrics.errors_per_hour) == 1

    def test_console_log_processor(self):
        """Test console log processor"""
        processor = ConsoleLogProcessor(colored_output=False)

        entry = ErrorLogEntry(
            id="test-id",
            timestamp=datetime.now(),
            level=LogLevel.ERROR,
            error_code="TEST_ERROR",
            error_type="TestError",
            message="Test message",
            user_message="User message",
            severity=ErrorSeverity.MEDIUM,
            request_id="req-123",
        )

        # This should not raise an exception
        result = asyncio.run(processor.process(entry))
        assert result is True

    def test_alert_manager(self):
        """Test alert manager functionality"""
        alert_manager = AlertManager()

        # Test adding custom rule
        custom_rule = AlertRule(
            name="Test Rule",
            condition=lambda m: m.total_errors > 5,
            severity=ErrorSeverity.HIGH,
            message_template="Test alert: {name}",
        )

        alert_manager.add_rule(custom_rule)

        # Test notification handler
        notifications = []

        def test_handler(notification_data):
            notifications.append(notification_data)

        alert_manager.add_notification_handler(test_handler)

        # Create metrics that trigger alert
        metrics = ErrorMetrics()
        metrics.total_errors = 10

        # Check alerts
        asyncio.run(alert_manager.check_alerts(metrics))

        # Should have triggered notification
        assert len(notifications) > 0
        notification = notifications[0]
        assert notification["severity"] == "high"
        assert "Test alert" in notification["message"]


# ==================== ERROR CONTEXT TESTS ====================


class TestErrorContext:
    """Test error context and tracing utilities"""

    def test_error_context_creation(self):
        """Test error context creation"""
        ctx = ErrorContextData.create_from_current_context()

        assert ctx.error_id is not None
        assert ctx.timestamp is not None
        assert ctx.correlation_id is not None
        assert isinstance(ctx.call_stack, list)

    def test_error_context_annotations(self):
        """Test error context annotations"""
        ctx = ErrorContextData.create_from_current_context()

        ctx.add_annotation("Test annotation")
        ctx.add_database_query("SELECT * FROM users", 150.5)
        ctx.add_external_call("email_service", "/send", 200.0)

        assert len(ctx.annotations) == 1
        assert "Test annotation" in ctx.annotations[0]
        assert len(ctx.database_queries) == 1
        assert ctx.database_queries[0]["duration_ms"] == 150.5
        assert len(ctx.external_calls) == 1
        assert ctx.external_calls[0]["service"] == "email_service"

        # Test serialization
        data = ctx.to_dict()
        assert "error_id" in data
        assert "timestamp" in data
        assert "code_context" in data
        assert "performance_context" in data

    def test_error_context_manager(self):
        """Test error context manager"""

        with error_context(
            operation_name="test_operation", user_id="user123", entity_type="test"
        ) as ctx:
            assert ctx.business_operation == "test_operation"
            assert ctx.operation_start_time is not None

            # Test annotation within context
            ctx.add_annotation("Inside context")
            assert len(ctx.annotations) == 1

        # Processing time should be calculated
        assert ctx.processing_time_ms is not None
        assert ctx.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_async_error_context_manager(self):
        """Test async error context manager"""

        async with async_error_context(
            operation_name="async_test_operation", user_id="user123"
        ) as ctx:
            assert ctx.business_operation == "async_test_operation"

            # Simulate some async work
            await asyncio.sleep(0.01)

            ctx.add_annotation("Async operation completed")

        assert ctx.processing_time_ms is not None
        assert ctx.processing_time_ms > 10  # Should be at least 10ms

    def test_tracing_manager(self):
        """Test distributed tracing manager"""
        tracer = TracingManager()

        # Create trace and span
        trace_context = tracer.create_trace("trace-123")
        span = tracer.start_span("test_operation", SpanKind.INTERNAL, "trace-123")

        assert trace_context.trace_id == "trace-123"
        assert span.trace_id == "trace-123"
        assert span.operation_name == "test_operation"
        assert span.kind == SpanKind.INTERNAL
        assert span.start_time is not None

        # Add events and tags
        span.add_event("Test event", {"key": "value"})
        span.set_tag("user.id", "123")
        span.add_log("Test log message", level="info")

        assert len(span.events) == 1
        assert span.tags["user.id"] == "123"
        assert len(span.logs) == 1

        # Finish span
        tracer.finish_span(span, SpanStatus.OK)

        assert span.end_time is not None
        assert span.duration_ms is not None
        assert span.status == SpanStatus.OK

    def test_tracing_span_context_manager(self):
        """Test tracing span context manager"""

        with tracing_span("test_span", SpanKind.INTERNAL) as span:
            assert span.operation_name == "test_span"
            assert span.kind == SpanKind.INTERNAL

            span.set_tag("test", "value")
            span.add_event("Test event")

        # Span should be finished
        assert span.end_time is not None
        assert span.status == SpanStatus.OK

    def test_decorators(self):
        """Test error context and tracing decorators"""

        @error_context_decorator("test_function", capture_args=True)
        @trace_operation("test_trace")
        def test_function(arg1: str, arg2: int = 42):
            return f"Result: {arg1}, {arg2}"

        result = test_function("test", arg2=100)
        assert result == "Result: test, 100"

        # Test async decorator
        @error_context_decorator("async_test_function")
        @trace_operation("async_test_trace")
        async def async_test_function(value: str):
            await asyncio.sleep(0.001)
            return f"Async result: {value}"

        result = asyncio.run(async_test_function("test"))
        assert result == "Async result: test"


# ==================== INTEGRATION TESTS ====================


class TestErrorHandlingIntegration:
    """Integration tests for the complete error handling system"""

    @pytest.mark.asyncio
    async def test_complete_error_flow(self):
        """Test complete error flow from exception to logging"""

        # Setup monitoring
        monitor = ErrorMonitor()

        # Create test exception with context
        async with async_error_context(
            operation_name="test_complete_flow", user_id="user123", entity_type="test"
        ) as ctx:
            try:
                # Simulate an operation that fails
                raise DatabaseError("Connection failed", operation="select")

            except Exception as e:
                # Log error with context
                await monitor.log_error(e, ctx.to_dict(), ErrorSeverity.HIGH)

                # Verify error was logged
                assert monitor.metrics.total_errors == 1
                assert "DatabaseError" in monitor.metrics.errors_by_type
                assert monitor.metrics.errors_by_severity["high"] == 1

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test error recovery functionality"""

        config = ExceptionHandlerConfig(enable_error_recovery=True)
        handler = GlobalExceptionHandler(config)

        # Register recovery function
        async def test_recovery(error, context):
            return {"message": "Recovered from error", "fallback": True}

        handler.register_recovery_function(DatabaseError, test_recovery)

        # Test recovery
        error = DatabaseError("Test error")
        context = Mock()
        context.request_method = "GET"

        recovery_data = await handler._attempt_recovery(error, context)

        assert recovery_data is not None
        assert recovery_data["fallback"] is True

    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""

        tracker = ErrorTracker()
        endpoint = "/api/test"

        # Simulate multiple high-severity errors
        context = Mock()
        for i in range(15):  # More than threshold
            tracker.record_error(
                "DatabaseError", endpoint, ErrorSeverity.CRITICAL, context
            )

        # Circuit breaker should be open
        assert tracker.is_circuit_breaker_open(endpoint) is True

        # Test that circuit breaker eventually closes
        tracker.circuit_breakers[endpoint]["opened_at"] = datetime.now() - timedelta(
            seconds=400
        )  # Past timeout

        assert tracker.is_circuit_breaker_open(endpoint) is False


# ==================== PERFORMANCE TESTS ====================


class TestErrorHandlingPerformance:
    """Performance tests for error handling system"""

    def test_error_context_performance(self):
        """Test error context creation performance"""
        import time

        start_time = time.time()

        # Create many error contexts
        contexts = []
        for i in range(100):
            ctx = ErrorContextData.create_from_current_context()
            contexts.append(ctx)

        end_time = time.time()
        duration = end_time - start_time

        # Should be reasonably fast (less than 1 second for 100 contexts)
        assert duration < 1.0
        assert len(contexts) == 100

    @pytest.mark.asyncio
    async def test_error_logging_performance(self):
        """Test error logging performance"""
        import time

        monitor = ErrorMonitor()

        start_time = time.time()

        # Log many errors
        for i in range(50):
            error = ValidationError(f"Test error {i}")
            context = {"test_id": i, "operation": "performance_test"}
            await monitor.log_error(error, context, ErrorSeverity.LOW)

        end_time = time.time()
        duration = end_time - start_time

        # Should be reasonably fast
        assert duration < 2.0
        assert monitor.metrics.total_errors == 50


if __name__ == "__main__":
    # Run basic tests
    print("Running Error Handling System Tests...")

    # Test exception hierarchy
    print("\n🧪 Testing Exception Hierarchy...")
    test_exceptions = TestExceptionHierarchy()
    test_exceptions.test_basic_service_error()
    test_exceptions.test_enhanced_service_error()
    test_exceptions.test_validation_error()
    print("[CHECK] Exception Hierarchy tests passed")

    # Test error factory
    print("\n🧪 Testing Error Factory...")
    test_factory = TestErrorFactory()
    test_factory.test_validation_error_factory()
    test_factory.test_not_found_error_factory()
    print("[CHECK] Error Factory tests passed")

    # Test error monitoring
    print("\n🧪 Testing Error Monitoring...")
    test_monitoring = TestErrorMonitoring()
    test_monitoring.setup_method()
    test_monitoring.test_monitor_initialization()
    test_monitoring.test_error_metrics_update()
    print("[CHECK] Error Monitoring tests passed")

    # Test error context
    print("\n🧪 Testing Error Context...")
    test_context = TestErrorContext()
    test_context.test_error_context_creation()
    test_context.test_error_context_annotations()
    test_context.test_tracing_manager()
    print("[CHECK] Error Context tests passed")

    print("\n[PARTY] All Error Handling System tests completed successfully!")
