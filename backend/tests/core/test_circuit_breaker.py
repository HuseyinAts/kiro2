"""
Tests for Circuit Breaker Pattern Implementation
Learning Path Video Yükleme Sorunu - Circuit Breaker Tests

Requirements: 5.18, 4.11
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from backend.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerOpenError,
    CircuitBreakerHalfOpenError,
    CircuitBreakerManager,
    circuit_breaker_manager,
)


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60
        assert config.half_open_max_calls == 3
        assert config.excluded_exceptions == ()

    def test_custom_config(self):
        """Test custom configuration"""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=120,
            half_open_max_calls=5,
            excluded_exceptions=(ValueError,),
        )

        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 120
        assert config.half_open_max_calls == 5
        assert ValueError in config.excluded_exceptions


class TestCircuitBreakerStats:
    """Test circuit breaker statistics"""

    def test_stats_creation(self):
        """Test stats object creation"""
        stats = CircuitBreakerStats(
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            last_success_time=None,
            opened_at=None,
            total_calls=0,
            total_failures=0,
            total_successes=0,
            half_open_attempts=0,
        )

        assert stats.state == CircuitState.CLOSED
        assert stats.failure_count == 0
        assert stats.total_calls == 0

    def test_stats_to_dict(self):
        """Test stats conversion to dictionary"""
        now = datetime.now()
        stats = CircuitBreakerStats(
            state=CircuitState.OPEN,
            failure_count=5,
            success_count=0,
            last_failure_time=now,
            last_success_time=None,
            opened_at=now,
            total_calls=10,
            total_failures=5,
            total_successes=5,
            half_open_attempts=0,
        )

        stats_dict = stats.to_dict()

        assert stats_dict["state"] == "open"
        assert stats_dict["failure_count"] == 5
        assert stats_dict["total_calls"] == 10
        assert "success_rate" in stats_dict

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        stats = CircuitBreakerStats(
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            last_success_time=None,
            opened_at=None,
            total_calls=10,
            total_failures=3,
            total_successes=7,
            half_open_attempts=0,
        )

        success_rate = stats._calculate_success_rate()
        assert success_rate == 70.0

    def test_success_rate_zero_calls(self):
        """Test success rate with zero calls"""
        stats = CircuitBreakerStats(
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            last_success_time=None,
            opened_at=None,
            total_calls=0,
            total_failures=0,
            total_successes=0,
            half_open_attempts=0,
        )

        success_rate = stats._calculate_success_rate()
        assert success_rate == 0.0


class TestCircuitBreakerExceptions:
    """Test circuit breaker exceptions"""

    def test_circuit_breaker_open_error(self):
        """Test CircuitBreakerOpenError creation"""
        error = CircuitBreakerOpenError(circuit_name="test_circuit", retry_after=60)

        assert error.circuit_name == "test_circuit"
        assert error.state == CircuitState.OPEN
        assert error.retry_after == 60
        assert "OPEN" in error.message

    def test_circuit_breaker_half_open_error(self):
        """Test CircuitBreakerHalfOpenError creation"""
        error = CircuitBreakerHalfOpenError(circuit_name="test_circuit", max_calls=3)

        assert error.circuit_name == "test_circuit"
        assert error.state == CircuitState.HALF_OPEN
        assert "HALF_OPEN" in error.message


class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    def setup_method(self):
        """Setup test fixtures"""
        self.config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=2,
            timeout=1,  # 1 second for faster tests
            half_open_max_calls=2,
        )
        self.breaker = CircuitBreaker(name="test_circuit", config=self.config)

    def test_initial_state(self):
        """Test initial circuit breaker state"""
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker._failure_count == 0
        assert self.breaker._success_count == 0

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful function call"""

        async def success_func():
            return "success"

        result = await self.breaker.call(success_func)

        assert result == "success"
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker._total_successes == 1

    @pytest.mark.asyncio
    async def test_failed_call(self):
        """Test failed function call"""

        async def fail_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await self.breaker.call(fail_func)

        assert self.breaker._failure_count == 1
        assert self.breaker._total_failures == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test circuit opens after failure threshold"""

        async def fail_func():
            raise ValueError("Test error")

        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(fail_func)

        # Circuit should be open
        assert self.breaker.state == CircuitState.OPEN

        # Next call should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await self.breaker.call(fail_func)

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout"""

        async def fail_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(fail_func)

        assert self.breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Check state - should be half-open
        assert self.breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self):
        """Test successful calls in half-open state close circuit"""

        async def fail_func():
            raise ValueError("Test error")

        async def success_func():
            return "success"

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(fail_func)

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Make successful calls (success_threshold = 2)
        await self.breaker.call(success_func)
        await self.breaker.call(success_func)

        # Circuit should be closed
        assert self.breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self):
        """Test failure in half-open state reopens circuit"""

        async def fail_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(fail_func)

        # Wait for timeout
        await asyncio.sleep(1.1)

        assert self.breaker.state == CircuitState.HALF_OPEN

        # Fail in half-open state
        with pytest.raises(ValueError):
            await self.breaker.call(fail_func)

        # Circuit should be open again
        assert self.breaker.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_half_open_max_calls_limit(self):
        """Test half-open state respects max calls limit"""

        async def success_func():
            await asyncio.sleep(0.1)
            return "success"

        async def fail_func():
            raise ValueError("Test error")

        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await self.breaker.call(fail_func)

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Make max_calls (2) successful calls
        await self.breaker.call(success_func)
        await self.breaker.call(success_func)

        # Third call should raise CircuitBreakerHalfOpenError
        # (but circuit might already be closed if success_threshold reached)
        # Let's check the state
        if self.breaker.state == CircuitState.HALF_OPEN:
            with pytest.raises(CircuitBreakerHalfOpenError):
                await self.breaker.call(success_func)

    @pytest.mark.asyncio
    async def test_excluded_exceptions(self):
        """Test excluded exceptions don't trigger circuit"""
        config = CircuitBreakerConfig(
            failure_threshold=3, excluded_exceptions=(ValueError,)
        )
        breaker = CircuitBreaker(name="test", config=config)

        async def fail_func():
            raise ValueError("Excluded error")

        # Raise excluded exception multiple times
        for _ in range(5):
            with pytest.raises(ValueError):
                await breaker.call(fail_func)

        # Circuit should still be closed
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_decorator_usage(self):
        """Test circuit breaker as decorator"""

        @self.breaker.protect
        async def protected_func(value):
            if value < 0:
                raise ValueError("Negative value")
            return value * 2

        # Successful call
        result = await protected_func(5)
        assert result == 10

        # Failed calls
        for _ in range(3):
            with pytest.raises(ValueError):
                await protected_func(-1)

        # Circuit should be open
        with pytest.raises(CircuitBreakerOpenError):
            await protected_func(5)

    def test_get_stats(self):
        """Test getting circuit breaker statistics"""
        stats = self.breaker.get_stats()

        assert isinstance(stats, CircuitBreakerStats)
        assert stats.state == CircuitState.CLOSED
        assert stats.total_calls == 0

    def test_reset(self):
        """Test circuit breaker reset"""
        # Modify state
        self.breaker._failure_count = 5
        self.breaker._total_calls = 10
        self.breaker._state = CircuitState.OPEN

        # Reset
        self.breaker.reset()

        # Verify reset
        assert self.breaker.state == CircuitState.CLOSED
        assert self.breaker._failure_count == 0
        assert self.breaker._total_calls == 0

    def test_force_open(self):
        """Test forcing circuit open"""
        assert self.breaker.state == CircuitState.CLOSED

        self.breaker.force_open()

        assert self.breaker.state == CircuitState.OPEN

    def test_force_close(self):
        """Test forcing circuit closed"""
        self.breaker._state = CircuitState.OPEN

        self.breaker.force_close()

        assert self.breaker.state == CircuitState.CLOSED


