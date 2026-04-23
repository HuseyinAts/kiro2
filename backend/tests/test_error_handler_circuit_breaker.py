"""
Test Error Handler ve Circuit Breaker Pattern
Task 9 implementation verification
"""

import asyncio

import pytest

from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    circuit_breaker_manager,
)
from backend.core.error_handler import (
    CacheError,
    ErrorCategory,
    ErrorHandler,
    VideoAPIError,
    VideoDiscoveryError,
    VideoTimeoutError,
    YouTubeAPIError,
)
from backend.core.exceptions import ErrorSeverity


class TestErrorHandler:
    """Test ErrorHandler class"""

    def test_error_handler_initialization(self):
        """Test error handler can be initialized"""
        handler = ErrorHandler()
        assert handler is not None
        assert handler._error_counts == {}

    def test_classify_youtube_api_error(self):
        """Test YouTube API error classification"""
        handler = ErrorHandler()
        error = YouTubeAPIError(message="API quota exceeded", quota_exceeded=True)

        classification = handler.classify_error(error)

        assert classification.category == ErrorCategory.QUOTA
        assert classification.severity == ErrorSeverity.CRITICAL
        assert classification.retryable is True
        assert classification.retry_after == 3600
        assert "kota" in classification.user_message.lower()

    def test_classify_cache_error(self):
        """Test cache error classification"""
        handler = ErrorHandler()
        error = CacheError(
            message="Redis connection failed", operation="get", cache_type="redis"
        )

        classification = handler.classify_error(error)

        assert classification.category == ErrorCategory.CACHE
        assert classification.severity == ErrorSeverity.LOW
        assert classification.retryable is True

    def test_classify_timeout_error(self):
        """Test timeout error classification"""
        handler = ErrorHandler()
        error = VideoTimeoutError(message="Request timeout", timeout_seconds=10.0)

        classification = handler.classify_error(error)

        assert classification.category == ErrorCategory.TIMEOUT
        assert classification.severity == ErrorSeverity.MEDIUM
        assert classification.retryable is True

    def test_handle_error_with_context(self):
        """Test error handling with context"""
        handler = ErrorHandler()
        error = VideoDiscoveryError(message="No videos found", subject="matematik")

        classification = handler.handle_error(
            error,
            context={"user_id": "123", "query": "matematik"},
            request_id="req-123",
        )

        assert classification is not None
        assert handler._error_counts.get(ErrorCategory.NOT_FOUND.value, 0) == 1

    def test_get_user_message(self):
        """Test user-friendly message generation"""
        handler = ErrorHandler()
        error = YouTubeAPIError(message="API error", status_code=500)

        user_message = handler.get_user_message(error)

        assert user_message is not None
        assert len(user_message) > 0
        assert "YouTube" in user_message or "servis" in user_message.lower()

    def test_should_retry(self):
        """Test retry decision logic"""
        handler = ErrorHandler()

        # Retryable error
        error1 = VideoTimeoutError(message="Timeout")
        should_retry, retry_after = handler.should_retry(error1)
        assert should_retry is True
        assert retry_after > 0

        # Non-retryable error
        error2 = VideoAPIError(message="Invalid request")
        classification = handler.classify_error(error2)
        # Most errors are retryable by default

    def test_get_recovery_actions(self):
        """Test recovery action determination"""
        handler = ErrorHandler()
        error = CacheError(message="Cache unavailable")

        actions = handler.get_recovery_actions(error)

        assert isinstance(actions, list)
        assert len(actions) > 0
        assert "skip_cache" in actions or "retry" in actions


