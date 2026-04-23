"""
Öğrenme Modelleri için Testler
Coverage target: learning_models.py (201 statements, 0% → 80%+)
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add backend to path and import directly to avoid SQLAlchemy metadata conflicts
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from models.learning_models import (
    AgentMessage,
    BionicReadingResult,
    BlackboardEntry,
    CulturalContext,
    FelderDimension,
    Flashcard,
    FSRSCard,
    HybridLearningProfile,
    LearningSession,
    LearningStyleType,
    MorphologyAnalysis,
    Question,
    SimplificationLevel,
    Student,
    TurkishZPDRange,
    create_sample_hybrid_profile,
    create_sample_student,
    create_sample_zpd_range,
)


class TestEnums:
    """Enum değerlerini test et"""

    def test_learning_style_type_enum(self):
        """LearningStyleType enum değerleri"""
        assert LearningStyleType.VISUAL.value == "visual"
        assert LearningStyleType.AUDITORY.value == "auditory"
        assert LearningStyleType.READING.value == "reading"
        assert LearningStyleType.KINESTHETIC.value == "kinesthetic"

    def test_felder_dimension_enum(self):
        """FelderDimension enum değerleri"""
        assert FelderDimension.ACTIVE_REFLECTIVE.value == "active_reflective"
        assert FelderDimension.SENSING_INTUITIVE.value == "sensing_intuitive"
        assert FelderDimension.VISUAL_VERBAL.value == "visual_verbal"
        assert FelderDimension.SEQUENTIAL_GLOBAL.value == "sequential_global"


class TestHybridLearningProfile:
    """HybridLearningProfile model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        profile = HybridLearningProfile(
            student_id="std1",
            vark_profile={
                "visual": 0.8,
                "auditory": 0.3,
                "reading": 0.6,
                "kinesthetic": 0.4,
            },
            felder_profile={
                "active_reflective": 0.7,
                "sensing_intuitive": 0.6,
                "visual_verbal": 0.8,
                "sequential_global": 0.5,
            },
            hybrid_code="V-A-S-S",
            confidence_level=0.85,
        )
        assert profile.student_id == "std1"
        assert profile.confidence_level == 0.85

    def test_get_dominant_vark_style(self):
        """Baskın VARK stili"""
        profile = HybridLearningProfile(
            student_id="std1",
            vark_profile={
                "visual": 0.9,
                "auditory": 0.3,
                "reading": 0.6,
                "kinesthetic": 0.4,
            },
            felder_profile={},
            hybrid_code="V",
            confidence_level=0.85,
        )
        assert profile.get_dominant_vark_style() == "visual"

    def test_get_learning_preferences(self):
        """Öğrenme tercihlerini alma"""
        profile = HybridLearningProfile(
            student_id="std1",
            vark_profile={
                "visual": 0.8,
                "auditory": 0.3,
                "reading": 0.6,
                "kinesthetic": 0.4,
            },
            felder_profile={"active_reflective": 0.7},
            hybrid_code="V-A",
            confidence_level=0.85,
        )
        prefs = profile.get_learning_preferences()
        assert prefs["dominant_vark"] == "visual"
        assert prefs["hybrid_code"] == "V-A"
        assert prefs["confidence"] == 0.85


