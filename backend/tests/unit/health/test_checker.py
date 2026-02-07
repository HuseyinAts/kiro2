"""
Unit Tests - Health Checker

Bu modül, HealthChecker sınıfı için unit testler içerir.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.checker import HealthChecker
from app.health.models import (
    CircuitState,
    EndpointMetadata,
    HealthCheckResult,
    HealthStatus,
)


class TestHealthChecker:
    """HealthChecker unit testleri."""

    def setup_method(self):
        """Test setup."""
        self.checker = HealthChecker(
            base_url="http://localhost:8000",
            timeout=30
        )

    def test_initialization(self):
        """Test: Başlatma parametreleri doğru atanmalı."""
        assert self.checker.base_url == "http://localhost:8000"
        assert self.checker.timeout == 30
        assert self.checker.window_size == 100
        assert len(self.checker.response_times) == 0

    @pytest.mark.asyncio
    async def test_check_endpoint_circuit_open(self):
        """Test: Circuit OPEN ise request göndermemeli."""
        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="test_handler"
        )

        result = await self.checker.check_endpoint(
            metadata,
            circuit_state=CircuitState.OPEN
        )

        assert result.status == HealthStatus.UNHEALTHY
        assert result.status_code == 503
        assert "Circuit breaker is OPEN" in result.error_message

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_endpoint_success(self, mock_client):
        """Test: Başarılı request doğru sonuç döndürmeli."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()

        mock_client.return_value = mock_client_instance

        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="test_handler",
            expected_status_codes=[200]
        )

        result = await self.checker.check_endpoint(metadata)

        assert result.status == HealthStatus.HEALTHY
        assert result.status_code == 200
        assert result.error_message is None

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_check_endpoint_unexpected_status(self, mock_client):
        """Test: Beklenmeyen status code UNHEALTHY döndürmeli."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()

        mock_client.return_value = mock_client_instance

        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="test_handler",
            expected_status_codes=[200]
        )

        result = await self.checker.check_endpoint(metadata)

        assert result.status == HealthStatus.UNHEALTHY
        assert result.status_code == 500
        assert "Unexpected status code" in result.error_message

    def test_record_response_time(self):
        """Test: Response time sliding window'a eklenmeli."""
        endpoint_key = "GET:/api/v1/test"

        self.checker._record_response_time(endpoint_key, 100.0)
        self.checker._record_response_time(endpoint_key, 150.0)
        self.checker._record_response_time(endpoint_key, 200.0)

        assert len(self.checker.response_times[endpoint_key]) == 3
        assert list(self.checker.response_times[endpoint_key]) == [100.0, 150.0, 200.0]

    def test_calculate_percentiles_empty(self):
        """Test: Boş veri için sıfır percentile döndürmeli."""
        percentiles = self.checker.calculate_percentiles("nonexistent")

        assert percentiles["p50"] == 0.0
        assert percentiles["p95"] == 0.0
        assert percentiles["p99"] == 0.0

    def test_calculate_percentiles_with_data(self):
        """Test: Veri varken doğru percentile hesaplamalı."""
        endpoint_key = "GET:/api/v1/test"

        # 100 veri noktası ekle
        for i in range(100):
            self.checker._record_response_time(endpoint_key, float(i + 1))

        percentiles = self.checker.calculate_percentiles(endpoint_key)

        # P50 ~ 50, P95 ~ 95, P99 ~ 99
        assert 45 <= percentiles["p50"] <= 55
        assert 90 <= percentiles["p95"] <= 100
        assert 95 <= percentiles["p99"] <= 100

    def test_sliding_window_max_size(self):
        """Test: Sliding window maksimum boyutu aşmamalı."""
        endpoint_key = "GET:/api/v1/test"

        # Window size'dan fazla veri ekle
        for i in range(150):
            self.checker._record_response_time(endpoint_key, float(i))

        # Maksimum 100 olmalı (window_size)
        assert len(self.checker.response_times[endpoint_key]) == 100

    @pytest.mark.asyncio
    async def test_check_multiple_endpoints_parallel(self):
        """Test: Birden fazla endpoint paralel kontrol edilmeli."""
        endpoints = [
            EndpointMetadata(path=f"/api/v1/test{i}", method="GET", handler="handler")
            for i in range(3)
        ]

        # Mock olmadan sadece exception handling test
        with patch.object(self.checker, "check_endpoint") as mock_check:
            mock_check.return_value = HealthCheckResult(
                endpoint="/test",
                status=HealthStatus.HEALTHY,
                response_time_ms=50.0,
                status_code=200
            )

            results = await self.checker.check_multiple_endpoints(endpoints)

            assert len(results) == 3
            assert mock_check.call_count == 3

    @pytest.mark.asyncio
    async def test_send_critical_alert_non_critical(self):
        """Test: Kritik olmayan endpoint için alert göndermemeli."""
        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="handler",
            is_critical=False
        )

        result = HealthCheckResult(
            endpoint="/api/v1/test",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=100.0,
            status_code=500
        )

        # Exception fırlatmamalı
        await self.checker.send_critical_alert(metadata, result)

    @pytest.mark.asyncio
    async def test_send_critical_alert_healthy(self):
        """Test: Sağlıklı endpoint için alert göndermemeli."""
        metadata = EndpointMetadata(
            path="/api/v1/test",
            method="GET",
            handler="handler",
            is_critical=True
        )

        result = HealthCheckResult(
            endpoint="/api/v1/test",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
            status_code=200
        )

        # Exception fırlatmamalı
        await self.checker.send_critical_alert(metadata, result)


class TestHealthCheckerWithRedis:
    """Redis entegrasyonlu HealthChecker testleri."""

    def setup_method(self):
        """Test setup with mock Redis."""
        self.mock_redis = AsyncMock()
        self.checker = HealthChecker(
            base_url="http://localhost:8000",
            redis_client=self.mock_redis,
            timeout=30
        )

    @pytest.mark.asyncio
    async def test_store_result_to_redis(self):
        """Test: Sonuç Redis'e kaydedilmeli."""
        result = HealthCheckResult(
            endpoint="/api/v1/test",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
            status_code=200
        )

        await self.checker._store_result(result)

        self.mock_redis.hset.assert_called_once()
        self.mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_result_redis_error(self):
        """Test: Redis hatası loglama yapmalı ama exception fırlatmamalı."""
        self.mock_redis.hset.side_effect = Exception("Redis error")

        result = HealthCheckResult(
            endpoint="/api/v1/test",
            status=HealthStatus.HEALTHY,
            response_time_ms=50.0,
            status_code=200
        )

        # Exception fırlatmamalı
        await self.checker._store_result(result)
