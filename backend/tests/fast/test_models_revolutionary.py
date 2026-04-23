"""
Devrimsel AI Modelleri için Testler
Coverage target: revolutionary_models.py (296 statements, 0% → 80%+)
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

# Add backend to path and import directly to avoid SQLAlchemy metadata conflicts
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from models.revolutionary_models import (
    AgentState,
    AgentType,
    BionicReadingConfig,
    BionicReadingResult,
    BlackboardEvent,
    BlackboardMessage,
    CulturalAdjustments,
    FelderSilvermanProfile,
    FSRSCard,
    FSRSParameters,
    HybridLearningAnalysis,
    IRTAnalysisResult,
    LexicalReplacement,
    MaarifValues,
    MessageType,
    MorphologyComplexity,
    SimplificationLevel,
    SimplificationResult,
    SyntacticPattern,
    VARKProfile,
    ZPDCalculationResult,
    create_sample_bionic_result,
    create_sample_simplification_result,
)


class TestEnums:
    """Enum değerlerini test et"""

    def test_simplification_level_enum(self):
        """SimplificationLevel enum değerleri"""
        assert SimplificationLevel.LEXICAL.value == "lexical"
        assert SimplificationLevel.SYNTACTIC.value == "syntactic"
        assert SimplificationLevel.SEMANTIC.value == "semantic"

    def test_agent_type_enum(self):
        """AgentType enum değerleri"""
        assert AgentType.LEARNING_PATH.value == "learning_path"
        assert AgentType.STUDY_BUDDY.value == "study_buddy"
        assert AgentType.ACCESSIBILITY.value == "accessibility"

    def test_message_type_enum(self):
        """MessageType enum değerleri"""
        assert MessageType.DATA_UPDATE.value == "data_update"
        assert MessageType.REQUEST.value == "request"
        assert MessageType.RESPONSE.value == "response"
        assert MessageType.NOTIFICATION.value == "notification"


class TestSimplificationResult:
    """SimplificationResult model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        result = SimplificationResult(
            original_text="Mütalaaya göre",
            level1_lexical="Okumaya göre",
            level2_syntactic="Okunan şeye göre",
            level3_semantic="Okunan metne göre",
            complexity_reduction=0.5,
            readability_score=7.0,
        )
        assert result.original_text == "Mütalaaya göre"
        assert result.complexity_reduction == 0.5
        assert result.readability_score == 7.0

    def test_get_final_text(self):
        """Final metni döndürme"""
        result = SimplificationResult(
            original_text="A",
            level1_lexical="B",
            level2_syntactic="C",
            level3_semantic="D",
            complexity_reduction=0.5,
            readability_score=7.0,
        )
        assert result.get_final_text() == "D"

    def test_get_improvement_percentage(self):
        """İyileştirme yüzdesi"""
        result = SimplificationResult(
            original_text="A",
            level1_lexical="B",
            level2_syntactic="C",
            level3_semantic="D",
            complexity_reduction=0.65,
            readability_score=7.0,
        )
        assert result.get_improvement_percentage() == 65.0

    def test_default_values(self):
        """Varsayılan değerler"""
        result = SimplificationResult(
            original_text="A",
            level1_lexical="B",
            level2_syntactic="C",
            level3_semantic="D",
            complexity_reduction=0.5,
            readability_score=7.0,
        )
        assert result.processing_time_ms == 0.0
        assert result.applied_rules == []


class TestLexicalReplacement:
    """LexicalReplacement model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        replacement = LexicalReplacement(
            original="mütalaa", replacement="okuma", category="ottoman", confidence=0.95
        )
        assert replacement.original == "mütalaa"
        assert replacement.replacement == "okuma"
        assert replacement.category == "ottoman"
        assert replacement.confidence == 0.95

    def test_to_dict(self):
        """Dictionary'ye çevirme"""
        replacement = LexicalReplacement(
            original="mütalaa",
            replacement="okuma",
            category="ottoman",
            confidence=0.95,
            context="eğitim",
        )
        result = replacement.to_dict()
        assert result["original"] == "mütalaa"
        assert result["replacement"] == "okuma"
        assert result["category"] == "ottoman"
        assert result["confidence"] == 0.95
        assert result["context"] == "eğitim"