class TestTurkishZPDRange:
    """TurkishZPDRange model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        zpd = TurkishZPDRange(
            student_id="std1",
            subject="Matematik",
            lower_bound=4.0,
            upper_bound=6.0,
            optimal_challenge=5.0,
            cultural_factors={"group_learning": 0.8},
            maarif_alignment=0.85,
        )
        assert zpd.student_id == "std1"
        assert zpd.subject == "Matematik"

    def test_get_zpd_width(self):
        """ZPD genişliği"""
        zpd = TurkishZPDRange(
            student_id="std1",
            subject="Matematik",
            lower_bound=4.0,
            upper_bound=7.0,
            optimal_challenge=5.5,
            cultural_factors={},
            maarif_alignment=0.85,
        )
        assert zpd.get_zpd_width() == 3.0

    def test_is_in_zpd(self):
        """ZPD içinde mi kontrolü"""
        zpd = TurkishZPDRange(
            student_id="std1",
            subject="Matematik",
            lower_bound=4.0,
            upper_bound=6.0,
            optimal_challenge=5.0,
            cultural_factors={},
            maarif_alignment=0.85,
        )
        assert zpd.is_in_zpd(5.0) == True
        assert zpd.is_in_zpd(3.0) == False
        assert zpd.is_in_zpd(7.0) == False


class TestQuestion:
    """Question model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        question = Question(
            text="2 + 2 = ?",
            difficulty=0.5,
            discrimination=1.2,
            subject="Matematik",
            topic="Toplama",
        )
        assert question.text == "2 + 2 = ?"
        assert question.difficulty == 0.5
        assert question.guessing_parameter == 0.2

    def test_get_irt_parameters(self):
        """IRT parametrelerini alma"""
        question = Question(
            text="Test",
            difficulty=0.5,
            discrimination=1.2,
            subject="Matematik",
            topic="Test",
            guessing_parameter=0.25,
        )
        params = question.get_irt_parameters()
        assert params["difficulty"] == 0.5
        assert params["discrimination"] == 1.2
        assert params["guessing"] == 0.25


class TestStudent:
    """Student model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        student = Student(
            id="std1", ability=1.5, morphology_awareness=0.7, name="Ahmet"
        )
        assert student.id == "std1"
        assert student.ability == 1.5
        assert student.morphology_awareness == 0.7

    def test_get_zpd_for_subject(self):
        """Ders için ZPD alma"""
        zpd = TurkishZPDRange(
            student_id="std1",
            subject="Matematik",
            lower_bound=4.0,
            upper_bound=6.0,
            optimal_challenge=5.0,
            cultural_factors={},
            maarif_alignment=0.85,
        )
        student = Student(
            id="std1",
            ability=1.5,
            morphology_awareness=0.7,
            zpd_ranges={"Matematik": zpd},
        )
        result = student.get_zpd_for_subject("Matematik")
        assert result is not None
        assert result.subject == "Matematik"

        # Olmayan ders
        assert student.get_zpd_for_subject("Fizik") is None

    def test_update_ability(self):
        """Yetenek güncelleme"""
        student = Student(id="std1", ability=1.5, morphology_awareness=0.7)
        student.update_ability(2.0)
        assert student.ability == 2.0

        # Sınır kontrolü - üst sınır
        student.update_ability(5.0)
        assert student.ability == 3.0

        # Sınır kontrolü - alt sınır
        student.update_ability(-5.0)
        assert student.ability == -3.0


class TestFlashcard:
    """Flashcard model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        card = Flashcard(
            id="card1",
            content="Osmanlı ne zaman kuruldu?",
            answer="1299",
            difficulty=0.5,
            last_review=datetime.now(),
            review_count=5,
            success_rate=0.8,
        )
        assert card.id == "card1"
        assert card.difficulty == 0.5

    def test_calculate_retention(self):
        """Hafızada kalma hesaplama"""
        card = Flashcard(
            id="card1",
            content="Test",
            answer="Answer",
            difficulty=0.5,
            last_review=datetime.now() - timedelta(days=5),
            review_count=3,
            success_rate=0.8,
            stability=2.0,
        )
        retention = card.calculate_retention(5)
        assert 0.0 <= retention <= 1.0

    def test_calculate_retention_zero_stability(self):
        """Sıfır stability durumu"""
        card = Flashcard(
            id="card1",
            content="Test",
            answer="Answer",
            difficulty=0.5,
            last_review=datetime.now(),
            review_count=0,
            success_rate=0.0,
            stability=0.0,
        )
        retention = card.calculate_retention(5)
        assert retention == 0.0

    def test_needs_review(self):
        """Tekrar gerekli mi"""
        card = Flashcard(
            id="card1",
            content="Test",
            answer="Answer",
            difficulty=0.5,
            last_review=datetime.now() - timedelta(days=30),
            review_count=1,
            success_rate=0.5,
            stability=1.0,
        )
        # 30 gün geçmiş, stability düşük -> tekrar gerekli
        assert card.needs_review() == True


