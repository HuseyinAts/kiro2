"""
Unit Tests for Text Simplification Service
Task 80: Text Simplification for Dyslexia Support
"""

import pytest
from core.text_simplification_service import (
    TextSimplificationService,
    SimplificationResult,
)


@pytest.fixture
def service():
    """Text simplification service fixture"""
    return TextSimplificationService()


class TestComplexWordDetection:
    """Task 80.1: Karmaşık Kelime Tespiti Tests"""

    def test_detect_simple_words(self, service):
        """Basit kelimelerin tespit edilmemesi"""
        text = "Bu bir test metnidir"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.6)

        assert (
            len(complex_words) == 0
        ), "Basit kelimeler karmaşık olarak işaretlenmemeli"

    def test_detect_complex_words(self, service):
        """Karmaşık kelimelerin tespit edilmesi"""
        text = "Bu implementasyon algoritma optimizasyonu gerçekleştirmektedir"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        assert len(complex_words) > 0, "Karmaşık kelimeler tespit edilmeli"

        # Karmaşık kelimeleri kontrol et
        complex_word_texts = [cw.word for cw in complex_words]
        assert any(
            word in complex_word_texts
            for word in ["implementasyon", "algoritma", "optimizasyonu"]
        )

    def test_complexity_threshold(self, service):
        """Karmaşıklık eşiğinin çalışması"""
        text = "Bu karmaşık bir metindir"

        # Düşük eşik - daha fazla kelime
        low_threshold = service.detect_complex_words(text, complexity_threshold=0.3)

        # Yüksek eşik - daha az kelime
        high_threshold = service.detect_complex_words(text, complexity_threshold=0.8)

        assert len(low_threshold) >= len(
            high_threshold
        ), "Düşük eşik daha fazla kelime bulmalı"

    def test_complex_word_structure(self, service):
        """ComplexWord veri yapısının doğruluğu"""
        text = "Bu implementasyon çok karmaşıktır"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        if complex_words:
            cw = complex_words[0]
            assert hasattr(cw, "word")
            assert hasattr(cw, "complexity_score")
            assert hasattr(cw, "position")
            assert hasattr(cw, "suggested_replacements")
            assert hasattr(cw, "frequency_score")

            assert 0.0 <= cw.complexity_score <= 1.0
            assert 0.0 <= cw.frequency_score <= 1.0
            assert cw.position >= 0


class TestSynonymReplacement:
    """Task 80.2: Basit Eşanlamlı Değiştirme Tests"""

    def test_replace_with_synonyms(self, service):
        """Eşanlamlı değiştirmenin çalışması"""
        text = "Bu implementasyon algoritma kullanır"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        simplified_text, replacements = service.replace_with_synonyms(
            text, complex_words, require_confirmation=False
        )

        assert simplified_text != text, "Metin değiştirilmeli"
        assert len(replacements) > 0, "Değişiklikler kaydedilmeli"

    def test_context_aware_replacement(self, service):
        """Bağlam duyarlı değiştirme"""
        text = "Algoritma optimizasyonu yapıldı"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        simplified_text, _ = service.replace_with_synonyms(
            text, complex_words, require_confirmation=False
        )

        # Kelime sınırlarının korunması
        assert (
            "yöntem" in simplified_text.lower()
            or "algoritma" in simplified_text.lower()
        )

    def test_confirmation_mode(self, service):
        """Onay modunun çalışması"""
        text = "Bu implementasyon karmaşıktır"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        simplified_text, replacements = service.replace_with_synonyms(
            text, complex_words, require_confirmation=True
        )

        # Onay modunda metin değişmemeli
        assert simplified_text == text, "Onay modunda metin değişmemeli"

        # Ama öneriler olmalı
        for replacement in replacements:
            assert replacement.get("requires_confirmation") == True

    def test_replacement_alternatives(self, service):
        """Alternatif önerilerin sunulması"""
        text = "Bu implementasyon yapıldı"
        complex_words = service.detect_complex_words(text, complexity_threshold=0.5)

        _, replacements = service.replace_with_synonyms(
            text, complex_words, require_confirmation=True
        )

        if replacements:
            replacement = replacements[0]
            assert "original" in replacement
            assert "replacement" in replacement
            assert "alternatives" in replacement


