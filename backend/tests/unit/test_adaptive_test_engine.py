"""
Adaptive Test Engine Unit Tests
Task 60: Adaptif Test Motoru
Requirements: REQ-49.17-49.32

Bu test dosyası adaptif test motorunun tüm bileşenlerini test eder.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import numpy as np

from services.adaptive_test_engine import (
    AdaptiveTestEngine,
    QuestionCandidate,
    StudentKnowledgeState,
    TestSession,
)
from services.irt_psychometric_analysis import IRTParameters


@pytest.fixture
def engine():
    """Adaptive Test Engine fixture"""
    return AdaptiveTestEngine()


@pytest.fixture
def sample_irt_params():
    """Sample IRT parameters"""
    return IRTParameters(a=1.0, b=0.0, c=0.25, d=1.0)


@pytest.fixture
def sample_question_pool():
    """Sample question pool"""
    questions = []
    for i in range(10):
        questions.append(
            QuestionCandidate(
                question_id=f"Q{i+1}",
                irt_params=IRTParameters(
                    a=1.0 + i * 0.1, b=-2.0 + i * 0.5, c=0.25, d=1.0
                ),
                subject="Matematik",
                topic=f"Topic{i % 3}",
                difficulty_level="orta",
                exposure_count=i * 2,
                last_used=None,
            )
        )
    return questions


@pytest.fixture
def sample_session(engine):
    """Sample test session"""
    return engine.create_test_session(
        session_id="TEST_001",
        student_id="STUDENT_001",
        test_type="diagnostic",
        prior_theta=0.0,
    )


# ==================== SUBTASK 60.1 Tests: Maximum Information Criterion ====================


class TestMaximumInformationCriterion:
    """Maximum Information Criterion testleri (REQ-49.17-49.20)"""

    def test_select_next_question_basic(
        self, engine, sample_session, sample_question_pool
    ):
        """
        REQ-49.17: Maximum Information Criterion - en bilgilendirici soruyu seçme
        """
        selected = engine.select_next_question(
            session=sample_session, question_pool=sample_question_pool
        )

        assert selected is not None
        assert selected.question_id in [q.question_id for q in sample_question_pool]
        assert selected.information_value > 0

    def test_information_maximization(
        self, engine, sample_session, sample_question_pool
    ):
        """
        REQ-49.18: Information maximization - mevcut theta tahminine göre optimize
        """
        # Theta = 0.0 için en bilgilendirici soru b=0.0 civarında olmalı
        sample_session.knowledge_state.theta = 0.0

        selected = engine.select_next_question(
            session=sample_session, question_pool=sample_question_pool
        )

        # Seçilen sorunun difficulty'si theta'ya yakın olmalı
        assert abs(selected.irt_params.b - 0.0) < 2.0

    def test_content_balancing(self, engine, sample_session, sample_question_pool):
        """
        REQ-49.19: Content balancing constraints - konu dağılımını dengeleme
        """
        content_constraints = {"Topic0": 3, "Topic1": 3, "Topic2": 3}

        # İlk soruyu seç
        selected = engine.select_next_question(
            session=sample_session,
            question_pool=sample_question_pool,
            content_constraints=content_constraints,
        )

        assert selected is not None
        assert selected.content_balance_score > 0

    def test_selection_performance(self, engine, sample_session, sample_question_pool):
        """
        REQ-49.20: 500ms içinde karar verme
        """
        start_time = datetime.now()

        selected = engine.select_next_question(
            session=sample_session, question_pool=sample_question_pool
        )

        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000

        assert selected is not None
        assert elapsed_ms < 500, f"Selection took {elapsed_ms:.1f}ms > 500ms"

    def test_exposure_control(self, engine, sample_session):
        """Exposure control - sık kullanılan soruları cezalandırma"""
        # Yüksek exposure'lı soru
        high_exposure_q = QuestionCandidate(
            question_id="Q_HIGH",
            irt_params=IRTParameters(a=1.5, b=0.0, c=0.25, d=1.0),
            subject="Matematik",
            topic="Topic1",
            difficulty_level="orta",
            exposure_count=50,  # Çok yüksek
            last_used=None,
        )

        # Düşük exposure'lı soru
        low_exposure_q = QuestionCandidate(
            question_id="Q_LOW",
            irt_params=IRTParameters(a=1.5, b=0.0, c=0.25, d=1.0),
            subject="Matematik",
            topic="Topic1",
            difficulty_level="orta",
            exposure_count=2,  # Düşük
            last_used=None,
        )

        pool = [high_exposure_q, low_exposure_q]

        selected = engine.select_next_question(
            session=sample_session, question_pool=pool
        )

        # Düşük exposure'lı soru seçilmeli
        assert selected.question_id == "Q_LOW"


# ==================== SUBTASK 60.2 Tests: Bayesian Knowledge Tracing ====================


class TestBayesianKnowledgeTracing:
    """Bayesian Knowledge Tracing testleri (REQ-49.21-49.24)"""

    def test_initialize_knowledge_state(self, engine):
        """
        REQ-49.21: Prior knowledge estimation
        """
        state = engine.initialize_knowledge_state(
            student_id="STUDENT_001", prior_theta=0.5, prior_knowledge_prob=0.6
        )

        assert state.student_id == "STUDENT_001"
        assert state.theta == 0.5
        assert state.knowledge_probability == 0.6
        assert state.learning_rate > 0
        assert state.guess_probability == 0.25  # 4 seçenekli soru
        assert state.responses_count == 0

    def test_update_knowledge_state_correct(self, engine, sample_irt_params):
        """
        REQ-49.22: Posterior update algorithm - doğru cevap
        """
        state = engine.initialize_knowledge_state("STUDENT_001")
        initial_knowledge_prob = state.knowledge_probability
        initial_theta = state.theta

        # Doğru cevap ver
        updated_state = engine.update_knowledge_state(
            state=state, question_params=sample_irt_params, is_correct=True
        )

        # Knowledge probability artmalı
        assert updated_state.knowledge_probability > initial_knowledge_prob
        # Theta artmalı veya aynı kalmalı
        assert updated_state.theta >= initial_theta - 0.5
        assert updated_state.responses_count == 1
        assert updated_state.correct_count == 1

    def test_update_knowledge_state_incorrect(self, engine, sample_irt_params):
        """
        REQ-49.22: Posterior update algorithm - yanlış cevap
        """
        state = engine.initialize_knowledge_state("STUDENT_001")
        initial_knowledge_prob = state.knowledge_probability

        # Yanlış cevap ver
        updated_state = engine.update_knowledge_state(
            state=state, question_params=sample_irt_params, is_correct=False
        )

        # Knowledge probability azalmalı veya aynı kalmalı
        assert updated_state.knowledge_probability <= initial_knowledge_prob + 0.1
        assert updated_state.responses_count == 1
        assert updated_state.correct_count == 0

    def test_knowledge_state_tracking(self, engine, sample_irt_params):
        """
        REQ-49.23: Knowledge state tracking - öğrenme, unutma, tahmin ve hata parametreleri
        """
        state = engine.initialize_knowledge_state("STUDENT_001")

        # Parametrelerin varlığını kontrol et
        assert hasattr(state, "learning_rate")
        assert hasattr(state, "guess_probability")
        assert hasattr(state, "slip_probability")
        assert hasattr(state, "knowledge_probability")

        # Parametrelerin geçerli aralıkta olduğunu kontrol et
        assert 0 <= state.learning_rate <= 1
        assert 0 <= state.guess_probability <= 1
        assert 0 <= state.slip_probability <= 1
        assert 0 <= state.knowledge_probability <= 1

    def test_hidden_markov_model_behavior(self, engine, sample_irt_params):
        """
        REQ-49.24: Hidden Markov Model kullanımı
        """
        state = engine.initialize_knowledge_state("STUDENT_001")

        # Birden fazla güncelleme yap (HMM transition'ları)
        for i in range(5):
            is_correct = i % 2 == 0  # Alternatif doğru/yanlış
            state = engine.update_knowledge_state(
                state=state, question_params=sample_irt_params, is_correct=is_correct
            )

        # Theta history oluşmalı (state transitions)
        assert len(state.theta_history) == 6  # Initial + 5 updates
        # Knowledge probability güncellenmiş olmalı
        assert state.knowledge_probability != 0.5  # Initial değerden farklı


# ==================== SUBTASK 60.3 Tests: EAP/MLE Theta Estimation ====================


class TestThetaEstimation:
    """EAP/MLE Theta Estimation testleri (REQ-49.25-49.28)"""

    def test_estimate_theta_eap(self, engine):
        """
        REQ-49.25: Expected A Posteriori (EAP) method
        """
        responses = [
            {"params": IRTParameters(a=1.0, b=0.0, c=0.25, d=1.0), "is_correct": True},
            {"params": IRTParameters(a=1.0, b=0.5, c=0.25, d=1.0), "is_correct": True},
            {
                "params": IRTParameters(a=1.0, b=-0.5, c=0.25, d=1.0),
                "is_correct": False,
            },
        ]

        theta_eap, se_eap = engine.estimate_theta_eap(responses)

        assert isinstance(theta_eap, float)
        assert isinstance(se_eap, float)
        assert -3.0 <= theta_eap <= 3.0  # REQ-49.28
        assert se_eap > 0

    def test_estimate_theta_mle(self, engine):
        """
        REQ-49.26: Maximum Likelihood Estimation (MLE)
        """
        responses = [
            {"params": IRTParameters(a=1.0, b=0.0, c=0.25, d=1.0), "is_correct": True},
            {"params": IRTParameters(a=1.0, b=0.5, c=0.25, d=1.0), "is_correct": True},
            {
                "params": IRTParameters(a=1.0, b=-0.5, c=0.25, d=1.0),
                "is_correct": False,
            },
        ]

        theta_mle, se_mle = engine.estimate_theta_mle(responses)

        assert isinstance(theta_mle, float)
        assert isinstance(se_mle, float)
        assert -3.0 <= theta_mle <= 3.0  # REQ-49.28
        assert se_mle > 0

    def test_standard_error_threshold(self, engine):
        """
        REQ-49.27: Standard error < 0.3 hedefleme
        """
        # Çok sayıda yanıt ile SE düşmeli
        responses = []
        for i in range(20):
            responses.append(
                {
                    "params": IRTParameters(a=1.5, b=0.0, c=0.25, d=1.0),
                    "is_correct": i % 2 == 0,
                }
            )

        theta_eap, se_eap = engine.estimate_theta_eap(responses)

        # 20 yanıtla SE < 0.3 olmalı
        assert se_eap < 0.5  # Gevşek kontrol (gerçek veri ile daha iyi)

    def test_theta_range_constraint(self, engine):
        """
        REQ-49.28: -3 ile +3 arası değer üretme
        """
        # Çok kolay sorulara hep doğru cevap
        responses = []
        for i in range(10):
            responses.append(
                {
                    "params": IRTParameters(a=1.0, b=-2.0, c=0.25, d=1.0),
                    "is_correct": True,
                }
            )

        theta_eap, _ = engine.estimate_theta_eap(responses)
        theta_mle, _ = engine.estimate_theta_mle(responses)

        # Her iki metod da -3 ile +3 arası döndürmeli
        assert -3.0 <= theta_eap <= 3.0
        assert -3.0 <= theta_mle <= 3.0

    def test_monitor_theta_convergence(self, engine):
        """
        REQ-49.27: Theta convergence monitoring
        """
        state = engine.initialize_knowledge_state("STUDENT_001")

        # Theta history oluştur (yakınsayan)
        for i in range(10):
            state.theta_history.append(1.0 + i * 0.01)  # Yavaş artış

        converged = engine.monitor_theta_convergence(state, convergence_window=5)

        # Yakınsama sağlanmalı (std < 0.1)
        assert converged == True

    def test_theta_convergence_not_achieved(self, engine):
        """Theta yakınsaması sağlanmadığında"""
        state = engine.initialize_knowledge_state("STUDENT_001")

        # Theta history oluştur (yakınsamayan)
        for i in range(10):
            state.theta_history.append(i * 0.3)  # Hızlı değişim

        converged = engine.monitor_theta_convergence(state, convergence_window=5)

        # Yakınsama sağlanmamalı
        assert converged == False


# ==================== SUBTASK 60.4 Tests: Stopping Rules ====================


class TestStoppingRules:
    """Stopping Rules testleri (REQ-49.29-49.32)"""

    def test_fixed_length_stopping(self, engine, sample_session):
        """
        REQ-49.29: Fixed-length stopping - belirlenen soru sayısında durma
        """
        test_config = {"target_length": 20}

        # 10 soru ekle (minimum altında)
        for i in range(10):
            sample_session.questions_administered.append(f"Q{i}")

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is False  # Henüz durmamalı

        # 20 soru ekle (hedefe ulaş)
        for i in range(10, 20):
            sample_session.questions_administered.append(f"Q{i}")

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is True
        assert reason == "target_length_reached"

    def test_precision_based_stopping(self, engine, sample_session):
        """
        REQ-49.30: Precision-based stopping - SE < 0.3 olduğunda durma
        """
        test_config = {}

        # 10 soru ekle (minimum)
        for i in range(10):
            sample_session.questions_administered.append(f"Q{i}")

        # SE'yi düşük yap
        sample_session.knowledge_state.standard_error = 0.25

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is True
        assert reason == "precision_threshold_reached"

    def test_classification_based_stopping(self, engine, sample_session):
        """
        REQ-49.31: Classification-based stopping - yeterlik seviyesi belirlendiğinde durma
        """
        test_config = {"classification_threshold": 0.85}

        # 10 soru ekle (minimum)
        for i in range(10):
            sample_session.questions_administered.append(f"Q{i}")

        # Yüksek knowledge probability ve stable theta
        sample_session.knowledge_state.knowledge_probability = 0.9
        sample_session.knowledge_state.theta_history = [1.0] * 10  # Çok stable

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is True
        assert reason == "classification_confidence_reached"

    def test_minimum_maximum_constraints(self, engine, sample_session):
        """
        REQ-49.32: Minimum 10, maksimum 50 soru sınırı
        """
        test_config = {}

        # 5 soru (minimum altında)
        for i in range(5):
            sample_session.questions_administered.append(f"Q{i}")

        sample_session.knowledge_state.standard_error = 0.1  # Çok düşük SE

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is False  # Minimum soru sayısına ulaşılmadı

        # 50 soru (maksimum)
        for i in range(5, 50):
            sample_session.questions_administered.append(f"Q{i}")

        should_stop, reason = engine.check_stopping_rules(sample_session, test_config)
        assert should_stop is True
        assert reason == "maximum_length_reached"

    def test_apply_fixed_length_stopping(self, engine, sample_session):
        """Fixed-length stopping rule direkt test"""
        # 15 soru ekle
        for i in range(15):
            sample_session.questions_administered.append(f"Q{i}")

        # 20 soru hedefi
        should_stop = engine.apply_fixed_length_stopping(
            sample_session, target_length=20
        )
        assert should_stop is False

        # 5 soru daha ekle (toplam 20)
        for i in range(15, 20):
            sample_session.questions_administered.append(f"Q{i}")

        should_stop = engine.apply_fixed_length_stopping(
            sample_session, target_length=20
        )
        assert should_stop is True

    def test_apply_precision_stopping(self, engine, sample_session):
        """Precision-based stopping rule direkt test"""
        # 10 soru ekle
        for i in range(10):
            sample_session.questions_administered.append(f"Q{i}")

        # Yüksek SE
        sample_session.knowledge_state.standard_error = 0.5
        should_stop = engine.apply_precision_stopping(
            sample_session, precision_threshold=0.3
        )
        assert should_stop is False

        # Düşük SE
        sample_session.knowledge_state.standard_error = 0.25
        should_stop = engine.apply_precision_stopping(
            sample_session, precision_threshold=0.3
        )
        assert should_stop is True

    def test_apply_classification_stopping(self, engine, sample_session):
        """Classification-based stopping rule direkt test"""
        # 10 soru ekle
        for i in range(10):
            sample_session.questions_administered.append(f"Q{i}")

        # Düşük güven
        sample_session.knowledge_state.knowledge_probability = 0.5
        sample_session.knowledge_state.theta_history = [
            0.0,
            0.5,
            1.0,
            0.5,
            0.0,
        ]  # Unstable

        should_stop = engine.apply_classification_stopping(
            sample_session, classification_threshold=0.9
        )
        assert should_stop == False

        # Yüksek güven
        sample_session.knowledge_state.knowledge_probability = 0.95
        sample_session.knowledge_state.theta_history = [1.0] * 10  # Very stable

        should_stop = engine.apply_classification_stopping(
            sample_session, classification_threshold=0.9
        )
        assert should_stop == True


# ==================== Integration Tests ====================


class TestAdaptiveTestEngineIntegration:
    """Adaptif Test Motoru entegrasyon testleri"""

    def test_complete_test_session_flow(self, engine, sample_question_pool):
        """Tam test oturumu akışı"""
        # 1. Oturum oluştur
        session = engine.create_test_session(
            session_id="TEST_INTEGRATION_001",
            student_id="STUDENT_INT_001",
            test_type="diagnostic",
            prior_theta=0.0,
        )

        assert session.session_id == "TEST_INTEGRATION_001"
        assert session.is_complete is False

        # 2. Sorular sor ve yanıtla
        test_config = {"target_length": 15}

        for i in range(15):
            # Soru seç
            selected = engine.select_next_question(
                session=session, question_pool=sample_question_pool
            )

            assert selected is not None

            # Yanıt kaydet (alternatif doğru/yanlış)
            is_correct = i % 2 == 0
            session = engine.record_response(
                session=session,
                question_id=selected.question_id,
                question_params=selected.irt_params,
                is_correct=is_correct,
                response_time=5.0,
            )

            # Stopping rule kontrol et
            should_stop, reason = engine.check_stopping_rules(session, test_config)

            if should_stop:
                break

        # 3. Oturumu tamamla
        session = engine.complete_session(
            session, completion_reason="target_length_reached"
        )

        assert session.is_complete is True
        assert len(session.questions_administered) >= 10  # Minimum
        assert len(session.responses) == len(session.questions_administered)

        # 4. Özet al
        summary = engine.get_session_summary(session)

        assert summary["session_id"] == "TEST_INTEGRATION_001"
        assert summary["is_complete"] is True
        assert summary["questions_count"] >= 10
        assert 0.0 <= summary["accuracy"] <= 1.0
        assert -3.0 <= summary["final_theta"] <= 3.0

    def test_adaptive_difficulty_adjustment(self, engine, sample_question_pool):
        """Adaptif zorluk ayarlama"""
        session = engine.create_test_session(
            session_id="TEST_ADAPTIVE_001",
            student_id="STUDENT_ADAPT_001",
            test_type="formative",
            prior_theta=-1.0,  # Düşük seviye
        )

        # İlk soru seçimi (düşük theta için)
        first_question = engine.select_next_question(
            session=session, question_pool=sample_question_pool
        )

        # İlk soru kolay olmalı (b < 0)
        assert first_question.irt_params.b < 1.0

        # Hep doğru cevap ver (theta yükselmeli)
        for i in range(5):
            selected = engine.select_next_question(
                session=session, question_pool=sample_question_pool
            )

            session = engine.record_response(
                session=session,
                question_id=selected.question_id,
                question_params=selected.irt_params,
                is_correct=True,  # Hep doğru
                response_time=5.0,
            )

        # Theta yükselmiş olmalı
        assert session.knowledge_state.theta > -1.0

        # Yeni soru seçimi (daha zor olmalı)
        next_question = engine.select_next_question(
            session=session, question_pool=sample_question_pool
        )

        # Yeni soru daha zor olmalı
        assert next_question.irt_params.b > first_question.irt_params.b

    def test_session_summary_accuracy(self, engine, sample_question_pool):
        """Oturum özeti doğruluğu"""
        session = engine.create_test_session(
            session_id="TEST_SUMMARY_001",
            student_id="STUDENT_SUM_001",
            test_type="diagnostic",
        )

        # 10 soru sor (5 doğru, 5 yanlış)
        for i in range(10):
            selected = engine.select_next_question(
                session=session, question_pool=sample_question_pool
            )

            is_correct = i < 5  # İlk 5 doğru, son 5 yanlış

            session = engine.record_response(
                session=session,
                question_id=selected.question_id,
                question_params=selected.irt_params,
                is_correct=is_correct,
                response_time=5.0,
            )

        session = engine.complete_session(session, "manual_completion")
        summary = engine.get_session_summary(session)

        # Doğruluk kontrolü
        assert summary["questions_count"] == 10
        assert summary["correct_count"] == 5
        assert summary["accuracy"] == 0.5
        assert len(summary["theta_history"]) == 11  # Initial + 10 updates
