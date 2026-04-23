"""
KIRO2 Spesifik Validasyonlar - CLAUDE.md Self-Improvement.

Bu modül KIRO2 platformuna özgü validasyonları içerir:
- REQ-10.1: IRT parametre sınırları
- REQ-10.2: Türkçe I/ı dönüşümü
- REQ-10.3: ZPD olasılık kontrolü
- REQ-10.4: Soru kalite metrikleri

Boris Cherny Standards - Verification Feedback Loops
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# REQ-10.1: IRT PARAMETRE VALİDASYONU
# =============================================================================

class IRTParamType(str, Enum):
    """IRT parametre türleri."""

    DIFFICULTY = "difficulty"
    DISCRIMINATION = "discrimination"
    GUESSING = "guessing"
    SLIP = "slip"


@dataclass
class IRTBounds:
    """IRT parametre sınırları."""

    # 3PL Model sınırları
    DIFFICULTY_MIN: float = -4.0
    DIFFICULTY_MAX: float = 4.0
    DISCRIMINATION_MIN: float = 0.2
    DISCRIMINATION_MAX: float = 4.0
    GUESSING_MIN: float = 0.0
    GUESSING_MAX: float = 0.35
    SLIP_MIN: float = 0.0
    SLIP_MAX: float = 0.25


def validate_irt_difficulty(difficulty: float) -> tuple[bool, str]:
    """
    IRT difficulty parametresini doğrula.

    REQ-10.1: difficulty [-4.0, 4.0] aralığında olmalı.

    Args:
        difficulty: Zorluk parametresi (b)

    Returns:
        (is_valid, message) tuple
    """
    bounds = IRTBounds()

    if not isinstance(difficulty, (int, float)):
        return False, f"difficulty sayısal olmalı, verilen: {type(difficulty).__name__}"

    if difficulty < bounds.DIFFICULTY_MIN:
        return False, f"difficulty çok düşük: {difficulty} < {bounds.DIFFICULTY_MIN}"

    if difficulty > bounds.DIFFICULTY_MAX:
        return False, f"difficulty çok yüksek: {difficulty} > {bounds.DIFFICULTY_MAX}"

    return True, "OK"


def validate_irt_discrimination(discrimination: float) -> tuple[bool, str]:
    """
    IRT discrimination parametresini doğrula.

    REQ-10.1: discrimination [0.2, 4.0] aralığında olmalı.

    Args:
        discrimination: Ayırt edicilik parametresi (a)

    Returns:
        (is_valid, message) tuple
    """
    bounds = IRTBounds()

    if not isinstance(discrimination, (int, float)):
        return False, f"discrimination sayısal olmalı, verilen: {type(discrimination).__name__}"

    if discrimination < bounds.DISCRIMINATION_MIN:
        return False, f"discrimination çok düşük: {discrimination} < {bounds.DISCRIMINATION_MIN}"

    if discrimination > bounds.DISCRIMINATION_MAX:
        return False, f"discrimination çok yüksek: {discrimination} > {bounds.DISCRIMINATION_MAX}"

    return True, "OK"


def validate_irt_guessing(guessing: float) -> tuple[bool, str]:
    """
    IRT guessing parametresini doğrula.

    REQ-10.1: guessing [0.0, 0.35] aralığında olmalı.

    Args:
        guessing: Tahmin parametresi (c)

    Returns:
        (is_valid, message) tuple
    """
    bounds = IRTBounds()

    if not isinstance(guessing, (int, float)):
        return False, f"guessing sayısal olmalı, verilen: {type(guessing).__name__}"

    if guessing < bounds.GUESSING_MIN:
        return False, f"guessing negatif olamaz: {guessing}"

    if guessing > bounds.GUESSING_MAX:
        return False, f"guessing çok yüksek: {guessing} > {bounds.GUESSING_MAX}"

    return True, "OK"


def validate_irt_params(
    difficulty: float,
    discrimination: float,
    guessing: float = 0.0
) -> tuple[bool, list[str]]:
    """
    Tüm IRT parametrelerini toplu doğrula.

    REQ-10.1 Full Implementation.

    Args:
        difficulty: Zorluk parametresi (b)
        discrimination: Ayırt edicilik parametresi (a)
        guessing: Tahmin parametresi (c), varsayılan 0.0

    Returns:
        (all_valid, error_messages) tuple
    """
    errors = []

    valid_d, msg_d = validate_irt_difficulty(difficulty)
    if not valid_d:
        errors.append(msg_d)

    valid_a, msg_a = validate_irt_discrimination(discrimination)
    if not valid_a:
        errors.append(msg_a)

    valid_c, msg_c = validate_irt_guessing(guessing)
    if not valid_c:
        errors.append(msg_c)

    return len(errors) == 0, errors


# =============================================================================
# REQ-10.2: TÜRKÇE KARAKTER NORMALİZASYONU
# =============================================================================

# Türkçe karakter mapping
TURKISH_LOWER_MAP = {
    'I': 'ı',  # Büyük I -> küçük ı
    'İ': 'i',  # Büyük İ -> küçük i
}

TURKISH_UPPER_MAP = {
    'i': 'İ',  # Küçük i -> büyük İ
    'ı': 'I',  # Küçük ı -> büyük I
}

TURKISH_CHARS = "çÇğĞıIiİöÖşŞüÜ"


def turkish_lower(text: str) -> str:
    """
    Türkçe kurallarına göre küçük harfe çevir.

    REQ-10.2: I -> ı, İ -> i dönüşümü.

    Args:
        text: Dönüştürülecek metin

    Returns:
        Küçük harfli metin
    """
    result = text
    for upper, lower in TURKISH_LOWER_MAP.items():
        result = result.replace(upper, lower)
    return result.lower()


def turkish_upper(text: str) -> str:
    """
    Türkçe kurallarına göre büyük harfe çevir.

    REQ-10.2: i -> İ, ı -> I dönüşümü.

    Args:
        text: Dönüştürülecek metin

    Returns:
        Büyük harfli metin
    """
    result = text
    for lower, upper in TURKISH_UPPER_MAP.items():
        result = result.replace(lower, upper)
    return result.upper()


def turkish_normalize(text: str, case: str = "lower") -> str:
    """
    Türkçe metin normalizasyonu.

    REQ-10.2 Full Implementation.

    Args:
        text: Normalize edilecek metin
        case: "lower" veya "upper"

    Returns:
        Normalize edilmiş metin
    """
    if case == "lower":
        return turkish_lower(text)
    if case == "upper":
        return turkish_upper(text)
    raise ValueError(f"Geçersiz case: {case}, 'lower' veya 'upper' olmalı")


def is_turkish_text(text: str, threshold: float = 0.1) -> bool:
    """
    Metnin Türkçe olup olmadığını kontrol et.

    Args:
        text: Kontrol edilecek metin
        threshold: Türkçe karakter oranı eşiği

    Returns:
        Türkçe ise True
    """
    if not text:
        return False

    turkish_char_count = sum(1 for c in text if c in TURKISH_CHARS)
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return False

    return (turkish_char_count / total_alpha) >= threshold


def fix_turkish_encoding(text: str) -> str:
    """
    Bozuk Türkçe karakter encoding'ini düzelt.

    Common encoding issues: UTF-8 -> Latin1 -> UTF-8

    Args:
        text: Bozuk encoding'li metin

    Returns:
        Düzeltilmiş metin
    """
    # Yaygın bozuk encoding pattern'leri
    replacements = {
        'Ã¼': 'ü',
        'Ã¶': 'ö',
        'Ã§': 'ç',
        'ÅŸ': 'ş',
        'Äž': 'ğ',
        'Ä±': 'ı',
        'Ä°': 'İ',
        'Ãœ': 'Ü',
        'Ã–': 'Ö',
        'Ã‡': 'Ç',
        'Åž': 'Ş',
        'Äž': 'Ğ',
    }

    result = text
    for bad, good in replacements.items():
        result = result.replace(bad, good)

    return result


# =============================================================================
# REQ-10.3: ZPD OLASILIK KONTROLÜ
# =============================================================================

@dataclass
class ZPDBounds:
    """Zone of Proximal Development sınırları."""

    OPTIMAL_MIN: float = 0.15  # %15 minimum başarı olasılığı
    OPTIMAL_MAX: float = 0.85  # %85 maksimum başarı olasılığı

    # Genişletilmiş sınırlar (esnek mod)
    EXTENDED_MIN: float = 0.10
    EXTENDED_MAX: float = 0.90


def validate_zpd_probability(probability: float, strict: bool = True) -> tuple[bool, str]:
    """
    ZPD olasılık değerini doğrula.

    REQ-10.3: Optimal öğrenme için %15-%85 aralığı.

    Args:
        probability: Başarı olasılığı [0.0, 1.0]
        strict: Sıkı mod (True) veya esnek mod (False)

    Returns:
        (is_valid, message) tuple
    """
    bounds = ZPDBounds()

    if not isinstance(probability, (int, float)):
        return False, f"probability sayısal olmalı, verilen: {type(probability).__name__}"

    if probability < 0.0 or probability > 1.0:
        return False, f"probability [0, 1] aralığında olmalı: {probability}"

    min_bound = bounds.OPTIMAL_MIN if strict else bounds.EXTENDED_MIN
    max_bound = bounds.OPTIMAL_MAX if strict else bounds.EXTENDED_MAX

    if probability < min_bound:
        return False, f"probability ZPD altında (çok zor): {probability:.2%} < {min_bound:.0%}"

    if probability > max_bound:
        return False, f"probability ZPD üstünde (çok kolay): {probability:.2%} > {max_bound:.0%}"

    return True, "OK"


def calculate_zpd_score(probability: float) -> float:
    """
    ZPD uygunluk skorunu hesapla.

    Optimal nokta: 0.50 (tam orta)

    Args:
        probability: Başarı olasılığı

    Returns:
        ZPD skoru [0, 1] - 1.0 = optimal
    """
    bounds = ZPDBounds()

    if probability < bounds.OPTIMAL_MIN or probability > bounds.OPTIMAL_MAX:
        return 0.0

    # Optimal nokta: 0.50
    optimal = 0.50
    distance = abs(probability - optimal)
    max_distance = optimal - bounds.OPTIMAL_MIN  # 0.35

    return 1.0 - (distance / max_distance)


def suggest_difficulty_adjustment(
    current_probability: float,
    target_probability: float = 0.50
) -> tuple[str, float]:
    """
    Zorluk ayarlama önerisi.

    Args:
        current_probability: Mevcut başarı olasılığı
        target_probability: Hedef başarı olasılığı

    Returns:
        (direction, magnitude) - "easier"/"harder", adjustment magnitude
    """
    diff = target_probability - current_probability

    if abs(diff) < 0.05:
        return "optimal", 0.0
    if diff > 0:
        # Mevcut çok zor, kolaylaştır
        return "easier", abs(diff)
    # Mevcut çok kolay, zorlaştır
    return "harder", abs(diff)


# =============================================================================
# REQ-10.4: SORU KALİTE VALİDASYONU
# =============================================================================

class QuestionQualityMetrics(BaseModel):
    """Soru kalite metrikleri."""

    question_id: str = Field(..., description="Soru ID")

    # IRT parametreleri
    difficulty: float = Field(..., ge=-4.0, le=4.0)
    discrimination: float = Field(..., ge=0.2, le=4.0)
    guessing: float = Field(default=0.0, ge=0.0, le=0.35)

    # Kalite metrikleri
    content_length: int = Field(..., ge=10, description="Soru uzunluğu (karakter)")
    option_count: int = Field(default=5, ge=2, le=6, description="Seçenek sayısı")
    has_image: bool = Field(default=False)
    has_latex: bool = Field(default=False)

    # Türkçe metrikleri
    turkish_char_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    encoding_valid: bool = Field(default=True)

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: float) -> float:
        valid, msg = validate_irt_difficulty(v)
        if not valid:
            raise ValueError(msg)
        return v

    @field_validator('discrimination')
    @classmethod
    def validate_discrimination(cls, v: float) -> float:
        valid, msg = validate_irt_discrimination(v)
        if not valid:
            raise ValueError(msg)
        return v

    def calculate_quality_score(self) -> float:
        """Genel kalite skorunu hesapla."""
        scores = []

        # IRT uygunluğu
        if -2.0 <= self.difficulty <= 2.0:
            scores.append(1.0)
        else:
            scores.append(0.5)

        if 0.5 <= self.discrimination <= 2.0:
            scores.append(1.0)
        else:
            scores.append(0.5)

        # İçerik uzunluğu
        if 50 <= self.content_length <= 500:
            scores.append(1.0)
        elif self.content_length >= 10:
            scores.append(0.7)
        else:
            scores.append(0.3)

        # Seçenek sayısı (5 optimal)
        if self.option_count == 5:
            scores.append(1.0)
        elif self.option_count == 4:
            scores.append(0.9)
        else:
            scores.append(0.7)

        # Türkçe encoding
        if self.encoding_valid:
            scores.append(1.0)
        else:
            scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0


# =============================================================================
# COMPOSITE VALIDATOR
# =============================================================================

class KIRO2ValidationResult(BaseModel):
    """KIRO2 validasyon sonucu."""

    is_valid: bool = Field(..., description="Genel geçerlilik")
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Alt validasyonlar
    irt_valid: bool = Field(default=True)
    turkish_valid: bool = Field(default=True)
    zpd_valid: bool = Field(default=True)
    quality_valid: bool = Field(default=True)

    # Skorlar
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    zpd_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # Öneriler
    suggestions: list[str] = Field(default_factory=list)


def validate_kiro2_question(
    content: str,
    difficulty: float,
    discrimination: float,
    guessing: float = 0.0,
    success_probability: float | None = None,
    strict: bool = True
) -> KIRO2ValidationResult:
    """
    KIRO2 platformu için tam soru validasyonu.

    REQ-10 Full Implementation.

    Args:
        content: Soru içeriği
        difficulty: IRT zorluk parametresi
        discrimination: IRT ayırt edicilik parametresi
        guessing: IRT tahmin parametresi
        success_probability: Başarı olasılığı (opsiyonel)
        strict: Sıkı mod

    Returns:
        KIRO2ValidationResult
    """
    result = KIRO2ValidationResult(is_valid=True)

    # REQ-10.1: IRT validasyonu
    irt_valid, irt_errors = validate_irt_params(difficulty, discrimination, guessing)
    result.irt_valid = irt_valid
    if not irt_valid:
        result.errors.extend(irt_errors)
        result.is_valid = False

    # REQ-10.2: Türkçe validasyonu
    if content:
        # Encoding kontrolü
        fixed_content = fix_turkish_encoding(content)
        if fixed_content != content:
            result.warnings.append("Türkçe encoding sorunu tespit edildi ve düzeltildi")
            result.turkish_valid = False

        # Türkçe karakter kontrolü
        if not is_turkish_text(content, threshold=0.05):
            result.warnings.append("Metin Türkçe karakter içermiyor")
    else:
        result.errors.append("Soru içeriği boş olamaz")
        result.is_valid = False

    # REQ-10.3: ZPD validasyonu
    if success_probability is not None:
        zpd_valid, zpd_msg = validate_zpd_probability(success_probability, strict=strict)
        result.zpd_valid = zpd_valid
        result.zpd_score = calculate_zpd_score(success_probability)

        if not zpd_valid:
            result.warnings.append(zpd_msg)

            # Öneri ekle
            direction, magnitude = suggest_difficulty_adjustment(success_probability)
            if direction != "optimal":
                result.suggestions.append(
                    f"Soru {direction} yapılmalı (magnitude: {magnitude:.2f})"
                )

    # REQ-10.4: Kalite kontrolü
    if content:
        content_length = len(content)
        if content_length < 10:
            result.errors.append(f"Soru çok kısa: {content_length} karakter")
            result.quality_valid = False
            result.is_valid = False
        elif content_length > 2000:
            result.warnings.append(f"Soru çok uzun: {content_length} karakter")

    # Kalite skoru
    try:
        metrics = QuestionQualityMetrics(
            question_id="temp",
            difficulty=difficulty,
            discrimination=discrimination,
            guessing=guessing,
            content_length=len(content) if content else 0,
            encoding_valid=result.turkish_valid
        )
        result.quality_score = metrics.calculate_quality_score()
    except ValueError as e:
        result.quality_score = 0.0
        result.errors.append(str(e))

    return result


# =============================================================================
# HELPER FUNCTIONS FOR HOOKS
# =============================================================================

def validate_feedback_content(content: str) -> tuple[bool, list[str]]:
    """
    Feedback içeriğini KIRO2 kurallarına göre doğrula.

    Hook entegrasyonu için kullanılır.
    """
    errors = []

    if not content or len(content.strip()) < 5:
        errors.append("Feedback içeriği çok kısa")

    if len(content) > 10000:
        errors.append("Feedback içeriği çok uzun (max 10000 karakter)")

    # Türkçe karakter kontrolü
    fixed = fix_turkish_encoding(content)
    if fixed != content:
        errors.append("Türkçe encoding sorunu tespit edildi")

    return len(errors) == 0, errors


def validate_rule_update(
    old_text: str,
    new_text: str,
    rule_type: str = "general"
) -> tuple[bool, list[str], list[str]]:
    """
    CLAUDE.md kural güncellemesini doğrula.

    Args:
        old_text: Eski kural metni
        new_text: Yeni kural metni
        rule_type: Kural türü

    Returns:
        (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    # Boş kontrolü
    if not new_text or len(new_text.strip()) < 10:
        errors.append("Yeni kural metni çok kısa")

    # Çok büyük değişiklik kontrolü
    if old_text and new_text:
        old_len = len(old_text)
        new_len = len(new_text)

        if new_len > old_len * 3:
            warnings.append(f"Kural çok genişledi ({old_len} -> {new_len} karakter)")

        if new_len < old_len * 0.3:
            warnings.append(f"Kural çok küçüldü ({old_len} -> {new_len} karakter)")

    # Türkçe karakter kontrolü
    if new_text:
        fixed = fix_turkish_encoding(new_text)
        if fixed != new_text:
            warnings.append("Türkçe encoding sorunu tespit edildi")

    # Reward hacking pattern kontrolü
    reward_hacking_patterns = [
        r'assert\s+True',
        r'assert\s+true',
        r'ASSERT_TRUE\s*\(\s*true\s*\)',
        r'echo\s+Success',
        r'print\s*\(\s*["\']Success["\']\s*\)',
        r'pass\s*#\s*placeholder',
        r'return\s+None\s*#\s*stub',
    ]

    for pattern in reward_hacking_patterns:
        if re.search(pattern, new_text, re.IGNORECASE):
            errors.append(f"Reward hacking pattern tespit edildi: {pattern}")

    return len(errors) == 0, errors, warnings