class TestSyntacticPattern:
    """SyntacticPattern model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        pattern = SyntacticPattern(
            pattern=r"\w+yor",
            replacement_template="{verb}",
            description="Present continuous",
            complexity_reduction=0.2,
        )
        assert pattern.pattern == r"\w+yor"
        assert pattern.complexity_reduction == 0.2

    def test_matches_true(self):
        """Eşleşme testi - pozitif"""
        pattern = SyntacticPattern(
            pattern=r"yor$",
            replacement_template="",
            description="",
            complexity_reduction=0.2,
        )
        assert pattern.matches("oynuyor") == True

    def test_matches_false(self):
        """Eşleşme testi - negatif"""
        pattern = SyntacticPattern(
            pattern=r"yor$",
            replacement_template="",
            description="",
            complexity_reduction=0.2,
        )
        assert pattern.matches("oynadı") == False


class TestBionicReadingConfig:
    """BionicReadingConfig model testleri"""

    def test_default_values(self):
        """Varsayılan değerler"""
        config = BionicReadingConfig()
        assert config.root_bold_ratio == 0.4
        assert config.suffix_bold_ratio == 0.0
        assert config.min_bold_chars == 2
        assert config.max_bold_chars == 4
        assert config.dyslexia_mode == False
        assert config.high_contrast == False

    def test_adjust_for_dyslexia(self):
        """Disleksi ayarlaması"""
        config = BionicReadingConfig()
        config.adjust_for_dyslexia()
        assert config.dyslexia_mode == True
        assert config.root_bold_ratio == 0.5
        assert config.min_bold_chars == 3
        assert config.high_contrast == True


class TestBionicReadingResult:
    """BionicReadingResult model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        config = BionicReadingConfig()
        result = BionicReadingResult(
            original_text="test", bionic_text="**te**st", config=config
        )
        assert result.original_text == "test"
        assert result.bionic_text == "**te**st"

    def test_get_statistics(self):
        """İstatistik hesaplama"""
        config = BionicReadingConfig()
        result = BionicReadingResult(
            original_text="test word",
            bionic_text="**te**st **wo**rd",
            config=config,
            processing_time_ms=10.5,
        )
        stats = result.get_statistics()
        assert stats["word_count"] == 2
        assert stats["processing_time_ms"] == 10.5
        assert stats["morphology_aware"] == True


class TestFSRSParameters:
    """FSRSParameters model testleri"""

    def test_default_17_parameters(self):
        """Varsayılan 17 parametre"""
        params = FSRSParameters()
        assert len(params.w) == 17

    def test_invalid_parameter_count(self):
        """Geçersiz parametre sayısı"""
        with pytest.raises(ValueError, match="FSRS requires exactly 17 parameters"):
            FSRSParameters(w=[0.4, 0.7])

    def test_get_parameter(self):
        """Parametre alma"""
        params = FSRSParameters()
        assert params.get_parameter(0) == 0.4
        assert params.get_parameter(1) == 0.7

    def test_get_parameter_invalid_index(self):
        """Geçersiz index"""
        params = FSRSParameters()
        with pytest.raises(
            IndexError, match="Parameter index must be between 0 and 16"
        ):
            params.get_parameter(17)