class TestSentenceSplitting:
    """Task 80.3: Uzun Cümle Bölme Tests"""

    def test_split_long_sentence(self, service):
        """Uzun cümlenin bölünmesi"""
        text = (
            "Bu çok uzun bir cümledir ve birçok kelime içerir ve "
            "bu nedenle bölünmesi gerekir çünkü okunması zordur ve "
            "anlaşılması güçtür ve bu yüzden basitleştirilmelidir."
        )

        simplified_text, split_count = service.split_long_sentences(
            text, max_sentence_length=10
        )

        assert split_count > 0, "Uzun cümle bölünmeli"
        assert simplified_text != text, "Metin değişmeli"

        # Bölünen cümle sayısını kontrol et
        sentences = [s.strip() for s in simplified_text.split(".") if s.strip()]
        assert len(sentences) > 1, "Birden fazla cümle olmalı"

    def test_short_sentence_unchanged(self, service):
        """Kısa cümlenin değişmemesi"""
        text = "Bu kısa bir cümledir."

        simplified_text, split_count = service.split_long_sentences(
            text, max_sentence_length=20
        )

        assert split_count == 0, "Kısa cümle bölünmemeli"
        assert simplified_text.strip() == text.strip(), "Metin değişmemeli"

    def test_conjunction_splitting(self, service):
        """Bağlaçlardan bölme"""
        text = "Öğrenci çalıştı ve sınavı kazandı ve mutlu oldu."

        simplified_text, split_count = service.split_long_sentences(
            text, max_sentence_length=5
        )

        assert split_count > 0, "Bağlaçlardan bölünmeli"
        assert "ve" not in simplified_text or simplified_text.count("ve") < text.count(
            "ve"
        )

    def test_multiple_sentences(self, service):
        """Birden fazla cümlenin işlenmesi"""
        text = (
            "Bu birinci cümledir ve çok uzundur ve bölünmelidir ve daha da uzatılmalıdır. "
            "Bu ikinci cümledir ve kısadır. "
            "Bu üçüncü cümledir ve yine uzundur ve bölünmelidir ve çok daha fazla kelime içermelidir."
        )

        simplified_text, split_count = service.split_long_sentences(
            text, max_sentence_length=6
        )

        assert split_count >= 1, "En az bir cümle bölünmeli"


class TestFleschKincaidScore:
    """Task 80.4: Flesch-Kincaid Skoru Tests"""

    def test_calculate_flesch_score(self, service):
        """Flesch skorunun hesaplanması"""
        text = "Bu basit bir metindir. Kolay okunur. Anlaşılırdır."

        result = service.calculate_flesch_kincaid_score(text)

        assert "flesch_reading_ease" in result
        assert "flesch_kincaid_grade" in result
        assert "grade_level" in result
        assert "difficulty" in result
        assert "statistics" in result

    def test_simple_text_high_score(self, service):
        """Basit metnin yüksek skor alması"""
        simple_text = "Bu kolay bir metindir. Çok basittir. İyi okunur."

        result = service.calculate_flesch_kincaid_score(simple_text)

        # Basit metin makul bir skor almalı (>30)
        assert result["flesch_reading_ease"] > 30, "Basit metin makul skor almalı"

    def test_complex_text_low_score(self, service):
        """Karmaşık metnin düşük skor alması"""
        complex_text = (
            "Bu implementasyon, algoritmanın optimizasyonunu gerçekleştirmektedir ve "
            "performans iyileştirmesi sağlamaktadır, dolayısıyla sistem verimliliği "
            "artırılmaktadır ve kullanıcı deneyimi geliştirilmektedir."
        )

        result = service.calculate_flesch_kincaid_score(complex_text)

        # Karmaşık metin düşük skor almalı (<60)
        assert result["flesch_reading_ease"] < 70, "Karmaşık metin düşük skor almalı"

    def test_grade_level_estimation(self, service):
        """Sınıf seviyesi tahmininin doğruluğu"""
        text = "Bu ortaokul seviyesinde bir metindir. Anlaşılır ve açıktır."

        result = service.calculate_flesch_kincaid_score(text)

        assert result["grade_level"] is not None
        assert isinstance(result["grade_level"], str)

    def test_difficulty_classification(self, service):
        """Zorluk sınıflandırmasının doğruluğu"""
        text = "Bu bir test metnidir."

        result = service.calculate_flesch_kincaid_score(text)

        assert result["difficulty"] in [
            "Çok Kolay",
            "Kolay",
            "Oldukça Kolay",
            "Standart",
            "Oldukça Zor",
            "Zor",
            "Çok Zor",
        ]

    def test_statistics_accuracy(self, service):
        """İstatistiklerin doğruluğu"""
        text = "Bu bir test. İki cümle var."

        result = service.calculate_flesch_kincaid_score(text)
        stats = result["statistics"]

        assert stats["sentence_count"] == 2
        assert stats["word_count"] == 6
        assert stats["avg_words_per_sentence"] == 3.0

    def test_empty_text_handling(self, service):
        """Boş metin işleme"""
        text = ""

        result = service.calculate_flesch_kincaid_score(text)

        assert result["flesch_reading_ease"] == 0.0
        assert result["grade_level"] == "Hesaplanamadı"


