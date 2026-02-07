"""
Integration Tests - Health Check Workflow

Bu modul, tam health check workflow'u icin integration testler icerir.
"""

import pytest
from unittest.mock import patch
from fastapi import FastAPI

# conftest.py handles sys.path setup
from app.health.discovery import EndpointDiscovery
from app.health.checker import HealthChecker
from app.health.circuit_breaker import CircuitBreaker
from app.health.sla_monitor import SLAMonitor
from app.health.score_calculator import HealthScoreCalculator
from app.health.models import (
    CircuitState,
    EndpointMetadata,
    HealthCheckResult,
    HealthStatus,
    SLATarget,
)


# Test FastAPI app
def create_test_app():
    """Test icin FastAPI uygulamasi olusturur."""
    app = FastAPI()

    @app.get("/api/v1/users")
    async def get_users():
        return []

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/v1/critical")
    async def critical_endpoint():
        return {"data": "critical"}

    return app


class TestDiscoveryToCheckerWorkflow:
    """Endpoint discovery'den checker'a workflow testi."""

    def setup_method(self):
        """Test setup."""
        self.app = create_test_app()
        self.discovery = EndpointDiscovery(self.app)
        self.checker = HealthChecker(base_url="http://localhost:8000")

    @pytest.mark.asyncio
    async def test_discover_and_check_endpoints(self):
        """Test: Kesfedilen endpoint'ler kontrol edilebilmeli."""
        # Discover endpoints
        endpoints = await self.discovery.discover_all_endpoints()

        assert len(endpoints) >= 3

        # Mock HTTP client for checking
        with patch.object(self.checker, "check_endpoint") as mock_check:
            mock_check.return_value = HealthCheckResult(
                endpoint="/test",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            )

            # Check each endpoint
            results = await self.checker.check_multiple_endpoints(endpoints)

            assert len(results) == len(endpoints)
            assert mock_check.call_count == len(endpoints)

    @pytest.mark.asyncio
    async def test_critical_endpoints_identified(self):
        """Test: Critical endpoint'ler dogru tespit edilmeli."""
        endpoints = await self.discovery.discover_all_endpoints()

        # /health critical olmali
        health_ep = next(
            (e for e in endpoints if e.path == "/health"),
            None
        )

        assert health_ep is not None
        assert health_ep.is_critical is True


class TestCircuitBreakerIntegration:
    """Circuit breaker integration testleri."""

    def setup_method(self):
        """Test setup."""
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1  # 1 saniye
        )
        self.checker = HealthChecker(base_url="http://localhost:8000")

    @pytest.mark.asyncio
    async def test_circuit_opens_on_failures(self):
        """Test: Ardisik hatalardan sonra circuit acilmali."""
        endpoint = "GET:/api/v1/test"

        # Record failures
        for _ in range(3):
            await self.circuit_breaker.record_failure(endpoint)

        state = await self.circuit_breaker.get_state(endpoint)
        assert state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_affects_health_check(self):
        """Test: OPEN circuit health check'i engellemeli."""
        endpoint = "GET:/api/v1/test"

        # Open circuit
        for _ in range(5):
            await self.circuit_breaker.record_failure(endpoint)

        state = await self.circuit_breaker.get_state(endpoint)
        assert state == CircuitState.OPEN

        # Check endpoint with open circuit
        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="handler"
        )

        result = await self.checker.check_endpoint(metadata, circuit_state=state)

        assert result.status == HealthStatus.UNHEALTHY
        assert "Circuit breaker is OPEN" in result.error_message


class TestSLAMonitorIntegration:
    """SLA Monitor integration testleri."""

    def setup_method(self):
        """Test setup."""
        self.sla_monitor = SLAMonitor()
        self.sla_monitor.set_target(
            "GET:/api/v1/users",
            SLATarget(
                target_uptime=99.0,
                target_response_time_ms=200.0,
                target_error_rate=1.0
            )
        )

    @pytest.mark.asyncio
    async def test_record_and_check_sla(self):
        """Test: SLA kaydi ve kontrolu calisabilmeli."""
        endpoint_key = "GET:/api/v1/users"

        # Record healthy results
        for _ in range(100):
            result = HealthCheckResult(
                endpoint="/api/v1/users",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            )
            await self.sla_monitor.record_check(endpoint_key, result)

        # Check SLA compliance
        report = await self.sla_monitor.get_compliance_report(endpoint_key)

        assert report.uptime_percentage >= 99.0
        assert report.is_compliant is True

    @pytest.mark.asyncio
    async def test_sla_violation_detected(self):
        """Test: SLA ihlali tespit edilmeli."""
        endpoint_key = "GET:/api/v1/users"

        # Record many failures (uptime violation)
        for _ in range(50):
            fail_result = HealthCheckResult(
                endpoint="/api/v1/users",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=500.0,
                status_code=500
            )
            await self.sla_monitor.record_check(endpoint_key, fail_result)

        for _ in range(50):
            success_result = HealthCheckResult(
                endpoint="/api/v1/users",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            )
            await self.sla_monitor.record_check(endpoint_key, success_result)

        report = await self.sla_monitor.get_compliance_report(endpoint_key)

        # 50% uptime < 99% target
        assert report.uptime_percentage < 99.0
        assert report.is_compliant is False