class TestFSRSCard:
    """FSRSCard model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        card = FSRSCard(
            id="card1", content="Osmanlı İmparatorluğu ne zaman kuruldu?", answer="1299"
        )
        assert card.id == "card1"
        assert card.state == "new"
        assert card.review_count == 0
        assert card.lapses == 0

    def test_is_due_no_due_date(self):
        """Due date yoksa hep due"""
        card = FSRSCard(id="1", content="Q", answer="A")
        assert card.is_due() == True

    def test_is_due_past_date(self):
        """Geçmiş tarih - due"""
        card = FSRSCard(id="1", content="Q", answer="A")
        card.due_date = datetime.now() - timedelta(days=1)
        assert card.is_due() == True

    def test_is_due_future_date(self):
        """Gelecek tarih - not due"""
        card = FSRSCard(id="1", content="Q", answer="A")
        card.due_date = datetime.now() + timedelta(days=1)
        assert card.is_due() == False

    def test_update_after_review(self):
        """Review sonrası güncelleme"""
        card = FSRSCard(id="1", content="Q", answer="A")
        card.update_after_review(grade=3, new_stability=5.0, new_difficulty=0.3)
        assert card.stability == 5.0
        assert card.difficulty == 0.3
        assert card.review_count == 1
        assert card.last_review is not None

    def test_update_after_review_fail(self):
        """Review başarısız - lapses artmalı"""
        card = FSRSCard(id="1", content="Q", answer="A")
        card.update_after_review(grade=1, new_stability=1.0, new_difficulty=0.5)
        assert card.lapses == 1


class TestCulturalAdjustments:
    """CulturalAdjustments model testleri"""

    def test_default_values(self):
        """Varsayılan değerler"""
        adj = CulturalAdjustments()
        assert adj.ramadan_factor == 0.8
        assert adj.exam_season_stress == 1.3
        assert adj.summer_break_decay == 0.6
        assert adj.group_study_bonus == 1.2
        assert adj.family_pressure == 1.1

    def test_get_adjustment_factor_neutral(self):
        """Nötr faktör"""
        adj = CulturalAdjustments()
        factor = adj.get_adjustment_factor({})
        assert factor == 1.0

    def test_get_adjustment_factor_ramadan(self):
        """Ramazan faktörü"""
        adj = CulturalAdjustments()
        factor = adj.get_adjustment_factor({"ramadan_period": True})
        assert factor == 0.8

    def test_get_adjustment_factor_multiple(self):
        """Çoklu faktör"""
        adj = CulturalAdjustments()
        factor = adj.get_adjustment_factor(
            {"ramadan_period": True, "exam_season": True}
        )
        assert factor == pytest.approx(0.8 * 1.3)


class TestBlackboardMessage:
    """BlackboardMessage model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        msg = BlackboardMessage(
            id="msg1",
            key="student_progress",
            value={"score": 85},
            source_agent="learning_path",
        )
        assert msg.id == "msg1"
        assert msg.key == "student_progress"
        assert msg.source_agent == "learning_path"

    def test_is_broadcast_true(self):
        """Broadcast mesajı"""
        msg = BlackboardMessage(id="msg1", key="key", value={}, source_agent="agent1")
        assert msg.is_broadcast() == True

    def test_is_broadcast_false(self):
        """Directed mesajı"""
        msg = BlackboardMessage(
            id="msg1",
            key="key",
            value={},
            source_agent="agent1",
            target_agents=["agent2"],
        )
        assert msg.is_broadcast() == False

    def test_mark_processed(self):
        """İşlenmiş olarak işaretle"""
        msg = BlackboardMessage(id="msg1", key="key", value={}, source_agent="agent1")
        msg.mark_processed("agent2")
        assert "agent2" in msg.processed_by

        # Tekrar eklenmemeli
        msg.mark_processed("agent2")
        assert msg.processed_by.count("agent2") == 1

    def test_to_dict(self):
        """Dictionary'ye çevirme"""
        msg = BlackboardMessage(
            id="msg1", key="key", value={"data": 123}, source_agent="agent1"
        )
        result = msg.to_dict()
        assert result["id"] == "msg1"
        assert result["key"] == "key"
        assert result["source_agent"] == "agent1"
        assert "timestamp" in result


class TestAgentState:
    """AgentState model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        state = AgentState(
            agent_name="learning_agent", agent_type=AgentType.LEARNING_PATH
        )
        assert state.agent_name == "learning_agent"
        assert state.agent_type == AgentType.LEARNING_PATH
        assert state.is_active == True

    def test_subscribe_to(self):
        """Abonelik ekleme"""
        state = AgentState(agent_name="agent", agent_type=AgentType.LEARNING_PATH)
        state.subscribe_to("progress_update")
        assert "progress_update" in state.subscriptions

        # Tekrar eklemede çift eklenmemeli
        state.subscribe_to("progress_update")
        assert state.subscriptions.count("progress_update") == 1

    def test_unsubscribe_from(self):
        """Abonelik kaldırma"""
        state = AgentState(agent_name="agent", agent_type=AgentType.LEARNING_PATH)
        state.subscribe_to("event1")
        state.unsubscribe_from("event1")
        assert "event1" not in state.subscriptions

    def test_add_message(self):
        """Mesaj ekleme"""
        state = AgentState(agent_name="agent", agent_type=AgentType.LEARNING_PATH)
        msg = BlackboardMessage(id="1", key="k", value={}, source_agent="a")
        state.add_message(msg)
        assert len(state.message_queue) == 1

    def test_get_pending_messages(self):
        """Bekleyen mesajlar"""
        state = AgentState(agent_name="agent1", agent_type=AgentType.LEARNING_PATH)
        msg1 = BlackboardMessage(id="1", key="k", value={}, source_agent="a")
        msg2 = BlackboardMessage(id="2", key="k", value={}, source_agent="a")
        msg2.mark_processed("agent1")

        state.add_message(msg1)
        state.add_message(msg2)

        pending = state.get_pending_messages()
        assert len(pending) == 1
        assert pending[0].id == "1"


class TestBlackboardEvent:
    """BlackboardEvent model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        event = BlackboardEvent(
            event_id="evt1",
            event_type="progress_update",
            data={"score": 90},
            source_agent="agent1",
        )
        assert event.event_id == "evt1"
        assert event.event_type == "progress_update"

    def test_notify_subscriber(self):
        """Abone bildirimi"""
        event = BlackboardEvent(
            event_id="evt1", event_type="type", data={}, source_agent="agent1"
        )
        event.notify_subscriber("agent2")
        assert "agent2" in event.subscribers_notified

        # Tekrar eklemede çift eklenmemeli
        event.notify_subscriber("agent2")
        assert event.subscribers_notified.count("agent2") == 1


