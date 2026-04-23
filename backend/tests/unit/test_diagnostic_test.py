import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Unit Tests for Diagnostic Test
Task 61.1: Diagnostic Test
"""

import pytest

from services.diagnostic_test import DiagnosticTest


class TestDiagnosticTest:
    """Diagnostic Test unit testleri"""

    @pytest.fixture
    def diagnostic_test(self):
        """Diagnostic test instance"""
        return DiagnosticTest()

    @pytest.fixture
    def sample_session_data(self):
        """Örnek test oturum verisi"""
        return {
            "session_id": "test-session-1",
            "student_id": "student-123",
            "responses": [
                # Matematik - zayıf (2/5 = %40)
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 45,
                    "difficulty": "easy",
                },
                {
                    "topic": "matematik",
                    "is_correct": False,
                    "response_time": 90,
                    "difficulty": "medium",
                },
                {
                    "topic": "matematik",
                    "is_correct": False,
                    "response_time": 120,
                    "difficulty": "medium",
                },
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 60,
                    "difficulty": "easy",
                },
                {
                    "topic": "matematik",
                    "is_correct": False,
                    "response_time": 150,
                    "difficulty": "hard",
                },
                # Fizik - çok zayıf (1/5 = %20)
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 100,
                    "difficulty": "easy",
                },
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 110,
                    "difficulty": "medium",
                },
                {
                    "topic": "fizik",
                    "is_correct": True,
                    "response_time": 80,
                    "difficulty": "easy",
                },
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 130,
                    "difficulty": "medium",
                },
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 140,
                    "difficulty": "hard",
                },
                # Türkçe - iyi (4/5 = %80)
                {
                    "topic": "turkce",
                    "is_correct": True,
                    "response_time": 40,
                    "difficulty": "easy",
                },
                {
                    "topic": "turkce",
                    "is_correct": True,
                    "response_time": 50,
                    "difficulty": "medium",
                },
                {
                    "topic": "turkce",
                    "is_correct": True,
                    "response_time": 55,
                    "difficulty": "medium",
                },
                {
                    "topic": "turkce",
                    "is_correct": False,
                    "response_time": 70,
                    "difficulty": "hard",
                },
                {
                    "topic": "turkce",
                    "is_correct": True,
                    "response_time": 45,
                    "difficulty": "easy",
                },
                # Tarih - orta (3/5 = %60)
                {
                    "topic": "tarih",
                    "is_correct": True,
                    "response_time": 50,
                    "difficulty": "easy",
                },
                {
                    "topic": "tarih",
                    "is_correct": True,
                    "response_time": 60,
                    "difficulty": "medium",
                },
                {
                    "topic": "tarih",
                    "is_correct": False,
                    "response_time": 80,
                    "difficulty": "medium",
                },
                {
                    "topic": "tarih",
                    "is_correct": True,
                    "response_time": 55,
                    "difficulty": "easy",
                },
                {
                    "topic": "tarih",
                    "is_correct": False,
                    "response_time": 90,
                    "difficulty": "hard",
                },
            ],
        }

    # ==================== Test Configuration ====================

    def test_get_configuration(self, diagnostic_test):
        """REQ-49.34: Comprehensive topic coverage testi"""
        config = diagnostic_test.get_configuration()

        assert config.test_type == "diagnostic"
        assert config.target_length == 50
        assert config.min_length == 30
        assert config.max_length == 50
        assert config.adaptive_difficulty is True
        assert config.immediate_feedback is False

        # Tüm konuları kapsama kontrolü (REQ-49.34)
        assert config.content_constraints is not None
        assert len(config.content_constraints) >= 10  # En az 10 konu
        assert "matematik" in config.content_constraints
        assert "fizik" in config.content_constraints
        assert "turkce" in config.content_constraints

    # ==================== Test Weak Area Identification ====================

    def test_identify_weak_areas(self, diagnostic_test, sample_session_data):
        """REQ-49.33: Weakness identification focus testi"""
        weak_areas = diagnostic_test.identify_weak_areas(sample_session_data)

        # Zayıf alanlar tespit edilmeli
        assert len(weak_areas) > 0

        # Fizik ve matematik zayıf olmalı (%60 altı)
        weak_topics = [wa.topic for wa in weak_areas]
        assert "fizik" in weak_topics
        assert "matematik" in weak_topics

        # Türkçe zayıf olmamalı (%80 başarı)
        assert "turkce" not in weak_topics

        # Öncelik sıralaması kontrolü (en zayıf en başta)
        if len(weak_areas) >= 2:
            # Fizik (%20) matematik'ten (%40) daha zayıf, önce gelmeli
            fizik_index = next(
                i for i, wa in enumerate(weak_areas) if wa.topic == "fizik"
            )
            matematik_index = next(
                i for i, wa in enumerate(weak_areas) if wa.topic == "matematik"
            )
            assert fizik_index < matematik_index

    def test_weak_area_severity(self, diagnostic_test, sample_session_data):
        """Zayıflık şiddeti testi"""
        weak_areas = diagnostic_test.identify_weak_areas(sample_session_data)

        for wa in weak_areas:
            # Severity doğru atanmış mı?
            if wa.accuracy < 0.3:
                assert wa.severity == "critical"
            elif wa.accuracy < 0.45:
                assert wa.severity == "high"
            else:
                assert wa.severity == "medium"

    def test_identify_weak_areas_empty_responses(self, diagnostic_test):
        """Boş yanıt listesi testi"""
        session_data = {"responses": []}
        weak_areas = diagnostic_test.identify_weak_areas(session_data)

        assert weak_areas == []

    # ==================== Test Feedback Generation ====================

    def test_generate_feedback(self, diagnostic_test, sample_session_data):
        """REQ-49.35: Detailed feedback generation testi"""
        feedback = diagnostic_test.generate_feedback(sample_session_data)

        # Temel yapı kontrolü
        assert "test_type" in feedback
        assert feedback["test_type"] == "diagnostic"
        assert "weak_areas" in feedback
        assert "topic_analysis" in feedback
        assert "overall_assessment" in feedback

        # Zayıf alanlar detayları
        assert len(feedback["weak_areas"]) > 0
        for wa in feedback["weak_areas"]:
            assert "topic" in wa
            assert "accuracy" in wa
            assert "severity" in wa
            assert "priority" in wa

        # Konu analizi detayları
        assert len(feedback["topic_analysis"]) > 0
        for topic, analysis in feedback["topic_analysis"].items():
            assert "accuracy" in analysis
            assert "status" in analysis
            assert "feedback_message" in analysis
            assert "improvement_areas" in analysis

    def test_feedback_topic_analysis(self, diagnostic_test, sample_session_data):
        """Konu bazlı analiz testi"""
        feedback = diagnostic_test.generate_feedback(sample_session_data)
        topic_analysis = feedback["topic_analysis"]

        # Matematik analizi
        assert "matematik" in topic_analysis
        mat_analysis = topic_analysis["matematik"]
        assert mat_analysis["accuracy"] == 0.4  # 2/5
        assert mat_analysis["status"] == "needs_improvement"

        # Fizik analizi
        assert "fizik" in topic_analysis
        fiz_analysis = topic_analysis["fizik"]
        assert fiz_analysis["accuracy"] == 0.2  # 1/5
        assert fiz_analysis["status"] == "critical"

        # Türkçe analizi
        assert "turkce" in topic_analysis
        tur_analysis = topic_analysis["turkce"]
        assert tur_analysis["accuracy"] == 0.8  # 4/5
        assert tur_analysis["status"] == "excellent"

    # ==================== Test Recommendations ====================

    def test_calculate_recommendations(self, diagnostic_test, sample_session_data):
        """REQ-49.36: Özel çalışma planı önerme testi"""
        recommendations = diagnostic_test.calculate_recommendations(sample_session_data)

        # Öneriler oluşturulmalı
        assert len(recommendations) > 0

        # Çalışma planı içermeli
        recommendations_text = "\n".join(recommendations)
        assert (
            "Çalışma Planı" in recommendations_text
            or "çalışma" in recommendations_text.lower()
        )

        # Zayıf alanlar için öneriler içermeli
        assert (
            "fizik" in recommendations_text.lower()
            or "matematik" in recommendations_text.lower()
        )

    def test_recommendations_no_weak_areas(self, diagnostic_test):
        """Zayıf alan olmadığında öneriler testi"""
        # Tüm sorular doğru
        perfect_session = {
            "responses": [
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 45,
                    "difficulty": "easy",
                },
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 50,
                    "difficulty": "medium",
                },
                {
                    "topic": "fizik",
                    "is_correct": True,
                    "response_time": 40,
                    "difficulty": "easy",
                },
                {
                    "topic": "fizik",
                    "is_correct": True,
                    "response_time": 45,
                    "difficulty": "medium",
                },
            ]
        }

        recommendations = diagnostic_test.calculate_recommendations(perfect_session)

        assert len(recommendations) > 0
        recommendations_text = "\n".join(recommendations)
        assert (
            "Tebrikler" in recommendations_text
            or "tebrikler" in recommendations_text.lower()
        )

    # ==================== Test Helper Methods ====================

    def test_determine_severity(self, diagnostic_test):
        """Severity belirleme testi"""
        assert diagnostic_test._determine_severity(0.2) == "critical"
        assert diagnostic_test._determine_severity(0.35) == "high"
        assert diagnostic_test._determine_severity(0.5) == "medium"

    def test_calculate_priority(self, diagnostic_test):
        """Öncelik hesaplama testi"""
        # Düşük accuracy = yüksek öncelik (düşük sayı)
        priority_low_acc = diagnostic_test._calculate_priority(0.2, 5)
        priority_high_acc = diagnostic_test._calculate_priority(0.6, 5)

        assert priority_low_acc < priority_high_acc

        # Daha fazla soru = daha güvenilir = daha yüksek öncelik
        priority_few_q = diagnostic_test._calculate_priority(0.4, 3)
        priority_many_q = diagnostic_test._calculate_priority(0.4, 10)

        assert priority_many_q < priority_few_q

    def test_get_performance_status(self, diagnostic_test):
        """Performans durumu testi"""
        assert diagnostic_test._get_performance_status(0.85) == "excellent"
        assert diagnostic_test._get_performance_status(0.7) == "good"
        assert diagnostic_test._get_performance_status(0.5) == "needs_improvement"
        assert diagnostic_test._get_performance_status(0.3) == "critical"

    def test_generate_topic_feedback_message(self, diagnostic_test):
        """Konu feedback mesajı testi"""
        # Mükemmel performans
        msg_excellent = diagnostic_test._generate_topic_feedback_message(
            "matematik", 0.85
        )
        assert "başarılı" in msg_excellent.lower()

        # İyi performans
        msg_good = diagnostic_test._generate_topic_feedback_message("fizik", 0.7)
        assert "iyi" in msg_good.lower()

        # Gelişmeli
        msg_needs_improvement = diagnostic_test._generate_topic_feedback_message(
            "kimya", 0.5
        )
        assert "gelişme" in msg_needs_improvement.lower()

        # Kritik
        msg_critical = diagnostic_test._generate_topic_feedback_message("biyoloji", 0.3)
        assert "ciddi" in msg_critical.lower() or "acil" in msg_critical.lower()

    def test_identify_improvement_areas(self, diagnostic_test):
        """İyileştirme alanları testi"""
        analysis = {
            "difficulty_distribution": {"easy": 2, "medium": 2, "hard": 1},
            "avg_response_time": 150,  # Yavaş
            "questions": [
                {"difficulty": "easy", "is_correct": False},
                {"difficulty": "easy", "is_correct": False},
                {"difficulty": "medium", "is_correct": True},
                {"difficulty": "medium", "is_correct": False},
            ],
        }

        areas = diagnostic_test._identify_improvement_areas("matematik", analysis)

        assert len(areas) > 0
        areas_text = " ".join(areas).lower()

        # Temel kavramlar zayıf
        assert "temel" in areas_text or "kavram" in areas_text

        # Yavaş yanıt
        assert "hız" in areas_text or "zaman" in areas_text

    def test_generate_overall_assessment(self, diagnostic_test, sample_session_data):
        """Genel değerlendirme testi"""
        weak_areas = diagnostic_test.identify_weak_areas(sample_session_data)
        feedback = diagnostic_test.generate_feedback(sample_session_data)
        topic_analysis = feedback["topic_analysis"]

        assessment = diagnostic_test._generate_overall_assessment(
            sample_session_data, weak_areas, topic_analysis
        )

        assert len(assessment) > 0
        assert isinstance(assessment, str)

        # Başarı oranı içermeli
        assert "%" in assessment

    def test_get_study_strategy(self, diagnostic_test):
        """Çalışma stratejisi testi"""
        # Çok zayıf
        strategy_critical = diagnostic_test._get_study_strategy("matematik", 0.25)
        assert (
            "video" in strategy_critical.lower() or "temel" in strategy_critical.lower()
        )

        # Zayıf
        strategy_weak = diagnostic_test._get_study_strategy("fizik", 0.4)
        assert "formül" in strategy_weak.lower() or "örnek" in strategy_weak.lower()

        # Orta
        strategy_medium = diagnostic_test._get_study_strategy("kimya", 0.55)
        assert "orta" in strategy_medium.lower() or "hız" in strategy_medium.lower()

    # ==================== Integration Tests ====================

    def test_full_diagnostic_workflow(self, diagnostic_test, sample_session_data):
        """Tam diagnostic test workflow testi"""
        # 1. Konfigürasyon al
        config = diagnostic_test.get_configuration()
        assert config.test_type == "diagnostic"

        # 2. Zayıf alanları tespit et
        weak_areas = diagnostic_test.identify_weak_areas(sample_session_data)
        assert len(weak_areas) > 0

        # 3. Feedback oluştur
        feedback = diagnostic_test.generate_feedback(sample_session_data)
        assert "weak_areas" in feedback
        assert "topic_analysis" in feedback

        # 4. Öneriler oluştur
        recommendations = diagnostic_test.calculate_recommendations(sample_session_data)
        assert len(recommendations) > 0

        # Tüm bileşenler tutarlı olmalı
        assert len(feedback["weak_areas"]) == len(weak_areas)
