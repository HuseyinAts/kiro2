"""
API Endpoint Sağlık Doğrulama Sistemi - Model Testleri

Bu modül, health check sistemi Pydantic modellerinin unit testlerini içerir.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.health.models import (
    CircuitState,
    EndpointMetadata,
    HealthCheckResult,
    HealthScore,
    HealthStatus,
    SLAMetrics,
)


class TestHealthStatus:
    """HealthStatus enum testleri"""

    def test_health_status_values(self):
        """HealthStatus enum değerlerinin doğru olduğunu test eder"""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_health_status_from_string(self):
        """String'den HealthStatus oluşturulabildiğini test eder"""
        assert HealthStatus("healthy") == HealthStatus.HEALTHY
        assert HealthStatus("degraded") == HealthStatus.DEGRADED
        assert HealthStatus("unhealthy") == HealthStatus.UNHEALTHY

    def test_health_status_invalid_value(self):
        """Geçersiz değerle HealthStatus oluşturulamadığını test eder"""
        with pytest.raises(ValueError):
            HealthStatus("invalid")


class TestCircuitState:
    """CircuitState enum testleri"""

    def test_circuit_state_values(self):
        """CircuitState enum değerlerinin doğru olduğunu test eder"""
        assert CircuitState.CLOSED.value == "closed"
        assert CircuitState.OPEN.value == "open"
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_circuit_state_from_string(self):
        """String'den CircuitState oluşturulabildiğini test eder"""
        assert CircuitState("closed") == CircuitState.CLOSED
        assert CircuitState("open") == CircuitState.OPEN
        assert CircuitState("half_open") == CircuitState.HALF_OPEN

    def test_circuit_state_invalid_value(self):
        """Geçersiz değerle CircuitState oluşturulamadığını test eder"""
        with pytest.raises(ValueError):
            CircuitState("invalid")


class TestEndpointMetadata:
    """EndpointMetadata model testleri"""

    def test_endpoint_metadata_creation(self):
        """EndpointMetadata oluşturulabildiğini test eder"""
        metadata = EndpointMetadata(
            path="/api/v1/users",
            method="GET",
            handler="get_users"
        )
        assert metadata.path == "/api/v1/users"
        assert metadata.method == "GET"
        assert metadata.handler == "get_users"
        assert metadata.requires_auth is False
        assert metadata.is_critical is False
        assert metadata.expected_status_codes == [200, 201, 204]

    def test_endpoint_metadata_with_all_fields(self):
        """Tüm alanlarla EndpointMetadata oluşturulabildiğini test eder"""
        metadata = EndpointMetadata(
            path="/api/v1/admin/users",
            method="POST",
            handler="create_user",
            requires_auth=True,
            is_critical=True,
            expected_status_codes=[201]
        )
        assert metadata.path == "/api/v1/admin/users"
        assert metadata.method == "POST"
        assert metadata.handler == "create_user"
        assert metadata.requires_auth is True
        assert metadata.is_critical is True
        assert metadata.expected_status_codes == [201]

    def test_endpoint_metadata_missing_required_fields(self):
        """Zorunlu alanlar eksikse EndpointMetadata oluşturulamadığını test eder"""
        with pytest.raises(ValidationError):
            EndpointMetadata(path="/api/v1/users")

    def test_endpoint_metadata_json_serialization(self):
        """EndpointMetadata JSON'a serialize edilebilir"""
        metadata = EndpointMetadata(
            path="/api/v1/users",
            method="GET",
            handler="get_users"
        )
        json_data = metadata.model_dump()
        assert json_data["path"] == "/api/v1/users"
        assert json_data["method"] == "GET"
        assert json_data["handler"] == "get_users"