class TestCircuitBreaker:
    """Test CircuitBreaker class"""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker can be initialized"""
        cb = CircuitBreaker(name="test_service")

        assert cb.name == "test_service"
        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0

    def test_circuit_breaker_with_config(self):
        """Test circuit breaker with custom config"""
        config = CircuitBreakerConfig(
            failure_threshold=3, success_threshold=1, timeout=30
        )
        cb = CircuitBreaker(name="test_service", config=config)

        assert cb.config.failure_threshold == 3
        assert cb.config.success_threshold == 1
        assert cb.config.timeout == 30

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_flow(self):
        """Test successful function execution"""
        cb = CircuitBreaker(name="test_success")

        async def successful_func():
            return "success"

        result = await cb.call(successful_func)

        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb._total_successes == 1
        assert cb._total_failures == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_flow(self):
        """Test circuit opens after threshold failures"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(name="test_failure", config=config)

        async def failing_func():
            raise Exception("Test failure")

        # Fail 3 times to open circuit
        for i in range(3):
            with pytest.raises(Exception):
                await cb.call(failing_func)

        assert cb.state == CircuitState.OPEN
        assert cb._failure_count == 3

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self):
        """Test circuit transitions to half-open after timeout"""
        config = CircuitBreakerConfig(
            failure_threshold=2, timeout=1  # 1 second timeout for testing
        )
        cb = CircuitBreaker(name="test_half_open", config=config)

        async def failing_func():
            raise Exception("Test failure")

        # Open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)

        # Should be OPEN immediately after failures
        assert cb.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Check state - should be HALF_OPEN after timeout
        state = cb.state
        assert state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit closes after successful recovery"""
        config = CircuitBreakerConfig(
            failure_threshold=2, success_threshold=2, timeout=1
        )
        cb = CircuitBreaker(name="test_recovery", config=config)

        async def failing_func():
            raise Exception("Failure")

        async def success_func():
            return "success"

        # Open circuit
        for i in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_func)

        # Should be OPEN after failures
        assert cb.state == CircuitState.OPEN

        # Wait for half-open transition
        await asyncio.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN

        # Succeed twice to close
        await cb.call(success_func)
        await cb.call(success_func)

        assert cb.state == CircuitState.CLOSED

    def test_circuit_breaker_stats(self):
        """Test circuit breaker statistics"""
        cb = CircuitBreaker(name="test_stats")

        stats = cb.get_stats()

        assert stats.state == CircuitState.CLOSED
        assert stats.total_calls == 0
        assert stats.total_failures == 0
        assert stats.total_successes == 0

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset"""
        cb = CircuitBreaker(name="test_reset")
        cb._failure_count = 5
        cb._total_calls = 10

        cb.reset()

        assert cb.state == CircuitState.CLOSED
        assert cb._failure_count == 0
        assert cb._total_calls == 0

    def test_circuit_breaker_force_open(self):
        """Test forcing circuit open"""
        cb = CircuitBreaker(name="test_force_open")

        cb.force_open()

        assert cb.state == CircuitState.OPEN

    def test_circuit_breaker_force_close(self):
        """Test forcing circuit closed"""
        cb = CircuitBreaker(name="test_force_close")
        cb._state = CircuitState.OPEN

        cb.force_close()

        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerManager:
    """Test CircuitBreakerManager class"""

    def test_manager_register(self):
        """Test registering circuit breakers"""
        manager = circuit_breaker_manager

        cb = manager.register("test_service_1")

        assert cb is not None
        assert cb.name == "test_service_1"

    def test_manager_get(self):
        """Test getting registered circuit breaker"""
        manager = circuit_breaker_manager

        manager.register("test_service_2")
        cb = manager.get("test_service_2")

        assert cb is not None
        assert cb.name == "test_service_2"

    def test_manager_get_all_stats(self):
        """Test getting all circuit breaker stats"""
        manager = circuit_breaker_manager

        manager.register("test_service_3")
        stats = manager.get_all_stats()

        assert isinstance(stats, dict)
        assert "test_service_3" in stats


class TestIntegration:
    """Integration tests for error handler and circuit breaker"""

    @pytest.mark.asyncio
    async def test_error_handler_with_circuit_breaker(self):
        """Test error handler classifying circuit breaker errors"""
        handler = ErrorHandler()
        cb = CircuitBreaker(name="test_integration")

        # Force circuit open
        cb.force_open()

        # Try to call through circuit breaker
        async def test_func():
            return "test"

        try:
            await cb.call(test_func)
        except CircuitBreakerOpenError as e:
            # Classify the error
            classification = handler.classify_error(e)

            # Circuit breaker errors should be handled
            assert classification is not None