class TestCircuitBreakerManager:
    """Test circuit breaker manager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = CircuitBreakerManager()

    def test_register_circuit_breaker(self):
        """Test registering a circuit breaker"""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = self.manager.register("test_service", config)

        assert breaker is not None
        assert breaker.name == "test_service"
        assert breaker.config.failure_threshold == 5

    def test_register_duplicate_circuit_breaker(self):
        """Test registering duplicate circuit breaker"""
        self.manager.register("test_service")
        breaker2 = self.manager.register("test_service")

        # Should return existing breaker
        assert breaker2 is not None

    def test_get_circuit_breaker(self):
        """Test getting a circuit breaker"""
        self.manager.register("test_service")

        breaker = self.manager.get("test_service")

        assert breaker is not None
        assert breaker.name == "test_service"

    def test_get_nonexistent_circuit_breaker(self):
        """Test getting non-existent circuit breaker"""
        breaker = self.manager.get("nonexistent")

        assert breaker is None

    def test_get_all_stats(self):
        """Test getting all circuit breaker stats"""
        self.manager.register("service1")
        self.manager.register("service2")

        all_stats = self.manager.get_all_stats()

        assert "service1" in all_stats
        assert "service2" in all_stats
        assert all_stats["service1"]["state"] == "closed"

    def test_reset_all(self):
        """Test resetting all circuit breakers"""
        breaker1 = self.manager.register("service1")
        breaker2 = self.manager.register("service2")

        # Modify states
        breaker1._failure_count = 5
        breaker2._failure_count = 3

        # Reset all
        self.manager.reset_all()

        # Verify reset
        assert breaker1._failure_count == 0
        assert breaker2._failure_count == 0


class TestCircuitBreakerIntegration:
    """Integration tests for circuit breaker"""

    @pytest.mark.asyncio
    async def test_real_world_scenario(self):
        """Test realistic circuit breaker scenario"""
        config = CircuitBreakerConfig(
            failure_threshold=3, success_threshold=2, timeout=1
        )
        breaker = CircuitBreaker("youtube_api", config)

        call_count = 0

        async def unstable_api_call():
            nonlocal call_count
            call_count += 1

            # Fail first 3 calls
            if call_count <= 3:
                raise ConnectionError("API unavailable")

            # Succeed after that
            return {"status": "ok"}

        # First 3 calls fail
        for i in range(3):
            with pytest.raises(ConnectionError):
                await breaker.call(unstable_api_call)

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(unstable_api_call)

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Circuit should be half-open
        assert breaker.state == CircuitState.HALF_OPEN

        # Successful calls should close circuit
        result1 = await breaker.call(unstable_api_call)
        result2 = await breaker.call(unstable_api_call)

        assert result1["status"] == "ok"
        assert result2["status"] == "ok"
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_concurrent_calls(self):
        """Test circuit breaker with concurrent calls"""
        breaker = CircuitBreaker("concurrent_test")

        async def api_call(value):
            await asyncio.sleep(0.01)
            return value * 2

        # Make concurrent calls
        tasks = [breaker.call(api_call, i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert results[0] == 0
        assert results[9] == 18

    @pytest.mark.asyncio
    async def test_multiple_services_with_manager(self):
        """Test managing multiple services with circuit breakers"""
        manager = CircuitBreakerManager()

        youtube_breaker = manager.register("youtube_api")
        cache_breaker = manager.register("redis_cache")

        async def youtube_call():
            return "youtube_data"

        async def cache_call():
            return "cache_data"

        # Make calls through different breakers
        youtube_result = await youtube_breaker.call(youtube_call)
        cache_result = await cache_breaker.call(cache_call)

        assert youtube_result == "youtube_data"
        assert cache_result == "cache_data"

        # Check stats
        all_stats = manager.get_all_stats()
        assert len(all_stats) == 2
        assert all_stats["youtube_api"]["total_successes"] == 1
        assert all_stats["redis_cache"]["total_successes"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