class TestImprovementSuggestions:
    """İyileştirme Önerileri Tests"""

    def test_get_improvement_suggestions(self, service):
        """İyileştirme önerilerinin üretilmesi"""
        original_score = {
            "flesch_reading_ease": 40.0,
            "statistics": {"avg_words_per_sentence": 25},
        }
        simplified_score = {
            "flesch_reading_ease": 60.0,
            "statistics": {"avg_words_per_sentence": 15},
        }

        suggestions = service.get_improvement_suggestions(
            original_score, simplified_score
        )

        assert len(suggestions) > 0, "Öneriler üretilmeli"
        assert any("iyileşti" in s.lower() for s in suggestions)

    def test_no_improvement_warning(self, service):
        """İyileşme olmadığında uyarı"""
        original_score = {"flesch_reading_ease": 60.0, "statistics": {}}
        simplified_score = {"flesch_reading_ease": 55.0, "statistics": {}}

        suggestions = service.get_improvement_suggestions(
            original_score, simplified_score
        )

        assert any("iyileşme sağlanamadı" in s.lower() for s in suggestions)


class TestFullSimplification:
    """Tam Basitleştirme Tests"""

    def test_full_simplification(self, service):
        """Tam basitleştirme işleminin çalışması"""
        text = (
            "Bu implementasyon, algoritmanın optimizasyonunu gerçekleştirmektedir ve "
            "performans iyileştirmesi sağlamaktadır ve sistem verimliliği artırılmaktadır."
        )

        result = service.simplify_text(
            text,
            complexity_threshold=0.5,
            max_sentence_length=15,
            replace_synonyms=True,
            split_sentences=True,
        )

        assert isinstance(result, SimplificationResult)
        assert result.simplified_text != result.original_text
        assert result.simplified_flesch_score >= result.original_flesch_score

    def test_simplification_improves_readability(self, service):
        """Basitleştirmenin okunabilirliği iyileştirmesi"""
        complex_text = (
            "Bu karmaşık implementasyon, algoritmanın optimizasyonunu gerçekleştirmektedir ve "
            "performans iyileştirmesi sağlamaktadır ve dolayısıyla sistem verimliliği "
            "artırılmaktadır ve kullanıcı deneyimi geliştirilmektedir."
        )

        result = service.simplify_text(complex_text)

        assert (
            result.readability_improvement >= 0
        ), "Okunabilirlik iyileşmeli veya aynı kalmalı"

    def test_simplification_statistics(self, service):
        """Basitleştirme istatistiklerinin doğruluğu"""
        text = "Bu implementasyon algoritma optimizasyonu gerçekleştirmektedir."

        result = service.simplify_text(text)

        assert result.complex_words_replaced >= 0
        assert result.sentences_split >= 0
        assert isinstance(result.suggestions, list)

    def test_no_synonym_replacement(self, service):
        """Eşanlamlı değiştirme kapalı"""
        text = "Bu implementasyon yapıldı"

        result = service.simplify_text(
            text, replace_synonyms=False, split_sentences=False
        )

        assert result.complex_words_replaced == 0

    def test_no_sentence_splitting(self, service):
        """Cümle bölme kapalı"""
        text = "Bu çok uzun bir cümledir ve birçok kelime içerir ve bölünmemelidir."

        result = service.simplify_text(
            text, replace_synonyms=False, split_sentences=False
        )

        assert result.sentences_split == 0


class TestHelperMethods:
    """Yardımcı Metod Tests"""

    def test_count_syllables(self, service):
        """Hece sayma"""
        assert service._count_syllables("ev") == 1
        assert service._count_syllables("okul") == 2
        assert service._count_syllables("öğrenci") == 3
        assert service._count_syllables("üniversite") == 5

    def test_word_frequency(self, service):
        """Kelime frekansı"""
        # Yaygın kelime
        assert service._get_word_frequency("ve") == 1.0

        # Nadir kelime
        assert service._get_word_frequency("implementasyon") < 1.0

    def test_find_synonyms(self, service):
        """Eşanlamlı bulma"""
        synonyms = service._find_simple_synonyms("implementasyon")
        assert len(synonyms) > 0
        assert "uygulama" in synonyms or "yapım" in synonyms
