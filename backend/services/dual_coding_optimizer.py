"""Dual Coding Optimizer - Paivio & Mayer Multimedia Principles.

Bilimsel temel:
- Paivio Dual Coding: Sözel + görsel kanallar birlikte → güçlü öğrenme
- Mayer 12 İlke: Coherence, Signaling, Redundancy, Spatial/Temporal Contiguity,
  Segmenting, Pre-training, Modality, Multimedia, Personalization, Voice, Image

YKS Uygulaması:
- Soru metinlerinin multimedya kalitesini değerlendirir
- Görsel ekleme/iyileştirme önerileri sunar
- Layout optimizasyonu yapar
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum


class VisualType(str, Enum):
    """Soru için uygun görsel tipi."""

    NONE = "none"
    DIAGRAM = "diagram"  # Geometri, fizik
    GRAPH = "graph"  # Fonksiyon grafikleri, istatistik
    TABLE = "table"  # Veri tablosu
    MAP = "map"  # Coğrafya haritası
    TIMELINE = "timeline"  # Tarih zaman çizelgesi
    FLOWCHART = "flowchart"  # Süreç akışı (biyoloji, kimya)
    CHEMICAL_STRUCTURE = "chemical"  # Kimya yapı formülü
    ILLUSTRATION = "illustration"  # Genel açıklayıcı görsel


class MayerPrinciple(str, Enum):
    """Mayer'in 12 Multimedya İlkesi."""

    COHERENCE = "coherence"  # Gereksiz bilgiyi çıkar
    SIGNALING = "signaling"  # Önemli bilgiyi vurgula
    REDUNDANCY = "redundancy"  # Aynı bilgiyi tekrarlama
    SPATIAL_CONTIGUITY = "spatial"  # Metin+görsel yakın olsun
    TEMPORAL_CONTIGUITY = "temporal"  # Eş zamanlı sun
    SEGMENTING = "segmenting"  # Parçalara böl
    PRETRAINING = "pretraining"  # Ön bilgi ver
    MODALITY = "modality"  # Yazı yerine ses
    MULTIMEDIA = "multimedia"  # Metin+görsel birlikte
    PERSONALIZATION = "personalization"  # Konuşma dili kullan
    VOICE = "voice"  # İnsan sesi
    IMAGE = "image"  # Anlatıcı görüntüsü


@dataclass
class PrincipleScore:
    """Tek bir Mayer ilkesi için skor."""

    principle: MayerPrinciple
    score: float  # 0.0 - 1.0
    feedback: str


@dataclass
class DualCodingScore:
    """Multimedya kalite analiz sonucu."""

    overall_score: float  # 0.0 - 1.0
    principle_scores: list[PrincipleScore] = field(default_factory=list)
    suggested_visual_type: VisualType = VisualType.NONE
    optimization_suggestions: list[str] = field(default_factory=list)
    word_count: int = 0
    has_visual: bool = False
    has_table: bool = False
    has_formula: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "overall_score": round(self.overall_score, 3),
            "principle_scores": [
                {
                    "principle": ps.principle.value,
                    "score": round(ps.score, 3),
                    "feedback": ps.feedback,
                }
                for ps in self.principle_scores
            ],
            "suggested_visual_type": self.suggested_visual_type.value,
            "optimization_suggestions": self.optimization_suggestions,
            "word_count": self.word_count,
            "has_visual": self.has_visual,
            "has_table": self.has_table,
            "has_formula": self.has_formula,
        }


@dataclass
class VisualSuggestion:
    """Görsel ekleme önerisi."""

    visual_type: VisualType
    reason: str
    priority: float  # 0-1, higher = more important
    description: str  # Ne tür görsel eklenmeli


