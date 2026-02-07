"""SOLO Taxonomy Classifier.

SOLO (Structure of Observed Learning Outcomes) classification for YKS questions.
Ported from orchestrator/core/taxonomy_classifier.py.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from models.question_generation import SOLOLevel


class SOLOLevelInt(Enum):
    """SOLO taksonomi seviyeleri (internal numeric mapping)."""

    PRESTRUCTURAL = 1  # Yapı-öncesi
    UNISTRUCTURAL = 2  # Tek-yapılı
    MULTISTRUCTURAL = 3  # Çok-yapılı
    RELATIONAL = 4  # İlişkisel
    EXTENDED_ABSTRACT = 5  # Genişletilmiş soyut


# SOLO seviye isimleri (Türkçe)
SOLO_LEVEL_NAMES: dict[int, str] = {
    1: "Yapı-öncesi",
    2: "Tek-yapılı",
    3: "Çok-yapılı",
    4: "İlişkisel",
    5: "Genişletilmiş soyut",
}

# SOLO_LEVEL_NAMES to SOLOLevel enum mapping
SOLO_INT_TO_ENUM: dict[int, SOLOLevel] = {
    1: SOLOLevel.PRESTRUCTURAL,
    2: SOLOLevel.UNISTRUCTURAL,
    3: SOLOLevel.MULTISTRUCTURAL,
    4: SOLOLevel.RELATIONAL,
    5: SOLOLevel.EXTENDED_ABSTRACT,
}

# Verbal subjects favor SOLO taxonomy
SOLO_SUBJECTS: list[str] = [
    "turkce",
    "edebiyat",
    "tarih",
    "felsefe",
    "din kulturu",
    "cografya",
    "sosyal bilimler",
]


@dataclass
class PatternEntry:
    """Ağırlıklı regex pattern girişi.

    Attributes:
        pattern: Regex pattern (re.UNICODE ile çalışır).
        weight: Ağırlık (1-5). Yüksek = güçlü sinyal.
        method: Tespit yöntemi ("verb", "structure", "relation", "scenario").
        cap_confidence: Bu pattern eşleştiğinde confidence üst sınırı.
    """

    pattern: str
    weight: int = 3
    method: str = "verb"
    cap_confidence: float = 0.95


# SOLO pattern bundles (weighted scoring)
SOLO_PATTERNS: dict[int, list[PatternEntry]] = {
    2: [  # Unistructural — tek bilgi, tek kural
        # Güçlü fiil kalıpları (w=3)
        PatternEntry(r"\btanımla\w*\b", 3, "verb"),
        PatternEntry(r"\badlandır\w*\b", 3, "verb"),
        PatternEntry(r"\bbelirt\w*\b", 3, "verb"),
        PatternEntry(r"\bveril\w*\s+tanım\w*\b", 3, "verb"),
        PatternEntry(r"\bnedir\b", 3, "verb"),
        PatternEntry(r"\bkimdir\b", 3, "verb"),
        PatternEntry(r"\bne\s+zaman\b", 3, "verb"),
        PatternEntry(r"\bnerede\b", 3, "verb"),
        PatternEntry(r"\bhatırla\w*\b", 3, "verb"),
        PatternEntry(r"\bsöyle\w*\b", 2, "verb"),
        # Zayıf / genel sinyaller (w=1) — tek başına seviye belirleyici DEĞİL
        PatternEntry(r"\başağıdakilerden\s+hangisi\b", 1, "structure"),
        PatternEntry(r"\bhangisi\b", 1, "structure"),
    ],
    3: [  # Multistructural — birden fazla parça, ilişki yok
        # Yapı sinyalleri (w=3) — casefold sonrası lowercase
        PatternEntry(r"\bi[.)]\s", 3, "structure"),
        PatternEntry(r"\bii[.)]\s", 3, "structure"),
        PatternEntry(r"\biii[.)]\s", 3, "structure"),
        PatternEntry(r"\biv[.)]\s", 3, "structure"),
        PatternEntry(r"\byargı\w*\b", 3, "structure"),
        PatternEntry(r"\böncül\w*\b", 3, "structure"),
        PatternEntry(r"\bnumaralı\b", 3, "structure"),
        PatternEntry(r"\başağıdakilerden\s+hangileri\b", 3, "structure"),
        PatternEntry(r"\bkaç\s+tane\b", 3, "structure"),
        PatternEntry(r"\bkaçıdır\b", 3, "structure"),
        # Fiil kalıpları (w=2)
        PatternEntry(r"\blistele\w*\b", 2, "verb"),
        PatternEntry(r"\bsırala\w*\b", 2, "verb"),
        PatternEntry(r"\bözellik\w*\b", 2, "verb"),
        PatternEntry(r"\bverilenler\w*\b", 2, "verb"),
        PatternEntry(r"\bözetle\w*\b", 2, "verb"),
        PatternEntry(r"\bbetimle\w*\b", 2, "verb"),
        PatternEntry(r"\bsayınız\b", 2, "verb"),
        PatternEntry(r"\bbelirtiniz\b", 2, "verb"),
        PatternEntry(r"\bhem\s+\w+\s+hem\b", 2, "structure"),
    ],
    4: [  # Relational — ilişki, çıkarım, neden-sonuç
        # İlişki operatörleri (w=4)
        PatternEntry(r"\bilişkilendir\w*\b", 4, "relation"),
        PatternEntry(r"\barasındaki\s+ilişki\b", 4, "relation"),
        PatternEntry(r"\bneden\w*\b.{0,10}\bsonuç\w*\b", 4, "relation"),
        PatternEntry(r"\bsebep\w*\b.{0,10}\bsonuç\w*\b", 4, "relation"),
        PatternEntry(r"\bbu\s+nedenle\b", 4, "relation"),
        PatternEntry(r"\bdolayısıyla\b", 4, "relation"),
        PatternEntry(r"\bçünkü\b", 4, "relation"),
        PatternEntry(r"\bbuna\s+rağmen\b", 4, "relation"),
        PatternEntry(r"\boysa\b", 3, "relation"),
        # Çıkarım/yorum (w=4)
        PatternEntry(r"\bçıkarım\w*\b", 4, "verb"),
        PatternEntry(r"\bçıkarıl\w*\b", 4, "verb"),
        PatternEntry(r"\bsonuç\s+çıkar\w*\b", 4, "verb"),
        PatternEntry(r"\byorumla\w*\b", 4, "verb"),
        PatternEntry(r"\bgerekçelendir\w*\b", 4, "verb"),
        PatternEntry(r"\bkanıtla\w*\b", 4, "verb"),
        PatternEntry(r"\banlam\s+bütünlüğü\b", 3, "verb"),
        PatternEntry(r"\bbağlantı\s+kur\w*\b", 3, "verb"),
        PatternEntry(r"\bbütünleştir\w*\b", 3, "verb"),
        # Karşılaştırma/ayırt etme (w=3)
        PatternEntry(r"\bkarşılaştır\w*\b", 3, "verb"),
        PatternEntry(r"\bfark\w*\b", 2, "verb"),
        PatternEntry(r"\bbenzer\w*\b", 2, "verb"),
        PatternEntry(r"\bayırt\w*\b", 3, "verb"),
        PatternEntry(r"\bçeliş\w*\b", 3, "verb"),
        # Türkçe paragraf özel (w=3)
        PatternEntry(r"\bana\s+düşünce\b", 3, "verb"),
        PatternEntry(r"\byardımcı\s+düşünce\b", 3, "verb"),
        PatternEntry(r"\byazar\w*\s+(?:tutumu|amacı)\b", 3, "verb"),
        PatternEntry(r"\bnasıl\w*\b.{0,15}\betkile\w*\b", 3, "verb"),
    ],
    5: [  # Extended Abstract — transfer, genelleme, hipotez
        # Transfer / yeni durum (w=5)
        PatternEntry(r"\bfarklı\s+bir\s+durum\w*\b", 5, "verb"),
        PatternEntry(r"\byeni\s+durum\w*\b", 5, "verb"),
        PatternEntry(r"\bfarklı\s+bağlam\w*\b", 5, "verb"),
        PatternEntry(r"\bfarklı\s+alan\w*\b", 5, "verb"),
        PatternEntry(r"\btransfer\w*\b", 5, "verb"),
        # Genelleme / kuramsallaştırma (w=5)
        PatternEntry(r"\bgenelle\w*\b", 5, "verb"),
        PatternEntry(r"\bevrensel\w*\b", 5, "verb"),
        PatternEntry(r"\bhipotez\w*\b", 5, "verb"),
        PatternEntry(r"\bvarsayım\w*\b", 5, "verb"),
        PatternEntry(r"\bkuram\w*\b", 5, "verb"),
        PatternEntry(r"\beleştir\w*\b", 5, "verb"),
        PatternEntry(r"\btartış\w*\b", 5, "verb"),
        PatternEntry(r"\bdeğerlendir\w*\b", 5, "verb"),
        PatternEntry(r"\böngör\w*\b", 4, "verb"),
        PatternEntry(r"\btahmin\s+et\w*\b", 4, "verb"),
        PatternEntry(r"\bbaşka\s+örnek\b", 4, "verb"),
    ],
}

# Minimum score thresholds per SOLO level
SOLO_THRESHOLDS: dict[int, int] = {2: 2, 3: 3, 4: 4, 5: 5}

# Structure cues: SOLO cross-cutting bonuses
STRUCTURE_CUES: list[tuple[str, dict[str, int]]] = [
    # Roman numerals → SOLO L3 boost (casefold sonrası lowercase)
    (r"\bi[.)]\s", {"solo_3": 3}),
    (r"\bii[.)]\s", {"solo_3": 3}),
    (r"\biii[.)]\s", {"solo_3": 3}),
    (r"\biv[.)]\s", {"solo_3": 3}),
]

# Relation cues: SOLO L4 boost
RELATION_CUES: list[tuple[str, dict[str, int]]] = [
    (r"\bçünkü\b", {"solo_4": 3}),
    (r"\bdolayısıyla\b", {"solo_4": 3}),
    (r"\bbu\s+nedenle\b", {"solo_4": 3}),
    (r"\bbuna\s+rağmen\b", {"solo_4": 3}),
    (r"\boysa\b", {"solo_4": 2}),
    (r"\bbuna\s+göre\b", {"solo_4": 2}),
]

# Precompile regex for preprocessing
_RE_OPTION_PREFIX = re.compile(r"^[A-E][).]\s*", re.MULTILINE | re.UNICODE)
_RE_MULTI_SPACE = re.compile(r"\s+")
_RE_ELLIPSIS = re.compile(r"…")
_RE_SMART_QUOTE = re.compile(r"[''ʼ]")


@dataclass
class SOLOResult:
    """SOLO sınıflandırma sonucu.

    Attributes:
        level: SOLO seviyesi (SOLOLevel enum).
        confidence: Güven skoru (0.0-1.0).
        matched_patterns: Eşleşen pattern sayısı.
        subject_weight: Ders ağırlığı (verbal subjects için yüksek).
    """

    level: SOLOLevel = SOLOLevel.UNISTRUCTURAL
    confidence: float = 0.0
    matched_patterns: list[str] = field(default_factory=list)
    subject_weight: float = 1.0

    def to_dict(self) -> dict:
        """Dict representation."""
        return {
            "level": self.level.value,
            "confidence": round(self.confidence, 3),
            "matched_patterns": self.matched_patterns[:5],  # Top 5
            "subject_weight": round(self.subject_weight, 2),
        }


def _normalize_tr(text: str) -> str:
    """Turkish text normalization.

    CRITICAL: NFC + Turkish lowercase mapping (İ→i, I→ı).
    """
    if not text:
        return text
    # Step 1: Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)
    # Step 2: Turkish-specific lowercase (casefold handles İ→i)
    text = text.casefold().strip()
    return text


def _preprocess(text: str) -> str:
    """Soru metnini ön işleme.

    1. Turkish normalization (casefold handles İ/I)
    2. Normalize punctuation
    3. Strip answer option prefixes (A-E only, NOT Roman numerals)
    4. Collapse whitespace
    """
    text = _normalize_tr(text)
    text = _RE_ELLIPSIS.sub("...", text)
    text = _RE_SMART_QUOTE.sub("'", text)
    text = _RE_OPTION_PREFIX.sub("", text)
    text = _RE_MULTI_SPACE.sub(" ", text)
    return text


def classify_solo(question_text: str, subject: str = "") -> SOLOResult:
    """SOLO taksonomisi sınıflandırması (weighted scoring).

    Args:
        question_text: Soru metni.
        subject: Ders adı (opsiyonel, subject_weight için).

    Returns:
        SOLOResult with level, confidence, matched_patterns.
    """
    text = _preprocess(question_text)

    # Score each level
    scores: dict[int, int] = {2: 0, 3: 0, 4: 0, 5: 0}
    all_matched: dict[int, list[str]] = {2: [], 3: [], 4: [], 5: []}

    for level, entries in SOLO_PATTERNS.items():
        for entry in entries:
            if re.search(entry.pattern, text, re.UNICODE):
                scores[level] += entry.weight
                all_matched[level].append(entry.pattern)

    # Add structure cue bonuses
    for pattern, bonuses in STRUCTURE_CUES:
        if re.search(pattern, text, re.UNICODE):
            for key, bonus in bonuses.items():
                if key.startswith("solo_"):
                    lvl = int(key.split("_")[1])
                    if lvl in scores:
                        scores[lvl] += bonus

    # Add relation cue bonuses
    for pattern, bonuses in RELATION_CUES:
        if re.search(pattern, text, re.UNICODE):
            for key, bonus in bonuses.items():
                if key.startswith("solo_"):
                    lvl = int(key.split("_")[1])
                    if lvl in scores:
                        scores[lvl] += bonus

    # Pick level: threshold gate → argmax → tiebreak higher level
    qualifying = {
        lvl: sc for lvl, sc in scores.items() if sc >= SOLO_THRESHOLDS.get(lvl, 2)
    }

    if not qualifying:
        # No qualifying level, default to UNISTRUCTURAL
        return SOLOResult(
            level=SOLOLevel.UNISTRUCTURAL,
            confidence=0.3,
            subject_weight=_get_subject_weight(subject),
        )

    # argmax with tiebreak: higher level wins
    best_level = max(qualifying, key=lambda lvl: (qualifying[lvl], lvl))
    best_score = qualifying[best_level]

    # Margin-based confidence
    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
    margin = (best_score - second_score) / max(best_score, 1)
    confidence = min(0.95, 0.5 + margin * 0.45)

    return SOLOResult(
        level=SOLO_INT_TO_ENUM[best_level],
        confidence=round(confidence, 3),
        matched_patterns=all_matched.get(best_level, [])[:5],
        subject_weight=_get_subject_weight(subject),
    )


def _get_subject_weight(subject: str) -> float:
    """Get subject weight (verbal subjects favor SOLO).

    Args:
        subject: Subject name.

    Returns:
        Weight (1.0-2.0).
    """
    if not subject:
        return 1.0
    subject_lower = _normalize_tr(subject)
    for solo_subj in SOLO_SUBJECTS:
        if solo_subj in subject_lower:
            return 1.5  # Verbal subject boost
    return 1.0
