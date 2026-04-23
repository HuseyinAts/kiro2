"""Marzano Taxonomy Classifier.

Marzano's New Taxonomy classification for YKS questions.
Ported from orchestrator/core/taxonomy_classifier.py.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from models.question_generation import MarzanoProcessLevel, MarzanoSystem

# Marzano system names (Turkish)
MARZANO_SYSTEM_NAMES: dict[int, str] = {
    1: "Öz-sistem",
    2: "Üstbilişsel",
    3: "Bilişsel",
}

# Marzano cognitive level names (Turkish)
MARZANO_COGNITIVE_NAMES: dict[int, str] = {
    1: "Geri çağırma",
    2: "Kavrama",
    3: "Analiz",
    4: "Bilgi kullanımı",
}

# Enum to int mapping
MARZANO_SYSTEM_TO_INT: dict[MarzanoSystem, int] = {
    MarzanoSystem.SELF_SYSTEM: 1,
    MarzanoSystem.METACOGNITIVE: 2,
    MarzanoSystem.COGNITIVE: 3,
}

MARZANO_PROCESS_TO_INT: dict[MarzanoProcessLevel, int] = {
    MarzanoProcessLevel.RETRIEVAL: 1,
    MarzanoProcessLevel.COMPREHENSION: 2,
    MarzanoProcessLevel.ANALYSIS: 3,
    MarzanoProcessLevel.KNOWLEDGE_UTILIZATION: 4,
}

# Int to enum mapping
INT_TO_MARZANO_SYSTEM: dict[int, MarzanoSystem] = {
    1: MarzanoSystem.SELF_SYSTEM,
    2: MarzanoSystem.METACOGNITIVE,
    3: MarzanoSystem.COGNITIVE,
}

INT_TO_MARZANO_PROCESS: dict[int, MarzanoProcessLevel] = {
    1: MarzanoProcessLevel.RETRIEVAL,
    2: MarzanoProcessLevel.COMPREHENSION,
    3: MarzanoProcessLevel.ANALYSIS,
    4: MarzanoProcessLevel.KNOWLEDGE_UTILIZATION,
}

# Quantitative subjects favor Marzano taxonomy
MARZANO_SUBJECTS: list[str] = [
    "matematik",
    "fizik",
    "kimya",
    "biyoloji",
    "geometri",
    "fen bilimleri",
]


@dataclass
class PatternEntry:
    """Ağırlıklı regex pattern girişi.

    Attributes:
        pattern: Regex pattern (re.UNICODE ile çalışır).
        weight: Ağırlık (1-5). Yüksek = güçlü sinyal.
        method: Tespit yöntemi ("verb", "structure", "relation", "scenario", "error").
        cap_confidence: Bu pattern eşleştiğinde confidence üst sınırı.
    """

    pattern: str
    weight: int = 3
    method: str = "verb"
    cap_confidence: float = 0.95


# Marzano pattern bundles (weighted scoring)
MARZANO_PATTERNS: dict[str, list[PatternEntry]] = {
    "self_system": [
        PatternEntry(r"\bneden\s+önemli\b", 2, "verb", 0.55),
        PatternEntry(r"\bdeğer\s+ver\w*\b", 2, "verb", 0.55),
        PatternEntry(r"\bdeğer\s+yargı\w*\b", 2, "verb", 0.55),
        PatternEntry(r"\btutum\w*\b", 2, "verb", 0.55),
        PatternEntry(r"\bmotivasyon\w*\b", 2, "verb", 0.55),
        PatternEntry(r"\bniçin\s+öğren\w*\b", 1, "verb", 0.55),
        PatternEntry(r"\bönem\s+taşı\w*\b", 1, "verb", 0.55),
    ],
    "metacognitive": [
        PatternEntry(r"\bhangi\s+yöntem\w*\b", 3, "verb", 0.65),
        PatternEntry(r"\bhangi\s+strateji\w*\b", 3, "verb", 0.65),
        PatternEntry(r"\bilk\s+adım\w*\b", 3, "verb", 0.65),
        PatternEntry(r"\bhangi\s+adım\w*\b", 3, "verb", 0.65),
        PatternEntry(r"\bplanla\w*\b", 2, "verb", 0.65),
        PatternEntry(r"\bkendini\s+kontrol\b", 2, "verb", 0.65),
        PatternEntry(r"\bgözden\s+geçir\w*\b", 2, "verb", 0.65),
        PatternEntry(r"\bstrateji\w*\b", 2, "verb", 0.65),
        PatternEntry(r"\bsistematik\w*\b", 2, "verb", 0.65),
        PatternEntry(r"\bnasıl\s+çözersin\b", 3, "verb", 0.65),
        PatternEntry(r"\badım\s+adım\b", 2, "verb", 0.65),
    ],
    "cognitive_retrieval": [
        PatternEntry(r"\btanım\w*\b", 4, "verb"),
        PatternEntry(r"\bformül\w*\b", 4, "verb"),
        PatternEntry(r"\bsembol\w*\b", 4, "verb"),
        PatternEntry(r"\bbirim\w*\b", 4, "verb"),
        PatternEntry(r"\bkural\w*\b", 4, "verb"),
        PatternEntry(r"\bilke\w*\b", 4, "verb"),
        PatternEntry(r"\bnedir\b", 4, "verb"),
        PatternEntry(r"\bkimdir\b", 4, "verb"),
        PatternEntry(r"\bhangisidir\b", 4, "verb"),
        PatternEntry(r"\bhatırla\w*\b", 3, "verb"),
        PatternEntry(r"\bbelirt\w*\b", 3, "verb"),
        PatternEntry(r"\badlandır\w*\b", 3, "verb"),
    ],
    "cognitive_comprehension": [
        PatternEntry(r"\baçıkla\w*\b", 4, "verb"),
        PatternEntry(r"\bözetle\w*\b", 4, "verb"),
        PatternEntry(r"\bne\s+anlama\w*\b", 4, "verb"),
        PatternEntry(r"\banlam\w*\b", 3, "verb"),
        PatternEntry(r"\bifade\s+et\w*\b", 4, "verb"),
        PatternEntry(r"\banlat\w*\b", 3, "verb"),
        PatternEntry(r"\bbu\s+parça\w*\b", 3, "verb"),
        PatternEntry(r"\bparça\w*\s+konusu\b", 4, "verb"),
        PatternEntry(r"\bnasıl\s+çalış\w*\b", 3, "verb"),
        PatternEntry(r"\banlamlandır\w*\b", 4, "verb"),
    ],
    "cognitive_analysis": [
        PatternEntry(r"\banaliz\s+et\w*\b", 5, "verb"),
        PatternEntry(r"\bçözümle\w*\b", 5, "verb"),
        PatternEntry(r"\bkarşılaştır\w*\b", 5, "verb"),
        PatternEntry(r"\bsınıflandır\w*\b", 5, "verb"),
        PatternEntry(r"\bhata\s+bul\w*\b", 5, "error"),
        PatternEntry(r"\byanlış\w*\b", 4, "error"),
        PatternEntry(r"\bdoğru\s+değildir\b", 5, "error"),
        PatternEntry(r"\bçıkarım\w*\b", 5, "verb"),
        PatternEntry(r"\bçıkarıl\w*\b", 5, "verb"),
        PatternEntry(r"\bilişki\b", 4, "relation"),
        PatternEntry(r"\bneden\w*\b.{0,10}\bsonuç\w*\b", 5, "relation"),
        PatternEntry(r"\bayırt\s+et\w*\b", 5, "verb"),
        PatternEntry(r"\bincele\w*\b", 4, "verb"),
        # YKS dil bilgisi hata bulma
        PatternEntry(r"\banlatım\s+bozukluğ\w*\b", 5, "error"),
        PatternEntry(r"\byazım\s+yanlış\w*\b", 5, "error"),
        PatternEntry(r"\bnoktalama\w*\b", 4, "error"),
    ],
    "cognitive_utilization": [
        PatternEntry(r"\bhesapla\w*\b", 5, "verb"),
        PatternEntry(r"\bçöz\w*\b", 4, "verb"),
        PatternEntry(r"\bbul\w*\b", 3, "verb"),
        PatternEntry(r"\bkaçtır\b", 5, "verb"),
        PatternEntry(r"\bsonuç\b", 3, "verb"),
        PatternEntry(r"\bverilenlere\s+göre\b", 5, "scenario"),
        PatternEntry(r"\bbuna\s+göre\b", 4, "scenario"),
        PatternEntry(r"\buygula\w*\b", 5, "verb"),
        PatternEntry(r"\bproblem\s+çöz\w*\b", 5, "verb"),
        # STEM senaryo / deney / grafik
        PatternEntry(r"\bdeney\w*\b", 5, "scenario"),
        PatternEntry(r"\bdüzene\w*\b", 4, "scenario"),
        PatternEntry(r"\bölçüm\w*\b", 4, "scenario"),
        PatternEntry(r"\bgrafik\w*\b", 5, "scenario"),
        PatternEntry(r"\btablo\w*\b", 5, "scenario"),
        PatternEntry(r"\bşekil\w*\b", 4, "scenario"),
        PatternEntry(r"\bgerçek\s+hayat\b", 4, "scenario"),
        PatternEntry(r"\bsenaryo\w*\b", 5, "scenario"),
        PatternEntry(r"\bkarar\s+ver\w*\b", 4, "verb"),
        PatternEntry(r"\ben\s+uygun\b", 4, "scenario"),
        PatternEntry(r"\ben\s+az\b", 3, "scenario"),
        PatternEntry(r"\ben\s+çok\b", 3, "scenario"),
        PatternEntry(r"\btasarla\w*\b", 4, "verb"),
        PatternEntry(r"\baraştır\w*\b", 4, "verb"),
    ],
}

# Category → (system, cognitive_level) mapping
_MARZANO_CATEGORY_MAP: dict[str, tuple[int, int]] = {
    "self_system": (1, 0),
    "metacognitive": (2, 0),
    "cognitive_retrieval": (3, 1),
    "cognitive_comprehension": (3, 2),
    "cognitive_analysis": (3, 3),
    "cognitive_utilization": (3, 4),
}

# Structure cues: Marzano cross-cutting bonuses
STRUCTURE_CUES: list[tuple[str, dict[str, int]]] = [
    # Tablo/grafik/şekil → Marzano utilization boost
    (r"\btablo\w*\b", {"marzano_cognitive_utilization": 3}),
    (r"\bgrafik\w*\b", {"marzano_cognitive_utilization": 3}),
    (r"\bşekil\w*\b", {"marzano_cognitive_utilization": 3}),
]

# Relation cues: Marzano Analysis boost
RELATION_CUES: list[tuple[str, dict[str, int]]] = [
    (r"\bçünkü\b", {"marzano_cognitive_analysis": 3}),
    (r"\bdolayısıyla\b", {"marzano_cognitive_analysis": 3}),
    (r"\bbu\s+nedenle\b", {"marzano_cognitive_analysis": 3}),
    (r"\bbuna\s+rağmen\b", {"marzano_cognitive_analysis": 3}),
    (r"\boysa\b", {"marzano_cognitive_analysis": 2}),
    (r"\bbuna\s+göre\b", {"marzano_cognitive_analysis": 2}),
]

# Precompile regex for preprocessing
_RE_OPTION_PREFIX = re.compile(r"^[A-E][).]\s*", re.MULTILINE | re.UNICODE)
_RE_MULTI_SPACE = re.compile(r"\s+")
_RE_ELLIPSIS = re.compile(r"…")
_RE_SMART_QUOTE = re.compile(r"[''ʼ]")


@dataclass
class MarzanoResult:
    """Marzano sınıflandırma sonucu.

    Attributes:
        system: Marzano system (enum).
        cognitive_level: Cognitive process level (enum, only for COGNITIVE system).
        confidence: Güven skoru (0.0-1.0).
        matched_patterns: Eşleşen pattern sayısı.
    """

    system: MarzanoSystem = MarzanoSystem.COGNITIVE
    cognitive_level: MarzanoProcessLevel = MarzanoProcessLevel.COMPREHENSION
    confidence: float = 0.0
    matched_patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Dict representation."""
        result = {
            "system": self.system.value,
            "confidence": round(self.confidence, 3),
            "matched_patterns": self.matched_patterns[:5],  # Top 5
        }
        if self.system == MarzanoSystem.COGNITIVE:
            result["cognitive_level"] = self.cognitive_level.value
        return result


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


