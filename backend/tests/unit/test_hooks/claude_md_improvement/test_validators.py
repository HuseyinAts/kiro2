"""
KIRO2 Validators Unit Tests.

Bu modül validators.py için kapsamlı testler içerir:
- IRT parametre validasyonu (REQ-10.1)
- Türkçe karakter normalizasyonu (REQ-10.2)
- ZPD olasılık kontrolü (REQ-10.3)
- Soru kalite metrikleri (REQ-10.4)

Boris Cherny Standards - Verification Feedback Loops
"""

import os
import sys

# Backend dizinini Python path'e ekle (import öncesi)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import pytest

# Validators import
from hooks.claude_md_improvement.validators import (
    # IRT Validation
    IRTBounds,
    validate_irt_difficulty,
    validate_irt_discrimination,
    validate_irt_guessing,
    validate_irt_params,
    # Turkish Normalization
    turkish_lower,
    turkish_upper,
    turkish_normalize,
    is_turkish_text,
    fix_turkish_encoding,
    TURKISH_CHARS,
    # ZPD Validation
    ZPDBounds,
    validate_zpd_probability,
    calculate_zpd_score,
    suggest_difficulty_adjustment,
    # Question Quality
    QuestionQualityMetrics,
)


# =============================================================================
# IRT PARAMETRE TESTLERİ (REQ-10.1)
# =============================================================================

class TestIRTBounds:
    """IRTBounds dataclass testleri."""

    def test_default_values(self):
        """Default değerler doğru."""
        bounds = IRTBounds()
        assert bounds.DIFFICULTY_MIN == -4.0
        assert bounds.DIFFICULTY_MAX == 4.0
        assert bounds.DISCRIMINATION_MIN == 0.2
        assert bounds.DISCRIMINATION_MAX == 4.0
        assert bounds.GUESSING_MIN == 0.0
        assert bounds.GUESSING_MAX == 0.35


class TestValidateIRTDifficulty:
    """validate_irt_difficulty() testleri."""

    @pytest.mark.parametrize("difficulty,expected_valid", [
        (-4.0, True),   # Min bound (inclusive)
        (0.0, True),    # Normal
        (4.0, True),    # Max bound (inclusive)
        (-4.1, False),  # Below min
        (4.1, False),   # Above max
        (-10.0, False), # Far below
        (10.0, False),  # Far above
    ])
    def test_difficulty_bounds(self, difficulty, expected_valid):
        """Difficulty sınır testleri."""
        is_valid, msg = validate_irt_difficulty(difficulty)
        assert is_valid == expected_valid

    def test_valid_difficulty_message(self):
        """Geçerli difficulty mesajı 'OK' olmalı."""
        is_valid, msg = validate_irt_difficulty(0.0)
        assert is_valid is True
        assert msg == "OK"

    def test_invalid_type(self):
        """Geçersiz tip hata verir."""
        is_valid, msg = validate_irt_difficulty("invalid")
        assert is_valid is False
        assert "sayısal olmalı" in msg


class TestValidateIRTDiscrimination:
    """validate_irt_discrimination() testleri."""

    @pytest.mark.parametrize("discrimination,expected_valid", [
        (0.2, True),    # Min bound
        (2.0, True),    # Normal
        (4.0, True),    # Max bound
        (0.1, False),   # Below min
        (4.1, False),   # Above max
    ])
    def test_discrimination_bounds(self, discrimination, expected_valid):
        """Discrimination sınır testleri."""
        is_valid, msg = validate_irt_discrimination(discrimination)
        assert is_valid == expected_valid


class TestValidateIRTGuessing:
    """validate_irt_guessing() testleri."""

    @pytest.mark.parametrize("guessing,expected_valid", [
        (0.0, True),    # Min bound
        (0.2, True),    # Normal
        (0.35, True),   # Max bound
        (-0.1, False),  # Negative
        (0.4, False),   # Above max
    ])
    def test_guessing_bounds(self, guessing, expected_valid):
        """Guessing sınır testleri."""
        is_valid, msg = validate_irt_guessing(guessing)
        assert is_valid == expected_valid


