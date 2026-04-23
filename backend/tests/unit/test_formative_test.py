import pytest

pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
Unit Tests for Formative Test
Task 61.2: Formative Test
"""

import pytest

from services.formative_test import FormativeTest, ImmediateFeedback


class TestFormativeTest:
    """Formative Test unit testleri"""

    @pytest.fixture
    def formative_test(self):
        """Formative test instance"""
        return FormativeTest()

    @pytest.fixture
    def sample_session_data(self):
        """Örnek test oturum verisi"""
        return {
            "session_id": "formative-session-1",
            "student_id": "student-123",
            "responses": [
                # Matematik - gelişen (3/5 = %60)
                {
                    "topic": "matematik",
                    "is_correct": False,
                    "response_time": 45,
                    "difficulty": "easy",
                },
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 50,
                    "difficulty": "easy",
                },
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 55,
                    "difficulty": "medium",
                },
                {
                    "topic": "matematik",
                    "is_correct": True,
                    "response_time": 60,
                    "difficulty": "medium",
                },
                {
                    "topic": "matematik",
                    "is_correct": False,
                    "response_time": 70,
                    "difficulty": "hard",
                },
                # Fizik - stabil (2/4 = %50)
                {
                    "topic": "fizik",
                    "is_correct": True,
                    "response_time": 40,
                    "difficulty": "easy",
                },
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 50,
                    "difficulty": "medium",
                },
                {
                    "topic": "fizik",
                    "is_correct": True,
                    "response_time": 55,
                    "difficulty": "medium",
                },
                {
                    "topic": "fizik",
                    "is_correct": False,
                    "response_time": 60,
                    "difficulty": "hard",
                },
            ],
            "previous_sessions": [
                {
                    "responses": [
                        {"topic": "matematik", "is_correct": False},
                        {"topic": "matematik", "is_correct": True},
                        {"topic": "matematik", "is_correct": False},
                        {"topic": "fizik", "is_correct": True},
                        {"topic": "fizik", "is_correct": True},
                    ]
                }
            ],
        }

    # ==================== Test Configuration ====================

    def test_get_configuration(self, formative_test):
        """REQ-49.38, REQ-49.39: Configuration testi"""
        config = formative_test.get_configuration()

        assert config.test_type == "formative"
        assert config.target_length == 20
        assert config.immediate_feedback is True  # REQ-49.39
        assert config.adaptive_difficulty is True  # REQ-49.38

    # ==================== Test Learning Progress Assessment ====================

    def test_assess_learning_progress(self, formative_test, sample_session_data):
        """REQ-49.37: Learning progress assessment testi"""
        progress = formative_test.assess_learning_progress(sample_session_data)

        assert len(progress) > 0

        # Matematik ve fizik için progress olmalı
        topics = [p.topic for p in progress]
        assert "matematik" in topics
        assert "fizik" in topics

        # Progress bilgileri doğru mu?
        for prog in progress:
            assert hasattr(prog, "initial_level")
            assert hasattr(prog, "current_level")
            assert hasattr(prog, "improvement")
            assert hasattr(prog, "trend")
            assert hasattr(prog, "mastery_percentage")

            assert 0 <= prog.current_level <= 1
            assert 0 <= prog.mastery_percentage <= 100

    def test_learning_progress_with_previous_sessions(
        self, formative_test, sample_session_data
    ):
        """Önceki oturumlarla ilerleme testi"""
        progress = formative_test.assess_learning_progress(
            sample_session_data, sample_session_data["previous_sessions"]
        )

        # Matematik için ilerleme kontrolü
        mat_progress = next((p for p in progress if p.topic == "matematik"), None)
        assert mat_progress is not None

        # Önceki oturumda %33 (1/3), şimdi %60 (3/5)
        # İyileşme olmalı
        assert mat_progress.improvement > 0

    def test_assess_learning_progress_empty(self, formative_test):
        """Boş veri ile progress testi"""
        session_data = {"responses": []}
        progress = formative_test.assess_learning_progress(session_data)

        assert progress == []

    # ==================== Test Adaptive Difficulty ====================

    def test_adjust_difficulty_increase(self, formative_test):
        """REQ-49.38: Zorluk artırma testi"""
        # %80 başarı -> zorluk artmalı
        recent_performance = [True, True, True, True, False]

        new_difficulty = formative_test.adjust_difficulty("easy", recent_performance)
        assert new_difficulty == "medium"

        new_difficulty = formative_test.adjust_difficulty("medium", recent_performance)
        assert new_difficulty == "hard"

    def test_adjust_difficulty_decrease(self, formative_test):
        """REQ-49.38: Zorluk azaltma testi"""
        # %20 başarı -> zorluk azalmalı
        recent_performance = [False, False, False, False, True]

        new_difficulty = formative_test.adjust_difficulty("hard", recent_performance)
        assert new_difficulty == "medium"

        new_difficulty = formative_test.adjust_difficulty("medium", recent_performance)
        assert new_difficulty == "easy"

    def test_adjust_difficulty_stable(self, formative_test):
        """REQ-49.38: Zorluk sabit kalma testi"""
        # %50 başarı -> zorluk sabit
        recent_performance = [True, False, True, False, True]

        new_difficulty = formative_test.adjust_difficulty("medium", recent_performance)
        assert new_difficulty == "medium"

    def test_adjust_difficulty_boundaries(self, formative_test):
        """Zorluk sınır değerleri testi"""
        # Easy'den daha düşük olamaz
        recent_performance = [False, False, False, False, False]
        new_difficulty = formative_test.adjust_difficulty("easy", recent_performance)
        assert new_difficulty == "easy"

        # Hard'dan daha yüksek olamaz
        recent_performance = [True, True, True, True, True]
        new_difficulty = formative_test.adjust_difficulty("hard", recent_performance)
        assert new_difficulty == "hard"

    # ==================== Test Immediate Feedback ====================

    def test_generate_immediate_feedback_correct(self, formative_test):
        """REQ-49.39: Doğru cevap için anında feedback testi"""
        question_data = {
            "question_id": "q1",
            "correct_answer": "A",
            "difficulty": "medium",
            "topic": "matematik",
        }

        feedback = formative_test.generate_immediate_feedback(
            question_data, student_answer="A", is_correct=True
        )

        assert isinstance(feedback, ImmediateFeedback)
        assert feedback.is_correct is True
        assert feedback.correct_answer == "A"
        assert feedback.student_answer == "A"
        assert len(feedback.explanation) > 0
        assert len(feedback.learning_tip) > 0
        assert feedback.next_difficulty_suggestion in ["easy", "medium", "hard"]

    def test_generate_immediate_feedback_incorrect(self, formative_test):
        """REQ-49.39: Yanlış cevap için anında feedback testi"""
        question_data = {
            "question_id": "q2",
            "correct_answer": "B",
            "difficulty": "hard",
            "topic": "fizik",
        }

        feedback = formative_test.generate_immediate_feedback(
            question_data, student_answer="C", is_correct=False
        )

        assert isinstance(feedback, ImmediateFeedback)
        assert feedback.is_correct is False
        assert feedback.correct_answer == "B"
        assert feedback.student_answer == "C"
        assert (
            "Doğru cevap" in feedback.explanation
            or "doğru" in feedback.explanation.lower()
        )
        assert len(feedback.learning_tip) > 0

    # ==================== Test Feedback Generation ====================

    def test_generate_feedback(self, formative_test, sample_session_data):
        """REQ-49.37, REQ-49.40: Feedback generation testi"""
        feedback = formative_test.generate_feedback(sample_session_data)

        assert "test_type" in feedback
        assert feedback["test_type"] == "formative"
        assert "learning_progress" in feedback
        assert "topic_analysis" in feedback

        # Learning progress detayları
        assert len(feedback["learning_progress"]) > 0
        for prog in feedback["learning_progress"]:
            assert "topic" in prog
            assert "current_level" in prog
            assert "improvement" in prog
            assert "trend" in prog

        # Topic analysis detayları
        assert len(feedback["topic_analysis"]) > 0
        for topic, analysis in feedback["topic_analysis"].items():
            assert "status" in analysis
            assert "mastery_percentage" in analysis
            assert "feedback_message" in analysis

    # ==================== Test Recommendations ====================

    def test_calculate_recommendations(self, formative_test, sample_session_data):
        """REQ-49.40: Öğrenme önerileri testi"""
        recommendations = formative_test.calculate_recommendations(sample_session_data)

        assert len(recommendations) > 0

        recommendations_text = "\n".join(recommendations)

        # Öneriler içerik kontrolü
        assert (
            "Formative Test" in recommendations_text
            or "formative" in recommendations_text.lower()
        )
        assert (
            "İlerleme" in recommendations_text
            or "ilerleme" in recommendations_text.lower()
        )

    def test_recommendations_empty_data(self, formative_test):
        """Boş veri ile öneriler testi"""
        session_data = {"responses": []}
        recommendations = formative_test.calculate_recommendations(session_data)

        assert len(recommendations) > 0
        assert any("veri" in r.lower() for r in recommendations)

    # ==================== Test Helper Methods ====================

    def test_get_initial_level_with_previous(self, formative_test):
        """Önceki oturumdan initial level testi"""
        previous_sessions = [
            {
                "responses": [
                    {"topic": "matematik", "is_correct": True},
                    {"topic": "matematik", "is_correct": False},
                    {"topic": "matematik", "is_correct": True},
                ]
            }
        ]

        level = formative_test._get_initial_level("matematik", previous_sessions)
        assert level == pytest.approx(2 / 3, rel=0.01)

    def test_get_initial_level_no_previous(self, formative_test):
        """Önceki oturum olmadan initial level testi"""
        level = formative_test._get_initial_level("matematik", None)
        assert level == 0.5  # Varsayılan

    def test_analyze_trend_improving(self, formative_test):
        """İyileşen trend testi"""
        # İlk yarı kötü, ikinci yarı iyi
        recent_correct = [False, False, True, True, True]
        trend = formative_test._analyze_trend(recent_correct)
        assert trend == "improving"

    def test_analyze_trend_declining(self, formative_test):
        """Kötüleşen trend testi"""
        # İlk yarı iyi, ikinci yarı kötü
        recent_correct = [True, True, True, False, False]
        trend = formative_test._analyze_trend(recent_correct)
        assert trend == "declining"

    def test_analyze_trend_stable(self, formative_test):
        """Stabil trend testi"""
        recent_correct = [True, False, True, False, True]
        trend = formative_test._analyze_trend(recent_correct)
        assert trend == "stable"

    def test_suggest_next_difficulty(self, formative_test):
        """Sonraki zorluk önerisi testi"""
        # Doğru cevap -> zorluk artır
        assert formative_test._suggest_next_difficulty("easy", True) == "medium"
        assert formative_test._suggest_next_difficulty("medium", True) == "hard"
        assert formative_test._suggest_next_difficulty("hard", True) == "hard"  # Max

        # Yanlış cevap -> zorluk azalt
        assert formative_test._suggest_next_difficulty("hard", False) == "medium"
        assert formative_test._suggest_next_difficulty("medium", False) == "easy"
        assert formative_test._suggest_next_difficulty("easy", False) == "easy"  # Min

    def test_get_mastery_status(self, formative_test):
        """Mastery durumu testi"""
        assert formative_test._get_mastery_status(85) == "mastered"
        assert formative_test._get_mastery_status(70) == "partial_mastery"
        assert formative_test._get_mastery_status(50) == "needs_work"

    # ==================== Integration Tests ====================

    def test_full_formative_workflow(self, formative_test, sample_session_data):
        """Tam formative test workflow testi"""
        # 1. Konfigürasyon
        config = formative_test.get_configuration()
        assert config.immediate_feedback is True
        assert config.adaptive_difficulty is True

        # 2. Öğrenme ilerlemesi değerlendirme
        progress = formative_test.assess_learning_progress(sample_session_data)
        assert len(progress) > 0

        # 3. Zorluk ayarlama
        recent_perf = [True, True, True, False, True]
        new_diff = formative_test.adjust_difficulty("medium", recent_perf)
        assert new_diff in ["easy", "medium", "hard"]

        # 4. Anında feedback
        question_data = {
            "question_id": "q1",
            "correct_answer": "A",
            "difficulty": "medium",
            "topic": "matematik",
        }
        feedback = formative_test.generate_immediate_feedback(question_data, "A", True)
        assert feedback.is_correct is True

        # 5. Genel feedback
        general_feedback = formative_test.generate_feedback(sample_session_data)
        assert "learning_progress" in general_feedback

        # 6. Öneriler
        recommendations = formative_test.calculate_recommendations(sample_session_data)
        assert len(recommendations) > 0
