"""Webb Depth of Knowledge (DOK) Classifier for YKS questions.

Norman Webb's DOK framework with 4 levels:
- Level 1 (RECALL): Recall & Reproduction
- Level 2 (SKILL): Skill & Concept
- Level 3 (STRATEGIC): Strategic Thinking
- Level 4 (EXTENDED): Extended Thinking
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

from models.question_generation import WebbDOKLevel


@dataclass
class WebbDOKResult:
    """Webb DOK siniflandirma sonucu."""

    level: WebbDOKLevel
    confidence: float  # 0.0 - 1.0
    matched_patterns: list[str]
    rationale: str  # Turkce aciklama

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "confidence": round(self.confidence, 3),
            "matched_patterns": self.matched_patterns,
            "rationale": self.rationale,
        }


# --- Turkish regex patterns per DOK level ---

DOK_PATTERNS: dict[WebbDOKLevel, list[str]] = {
    WebbDOKLevel.RECALL: [
        # Hatirlama: tanim, formul, dogrudan bilgi
        r"\btanımla\w*\b",
        r"\blistele\w*\b",
        r"\badlandır\w*\b",
        r"\bbelirt\w*\b",
        r"\bhangi\w+\s+(?:tanım|formül|kural)\b",
        r"\bnedir\b",
        r"\byazınız\b",
        r"\bezbere\w*\b",
        r"\btanım\w*\b.*\bnedir\b",
        r"\bhatırlayınız\b",
        r"\byeniden\s+yaz\w*\b",
        r"\btanımını\s+yap\w*\b",
        r"\badını\s+(?:ver|yaz|belirt)\w*\b",
        r"\bformül\w*\b.*\bnedir\b",
        r"\bkural\w*\b.*\bnedir\b",
    ],
    WebbDOKLevel.SKILL: [
        # Beceri: hesaplama, uygulama, cok adimli rutin
        r"\bhesaplayınız\b",
        r"\bçözünüz\b",
        r"\bbulunuz\b",
        r"\buygulayınız\b",
        r"\bgösteriniz\b",
        r"\bsınıflandırınız\b",
        r"\bkarşılaştırınız\b",
        r"\bözetleyiniz\b",
        r"\başağıdaki\w*\s+(?:işlemi|denklemi)\b",
        r"\bhesaplama\w*\b",
        r"\bçözüm\w*\b.*\byap\w*\b",
        r"\bişlem\w*\b.*\byap\w*\b",
        r"\bdenklem\w*\b.*\bçöz\w*\b",
        r"\bformül\w*\b.*\buygula\w*\b",
        r"\badım\w*\b.*\btakip\s+ed\w*\b",
    ],
    WebbDOKLevel.STRATEGIC: [
        # Stratejik dusunme: planlama, kanitlama, cikarim
        r"\bkanıtlayınız\b",
        r"\bneden\w*\s+açıklayınız\b",
        r"\byorumlayınız\b",
        r"\bçıkarım\w*\b",
        r"\bdeğerlendiriniz\b",
        r"\bgerekçe\w*\b",
        r"\bhipotez\w*\b",
        r"\bstratej\w*\b",
        r"\bplanlayınız\b",
        r"\bnasıl\s+(?:etkilenir|değişir|farklıdır)\b",
        r"\banali\wz\s+ed\w*\b",
        r"\btahmin\s+ed\w*\b",
        r"\bsonuç\w*\b.*\bçıkar\w*\b",
        r"\bkarar\s+ver\w*\b",
        r"\bneden\s+(?:öyle|böyle|farklı)\b",
        r"\bnasıl\s+açıkla\w*\b",
    ],
    WebbDOKLevel.EXTENDED: [
        # Genisletilmis dusunme: arastirma, sentez, proje
        r"\baraştırınız\b",
        r"\btasarlayınız\b",
        r"\büretiniz\b",
        r"\bsentez\w*\b",
        r"\bproje\w*\b",
        r"\bdisiplinler\s*arası\b",
        r"\bözgün\w*\s+(?:çözüm|yaklaşım)\b",
        r"\bbağlan\w*\s+kur\w*\b",
        r"\bmodel\w*\s+oluştur\w*\b",
        r"\byeni\s+bir\s+(?:yöntem|model|sistem)\b",
        r"\bunite\s+et\w*\b.*\bfarklı\s+(?:konu|alan)\b",
        r"\byaratıcı\w*\b",
        r"\binova\w*\b",
    ],
}

# --- Pattern agirlik skorlari (higher = stronger signal) ---
PATTERN_WEIGHTS: dict[WebbDOKLevel, float] = {
    WebbDOKLevel.RECALL: 1.0,
    WebbDOKLevel.SKILL: 1.2,
    WebbDOKLevel.STRATEGIC: 1.5,
    WebbDOKLevel.EXTENDED: 2.0,
}


def _normalize(text: str) -> str:
    """Turkce metin normalizasyonu.

    CRITICAL: NFC + İ→i, I→ı mapping for Turkish text.
    """
    text = unicodedata.normalize("NFC", text)
    return text.replace("İ", "i").replace("I", "ı").lower()


def _match_patterns(
    normalized_text: str, level: WebbDOKLevel
) -> tuple[int, list[str]]:
    """Belirli bir DOK seviyesi icin pattern eslestir.

    Args:
        normalized_text: Normalize edilmis soru metni.
        level: DOK seviyesi.

    Returns:
        (match_count, matched_pattern_strings)
    """
    patterns = DOK_PATTERNS.get(level, [])
    matched = []
    for pattern in patterns:
        if re.search(pattern, normalized_text, re.UNICODE):
            matched.append(pattern)
    return len(matched), matched


def classify_webb_dok(
    question_text: str,
    options: Optional[list[str]] = None,
) -> WebbDOKResult:
    """Soru icin Webb DOK seviyesini siniflandir.

    Args:
        question_text: Soru metni.
        options: Secenekler (opsiyonel, analiz icin kullanilabilir).

    Returns:
        WebbDOKResult with level, confidence, and rationale.

    Example:
        >>> result = classify_webb_dok("Asiret ne demektir?")
        >>> result.level
        <WebbDOKLevel.RECALL: 'hatirlama'>
        >>> result.confidence
        0.85
    """
    # Tam metni olustur
    full_text = question_text
    if options:
        full_text += " " + " ".join(options)

    norm = _normalize(full_text)

    # Her seviye icin pattern eslestirme
    level_scores: dict[WebbDOKLevel, float] = {}
    level_matches: dict[WebbDOKLevel, list[str]] = {}

    for level in WebbDOKLevel:
        count, matched = _match_patterns(norm, level)
        weight = PATTERN_WEIGHTS.get(level, 1.0)
        # Agirlikli skor: yuksek seviyeler oncelikli
        level_scores[level] = count * weight
        level_matches[level] = matched

    # En yuksek skoru bul
    if not any(level_scores.values()):
        # Hic eslesen pattern yok -> varsayilan SKILL (cogu YKS sorusu)
        return WebbDOKResult(
            level=WebbDOKLevel.SKILL,
            confidence=0.3,
            matched_patterns=[],
            rationale=(
                "Belirgin DOK pattern tespit edilemedi. "
                "YKS sorulari genellikle DOK Level 2 (Beceri) seviyesindedir."
            ),
        )

    # En yuksek skora sahip seviye
    best_level = max(level_scores, key=level_scores.get)  # type: ignore
    best_score = level_scores[best_level]
    best_matches = level_matches[best_level]

    # Guven hesaplama
    total_score = sum(level_scores.values())
    if total_score == 0:
        confidence = 0.3
    else:
        confidence = min(0.95, 0.5 + (best_score / total_score) * 0.5)

    # Eger bircok seviyede eslesen varsa guven dusur
    levels_with_matches = sum(1 for score in level_scores.values() if score > 0)
    if levels_with_matches > 1:
        confidence *= 0.85

    # Turkce aciklama
    rationale = _generate_rationale(best_level, best_matches, confidence)

    return WebbDOKResult(
        level=best_level,
        confidence=confidence,
        matched_patterns=best_matches,
        rationale=rationale,
    )


def _generate_rationale(
    level: WebbDOKLevel, matched_patterns: list[str], confidence: float
) -> str:
    """Turkce aciklama uret."""
    level_descriptions = {
        WebbDOKLevel.RECALL: (
            "Hatirlama ve Yeniden Uretim seviyesi. "
            "Ogrenci bilgiyi hatirlar, tanim yapar, formul yazar."
        ),
        WebbDOKLevel.SKILL: (
            "Beceri ve Kavram seviyesi. "
            "Ogrenci beceri uygular, cok adimli rutin islemler yapar."
        ),
        WebbDOKLevel.STRATEGIC: (
            "Stratejik Dusunme seviyesi. "
            "Ogrenci plan yapar, gerekcelendirir, karmasik problemleri cozer."
        ),
        WebbDOKLevel.EXTENDED: (
            "Genisletilmis Dusunme seviyesi. "
            "Ogrenci arastirma yapar, sentez olusturur, "
            "disiplinler arasi baglanti kurar."
        ),
    }

    base = level_descriptions.get(level, "Bilinmeyen seviye.")

    if confidence > 0.7:
        certainty = "Yuksek guvenle siniflandirildi."
    elif confidence > 0.5:
        certainty = "Orta guvenle siniflandirildi."
    else:
        certainty = "Dusuk guvenle siniflandirildi. Manuel dogrulama onerilir."

    return f"{base} {certainty}"


def estimate_dok_from_bloom(bloom_level: str) -> WebbDOKLevel:
    """Bloom taksonomisinden Webb DOK seviyesi tahmin et.

    Cross-reference mapping:
    - Bloom Remember/Understand -> DOK 1 (RECALL)
    - Bloom Apply -> DOK 2 (SKILL)
    - Bloom Analyze/Evaluate -> DOK 3 (STRATEGIC)
    - Bloom Create -> DOK 4 (EXTENDED)

    Args:
        bloom_level: Bloom seviyesi (or-normalized string).

    Returns:
        Tahmin edilen WebbDOKLevel.

    Example:
        >>> estimate_dok_from_bloom("understand")
        <WebbDOKLevel.RECALL: 'hatirlama'>
        >>> estimate_dok_from_bloom("analiz")
        <WebbDOKLevel.STRATEGIC: 'stratejik'>
    """
    bloom_norm = _normalize(bloom_level)

    # Bloom -> DOK mapping
    if any(
        keyword in bloom_norm
        for keyword in ["remember", "hatirlama", "understand", "anlama", "kavrama"]
    ):
        return WebbDOKLevel.RECALL
    elif any(keyword in bloom_norm for keyword in ["apply", "uygulama"]):
        return WebbDOKLevel.SKILL
    elif any(
        keyword in bloom_norm
        for keyword in ["analyze", "analiz", "evaluate", "degerlendirme"]
    ):
        return WebbDOKLevel.STRATEGIC
    elif any(keyword in bloom_norm for keyword in ["create", "yaratma", "sentez"]):
        return WebbDOKLevel.EXTENDED
    else:
        # Varsayilan: SKILL (cogu egitim icerigi)
        return WebbDOKLevel.SKILL