class TestLearningSession:
    """LearningSession model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        session = LearningSession(
            student_id="std1",
            session_id="sess1",
            start_time=datetime.now(),
            subject="Matematik",
        )
        assert session.student_id == "std1"
        assert session.subject == "Matematik"

    def test_get_success_rate(self):
        """Başarı oranı"""
        session = LearningSession(
            student_id="std1",
            session_id="sess1",
            start_time=datetime.now(),
            correct_answers=8,
            total_questions=10,
        )
        assert session.get_success_rate() == 0.8

    def test_get_success_rate_zero_questions(self):
        """Soru yoksa başarı oranı sıfır"""
        session = LearningSession(
            student_id="std1", session_id="sess1", start_time=datetime.now()
        )
        assert session.get_success_rate() == 0.0

    def test_get_duration_minutes(self):
        """Oturum süresi"""
        start = datetime.now()
        end = start + timedelta(minutes=30)
        session = LearningSession(
            student_id="std1", session_id="sess1", start_time=start, end_time=end
        )
        assert session.get_duration_minutes() == 30.0

    def test_get_duration_minutes_no_end(self):
        """Bitiş zamanı yoksa süre sıfır"""
        session = LearningSession(
            student_id="std1", session_id="sess1", start_time=datetime.now()
        )
        assert session.get_duration_minutes() == 0.0


class TestCulturalContext:
    """CulturalContext model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        context = CulturalContext(
            student_id="std1",
            group_learning_preference=0.8,
            teacher_respect_level=0.9,
            family_involvement=0.7,
            peer_competition=0.6,
            authority_acceptance=0.85,
        )
        assert context.student_id == "std1"
        assert context.ramadan_period == False

    def test_get_cultural_adjustment_factor(self):
        """Kültürel ayarlama faktörü"""
        context = CulturalContext(
            student_id="std1",
            group_learning_preference=0.8,
            teacher_respect_level=0.9,
            family_involvement=0.7,
            peer_competition=0.6,
            authority_acceptance=0.8,
        )
        factor = context.get_cultural_adjustment_factor()
        expected = (0.8 + 0.9 + 0.7 + 0.6 + 0.8) / 5
        assert factor == pytest.approx(expected)


class TestMorphologyAnalysis:
    """MorphologyAnalysis model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        analysis = MorphologyAnalysis(
            word="evlerimizden",
            root="ev",
            suffixes=["ler", "imiz", "den"],
            derivational_depth=1,
            is_compound=False,
            complexity_score=0.7,
        )
        assert analysis.word == "evlerimizden"
        assert analysis.root == "ev"

    def test_get_suffix_count(self):
        """Ek sayısı"""
        analysis = MorphologyAnalysis(
            word="evlerimizden",
            root="ev",
            suffixes=["ler", "imiz", "den"],
            derivational_depth=1,
            is_compound=False,
        )
        assert analysis.get_suffix_count() == 3

    def test_is_complex_word(self):
        """Karmaşık kelime mi"""
        analysis_complex = MorphologyAnalysis(
            word="test",
            root="test",
            suffixes=[],
            derivational_depth=3,
            is_compound=True,
            complexity_score=0.8,
        )
        assert analysis_complex.is_complex_word() == True

        analysis_simple = MorphologyAnalysis(
            word="ev",
            root="ev",
            suffixes=[],
            derivational_depth=0,
            is_compound=False,
            complexity_score=0.2,
        )
        assert analysis_simple.is_complex_word() == False


class TestFSRSCard:
    """FSRSCard model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        card = FSRSCard(id="card1", content="Test content")
        assert card.id == "card1"
        assert card.state == "new"
        assert card.review_count == 0

    def test_is_due_no_due_date(self):
        """Due date yoksa her zaman due"""
        card = FSRSCard(id="card1", content="Test")
        assert card.is_due() == True

    def test_is_due_past_date(self):
        """Geçmiş tarih - due"""
        card = FSRSCard(id="card1", content="Test")
        card.due_date = datetime.now() - timedelta(days=1)
        assert card.is_due() == True

    def test_is_due_future_date(self):
        """Gelecek tarih - not due"""
        card = FSRSCard(id="card1", content="Test")
        card.due_date = datetime.now() + timedelta(days=1)
        assert card.is_due() == False

    def test_days_overdue(self):
        """Kaç gün gecikmiş"""
        card = FSRSCard(id="card1", content="Test")
        card.due_date = datetime.now() - timedelta(days=5)
        # Yaklaşık 5 gün gecikmiş olmalı
        assert card.days_overdue() >= 4

    def test_days_overdue_not_due(self):
        """Due değilse 0"""
        card = FSRSCard(id="card1", content="Test")
        card.due_date = datetime.now() + timedelta(days=5)
        assert card.days_overdue() == 0