class TestMaarifValues:
    """MaarifValues model testleri"""

    def test_default_values(self):
        """Varsayılan değerler"""
        values = MaarifValues()
        assert "vatan" in values.national_values
        assert "adalet" in values.universal_values
        assert "sabır" in values.root_values

    def test_get_alignment_score(self):
        """Ders uyumu"""
        values = MaarifValues()
        assert values.get_alignment_score("Tarih") == 0.9
        assert values.get_alignment_score("Matematik") == 0.6
        assert values.get_alignment_score("BilinmeyenDers") == 0.7


class TestZPDCalculationResult:
    """ZPDCalculationResult model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        zpd = ZPDCalculationResult(
            student_id="std1",
            subject="Matematik",
            current_level=5.0,
            zpd_lower=4.5,
            zpd_upper=6.5,
            optimal_challenge=5.5,
            cultural_adjustment=1.0,
            maarif_alignment=0.8,
            confidence=0.85,
        )
        assert zpd.student_id == "std1"
        assert zpd.current_level == 5.0

    def test_get_zpd_width(self):
        """ZPD genişliği"""
        zpd = ZPDCalculationResult(
            student_id="std1",
            subject="Matematik",
            current_level=5.0,
            zpd_lower=4.0,
            zpd_upper=6.0,
            optimal_challenge=5.0,
            cultural_adjustment=1.0,
            maarif_alignment=0.8,
            confidence=0.85,
        )
        assert zpd.get_zpd_width() == 2.0

    def test_is_appropriate_difficulty(self):
        """Zorluk uygunluğu"""
        zpd = ZPDCalculationResult(
            student_id="std1",
            subject="Matematik",
            current_level=5.0,
            zpd_lower=4.0,
            zpd_upper=6.0,
            optimal_challenge=5.0,
            cultural_adjustment=1.0,
            maarif_alignment=0.8,
            confidence=0.85,
        )
        assert zpd.is_appropriate_difficulty(5.0) == True
        assert zpd.is_appropriate_difficulty(3.0) == False
        assert zpd.is_appropriate_difficulty(7.0) == False

    def test_get_recommendation(self):
        """Öneri oluşturma"""
        zpd_high = ZPDCalculationResult(
            student_id="std1",
            subject="Mat",
            current_level=5.0,
            zpd_lower=4.0,
            zpd_upper=6.0,
            optimal_challenge=5.0,
            cultural_adjustment=1.2,
            maarif_alignment=0.8,
            confidence=0.85,
        )
        assert "Grup" in zpd_high.get_recommendation()

        zpd_low = ZPDCalculationResult(
            student_id="std1",
            subject="Mat",
            current_level=5.0,
            zpd_lower=4.0,
            zpd_upper=6.0,
            optimal_challenge=5.0,
            cultural_adjustment=0.8,
            maarif_alignment=0.8,
            confidence=0.85,
        )
        assert "Bireysel" in zpd_low.get_recommendation()


class TestMorphologyComplexity:
    """MorphologyComplexity model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        morph = MorphologyComplexity(
            word="çocuklarımızdan",
            suffix_count=4,
            derivational_depth=2,
            compound_complexity=0.5,
            phonetic_changes=1,
            semantic_ambiguity=0.2,
            total_complexity=0.75,
        )
        assert morph.word == "çocuklarımızdan"
        assert morph.suffix_count == 4

    def test_is_highly_complex(self):
        """Yüksek karmaşıklık testi"""
        morph_high = MorphologyComplexity(
            word="test",
            suffix_count=5,
            derivational_depth=3,
            compound_complexity=0.8,
            phonetic_changes=2,
            semantic_ambiguity=0.5,
            total_complexity=0.8,
        )
        assert morph_high.is_highly_complex() == True

        morph_low = MorphologyComplexity(
            word="test",
            suffix_count=1,
            derivational_depth=0,
            compound_complexity=0.1,
            phonetic_changes=0,
            semantic_ambiguity=0.1,
            total_complexity=0.3,
        )
        assert morph_low.is_highly_complex() == False

    def test_get_complexity_category(self):
        """Karmaşıklık kategorisi"""
        morph_simple = MorphologyComplexity(
            word="ev",
            suffix_count=0,
            derivational_depth=0,
            compound_complexity=0.0,
            phonetic_changes=0,
            semantic_ambiguity=0.0,
            total_complexity=0.2,
        )
        assert morph_simple.get_complexity_category() == "Basit"

        morph_medium = MorphologyComplexity(
            word="evler",
            suffix_count=1,
            derivational_depth=0,
            compound_complexity=0.2,
            phonetic_changes=0,
            semantic_ambiguity=0.1,
            total_complexity=0.5,
        )
        assert morph_medium.get_complexity_category() == "Orta"

        morph_complex = MorphologyComplexity(
            word="evlerimizden",
            suffix_count=3,
            derivational_depth=1,
            compound_complexity=0.6,
            phonetic_changes=1,
            semantic_ambiguity=0.3,
            total_complexity=0.8,
        )
        assert morph_complex.get_complexity_category() == "Karmaşık"