class TestHealthCheckResult:
    """HealthCheckResult model testleri"""

    def test_health_check_result_creation(self):
        """HealthCheckResult oluşturulabildiğini test eder"""
        result = HealthCheckResult(
            endpoint="/api/v1/users",
            status=HealthStatus.HEALTHY,
            response_time_ms=45.2,
            status_code=200
        )
        assert result.endpoint == "/api/v1/users"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms == 45.2
        assert result.status_code == 200
        assert result.error_message is None
        assert isinstance(result.timestamp, datetime)
        assert result.circuit_state == CircuitState.CLOSED

    def test_health_check_result_with_error(self):
        """Hata mesajıyla HealthCheckResult oluşturulabildiğini test eder"""
        result = HealthCheckResult(
            endpoint="/api/v1/users",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=5000.0,
            status_code=500,
            error_message="Internal Server Error",
            circuit_state=CircuitState.OPEN
        )
        assert result.status == HealthStatus.UNHEALTHY
        assert result.error_message == "Internal Server Error"
        assert result.circuit_state == CircuitState.OPEN

    def test_health_check_result_missing_required_fields(self):
        """Zorunlu alanlar eksikse HealthCheckResult oluşturulamadığını test eder"""
        with pytest.raises(ValidationError):
            HealthCheckResult(
                endpoint="/api/v1/users",
                status=HealthStatus.HEALTHY
            )

    def test_health_check_result_json_serialization(self):
        """HealthCheckResult JSON'a serialize edilebilir"""
        result = HealthCheckResult(
            endpoint="/api/v1/users",
            status=HealthStatus.HEALTHY,
            response_time_ms=45.2,
            status_code=200
        )
        json_data = result.model_dump()
        assert json_data["endpoint"] == "/api/v1/users"
        assert json_data["status"] == "healthy"
        assert json_data["response_time_ms"] == 45.2


class TestHealthScore:
    """HealthScore model testleri"""

    def test_health_score_creation(self):
        """HealthScore oluşturulabildiğini test eder"""
        score = HealthScore(
            endpoint="/api/v1/users",
            score=95,
            response_time_score=100.0,
            error_rate_score=95.0,
            uptime_score=99.9,
            dependency_score=85.0
        )
        assert score.endpoint == "/api/v1/users"
        assert score.score == 95
        assert score.response_time_score == 100.0
        assert score.error_rate_score == 95.0
        assert score.uptime_score == 99.9
        assert score.dependency_score == 85.0
        assert isinstance(score.timestamp, datetime)

    def test_health_score_bounds_validation(self):
        """HealthScore'un 0-100 aralığında olduğunu test eder"""
        # Valid score
        score = HealthScore(
            endpoint="/api/v1/users",
            score=50,
            response_time_score=50.0,
            error_rate_score=50.0,
            uptime_score=50.0,
            dependency_score=50.0
        )
        assert 0 <= score.score <= 100

        # Invalid score - too high
        with pytest.raises(ValidationError):
            HealthScore(
                endpoint="/api/v1/users",
                score=101,
                response_time_score=100.0,
                error_rate_score=100.0,
                uptime_score=100.0,
                dependency_score=100.0
            )

        # Invalid score - negative
        with pytest.raises(ValidationError):
            HealthScore(
                endpoint="/api/v1/users",
                score=-1,
                response_time_score=100.0,
                error_rate_score=100.0,
                uptime_score=100.0,
                dependency_score=100.0
            )

    def test_health_score_component_bounds(self):
        """HealthScore bileşenlerinin 0-100 aralığında olduğunu test eder"""
        # Valid component scores
        score = HealthScore(
            endpoint="/api/v1/users",
            score=95,
            response_time_score=100.0,
            error_rate_score=100.0,
            uptime_score=100.0,
            dependency_score=100.0
        )
        assert 0 <= score.response_time_score <= 100
        assert 0 <= score.error_rate_score <= 100
        assert 0 <= score.uptime_score <= 100
        assert 0 <= score.dependency_score <= 100

    def test_health_score_json_serialization(self):
        """HealthScore JSON'a serialize edilebilir"""
        score = HealthScore(
            endpoint="/api/v1/users",
            score=95,
            response_time_score=100.0,
            error_rate_score=95.0,
            uptime_score=99.9,
            dependency_score=85.0
        )
        json_data = score.model_dump()
        assert json_data["endpoint"] == "/api/v1/users"
        assert json_data["score"] == 95


