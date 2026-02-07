"""
Property-Based Tests - Alert Triggering

Bu modul, hypothesis kullanarak alert triggering icin
property-based testler icerir.

Property 5: Alert Triggering - Kritik alert 5 saniye icinde tetiklenir

Task 9.2 - Optional tests for api-endpoint-saglik spec

Requirements Tested:
    REQ-8.3: Threshold-based alerting
    REQ-8.4: Alert throttling ve max 1 alert per 5 minutes
    REQ-2.6: Kritik endpoint basarisizliginda aninda alert
"""

import pytest
import time
from datetime import datetime, timedelta, UTC
from hypothesis import given, strategies as st, settings

import sys
sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.alerting.alert_manager import (
    AlertManager,
    AlertThreshold,
    AlertSeverity,
    AlertType
)


# =====================================================================
# Hypothesis Strategies
# =====================================================================

# Endpoint path generator
endpoint_paths = st.sampled_from([
    "/api/v1/users",
    "/api/v1/auth/login",
    "/api/v1/exams",
    "/api/v1/questions",
    "/health",
    "/api/v1/learning-path"
])

# Response time (ms)
response_times = st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)

# Error rate (0.0 - 1.0)
error_rates = st.floats(min_value=0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Health score (0 - 100)
health_scores = st.integers(min_value=0, max_value=100)

# Alert metrics generator
@st.composite
def alert_metrics(draw):
    """Generate complete alert metrics."""
    return {
        "endpoint": draw(endpoint_paths),
        "response_time_ms": draw(response_times),
        "error_rate": draw(error_rates),
        "health_score": draw(health_scores),
        "is_critical": draw(st.booleans())
    }


# =====================================================================
# Property Tests - Alert Timing
# =====================================================================

class TestAlertTimingProperties:
    """Alert timing property testleri."""

    @given(
        endpoint=endpoint_paths,
        response_time_ms=st.floats(min_value=500, max_value=10000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_critical_alert_triggered_within_5_seconds(
        self,
        endpoint: str,
        response_time_ms: float
    ):
        """
        Property 5: Kritik alert 5 saniye icinde tetiklenir.
        REQ-2.6: Kritik endpoint basarisizliginda aninda alert
        """
        manager = AlertManager()

        start_time = time.time()

        # Kritik latency ile alert olustur
        alert = await manager.check_and_alert(
            endpoint=endpoint,
            response_time_ms=response_time_ms,
            error_rate=0.0,
            health_score=100,
            is_critical=True
        )

        elapsed = time.time() - start_time

        # Property: Alert 5 saniye icinde olusturulur
        if alert:
            assert elapsed < 5.0, f"Alert creation took {elapsed:.2f}s, expected < 5s"
            # Alert timestamp da dogru olmali
            now = datetime.now(UTC)
            assert (now - alert.timestamp).total_seconds() < 5.0

    @given(
        metrics=alert_metrics()
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_alert_timestamp_is_current(self, metrics: dict):
        """
        Property: Alert timestamp mevcut zaman olmali.
        """
        # En az bir threshold'u gecmesi lazim
        metrics["response_time_ms"] = max(metrics["response_time_ms"], 200)

        manager = AlertManager()
        before = datetime.now(UTC)

        alert = await manager.check_and_alert(**metrics)

        after = datetime.now(UTC)

        if alert:
            # Property: Timestamp before ve after arasinda
            assert before <= alert.timestamp <= after


# =====================================================================
# Property Tests - Threshold-Based Alerting
# =====================================================================

class TestThresholdAlertingProperties:
    """Threshold-based alerting property testleri."""

    @given(
        response_time_ms=st.floats(min_value=500, max_value=10000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_high_latency_triggers_critical_alert(self, response_time_ms: float):
        """
        Property: Response time >= 500ms critical alert tetikler.
        REQ-8.3: Threshold-based alerting
        """
        thresholds = AlertThreshold(
            response_time_critical_ms=500.0,
            response_time_warning_ms=200.0
        )
        manager = AlertManager(thresholds=thresholds)

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        # Property: High latency -> critical alert
        assert alert is not None
        assert alert.type == AlertType.HIGH_LATENCY
        assert alert.severity == AlertSeverity.CRITICAL

    @given(
        response_time_ms=st.floats(min_value=200, max_value=499.9, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_moderate_latency_triggers_warning_alert(self, response_time_ms: float):
        """
        Property: Response time 200-500ms warning alert tetikler.
        """
        thresholds = AlertThreshold(
            response_time_critical_ms=500.0,
            response_time_warning_ms=200.0
        )
        manager = AlertManager(thresholds=thresholds)

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        # Property: Moderate latency -> warning alert
        assert alert is not None
        assert alert.type == AlertType.HIGH_LATENCY
        assert alert.severity == AlertSeverity.WARNING

    @given(
        error_rate=st.floats(min_value=0.05, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_high_error_rate_triggers_critical_alert(self, error_rate: float):
        """
        Property: Error rate >= 5% critical alert tetikler.
        """
        thresholds = AlertThreshold(
            error_rate_critical=0.05,
            error_rate_warning=0.01
        )
        manager = AlertManager(thresholds=thresholds)

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=50.0,  # Normal latency
            error_rate=error_rate,
            health_score=100,
            is_critical=False
        )

        # Property: High error rate -> critical alert
        assert alert is not None
        assert alert.type == AlertType.HIGH_ERROR_RATE
        assert alert.severity == AlertSeverity.CRITICAL

    @given(
        health_score=st.integers(min_value=0, max_value=49)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_low_health_score_triggers_critical_alert(self, health_score: int):
        """
        Property: Health score < 50 critical alert tetikler.
        """
        thresholds = AlertThreshold(
            health_score_critical=50,
            health_score_warning=70
        )
        manager = AlertManager(thresholds=thresholds)

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=50.0,  # Normal latency
            error_rate=0.0,  # Normal error rate
            health_score=health_score,
            is_critical=False
        )

        # Property: Low health score -> critical alert
        assert alert is not None
        assert alert.type == AlertType.LOW_HEALTH_SCORE
        assert alert.severity == AlertSeverity.CRITICAL


# =====================================================================
# Property Tests - Throttling
# =====================================================================

class TestThrottlingProperties:
    """Alert throttling property testleri."""

    @given(
        alert_count=st.integers(min_value=2, max_value=10)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_duplicate_alerts_throttled(self, alert_count: int):
        """
        Property: Ayni endpoint icin tekrar alertler throttle edilir.
        REQ-8.4: Max 1 alert per endpoint per 5 minutes
        """
        manager = AlertManager(throttle_minutes=5)

        alerts_created = []
        for _ in range(alert_count):
            alert = await manager.check_and_alert(
                endpoint="/api/v1/test",
                response_time_ms=600.0,  # Critical latency
                error_rate=0.0,
                health_score=100,
                is_critical=False  # Normal endpoint, throttling applies
            )
            if alert:
                alerts_created.append(alert)

        # Property: Throttle nedeniyle sadece 1 alert olusur
        assert len(alerts_created) == 1

    @given(
        alert_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_critical_alerts_bypass_throttle(self, alert_count: int):
        """
        Property: Kritik endpoint alertleri throttle'i atlar.
        REQ-2.6: Kritik endpoint basarisizliginda aninda alert
        """
        manager = AlertManager(throttle_minutes=5)

        alerts_created = []
        for _ in range(alert_count):
            alert = await manager.check_and_alert(
                endpoint="/health",
                response_time_ms=600.0,  # Critical latency
                error_rate=0.0,
                health_score=100,
                is_critical=True  # Kritik endpoint, throttle bypass
            )
            if alert:
                alerts_created.append(alert)

        # Property: Kritik alertler throttle edilmez
        assert len(alerts_created) == alert_count

    @pytest.mark.asyncio
    async def test_throttle_window_is_5_minutes(self):
        """
        Property: Throttle penceresi 5 dakika olmali.
        """
        manager = AlertManager(throttle_minutes=5)

        # Ilk alert
        alert1 = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )
        assert alert1 is not None

        # Hemen ikinci deneme - throttle edilmeli
        alert2 = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )
        assert alert2 is None

        # Throttle timeout'unu simule et
        throttle_key = "high_latency:/api/v1/test"
        manager._last_alerts[throttle_key] = datetime.now(UTC) - timedelta(minutes=6)

        # 5 dakika sonra tekrar gonderebilmeli
        alert3 = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )
        assert alert3 is not None


# =====================================================================
# Property Tests - Alert Content
# =====================================================================

class TestAlertContentProperties:
    """Alert content property testleri."""

    @given(
        endpoint=endpoint_paths
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_alert_contains_endpoint_info(self, endpoint: str):
        """
        Property: Alert endpoint bilgisini icermeli.
        """
        manager = AlertManager()

        alert = await manager.check_and_alert(
            endpoint=endpoint,
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        assert alert is not None
        assert alert.endpoint == endpoint
        assert endpoint in alert.message or len(alert.message) > 0

    @given(
        metrics=alert_metrics()
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_alert_severity_matches_threshold(self, metrics: dict):
        """
        Property: Alert severity threshold'a gore dogru belirlenmeli.
        """
        thresholds = AlertThreshold()
        manager = AlertManager(thresholds=thresholds)

        alert = await manager.check_and_alert(**metrics)

        if alert:
            # Response time critical
            if metrics["response_time_ms"] >= thresholds.response_time_critical_ms:
                assert alert.severity == AlertSeverity.CRITICAL
            # Response time warning
            elif metrics["response_time_ms"] >= thresholds.response_time_warning_ms:
                assert alert.severity == AlertSeverity.WARNING
            # Error rate critical
            elif metrics["error_rate"] >= thresholds.error_rate_critical:
                assert alert.severity == AlertSeverity.CRITICAL
            # Error rate warning
            elif metrics["error_rate"] >= thresholds.error_rate_warning:
                assert alert.severity == AlertSeverity.WARNING
            # Health score critical
            elif metrics["health_score"] < thresholds.health_score_critical:
                assert alert.severity == AlertSeverity.CRITICAL
            # Health score warning
            elif metrics["health_score"] < thresholds.health_score_warning:
                assert alert.severity == AlertSeverity.WARNING

    @given(
        response_time=st.floats(min_value=500, max_value=5000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=50)
    @pytest.mark.asyncio
    async def test_alert_details_contain_metrics(self, response_time: float):
        """
        Property: Alert details ilgili metrikleri icermeli.
        """
        manager = AlertManager()

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=response_time,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        assert alert is not None
        assert "response_time_ms" in alert.details
        assert alert.details["response_time_ms"] == response_time


# =====================================================================
# Property Tests - Notifier Behavior
# =====================================================================

class TestNotifierProperties:
    """Notifier property testleri."""

    @given(
        notifier_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_all_notifiers_called(self, notifier_count: int):
        """
        Property: Tum notifier'lar cagrilmali.
        """
        manager = AlertManager()

        notifiers_called = []
        for i in range(notifier_count):
            async def notifier(alert, idx=i):
                notifiers_called.append(idx)
            manager.add_notifier(notifier)

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        # Property: Tum notifier'lar cagrildi
        assert len(notifiers_called) == notifier_count
        assert set(notifiers_called) == set(range(notifier_count))

    @pytest.mark.asyncio
    async def test_notifier_error_does_not_block_others(self):
        """
        Property: Bir notifier hatasi digerlerini etkilememeli.
        """
        manager = AlertManager()

        success_calls = []

        async def failing_notifier(alert):
            raise Exception("Notifier failed!")

        async def success_notifier(alert):
            success_calls.append(alert.id)

        manager.add_notifier(failing_notifier)
        manager.add_notifier(success_notifier)

        # Hata olsa bile ikinci notifier cagrilmali
        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        assert len(success_calls) == 1
        assert alert.id in success_calls


# =====================================================================
# Property Tests - Alert Stats
# =====================================================================

class TestAlertStatsProperties:
    """Alert stats property testleri."""

    @given(
        num_alerts=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=30)
    @pytest.mark.asyncio
    async def test_active_alerts_count_correct(self, num_alerts: int):
        """
        Property: Active alert sayisi dogru olmali.
        """
        manager = AlertManager()

        # Farkli endpoint'lerden alert olustur (throttle onlemek icin)
        for i in range(num_alerts):
            await manager.check_and_alert(
                endpoint=f"/api/v1/resource{i}",
                response_time_ms=600.0,
                error_rate=0.0,
                health_score=100,
                is_critical=False
            )

        active_alerts = await manager.get_active_alerts()
        stats = await manager.get_alert_stats()

        # Property: Active count dogru
        assert len(active_alerts) == num_alerts
        assert stats["active_count"] == num_alerts

    @pytest.mark.asyncio
    async def test_resolved_alert_removed_from_active(self):
        """
        Property: Cozulen alert active listeden cikarilmali.
        """
        manager = AlertManager()

        # Alert olustur
        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=600.0,
            error_rate=0.0,
            health_score=100,
            is_critical=False
        )

        assert len(await manager.get_active_alerts()) == 1

        # Alert'i coz
        await manager.resolve_alert(alert.id)

        # Property: Active listeden cikarildi
        assert len(await manager.get_active_alerts()) == 0


# =====================================================================
# Property Tests - No Alert Scenarios
# =====================================================================

class TestNoAlertProperties:
    """Alert tetiklenmemesi gereken durumlar."""

    @given(
        response_time_ms=st.floats(min_value=0, max_value=199.9, allow_nan=False, allow_infinity=False),
        error_rate=st.floats(min_value=0, max_value=0.009, allow_nan=False, allow_infinity=False),
        health_score=st.integers(min_value=70, max_value=100)
    )
    @settings(max_examples=100)
    @pytest.mark.asyncio
    async def test_no_alert_when_all_metrics_healthy(
        self,
        response_time_ms: float,
        error_rate: float,
        health_score: int
    ):
        """
        Property: Saglikli metrikler alert tetiklememeli.
        """
        manager = AlertManager()

        alert = await manager.check_and_alert(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            health_score=health_score,
            is_critical=False
        )

        # Property: Saglikli metriklerde alert yok
        assert alert is None