class TestIRTAnalysisResult:
    """IRTAnalysisResult model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        irt = IRTAnalysisResult(
            question_id="q1",
            student_id="s1",
            standard_probability=0.65,
            morphology_aware_probability=0.75,
            morphology_advantage=0.10,
            complexity_score=0.7,
            recommendation="Morfoloji avantajı mevcut",
        )
        assert irt.question_id == "q1"
        assert irt.morphology_advantage == 0.10

    def test_has_morphology_advantage(self):
        """Morfoloji avantajı"""
        irt_yes = IRTAnalysisResult(
            question_id="q1",
            student_id="s1",
            standard_probability=0.6,
            morphology_aware_probability=0.7,
            morphology_advantage=0.10,
            complexity_score=0.7,
            recommendation="",
        )
        assert irt_yes.has_morphology_advantage() == True

        irt_no = IRTAnalysisResult(
            question_id="q1",
            student_id="s1",
            standard_probability=0.6,
            morphology_aware_probability=0.62,
            morphology_advantage=0.02,
            complexity_score=0.7,
            recommendation="",
        )
        assert irt_no.has_morphology_advantage() == False

    def test_needs_morphology_practice(self):
        """Morfoloji pratiği gerekli mi"""
        irt_needs = IRTAnalysisResult(
            question_id="q1",
            student_id="s1",
            standard_probability=0.6,
            morphology_aware_probability=0.45,
            morphology_advantage=-0.15,
            complexity_score=0.7,
            recommendation="",
        )
        assert irt_needs.needs_morphology_practice() == True


class TestVARKProfile:
    """VARKProfile model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        vark = VARKProfile(visual=0.8, auditory=0.3, reading=0.6, kinesthetic=0.4)
        assert vark.visual == 0.8
        assert vark.auditory == 0.3

    def test_get_dominant_style(self):
        """Baskın stil"""
        vark = VARKProfile(visual=0.8, auditory=0.3, reading=0.6, kinesthetic=0.4)
        assert vark.get_dominant_style() == "visual"

        vark2 = VARKProfile(visual=0.3, auditory=0.9, reading=0.4, kinesthetic=0.2)
        assert vark2.get_dominant_style() == "auditory"

    def test_is_multimodal(self):
        """Çok modlu öğrenme"""
        vark_multi = VARKProfile(visual=0.7, auditory=0.8, reading=0.5, kinesthetic=0.4)
        assert vark_multi.is_multimodal() == True

        vark_single = VARKProfile(
            visual=0.9, auditory=0.3, reading=0.2, kinesthetic=0.1
        )
        assert vark_single.is_multimodal() == False


