"""
Property-Based Tests - Health Score Calculator

Bu modül, hypothesis kullanarak health score calculator için
property-based testler içerir.

Property 4: Health Score Bounds - Score her zaman 0-100 arasında
"""

import sys

from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, "c:/Users/husey/kiro2/backend")

from app.health.models import HealthStatus
from app.health.score_calculator import HealthScoreCalculator


class TestHealthScoreProperties:
    """Health score property-based testleri."""

    def setup_method(self):
        """Test setup."""
        self.calculator = HealthScoreCalculator()

    @given(
        response_time_ms=st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
        error_rate=st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        uptime_percentage=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        dependency_health=st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200)
    def test_score_always_between_0_and_100(
        self,
        response_time_ms: float,
        error_rate: float,
        uptime_percentage: float,
        dependency_health: float
    ):
        """
        Property 4: Health score her zaman 0-100 arasında olmalı.

        REQ-8.1: Health score hesaplama (0-100 arası)
        """
        score = self.calculator.calculate_score(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            dependency_health=dependency_health
        )

        # Property: Score 0-100 arasında
        assert 0 <= score.score <= 100, f"Score out of bounds: {score.score}"

        # Alt skorlar da 0-100 arasında
        assert 0 <= score.response_time_score <= 100
        assert 0 <= score.error_rate_score <= 100
        assert 0 <= score.uptime_score <= 100
        assert 0 <= score.dependency_score <= 100

    @given(
        response_time_ms=st.floats(min_value=0, max_value=50, allow_nan=False, allow_infinity=False),
        error_rate=st.floats(min_value=0, max_value=0.001, allow_nan=False, allow_infinity=False),
        uptime_percentage=st.floats(min_value=99.9, max_value=100, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_excellent_metrics_give_high_score(
        self,
        response_time_ms: float,
        error_rate: float,
        uptime_percentage: float
    ):
        """
        Property: Mükemmel metrikler yüksek skor vermeli (>= 90).
        """
        score = self.calculator.calculate_score(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            dependency_health=100.0
        )

        # Mükemmel metrikler >= 90 skor
        assert score.score >= 85, f"Excellent metrics should give high score, got {score.score}"

    @given(
        response_time_ms=st.floats(min_value=1000, max_value=10000, allow_nan=False, allow_infinity=False),
        error_rate=st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False),
        uptime_percentage=st.floats(min_value=0, max_value=90, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_poor_metrics_give_low_score(
        self,
        response_time_ms: float,
        error_rate: float,
        uptime_percentage: float
    ):
        """
        Property: Kötü metrikler düşük skor vermeli (<= 50).
        """
        score = self.calculator.calculate_score(
            endpoint="/api/v1/test",
            response_time_ms=response_time_ms,
            error_rate=error_rate,
            uptime_percentage=uptime_percentage,
            dependency_health=50.0
        )

        # Kötü metrikler <= 50 skor
        assert score.score <= 60, f"Poor metrics should give low score, got {score.score}"

    @given(
        response_time_ms=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_response_time_score_monotonically_decreasing(
        self,
        response_time_ms: float
    ):
        """
        Property: Response time arttıkça skor azalmalı (monoton azalan).
        """
        score1 = self.calculator._calculate_response_time_score(response_time_ms)
        score2 = self.calculator._calculate_response_time_score(response_time_ms + 100)

        assert score1 >= score2, "Response time score should decrease as time increases"

    @given(
        error_rate=st.floats(min_value=0, max_value=0.5, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=100)
    def test_error_rate_score_monotonically_decreasing(
        self,
        error_rate: float
    ):
        """
        Property: Error rate arttıkça skor azalmalı (monoton azalan).
        """
        score1 = self.calculator._calculate_error_rate_score(error_rate)
        score2 = self.calculator._calculate_error_rate_score(error_rate + 0.01)

        assert score1 >= score2, "Error rate score should decrease as rate increases"

    def test_status_from_score_boundaries(self):
        """
        Test: Skor sınırlarında doğru status döndürülmeli.
        """
        # HEALTHY: >= 70
        assert self.calculator.get_status_from_score(100) == HealthStatus.HEALTHY
        assert self.calculator.get_status_from_score(70) == HealthStatus.HEALTHY

        # DEGRADED: 50-69
        assert self.calculator.get_status_from_score(69) == HealthStatus.DEGRADED
        assert self.calculator.get_status_from_score(50) == HealthStatus.DEGRADED

        # UNHEALTHY: < 50
        assert self.calculator.get_status_from_score(49) == HealthStatus.UNHEALTHY
        assert self.calculator.get_status_from_score(0) == HealthStatus.UNHEALTHY

    def test_score_label_categories(self):
        """
        Test: Skor etiketleri doğru kategorilerde olmalı.
        """
        assert "Excellent" in self.calculator.get_score_label(95)
        assert "Good" in self.calculator.get_score_label(75)
        assert "Fair" in self.calculator.get_score_label(55)
        assert "Poor" in self.calculator.get_score_label(35)
        assert "Critical" in self.calculator.get_score_label(15)