class TestSLAMetrics:
    """SLAMetrics model testleri"""

    def test_sla_metrics_creation(self):
        """SLAMetrics oluşturulabildiğini test eder"""
        metrics = SLAMetrics(
            endpoint="/api/v1/users",
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.005,
            uptime_percentage=99.95,
            sla_compliant=True
        )
        assert metrics.endpoint == "/api/v1/users"
        assert metrics.p50_ms == 45.2
        assert metrics.p95_ms == 180.5
        assert metrics.p99_ms == 450.0
        assert metrics.error_rate == 0.005
        assert metrics.uptime_percentage == 99.95
        assert metrics.sla_compliant is True

    def test_sla_metrics_error_rate_bounds(self):
        """SLAMetrics error_rate'in 0.0-1.0 aralığında olduğunu test eder"""
        # Valid error rate
        metrics = SLAMetrics(
            endpoint="/api/v1/users",
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.5,
            uptime_percentage=99.95,
            sla_compliant=True
        )
        assert 0.0 <= metrics.error_rate <= 1.0

        # Invalid error rate - too high
        with pytest.raises(ValidationError):
            SLAMetrics(
                endpoint="/api/v1/users",
                p50_ms=45.2,
                p95_ms=180.5,
                p99_ms=450.0,
                error_rate=1.5,
                uptime_percentage=99.95,
                sla_compliant=True
            )

        # Invalid error rate - negative
        with pytest.raises(ValidationError):
            SLAMetrics(
                endpoint="/api/v1/users",
                p50_ms=45.2,
                p95_ms=180.5,
                p99_ms=450.0,
                error_rate=-0.1,
                uptime_percentage=99.95,
                sla_compliant=True
            )

    def test_sla_metrics_uptime_bounds(self):
        """SLAMetrics uptime_percentage'in 0.0-100.0 aralığında olduğunu test eder"""
        # Valid uptime
        metrics = SLAMetrics(
            endpoint="/api/v1/users",
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.005,
            uptime_percentage=50.0,
            sla_compliant=False
        )
        assert 0.0 <= metrics.uptime_percentage <= 100.0

        # Invalid uptime - too high
        with pytest.raises(ValidationError):
            SLAMetrics(
                endpoint="/api/v1/users",
                p50_ms=45.2,
                p95_ms=180.5,
                p99_ms=450.0,
                error_rate=0.005,
                uptime_percentage=100.5,
                sla_compliant=True
            )

        # Invalid uptime - negative
        with pytest.raises(ValidationError):
            SLAMetrics(
                endpoint="/api/v1/users",
                p50_ms=45.2,
                p95_ms=180.5,
                p99_ms=450.0,
                error_rate=0.005,
                uptime_percentage=-1.0,
                sla_compliant=False
            )

    def test_sla_metrics_compliance_logic(self):
        """SLA compliance mantığını test eder"""
        # SLA compliant - P95 < 200ms, error rate < 1%, uptime > 99.9%
        compliant_metrics = SLAMetrics(
            endpoint="/api/v1/users",
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.005,
            uptime_percentage=99.95,
            sla_compliant=True
        )
        assert compliant_metrics.sla_compliant is True

        # SLA non-compliant - P95 > 200ms
        non_compliant_metrics = SLAMetrics(
            endpoint="/api/v1/slow",
            p50_ms=150.0,
            p95_ms=550.0,
            p99_ms=1000.0,
            error_rate=0.005,
            uptime_percentage=99.95,
            sla_compliant=False
        )
        assert non_compliant_metrics.sla_compliant is False

    def test_sla_metrics_json_serialization(self):
        """SLAMetrics JSON'a serialize edilebilir"""
        metrics = SLAMetrics(
            endpoint="/api/v1/users",
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.005,
            uptime_percentage=99.95,
            sla_compliant=True
        )
        json_data = metrics.model_dump()
        assert json_data["endpoint"] == "/api/v1/users"
        assert json_data["p95_ms"] == 180.5
        assert json_data["sla_compliant"] is True


class TestModelIntegration:
    """Model entegrasyon testleri"""

    def test_health_check_result_with_all_models(self):
        """Tüm modellerin birlikte kullanılabildiğini test eder"""
        # Endpoint metadata
        metadata = EndpointMetadata(
            path="/api/v1/users",
            method="GET",
            handler="get_users",
            is_critical=True
        )

        # Health check result
        result = HealthCheckResult(
            endpoint=metadata.path,
            status=HealthStatus.HEALTHY,
            response_time_ms=45.2,
            status_code=200,
            circuit_state=CircuitState.CLOSED
        )

        # Health score
        score = HealthScore(
            endpoint=metadata.path,
            score=95,
            response_time_score=100.0,
            error_rate_score=95.0,
            uptime_score=99.9,
            dependency_score=85.0
        )

        # SLA metrics
        metrics = SLAMetrics(
            endpoint=metadata.path,
            p50_ms=45.2,
            p95_ms=180.5,
            p99_ms=450.0,
            error_rate=0.005,
            uptime_percentage=99.95,
            sla_compliant=True
        )

        # Verify all models work together
        assert result.endpoint == metadata.path
        assert score.endpoint == metadata.path
        assert metrics.endpoint == metadata.path
        assert result.status == HealthStatus.HEALTHY
        assert metrics.sla_compliant is True