class TestValidateIRTParams:
    """validate_irt_params() toplu validasyon testleri."""

    def test_all_valid(self):
        """Tüm parametreler geçerli."""
        is_valid, errors = validate_irt_params(
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.2
        )
        assert is_valid is True
        assert len(errors) == 0

    def test_all_invalid(self):
        """Tüm parametreler geçersiz."""
        is_valid, errors = validate_irt_params(
            difficulty=10.0,
            discrimination=0.1,
            guessing=0.5
        )
        assert is_valid is False
        assert len(errors) == 3

    def test_partial_invalid(self):
        """Bazı parametreler geçersiz."""
        is_valid, errors = validate_irt_params(
            difficulty=10.0,  # Invalid
            discrimination=1.0,  # Valid
            guessing=0.2  # Valid
        )
        assert is_valid is False
        assert len(errors) == 1

    def test_default_guessing(self):
        """Default guessing değeri çalışıyor."""
        is_valid, errors = validate_irt_params(
            difficulty=0.0,
            discrimination=1.0
            # guessing default 0.0
        )
        assert is_valid is True


# =============================================================================
# TÜRKÇE KARAKTER TESTLERİ (REQ-10.2)
# =============================================================================

class TestTurkishLower:
    """turkish_lower() testleri."""

    @pytest.mark.parametrize("input_text,expected", [
        ("ISTANBUL", "ıstanbul"),      # I -> ı
        ("İZMİR", "izmir"),            # İ -> i
        ("DİYARBAKIR", "diyarbakır"),  # Mixed
        ("HELLO", "hello"),            # No Turkish chars
        ("", ""),                       # Empty
    ])
    def test_turkish_lower(self, input_text, expected):
        """Türkçe küçük harf dönüşümü."""
        result = turkish_lower(input_text)
        assert result == expected


class TestTurkishUpper:
    """turkish_upper() testleri."""

    @pytest.mark.parametrize("input_text,expected", [
        ("istanbul", "İSTANBUL"),      # i -> İ
        ("ıstanbul", "ISTANBUL"),      # ı -> I
        ("izmir", "İZMİR"),
        ("hello", "HELLO"),            # No Turkish chars
        ("", ""),                       # Empty
    ])
    def test_turkish_upper(self, input_text, expected):
        """Türkçe büyük harf dönüşümü."""
        result = turkish_upper(input_text)
        assert result == expected


class TestTurkishNormalize:
    """turkish_normalize() testleri."""

    def test_normalize_lower(self):
        """Lower case normalize."""
        result = turkish_normalize("İSTANBUL", "lower")
        assert result == "istanbul"

    def test_normalize_upper(self):
        """Upper case normalize."""
        result = turkish_normalize("istanbul", "upper")
        assert result == "İSTANBUL"

    def test_invalid_case_raises(self):
        """Geçersiz case ValueError fırlatır."""
        with pytest.raises(ValueError):
            turkish_normalize("test", "invalid")


class TestIsTurkishText:
    """is_turkish_text() testleri."""

    def test_turkish_text_detected(self):
        """Türkçe metin tespit edilir."""
        assert is_turkish_text("Merhaba dünya, nasılsın?") is True

    def test_english_text_not_turkish(self):
        """İngilizce metin Türkçe değil."""
        assert is_turkish_text("Hello world, how are you?") is False

    def test_empty_text(self):
        """Boş metin False döner."""
        assert is_turkish_text("") is False

    def test_custom_threshold(self):
        """Özel eşik değeri."""
        # Very low threshold
        assert is_turkish_text("Hello ü", threshold=0.01) is True


class TestFixTurkishEncoding:
    """fix_turkish_encoding() testleri."""

    def test_fix_common_encoding_issues(self):
        """Yaygın encoding sorunları düzeltilir."""
        broken = "MerhabaÃ¼"
        fixed = fix_turkish_encoding(broken)
        assert "ü" in fixed

    def test_already_correct_encoding(self):
        """Doğru encoding değişmez."""
        correct = "Merhaba dünya"
        result = fix_turkish_encoding(correct)
        assert result == correct


class TestTurkishChars:
    """TURKISH_CHARS sabiti testleri."""

    def test_contains_all_special_chars(self):
        """Tüm özel karakterler var."""
        assert "ç" in TURKISH_CHARS
        assert "ğ" in TURKISH_CHARS
        assert "ı" in TURKISH_CHARS
        assert "ö" in TURKISH_CHARS
        assert "ş" in TURKISH_CHARS
        assert "ü" in TURKISH_CHARS
        assert "İ" in TURKISH_CHARS


# =============================================================================
# ZPD VALİDASYON TESTLERİ (REQ-10.3)
# =============================================================================