def classify_marzano(question_text: str, subject: str = "") -> MarzanoResult:
    """Marzano taksonomisi sınıflandırması (weighted scoring).

    Args:
        question_text: Soru metni.
        subject: Ders adı (opsiyonel).

    Returns:
        MarzanoResult with system, cognitive_level, confidence.
    """
    text = _preprocess(question_text)

    # Score each category
    cat_scores: dict[str, int] = {}
    cat_matched: dict[str, list[str]] = {}
    cat_cap: dict[str, float] = {}

    for category, entries in MARZANO_PATTERNS.items():
        score = 0
        matched: list[str] = []
        min_cap = 0.95
        for entry in entries:
            if re.search(entry.pattern, text, re.UNICODE):
                score += entry.weight
                matched.append(entry.pattern)
                min_cap = min(min_cap, entry.cap_confidence)
        cat_scores[category] = score
        cat_matched[category] = matched
        cat_cap[category] = min_cap

    # Add structure cue bonuses
    for pattern, bonuses in STRUCTURE_CUES:
        if re.search(pattern, text, re.UNICODE):
            for key, bonus in bonuses.items():
                if key.startswith("marzano_"):
                    cat = key[len("marzano_") :]
                    if cat in cat_scores:
                        cat_scores[cat] += bonus

    # Add relation cue bonuses
    for pattern, bonuses in RELATION_CUES:
        if re.search(pattern, text, re.UNICODE):
            for key, bonus in bonuses.items():
                if key.startswith("marzano_"):
                    cat = key[len("marzano_") :]
                    if cat in cat_scores:
                        cat_scores[cat] += bonus

    # Pick best category by score
    best_cat = max(cat_scores, key=lambda c: cat_scores[c])
    best_score = cat_scores[best_cat]

    if best_score == 0:
        # No matches, default to COGNITIVE - COMPREHENSION
        return MarzanoResult(
            system=MarzanoSystem.COGNITIVE,
            cognitive_level=MarzanoProcessLevel.COMPREHENSION,
            confidence=0.3,
        )

    system_int, cognitive_int = _MARZANO_CATEGORY_MAP.get(best_cat, (3, 2))

    # Margin-based confidence with category cap
    sorted_scores = sorted(cat_scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
    margin = (best_score - second_score) / max(best_score, 1)
    confidence = min(0.95, 0.5 + margin * 0.45)

    # Apply category confidence cap
    cap = cat_cap.get(best_cat, 0.95)
    confidence = min(confidence, cap)

    system = INT_TO_MARZANO_SYSTEM[system_int]
    cognitive_level = (
        INT_TO_MARZANO_PROCESS[cognitive_int]
        if cognitive_int > 0
        else MarzanoProcessLevel.COMPREHENSION
    )

    return MarzanoResult(
        system=system,
        cognitive_level=cognitive_level,
        confidence=round(confidence, 3),
        matched_patterns=cat_matched.get(best_cat, [])[:5],
    )