class TestFelderSilvermanProfile:
    """FelderSilvermanProfile model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        profile = FelderSilvermanProfile(
            active_reflective=0.7,
            sensing_intuitive=0.4,
            visual_verbal=0.8,
            sequential_global=0.3,
        )
        assert profile.active_reflective == 0.7
        assert profile.visual_verbal == 0.8

    def test_get_learning_preferences(self):
        """Öğrenme tercihleri"""
        profile = FelderSilvermanProfile(
            active_reflective=0.7,
            sensing_intuitive=0.6,
            visual_verbal=0.8,
            sequential_global=0.4,
        )
        prefs = profile.get_learning_preferences()
        assert prefs["processing"] == "active"
        assert prefs["perception"] == "sensing"
        assert prefs["input"] == "visual"
        assert prefs["understanding"] == "global"


class TestHybridLearningAnalysis:
    """HybridLearningAnalysis model testleri"""

    def test_basic_creation(self):
        """Temel oluşturma"""
        vark = VARKProfile(visual=0.8, auditory=0.3, reading=0.6, kinesthetic=0.4)
        felder = FelderSilvermanProfile(
            active_reflective=0.7,
            sensing_intuitive=0.6,
            visual_verbal=0.8,
            sequential_global=0.4,
        )
        analysis = HybridLearningAnalysis(
            student_id="std1",
            vark_profile=vark,
            felder_profile=felder,
            hybrid_code="V-A-SE-G",
            confidence_level=0.85,
            behavioral_consistency=0.9,
            questionnaire_alignment=0.8,
        )
        assert analysis.student_id == "std1"
        assert analysis.confidence_level == 0.85

    def test_get_learning_recommendations(self):
        """Öğrenme önerileri"""
        vark = VARKProfile(visual=0.9, auditory=0.2, reading=0.3, kinesthetic=0.1)
        felder = FelderSilvermanProfile(
            active_reflective=0.7,
            sensing_intuitive=0.6,
            visual_verbal=0.8,
            sequential_global=0.3,
        )
        analysis = HybridLearningAnalysis(
            student_id="std1",
            vark_profile=vark,
            felder_profile=felder,
            hybrid_code="V-A-SE-G",
            confidence_level=0.85,
            behavioral_consistency=0.9,
            questionnaire_alignment=0.8,
        )
        recommendations = analysis.get_learning_recommendations()
        assert len(recommendations) > 0
        assert any("Görsel" in r for r in recommendations)

    def test_is_reliable_analysis(self):
        """Analiz güvenilirliği"""
        vark = VARKProfile(visual=0.8, auditory=0.3, reading=0.6, kinesthetic=0.4)
        felder = FelderSilvermanProfile(
            active_reflective=0.7,
            sensing_intuitive=0.6,
            visual_verbal=0.8,
            sequential_global=0.4,
        )

        analysis_reliable = HybridLearningAnalysis(
            student_id="std1",
            vark_profile=vark,
            felder_profile=felder,
            hybrid_code="V-A-SE-G",
            confidence_level=0.85,
            behavioral_consistency=0.9,
            questionnaire_alignment=0.8,
        )
        assert analysis_reliable.is_reliable_analysis() == True

        analysis_unreliable = HybridLearningAnalysis(
            student_id="std1",
            vark_profile=vark,
            felder_profile=felder,
            hybrid_code="V-A-SE-G",
            confidence_level=0.5,
            behavioral_consistency=0.6,
            questionnaire_alignment=0.4,
        )
        assert analysis_unreliable.is_reliable_analysis() == False


class TestUtilityFunctions:
    """Utility fonksiyon testleri"""

    def test_create_sample_simplification_result(self):
        """Örnek basitleştirme sonucu"""
        result = create_sample_simplification_result()
        assert isinstance(result, SimplificationResult)
        assert result.complexity_reduction > 0
        assert result.readability_score > 0
        assert len(result.applied_rules) > 0

    def test_create_sample_bionic_result(self):
        """Örnek Bionic Reading sonucu"""
        result = create_sample_bionic_result()
        assert isinstance(result, BionicReadingResult)
        assert "**" in result.bionic_text
        assert result.morphology_aware == True