class TestZPDBounds:
    """ZPDBounds dataclass testleri."""

    def test_default_bounds(self):
        """Default sınırlar doğru."""
        bounds = ZPDBounds()
        assert bounds.OPTIMAL_MIN == 0.15
        assert bounds.OPTIMAL_MAX == 0.85
        assert bounds.EXTENDED_MIN == 0.10
        assert bounds.EXTENDED_MAX == 0.90


class TestValidateZPDProbability:
    """validate_zpd_probability() testleri."""

    @pytest.mark.parametrize("probability,strict,expected_valid", [
        (0.50, True, True),    # Optimal center
        (0.15, True, True),    # Min strict bound
        (0.85, True, True),    # Max strict bound
        (0.10, True, False),   # Below strict min
        (0.90, True, False),   # Above strict max
        (0.10, False, True),   # Extended min
        (0.90, False, True),   # Extended max
        (0.05, False, False),  # Below extended
    ])
    def test_zpd_bounds(self, probability, strict, expected_valid):
        """ZPD sınır testleri."""
        is_valid, msg = validate_zpd_probability(probability, strict)
        assert is_valid == expected_valid

    def test_out_of_range(self):
        """[0, 1] dışındaki değerler geçersiz."""
        is_valid, msg = validate_zpd_probability(1.5, True)
        assert is_valid is False

        is_valid, msg = validate_zpd_probability(-0.1, True)
        assert is_valid is False


class TestCalculateZPDScore:
    """calculate_zpd_score() testleri."""

    def test_optimal_center(self):
        """0.50 optimal skor verir."""
        score = calculate_zpd_score(0.50)
        assert score == 1.0

    def test_boundaries_give_zero(self):
        """Sınır dışı 0 skor verir."""
        assert calculate_zpd_score(0.10) == 0.0
        assert calculate_zpd_score(0.90) == 0.0

    def test_moderate_probability(self):
        """Orta değerler pozitif skor verir."""
        score = calculate_zpd_score(0.30)
        assert 0 < score < 1


class TestSuggestDifficultyAdjustment:
    """suggest_difficulty_adjustment() testleri."""

    def test_optimal_no_adjustment(self):
        """Optimal değer ayarlama gerektirmez."""
        direction, magnitude = suggest_difficulty_adjustment(0.50)
        assert direction == "optimal"
        assert magnitude == 0.0

    def test_too_hard_suggest_easier(self):
        """Çok zor soru kolaylaştırılmalı."""
        direction, magnitude = suggest_difficulty_adjustment(0.10)
        assert direction == "easier"
        assert magnitude > 0

    def test_too_easy_suggest_harder(self):
        """Çok kolay soru zorlaştırılmalı."""
        direction, magnitude = suggest_difficulty_adjustment(0.90)
        assert direction == "harder"
        assert magnitude > 0


# =============================================================================
# SORU KALİTE METRİKLERİ TESTLERİ (REQ-10.4)
# =============================================================================

class TestQuestionQualityMetrics:
    """QuestionQualityMetrics Pydantic model testleri."""

    def test_valid_metrics(self):
        """Geçerli metrikler oluşturulabilir."""
        metrics = QuestionQualityMetrics(
            question_id="q-001",
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.2,
            content_length=100,
            option_count=5,
        )
        assert metrics.question_id == "q-001"
        assert metrics.difficulty == 0.0

    def test_invalid_difficulty_raises(self):
        """Geçersiz difficulty ValueError fırlatır."""
        with pytest.raises(ValueError):
            QuestionQualityMetrics(
                question_id="q-001",
                difficulty=10.0,  # Invalid
                discrimination=1.0,
                content_length=100,
            )

    def test_invalid_discrimination_raises(self):
        """Geçersiz discrimination ValueError fırlatır."""
        with pytest.raises(ValueError):
            QuestionQualityMetrics(
                question_id="q-001",
                difficulty=0.0,
                discrimination=0.1,  # Invalid (below 0.2)
                content_length=100,
            )

    def test_content_length_minimum(self):
        """Content length minimum kontrolü."""
        with pytest.raises(ValueError):
            QuestionQualityMetrics(
                question_id="q-001",
                difficulty=0.0,
                discrimination=1.0,
                content_length=5,  # Below minimum 10
            )

    def test_calculate_quality_score(self):
        """Kalite skoru hesaplanabilir."""
        metrics = QuestionQualityMetrics(
            question_id="q-001",
            difficulty=0.0,
            discrimination=1.0,
            guessing=0.2,
            content_length=100,
            option_count=5,
        )
        score = metrics.calculate_quality_score()
        assert 0 <= score <= 1