def _normalize_text(text: str) -> str:
    """NFC normalize + Turkish lowercase."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return text.replace("İ", "i").replace("I", "ı").lower()


# Subject → visual type mapping for YKS
_SUBJECT_VISUAL_MAP: dict[str, list[VisualType]] = {
    "matematik": [VisualType.GRAPH, VisualType.DIAGRAM, VisualType.TABLE],
    "geometri": [VisualType.DIAGRAM],
    "fizik": [VisualType.DIAGRAM, VisualType.GRAPH],
    "kimya": [VisualType.CHEMICAL_STRUCTURE, VisualType.TABLE],
    "biyoloji": [VisualType.FLOWCHART, VisualType.ILLUSTRATION],
    "tarih": [VisualType.TIMELINE, VisualType.MAP],
    "cografya": [VisualType.MAP, VisualType.TABLE],
    "turkce": [VisualType.NONE],
    "edebiyat": [VisualType.TIMELINE],
}

# Patterns suggesting visual content is present
_VISUAL_INDICATORS = [
    r"şekil",
    r"grafik",
    r"tablo",
    r"diyagram",
    r"harita",
    r"çizim",
    r"görsel",
    r"resim",
    r"figür",
    r"koordinat",
]

# Patterns suggesting redundancy (same info repeated)
_REDUNDANCY_PATTERNS = [
    r"yukarıda(ki)?\s+(belirtildiği|görüldüğü|açıklandığı)",
    r"tekrar\s+belirt",
    r"daha\s+önce\s+(söylendiği|belirtildiği)",
]

# Signaling keywords (emphasis markers)
_SIGNALING_PATTERNS = [
    r"özellikle",
    r"dikkat",
    r"önemli",
    r"unutma",
    r"not:",
    r"anahtar",
    r"kritik",
    r"temel\s+olarak",
]


def analyze_question_multimedia(
    question_text: str,
    visual_content: str | None = None,
    subject: str = "",
) -> DualCodingScore:
    """Soru metninin multimedya kalitesini analiz et.

    Mayer'in uygulanabilir ilkelerini değerlendirir.

    Args:
        question_text: Soru metni.
        visual_content: Görsel içerik metni (varsa).
        subject: Ders adı (matematik, fizik, vb.).

    Returns:
        DualCodingScore nesnesi.
    """
    if not question_text:
        return DualCodingScore(overall_score=0.0)

    normalized = _normalize_text(question_text)
    words = normalized.split()
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r"[.!?]", question_text) if s.strip()]

    has_visual = visual_content is not None and len(visual_content or "") > 0
    has_table = bool(re.search(r"tablo|çizelge", normalized))
    has_formula = bool(re.search(r"[=+\-*/^√∫∑]|formül", question_text))

    principles: list[PrincipleScore] = []
    suggestions: list[str] = []

    # 1. COHERENCE: Gereksiz bilgi yok mu?
    filler_count = len(
        re.findall(r"\b(aslında|gerçekten|kesinlikle|tabii ki)\b", normalized)
    )
    coherence_score = max(0.0, 1.0 - filler_count * 0.15)
    if word_count > 150:
        coherence_score *= 0.7
        suggestions.append("Soru metni çok uzun (>150 kelime). Sadeleştirme önerilir.")
    principles.append(
        PrincipleScore(
            MayerPrinciple.COHERENCE,
            coherence_score,
            "İyi" if coherence_score > 0.7 else "Gereksiz bilgi azaltılmalı",
        )
    )

    # 2. SIGNALING: Önemli bilgi vurgulanmış mı?
    signal_count = sum(1 for p in _SIGNALING_PATTERNS if re.search(p, normalized))
    signaling_score = min(1.0, 0.5 + signal_count * 0.2)
    signaling_feedback = (
        "Yeterli vurgu"
        if signaling_score > 0.6
        else "Anahtar bilgiler vurgulanmalı"
    )
    principles.append(
        PrincipleScore(MayerPrinciple.SIGNALING, signaling_score, signaling_feedback)
    )

    # 3. REDUNDANCY: Tekrar var mı?
    redundancy_hits = sum(1 for p in _REDUNDANCY_PATTERNS if re.search(p, normalized))
    redundancy_score = max(0.0, 1.0 - redundancy_hits * 0.3)
    if redundancy_hits > 0:
        suggestions.append("Tekrarlanan bilgi tespit edildi. Fazlalık çıkarılmalı.")
    principles.append(
        PrincipleScore(
            MayerPrinciple.REDUNDANCY,
            redundancy_score,
            "Tekrar yok" if redundancy_score > 0.8 else "Tekrar azaltılmalı",
        )
    )

    # 4. SEGMENTING: Uzun metin parçalara bölünmüş mü?
    if word_count > 80:
        segment_score = min(1.0, len(sentences) / (word_count / 25))
    else:
        segment_score = 1.0
    principles.append(
        PrincipleScore(
            MayerPrinciple.SEGMENTING,
            segment_score,
            "İyi bölünmüş" if segment_score > 0.6 else "Metin parçalara bölünmeli",
        )
    )

    # 5. MULTIMEDIA: Metin+görsel birlikte mi?
    subject_lower = _normalize_text(subject)
    expected_visuals = _SUBJECT_VISUAL_MAP.get(subject_lower, [])
    needs_visual = (
        len(expected_visuals) > 0 and VisualType.NONE not in expected_visuals
    )

    if needs_visual and has_visual:
        multimedia_score = 1.0
    elif needs_visual and not has_visual:
        multimedia_score = 0.3
        suggestions.append(f"{subject} sorusu için görsel eklenmesi önerilir.")
    elif not needs_visual:
        multimedia_score = 0.8  # Visual not expected
    else:
        multimedia_score = 0.9  # Has visual, not strictly needed
    principles.append(
        PrincipleScore(
            MayerPrinciple.MULTIMEDIA,
            multimedia_score,
            "Multimedya uygun" if multimedia_score > 0.6 else "Görsel eklenmeli",
        )
    )

    # 6. PERSONALIZATION: Konuşma dili mi?
    formal_markers = len(
        re.findall(r"\b(olup|olduğu|edilmiştir|bulunmaktadır)\b", normalized)
    )
    informal_markers = len(
        re.findall(r"\b(bulalım|hesaplayalım|düşünelim|bakalım)\b", normalized)
    )
    if formal_markers > 3 and informal_markers == 0:
        personal_score = 0.4
        suggestions.append("Daha konuşma diline yakın ifadeler kullanılabilir.")
    else:
        personal_score = 0.7 + min(0.3, informal_markers * 0.1)
    principles.append(
        PrincipleScore(
            MayerPrinciple.PERSONALIZATION,
            personal_score,
            "Uygun dil" if personal_score > 0.6 else "Daha samimi dil önerilir",
        )
    )

    # Determine suggested visual type
    visual_indicators = any(re.search(p, normalized) for p in _VISUAL_INDICATORS)
    if expected_visuals and not has_visual:
        suggested_visual = expected_visuals[0]
    elif visual_indicators and not has_visual:
        suggested_visual = VisualType.ILLUSTRATION
    else:
        suggested_visual = VisualType.NONE

    # Overall score (weighted average)
    weights = {
        MayerPrinciple.COHERENCE: 0.25,
        MayerPrinciple.SIGNALING: 0.10,
        MayerPrinciple.REDUNDANCY: 0.15,
        MayerPrinciple.SEGMENTING: 0.15,
        MayerPrinciple.MULTIMEDIA: 0.25,
        MayerPrinciple.PERSONALIZATION: 0.10,
    }
    overall = sum(ps.score * weights.get(ps.principle, 0.1) for ps in principles)
    overall = max(0.0, min(1.0, overall))

    return DualCodingScore(
        overall_score=overall,
        principle_scores=principles,
        suggested_visual_type=suggested_visual,
        optimization_suggestions=suggestions,
        word_count=word_count,
        has_visual=has_visual,
        has_table=has_table,
        has_formula=has_formula,
    )


def suggest_visual_enhancement(
    question_text: str,
    subject: str = "",
) -> VisualSuggestion:
    """Soru metnine uygun görsel tipi öner.

    Args:
        question_text: Soru metni.
        subject: Ders adı.

    Returns:
        VisualSuggestion nesnesi.
    """
    subject_lower = _normalize_text(subject)
    normalized = _normalize_text(question_text)

    # Subject-based suggestion
    expected = _SUBJECT_VISUAL_MAP.get(subject_lower, [])

    if not expected or VisualType.NONE in expected:
        return VisualSuggestion(
            visual_type=VisualType.NONE,
            reason="Bu ders için görsel gerekli değil",
            priority=0.0,
            description="Metin tabanlı soru yeterli",
        )

    # Check for specific content patterns
    if re.search(r"(grafik|fonksiyon|eğri|koordinat)", normalized):
        vtype = VisualType.GRAPH
        desc = "Fonksiyon grafiği veya koordinat düzlemi"
    elif re.search(r"(üçgen|kare|daire|açı|kenar|köşe|alan)", normalized):
        vtype = VisualType.DIAGRAM
        desc = "Geometrik şekil çizimi"
    elif re.search(r"(tablo|veri|istatistik|oran|yüzde)", normalized):
        vtype = VisualType.TABLE
        desc = "Veri tablosu"
    elif re.search(r"(harita|bölge|il|ülke|coğrafi)", normalized):
        vtype = VisualType.MAP
        desc = "Coğrafi harita"
    elif re.search(r"(dönem|yüzyıl|tarih|savaş|antlaşma)", normalized):
        vtype = VisualType.TIMELINE
        desc = "Kronolojik zaman çizelgesi"
    elif re.search(r"(reaksiyon|bileşik|element|molekül|asit|baz)", normalized):
        vtype = VisualType.CHEMICAL_STRUCTURE
        desc = "Kimyasal yapı formülü"
    elif re.search(r"(hücre|organ|sistem|canlı|bitki|hayvan)", normalized):
        vtype = VisualType.FLOWCHART
        desc = "Biyolojik süreç akış şeması"
    else:
        vtype = expected[0] if expected else VisualType.ILLUSTRATION
        desc = "Konu ile ilgili açıklayıcı görsel"

    # Priority based on how much visual would help
    words = normalized.split()
    priority = 0.5
    if len(words) > 80:
        priority += 0.2  # Long text benefits more from visuals
    if vtype in (VisualType.DIAGRAM, VisualType.GRAPH):
        priority += 0.15  # Spatial content strongly needs visual

    return VisualSuggestion(
        visual_type=vtype,
        reason=f"{subject} dersi için {vtype.value} önerilir",
        priority=min(1.0, round(priority, 2)),
        description=desc,
    )


def optimize_question_layout(
    question_text: str,
    options: list[str] | None = None,
) -> dict:
    """Soru layout'unu Mayer ilkelerine göre optimize et.

    Args:
        question_text: Soru metni.
        options: Şık listesi (A, B, C, D, E).

    Returns:
        Dict with original, optimized, changes, option_count.
    """
    if not question_text:
        return {"original": "", "optimized": "", "changes": [], "option_count": 0}

    changes: list[str] = []
    optimized = question_text

    # Segmenting: Add line breaks for long sentences
    sentences = re.split(r"(?<=[.!?])\s+", optimized)
    if len(sentences) > 3 and len(optimized) > 200:
        optimized = "\n".join(sentences)
        changes.append("Uzun metin paragraflara bölündü")

    # Coherence: Flag filler words (don't auto-remove, just flag)
    fillers = re.findall(
        r"\b(aslında|gerçekten|kesinlikle|tabii ki|esasen)\b",
        _normalize_text(optimized),
    )
    if fillers:
        changes.append(
            f"Gereksiz dolgu kelimeleri tespit edildi: {', '.join(set(fillers))}"
        )

    # Signaling: Suggest bold for key terms
    key_terms = re.findall(
        r"\b(hangisi|kaçtır|bulunuz|hesaplayınız|gösteriniz)\b",
        _normalize_text(optimized),
    )
    if key_terms:
        changes.append(f"Vurgulanması gereken terimler: {', '.join(set(key_terms))}")

    return {
        "original": question_text,
        "optimized": optimized,
        "changes": changes,
        "option_count": len(options) if options else 0,
    }