class TestSimplificationLevel:
    """SimplificationLevel model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        level = SimplificationLevel(
            level=1, name="lexical", description="Kelime seviyesi basitleştirme"
        )
        assert level.level == 1
        assert level.name == "lexical"

    def test_add_rule(self):
        """Kural ekleme"""
        level = SimplificationLevel(level=1, name="lexical", description="Test")
        level.add_rule("Osmanlıca kelime değiştirme", 0.15)
        assert len(level.rules_applied) == 1
        assert level.complexity_reduction == 0.15

        level.add_rule("Yabancı kelime basitleştirme", 0.10)
        assert len(level.rules_applied) == 2
        assert level.complexity_reduction == 0.25


class TestBionicReadingResult:
    """BionicReadingResult model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        result = BionicReadingResult(
            original_text="test word",
            bionic_text="**te**st **wo**rd",
            bold_ratio=0.4,
            processing_time_ms=10.5,
            word_count=2,
        )
        assert result.original_text == "test word"
        assert result.word_count == 2

    def test_get_bold_character_count(self):
        """Bold karakter sayısı"""
        result = BionicReadingResult(
            original_text="test word",
            bionic_text="**te**st **wo**rd",
            bold_ratio=0.4,
            processing_time_ms=10.5,
            word_count=2,
        )
        # 4 adet ** işareti var (2 çift) = 2 bold bölge
        assert result.get_bold_character_count() == 2


class TestAgentMessage:
    """AgentMessage model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        msg = AgentMessage(
            agent_name="learning_agent",
            message_type="data_update",
            content={"score": 85},
        )
        assert msg.agent_name == "learning_agent"
        assert msg.message_type == "data_update"

    def test_is_broadcast_true(self):
        """Broadcast mesajı"""
        msg = AgentMessage(agent_name="agent1", message_type="notification", content={})
        assert msg.is_broadcast() == True

    def test_is_broadcast_false(self):
        """Hedef belirtilmiş mesaj"""
        msg = AgentMessage(
            agent_name="agent1",
            message_type="request",
            content={},
            target_agents=["agent2", "agent3"],
        )
        assert msg.is_broadcast() == False


class TestBlackboardEntry:
    """BlackboardEntry model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        entry = BlackboardEntry(
            key="student_progress", value={"score": 85}, source_agent="learning_agent"
        )
        assert entry.key == "student_progress"
        assert entry.source_agent == "learning_agent"

    def test_add_subscriber_notification(self):
        """Abone bildirimi ekleme"""
        entry = BlackboardEntry(key="key", value={}, source_agent="agent1")
        entry.add_subscriber_notification("agent2")
        assert "agent2" in entry.subscribers_notified

        # Tekrar eklemede çift eklenmemeli
        entry.add_subscriber_notification("agent2")
        assert entry.subscribers_notified.count("agent2") == 1


class TestUtilityFunctions:
    """Utility fonksiyon testleri"""

    def test_create_sample_hybrid_profile(self):
        """Örnek hibrit profil oluşturma"""
        profile = create_sample_hybrid_profile("std123")
        assert profile.student_id == "std123"
        assert profile.vark_profile["visual"] == 0.8
        assert profile.confidence_level == 0.85

    def test_create_sample_zpd_range(self):
        """Örnek ZPD aralığı oluşturma"""
        zpd = create_sample_zpd_range("std123", "Matematik")
        assert zpd.student_id == "std123"
        assert zpd.subject == "Matematik"
        assert zpd.lower_bound == 5.0
        assert zpd.upper_bound == 7.5

    def test_create_sample_student(self):
        """Örnek öğrenci oluşturma"""
        student = create_sample_student("std123")
        assert student.id == "std123"
        assert student.ability == 1.5
        assert student.morphology_awareness == 0.7
        assert student.learning_profile is not None
        assert "Matematik" in student.zpd_ranges