class TestHealthScoreIntegration:
    """Health score integration testleri."""

    def setup_method(self):
        """Test setup."""
        self.calculator = HealthScoreCalculator()

    @pytest.mark.asyncio
    async def test_calculate_score_from_results(self):
        """Test: Health check sonuclarindan skor hesaplanabilmeli."""
        results = [
            HealthCheckResult(
                endpoint="/api/v1/users",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            ),
            HealthCheckResult(
                endpoint="/api/v1/posts",
                status=HealthStatus.HEALTHY,
                response_time_ms=75.0,
                status_code=200
            ),
            HealthCheckResult(
                endpoint="/api/v1/comments",
                status=HealthStatus.DEGRADED,
                response_time_ms=300.0,
                status_code=200
            ),
        ]

        score = await self.calculator.calculate_from_results(results)

        # Cogunlugu healthy, bir tanesi degraded
        assert 60 <= score <= 95
        assert isinstance(score, float)

    @pytest.mark.asyncio
    async def test_score_with_dependencies(self):
        """Test: Dependency durumu skora yansimali."""
        # All healthy endpoints
        results = [
            HealthCheckResult(
                endpoint="/api",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            )
        ]

        # Healthy dependencies
        score_healthy = await self.calculator.calculate_from_results(
            results,
            dependency_health=1.0
        )

        # Unhealthy dependencies
        score_unhealthy = await self.calculator.calculate_from_results(
            results,
            dependency_health=0.0
        )

        # Dependency unhealthy oldugunda skor dusmeli
        assert score_healthy > score_unhealthy


class TestFullHealthWorkflow:
    """Tam health check workflow testi."""

    def setup_method(self):
        """Test setup."""
        self.app = create_test_app()
        self.discovery = EndpointDiscovery(self.app)
        self.checker = HealthChecker(base_url="http://localhost:8000")
        self.circuit_breaker = CircuitBreaker()
        self.sla_monitor = SLAMonitor()
        self.calculator = HealthScoreCalculator()

    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test: Tam workflow bastan sona calisabilmeli."""
        # Step 1: Discover endpoints
        endpoints = await self.discovery.discover_all_endpoints()
        assert len(endpoints) >= 3

        # Step 2: Mock health checks
        results = []
        for endpoint in endpoints:
            endpoint_key = f"{endpoint.method}:{endpoint.path}"

            # Get circuit state
            state = await self.circuit_breaker.get_state(endpoint_key)

            if state != CircuitState.OPEN:
                # Simulate successful check
                result = HealthCheckResult(
                    endpoint=endpoint.path,
                    status=HealthStatus.HEALTHY,
                    response_time_ms=50.0,
                    status_code=200
                )
                await self.circuit_breaker.record_success(endpoint_key)
            else:
                result = HealthCheckResult(
                    endpoint=endpoint.path,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    status_code=503,
                    error_message="Circuit breaker is OPEN"
                )

            results.append(result)

            # Step 3: Record for SLA
            await self.sla_monitor.record_check(endpoint_key, result)

        # Step 4: Calculate health score
        score = await self.calculator.calculate_from_results(results)

        # All healthy, score should be high
        assert score >= 80

        # Step 5: Verify SLA compliance
        for endpoint in endpoints:
            endpoint_key = f"{endpoint.method}:{endpoint.path}"
            self.sla_monitor.set_target(
                endpoint_key,
                SLATarget(
                    target_uptime=99.0,
                    target_response_time_ms=200.0
                )
            )
            report = await self.sla_monitor.get_compliance_report(endpoint_key)
            assert report.is_compliant is True
