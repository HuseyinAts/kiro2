"""Taxonomy Classifier v2 - Ağırlıklı SOLO ve Marzano taksonomi sınıflandırması.

YKS soru metinlerini SOLO ve Marzano taksonomilerine göre sınıflandırır:
- Ağırlıklı skor (weighted scoring) — "en yüksek seviye kazansın" yerine
- Yapı sinyalleri (I/II/III, tablo, grafik) ve ilişki sinyalleri (çünkü, dolayısıyla)
- Ön işleme: casefold, noktalama normalize, boşluk collapse
- Margin tabanlı confidence (belirsizlik yönetimi)
- Türkçe morfoloji toleranslı regex (\\w* ek toleransı, re.UNICODE)
- Ders bazlı birincil taksonomi seçimi (SOLO: sözel, Marzano: sayısal)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaxonomyType(Enum):
    """Taksonomi türleri."""

    SOLO = "solo"
    MARZANO = "marzano"


class SOLOLevel(Enum):
    """SOLO taksonomi seviyeleri."""

    PRESTRUCTURAL = 1       # Yapı-öncesi
    UNISTRUCTURAL = 2       # Tek-yapılı
    MULTISTRUCTURAL = 3     # Çok-yapılı
    RELATIONAL = 4          # İlişkisel
    EXTENDED_ABSTRACT = 5   # Genişletilmiş soyut


class MarzanoSystem(Enum):
    """Marzano taksonomi sistemleri."""

    SELF_SYSTEM = 1         # Öz-sistem (motivasyon, inanç)
    METACOGNITIVE = 2       # Üstbilişsel (strateji, izleme)
    COGNITIVE = 3           # Bilişsel (geri çağırma → bilgi kullanımı)


class MarzanoCognitiveLevel(Enum):
    """Marzano bilişsel sistem alt seviyeleri."""

    RETRIEVAL = 1           # Geri çağırma
    COMPREHENSION = 2       # Kavrama
    ANALYSIS = 3            # Analiz
    KNOWLEDGE_UTILIZATION = 4  # Bilgi kullanımı


# --- Seviye isimleri (Türkçe) --- cognitive_profiler tarafından import edilir

SOLO_LEVEL_NAMES: dict[int, str] = {
    1: "Yapı-öncesi",
    2: "Tek-yapılı",
    3: "Çok-yapılı",
    4: "İlişkisel",
    5: "Genişletilmiş soyut",
}

MARZANO_SYSTEM_NAMES: dict[int, str] = {
    1: "Öz-sistem",
    2: "Üstbilişsel",
    3: "Bilişsel",
}

MARZANO_COGNITIVE_NAMES: dict[int, str] = {
    1: "Geri çağırma",
    2: "Kavrama",
    3: "Analiz",
    4: "Bilgi kullanımı",
}

# --- Subject → Primary Taxonomy Routing ---

SOLO_SUBJECTS: set[str] = {
    "Türkçe", "Edebiyat", "Tarih", "Felsefe", "Din Kültürü", "Coğrafya",
    "Türk Dili ve Edebiyatı", "Sosyal Bilimler", "Sosyal Bilimler-1",
    "Sosyal Bilimler-2",
}

MARZANO_SUBJECTS: set[str] = {
    "Matematik", "Fizik", "Kimya", "Biyoloji", "Geometri",
    "Temel Matematik", "Fen Bilimleri",
}


# ============================================================
# PatternEntry: ağırlıklı pattern tanımı
# ============================================================

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


# ============================================================
# SOLO Bundles — YKS odaklı, ağırlıklı
# ============================================================

SOLO_BUNDLES: dict[int, list[PatternEntry]] = {
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
        # Çıkarım/yorum (w=4) — çıkar\w* yerine spesifik
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

# ============================================================
# Marzano Bundles — YKS odaklı, ağırlıklı
# ============================================================

MARZANO_BUNDLES: dict[str, list[PatternEntry]] = {
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

# ============================================================
# Structure & Relation Cues (cross-cutting bonuses)
# ============================================================

# Structure cues: SOLO ve Marzano'ya çapraz bonus verir
STRUCTURE_CUES: list[tuple[str, dict[str, int]]] = [
    # Roman numerals → SOLO L3 boost (casefold sonrası lowercase)
    (r"\bi[.)]\s", {"solo_3": 3}),
    (r"\bii[.)]\s", {"solo_3": 3}),
    (r"\biii[.)]\s", {"solo_3": 3}),
    (r"\biv[.)]\s", {"solo_3": 3}),
    # Tablo/grafik/şekil → Marzano utilization boost
    (r"\btablo\w*\b", {"marzano_cognitive_utilization": 3}),
    (r"\bgrafik\w*\b", {"marzano_cognitive_utilization": 3}),
    (r"\bşekil\w*\b", {"marzano_cognitive_utilization": 3}),
]

# Relation cues: SOLO L4 ve Marzano Analysis boost
RELATION_CUES: list[tuple[str, dict[str, int]]] = [
    (r"\bçünkü\b", {"solo_4": 3, "marzano_cognitive_analysis": 3}),
    (r"\bdolayısıyla\b", {"solo_4": 3, "marzano_cognitive_analysis": 3}),
    (r"\bbu\s+nedenle\b", {"solo_4": 3, "marzano_cognitive_analysis": 3}),
    (r"\bbuna\s+rağmen\b", {"solo_4": 3, "marzano_cognitive_analysis": 3}),
    (r"\boysa\b", {"solo_4": 2, "marzano_cognitive_analysis": 2}),
    (r"\bbuna\s+göre\b", {"solo_4": 2, "marzano_cognitive_analysis": 2}),
]


# ============================================================
# Result dataclasses (unchanged API)
# ============================================================

@dataclass
class SOLOResult:
    """SOLO sınıflandırma sonucu."""

    level: int = 1                    # 1-5
    level_name: str = "Yapı-öncesi"
    confidence: float = 0.0
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "level_name": self.level_name,
            "confidence": round(self.confidence, 3),
        }


@dataclass
class MarzanoResult:
    """Marzano sınıflandırma sonucu."""

    system: int = 3                              # 1-3
    system_name: str = "Bilişsel"
    cognitive_level: int = 1                     # 1-4 (sadece system=3 için anlamlı)
    cognitive_level_name: str = "Geri çağırma"
    confidence: float = 0.0
    matched_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "system": self.system,
            "system_name": self.system_name,
            "confidence": round(self.confidence, 3),
        }
        if self.system == 3:
            result["cognitive_level"] = self.cognitive_level
            result["cognitive_level_name"] = self.cognitive_level_name
        return result


@dataclass
class TaxonomyResult:
    """Birleşik taksonomi sonucu."""

    subject: str = ""
    primary_taxonomy: TaxonomyType = TaxonomyType.SOLO
    solo: SOLOResult = field(default_factory=SOLOResult)
    marzano: MarzanoResult = field(default_factory=MarzanoResult)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "primary_taxonomy": self.primary_taxonomy.value,
            "solo": self.solo.to_dict(),
            "marzano": self.marzano.to_dict(),
        }


@dataclass
class TaxonomyConfig:
    """Sınıflandırma konfigürasyonu."""

    min_confidence: float = 0.3          # Bu altında "belirsiz"
    solo_default_level: int = 2          # Keyword bulunamazsa
    marzano_default_system: int = 3      # Default: bilişsel
    marzano_default_cognitive: int = 2   # Default: kavrama


# ============================================================
# TaxonomyClassifier — weighted scoring engine
# ============================================================

# Precompile regex for preprocessing
_RE_OPTION_PREFIX = re.compile(r"^[A-E][).]\s*", re.MULTILINE | re.UNICODE)
_RE_MULTI_SPACE = re.compile(r"\s+")
_RE_ELLIPSIS = re.compile(r"…")
_RE_SMART_QUOTE = re.compile(r"[''ʼ]")


@dataclass
class TaxonomyClassifier:
    """SOLO ve Marzano taksonomi sınıflandırma motoru (v2 — weighted scoring).

    Soru metnini ön işleme → ağırlıklı pattern eşleştirme → margin tabanlı
    confidence ile SOLO ve Marzano seviyelerini belirler.

    Example:
        >>> classifier = TaxonomyClassifier()
        >>> result = classifier.classify(
        ...     "Bu paragrafın ana düşüncesi nedir?", "Türkçe"
        ... )
        >>> print(result.solo.level_name)  # "İlişkisel"
        >>> print(result.primary_taxonomy)  # SOLO
    """

    config: TaxonomyConfig = field(default_factory=TaxonomyConfig)

    def classify(self, question_text: str, subject: str) -> TaxonomyResult:
        """Soruyu SOLO ve Marzano taksonomilerine göre sınıflandır.

        Args:
            question_text: Soru metni.
            subject: Ders adı.

        Returns:
            TaxonomyResult with both SOLO and Marzano scores.
        """
        solo = self.classify_solo(question_text)
        marzano = self.classify_marzano(question_text)
        primary = self.get_primary_taxonomy(subject)

        return TaxonomyResult(
            subject=subject,
            primary_taxonomy=primary,
            solo=solo,
            marzano=marzano,
        )

    def classify_solo(self, question_text: str) -> SOLOResult:
        """SOLO taksonomisi sınıflandırması (weighted scoring).

        Args:
            question_text: Soru metni.

        Returns:
            SOLOResult with level 1-5.
        """
        text = self._preprocess(question_text)

        # Score each level
        scores: dict[int, int] = {2: 0, 3: 0, 4: 0, 5: 0}
        all_matched: dict[int, list[str]] = {2: [], 3: [], 4: [], 5: []}

        for level, entries in SOLO_BUNDLES.items():
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
            lvl: sc for lvl, sc in scores.items()
            if sc >= SOLO_THRESHOLDS.get(lvl, 2)
        }

        if not qualifying:
            return SOLOResult(
                level=self.config.solo_default_level,
                level_name=SOLO_LEVEL_NAMES.get(
                    self.config.solo_default_level, "Bilinmeyen"
                ),
                confidence=self.config.min_confidence,
            )

        # argmax with tiebreak: higher level wins
        best_level = max(qualifying, key=lambda l: (qualifying[l], l))
        best_score = qualifying[best_level]

        # Margin-based confidence
        sorted_scores = sorted(scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
        margin = (best_score - second_score) / max(best_score, 1)
        confidence = min(0.95, 0.5 + margin * 0.45)

        return SOLOResult(
            level=best_level,
            level_name=SOLO_LEVEL_NAMES.get(best_level, "Bilinmeyen"),
            confidence=round(confidence, 3),
            matched_keywords=all_matched.get(best_level, [])[:5],
        )

    def classify_marzano(self, question_text: str) -> MarzanoResult:
        """Marzano taksonomisi sınıflandırması (weighted scoring).

        Args:
            question_text: Soru metni.

        Returns:
            MarzanoResult with system and cognitive level.
        """
        text = self._preprocess(question_text)

        # Score each category
        cat_scores: dict[str, int] = {}
        cat_matched: dict[str, list[str]] = {}
        cat_cap: dict[str, float] = {}

        for category, entries in MARZANO_BUNDLES.items():
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
                        cat = key[len("marzano_"):]
                        if cat in cat_scores:
                            cat_scores[cat] += bonus

        # Add relation cue bonuses
        for pattern, bonuses in RELATION_CUES:
            if re.search(pattern, text, re.UNICODE):
                for key, bonus in bonuses.items():
                    if key.startswith("marzano_"):
                        cat = key[len("marzano_"):]
                        if cat in cat_scores:
                            cat_scores[cat] += bonus

        # Pick best category by score
        best_cat = max(cat_scores, key=lambda c: cat_scores[c])
        best_score = cat_scores[best_cat]

        if best_score == 0:
            return MarzanoResult(
                system=self.config.marzano_default_system,
                system_name=MARZANO_SYSTEM_NAMES[self.config.marzano_default_system],
                cognitive_level=self.config.marzano_default_cognitive,
                cognitive_level_name=MARZANO_COGNITIVE_NAMES[
                    self.config.marzano_default_cognitive
                ],
                confidence=self.config.min_confidence,
            )

        system, cognitive_level = _MARZANO_CATEGORY_MAP.get(best_cat, (3, 2))

        # Margin-based confidence with category cap
        sorted_scores = sorted(cat_scores.values(), reverse=True)
        second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0
        margin = (best_score - second_score) / max(best_score, 1)
        confidence = min(0.95, 0.5 + margin * 0.45)

        # Apply category confidence cap
        cap = cat_cap.get(best_cat, 0.95)
        confidence = min(confidence, cap)

        return MarzanoResult(
            system=system,
            system_name=MARZANO_SYSTEM_NAMES[system],
            cognitive_level=cognitive_level,
            cognitive_level_name=MARZANO_COGNITIVE_NAMES.get(cognitive_level, ""),
            confidence=round(confidence, 3),
            matched_keywords=cat_matched.get(best_cat, [])[:5],
        )

    def get_primary_taxonomy(self, subject: str) -> TaxonomyType:
        """Ders bazlı birincil taksonomi seç.

        Args:
            subject: Ders adı.

        Returns:
            SOLO (sözel dersler) veya MARZANO (sayısal dersler).
        """
        if subject in SOLO_SUBJECTS:
            return TaxonomyType.SOLO
        if subject in MARZANO_SUBJECTS:
            return TaxonomyType.MARZANO
        lower = subject.lower()
        if any(kw in lower for kw in (
            "edebiyat", "tarih", "sosyal", "felsefe", "türkçe", "coğrafya",
        )):
            return TaxonomyType.SOLO
        if any(kw in lower for kw in (
            "matematik", "fizik", "kimya", "biyoloji", "fen", "geometri",
        )):
            return TaxonomyType.MARZANO
        return TaxonomyType.SOLO

    @staticmethod
    def _preprocess(text: str) -> str:
        """Soru metnini ön işleme.

        1. casefold (Turkish İ/I handling)
        2. Normalize punctuation
        3. Strip answer option prefixes (A-E only, NOT Roman numerals)
        4. Collapse whitespace
        """
        text = text.casefold().strip()
        text = _RE_ELLIPSIS.sub("...", text)
        text = _RE_SMART_QUOTE.sub("'", text)
        text = _RE_OPTION_PREFIX.sub("", text)
        text = _RE_MULTI_SPACE.sub(" ", text)
        return text
