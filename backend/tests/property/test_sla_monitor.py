"""
Property-Based Tests - SLA Monitor

Bu modül, hypothesis kullanarak SLA monitor için
property-based testler içerir.

Property 3: SLA Compliance Detection - P95 > 200ms marked as degraded/unhealthy
"""

import pytest
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.sla_monitor import SLAMonitor
from app.health.models import HealthStatus, SLAMetrics


class TestSLAMonitorProperties:
    """SLA monitor property-based testleri."""

    def setup_method(self):
        """Test setup."""
        self.monitor = SLAMonitor(
            healthy_threshold=200.0,
            degraded_threshold=500.0
        )

    @given(
        p95_ms=st.floats(min_value=0, max_value=199.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_healthy_when_p95_below_200ms(self, p95_ms: float):
        """
        Property 3a: P95 < 200ms -> HEALTHY

        REQ-3.2: P95 < 200ms → "healthy"
        """
        status = self.monitor.classify_health_status(p95_ms)
        assert status == HealthStatus.HEALTHY, \
            f"P95={p95_ms}ms should be HEALTHY, got {status}"

    @given(
        p95_ms=st.floats(min_value=200.0, max_value=499.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_degraded_when_p95_between_200_and_500ms(self, p95_ms: float):
        """
        Property 3b: P95 200-500ms -> DEGRADED

        REQ-3.3: P95 200-500ms → "degraded"
        """
        status = self.monitor.classify_health_status(p95_ms)
        assert status == HealthStatus.DEGRADED, \
            f"P95={p95_ms}ms should be DEGRADED, got {status}"

    @given(
        p95_ms=st.floats(min_value=500.0, max_value=10000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_unhealthy_when_p95_above_500ms(self, p95_ms: float):
        """
        Property 3c: P95 > 500ms -> UNHEALTHY

        REQ-3.4: P95 > 500ms → "unhealthy"
        """
        status = self.monitor.classify_health_status(p95_ms)
        assert status == HealthStatus.UNHEALTHY, \
            f"P95={p95_ms}ms should be UNHEALTHY, got {status}"

    def test_boundary_values(self):
        """
        Test: Sınır değerlerde doğru classification.
        """
        # Exactly 200ms -> DEGRADED (>= threshold)
        assert self.monitor.classify_health_status(200.0) == HealthStatus.DEGRADED

        # Just below 200ms -> HEALTHY
        assert self.monitor.classify_health_status(199.99) == HealthStatus.HEALTHY

        # Exactly 500ms -> UNHEALTHY (>= threshold)
        assert self.monitor.classify_health_status(500.0) == HealthStatus.UNHEALTHY

        # Just below 500ms -> DEGRADED
        assert self.monitor.classify_health_status(499.99) == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    @given(
        p95_ms=st.floats(min_value=0, max_value=199.9, allow_nan=False, allow_infinity=False),
        error_rate=st.floats(min_value=0, max_value=0.009, allow_nan=False, allow_infinity=False),
        uptime=st.floats(min_value=99.91, max_value=100.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    async def test_sla_compliant_with_good_metrics(
        self,
        p95_ms: float,
        error_rate: float,
        uptime: float
    ):
        """
        Property: İyi metriklerle SLA compliant olmalı.
        """
        metrics = SLAMetrics(
            endpoint="/api/v1/test",
            p50_ms=p95_ms * 0.5,
            p95_ms=p95_ms,
            p99_ms=p95_ms * 1.5,
            error_rate=error_rate,
            uptime_percentage=uptime,
            sla_compliant=True  # Will be recalculated
        )

        is_compliant = await self.monitor.check_sla_compliance("/api/v1/test", metrics)

        # Tüm metrikler iyi -> SLA compliant
        assert is_compliant is True

    @pytest.mark.asyncio
    @given(
        p95_ms=st.floats(min_value=201.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    async def test_sla_not_compliant_with_high_latency(self, p95_ms: float):
        """
        Property: Yüksek latency ile SLA compliant olmamalı.
        """
        metrics = SLAMetrics(
            endpoint="/api/v1/test",
            p50_ms=p95_ms * 0.5,
            p95_ms=p95_ms,
            p99_ms=p95_ms * 1.5,
            error_rate=0.001,
            uptime_percentage=99.99,
            sla_compliant=False
        )

        is_compliant = await self.monitor.check_sla_compliance("/api/v1/test_latency", metrics)

        # P95 > 200ms -> SLA not compliant
        assert is_compliant is False

    @pytest.mark.asyncio
    @given(
        error_rate=st.floats(min_value=0.011, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    async def test_sla_not_compliant_with_high_error_rate(self, error_rate: float):
        """
        Property: Yüksek error rate ile SLA compliant olmamalı.
        """
        metrics = SLAMetrics(
            endpoint="/api/v1/test",
            p50_ms=50.0,
            p95_ms=100.0,
            p99_ms=150.0,
            error_rate=error_rate,
            uptime_percentage=99.99,
            sla_compliant=False
        )

        is_compliant = await self.monitor.check_sla_compliance("/api/v1/test_error", metrics)

        # Error rate > 1% -> SLA not compliant
        assert is_compliant is False

    @pytest.mark.asyncio
    @given(
        uptime=st.floats(min_value=0, max_value=99.89, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    async def test_sla_not_compliant_with_low_uptime(self, uptime: float):
        """
        Property: Düşük uptime ile SLA compliant olmamalı.
        """
        metrics = SLAMetrics(
            endpoint="/api/v1/test",
            p50_ms=50.0,
            p95_ms=100.0,
            p99_ms=150.0,
            error_rate=0.001,
            uptime_percentage=uptime,
            sla_compliant=False
        )

        is_compliant = await self.monitor.check_sla_compliance("/api/v1/test_uptime", metrics)

        # Uptime < 99.9% -> SLA not compliant
        assert is_compliant is False

    def test_custom_thresholds(self):
        """
        Test: Özel threshold değerleri doğru çalışmalı.
        """
        custom_monitor = SLAMonitor(
            healthy_threshold=100.0,
            degraded_threshold=300.0
        )

        # Custom thresholds
        assert custom_monitor.classify_health_status(99.0) == HealthStatus.HEALTHY
        assert custom_monitor.classify_health_status(100.0) == HealthStatus.DEGRADED
        assert custom_monitor.classify_health_status(299.0) == HealthStatus.DEGRADED
        assert custom_monitor.classify_health_status(300.0) == HealthStatus.UNHEALTHY
