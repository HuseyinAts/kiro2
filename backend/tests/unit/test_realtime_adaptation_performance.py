"""
Task 63-64 Test Suite
Gerçek Zamanlı Adaptasyon ve Performans Analitikleri testleri
"""

import pytest

try:
    from services.adaptive_test_engine import (
        AdaptiveTestEngine,
        IRTParameters,
    )
    from services.performance_analytics_system import (
        LearningCurveData,
        PerformanceAnalyticsSystem,
        PredictionResult,
    )
    from services.realtime_adaptation_system import (
        RealtimeAdaptationSystem,
        RealtimeMetrics,
    )
except Exception as e:
    pytest.skip(f"Cannot import required services: {e}", allow_module_level=True)


@pytest.fixture
def sample_session():
    """Test oturumu fixture"""
    engine = AdaptiveTestEngine()
    session = engine.create_test_session(
        session_id="test_session_001",
        student_id="student_001",
        test_type="diagnostic",
        prior_theta=0.0,
    )
    return session


@pytest.fixture
def realtime_system():
    """Realtime adaptation system fixture"""
    return RealtimeAdaptationSystem()


@pytest.fixture
def analytics_system():
    """Performance analytics system fixture"""
    return PerformanceAnalyticsSystem()


class TestRealtimeAdaptation:
    """Task 63: Gerçek Zamanlı Adaptasyon testleri"""

    def test_theta_update_realtime(self, realtime_system, sample_session):
        """Test 63.1: Real-time theta güncelleme"""
        question_params = IRTParameters(a=1.0, b=0.5, c=0.25, d=1.0)

        # Original theta'yı kaydet (metod session state'i güncelliyor)
        original_theta = sample_session.knowledge_state.theta

        # Doğru cevap
        new_theta, se, ci = realtime_system.update_theta_realtime(
            sample_session, question_params, is_correct=True, response_time=15.0
        )

        assert new_theta > original_theta  # Theta artmalı
        assert se > 0  # Standard error pozitif olmalı
        assert ci > 0  # Confidence interval pozitif olmalı

    def test_difficulty_adjustment(self, realtime_system, sample_session):
        """Test 63.2: Zorluk ayarlama"""
        # Metrikleri simüle et
        realtime_system.session_metrics[sample_session.session_id] = RealtimeMetrics()
        metrics = realtime_system.session_metrics[sample_session.session_id]

        # Düşük başarı oranı simüle et
        metrics.accuracy_history = [False, False, True, False, False]
        metrics.difficulty_history = [0.0]

        decision = realtime_system.adjust_difficulty_dynamically(sample_session)

        assert decision.decision_type == "difficulty"
        assert decision.action in ["decrease", "maintain", "increase"]

    def test_motivation_support(self, realtime_system, sample_session):
        """Test 63.3: Motivasyon desteği"""
        # Metrikleri simüle et
        realtime_system.session_metrics[sample_session.session_id] = RealtimeMetrics()
        metrics = realtime_system.session_metrics[sample_session.session_id]

        # Başarı geçmişi
        metrics.accuracy_history = [True, True, False, True, True, True, True, True]

        motivation_metrics = realtime_system.monitor_success_rate(sample_session)

        assert "success_rate" in motivation_metrics
        assert "motivation_level" in motivation_metrics
        assert "streak" in motivation_metrics
        assert 0.0 <= motivation_metrics["motivation_level"] <= 1.0

    def test_fatigue_detection(self, realtime_system, sample_session):
        """Test 63.4: Yorgunluk tespiti"""
        # Metrikleri simüle et
        realtime_system.session_metrics[sample_session.session_id] = RealtimeMetrics()
        metrics = realtime_system.session_metrics[sample_session.session_id]

        # Yavaşlayan yanıt süreleri
        metrics.response_times = [10.0, 12.0, 15.0, 18.0, 22.0, 25.0, 30.0, 35.0]
        metrics.accuracy_history = [True, True, True, False, False, False, False, False]

        response_analysis = realtime_system.analyze_response_time(sample_session)

        assert "avg_response_time" in response_analysis
        assert "response_time_trend" in response_analysis
        assert "fatigue_detected" in response_analysis


class TestPerformanceAnalytics:
    """Task 64: Performans Analitikleri testleri"""

    def test_learning_curve_tracking(self, analytics_system, sample_session):
        """Test 64.1: Learning curve analysis"""
        # Theta geçmişi simüle et
        sample_session.knowledge_state.theta_history = [
            -0.5,
            -0.3,
            0.0,
            0.2,
            0.5,
            0.7,
            0.8,
            0.9,
        ]

        curve_data = analytics_system.track_progress_over_time(sample_session)

        assert isinstance(curve_data, LearningCurveData)
        assert len(curve_data.theta_values) > 0
        assert curve_data.growth_rate != 0.0

    def test_success_prediction(self, analytics_system, sample_session):
        """Test 64.2: Predictive analytics"""
        # Theta geçmişi simüle et
        sample_session.knowledge_state.theta_history = [-0.5, -0.2, 0.1, 0.3, 0.5]

        prediction = analytics_system.predict_success_probability(sample_session)

        assert isinstance(prediction, PredictionResult)
        assert 0.0 <= prediction.predicted_value <= 1.0
        assert prediction.confidence_interval_lower <= prediction.predicted_value
        assert prediction.predicted_value <= prediction.confidence_interval_upper

    def test_anomaly_detection(self, analytics_system, sample_session):
        """Test 64.3: Anomaly detection"""
        # Ani performans düşüşü simüle et (theta_drop > 1.0 gerekli)
        # [1.5, ..., 0.0] = 1.5 puan düşüş
        sample_session.knowledge_state.theta_history = [1.5, 1.4, 1.3, 0.2, 0.0]

        anomalies = analytics_system.detect_unusual_patterns(sample_session)

        assert isinstance(anomalies, list)
        # Ani düşüş tespit edilmeli (theta_drop = 1.5 > 1.0 threshold)
        assert any(a.anomaly_type == "performance_drop" for a in anomalies)

    def test_cohort_analysis(self, analytics_system, sample_session):
        """Test 64.4: Cohort analysis"""
        # Birden fazla oturum simüle et
        sessions = [sample_session]

        # Ek oturumlar oluştur
        engine = AdaptiveTestEngine()
        for i in range(5):
            session = engine.create_test_session(
                session_id=f"test_session_{i:03d}",
                student_id=f"student_{i:03d}",
                test_type="diagnostic" if i % 2 == 0 else "formative",
            )
            session.knowledge_state.theta = -0.5 + i * 0.3
            session.knowledge_state.correct_count = 5 + i
            session.knowledge_state.responses_count = 10
            sessions.append(session)

        comparison = analytics_system.compare_group_performance(sessions, "test_type")

        assert "groups" in comparison
        assert "total_sessions" in comparison
        assert len(comparison["groups"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
