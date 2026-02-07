"""Copy-Risk ve Kontaminasyon Tespiti.

Üretilen soruların mevcut soru bankasındaki sorulara benzerliğini
tespit eder ve kontaminasyon riskini değerlendirir.

3 katmanlı tespit:
1. Exact match: SHA-256 fingerprint
2. Near-duplicate: N-gram Jaccard similarity
3. Semantic: Embedding cosine similarity (pgvector ile)

Task 8: Copy-risk ve kontaminasyon sistemi
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class CopyRiskConfig:
    """Kontaminasyon tespit konfigürasyonu."""

    # Eşikler
    exact_match_threshold: float = 1.0      # Fingerprint eşleşme
    near_duplicate_threshold: float = 0.70  # N-gram Jaccard
    semantic_threshold: float = 0.85        # Embedding cosine

    # N-gram boyutu
    ngram_size: int = 3  # Trigram

    # Türkçe stop words (kısa liste, genişletilebilir)
    stop_words: set[str] = field(default_factory=lambda: {
        "bir", "bu", "ve", "ile", "de", "da", "den", "dan", "ne", "mi",
        "mu", "icin", "gibi", "kadar", "daha", "en", "her", "hangi",
        "olan", "olarak", "sonra", "once", "ise", "ama", "ancak",
    })


# ---------------------------------------------------------------------------
# Text Preprocessing
# ---------------------------------------------------------------------------

# Türkçe karakter normalizasyonu (büyük harfler dahil)
_TR_UPPER_MAP = str.maketrans("İĞÜŞÖÇ", "igusoc")
_TR_LOWER_MAP = str.maketrans("ığüşöç", "igusoc")


def normalize_text(text: str) -> str:
    """Metin normalizasyonu.

    Args:
        text: Ham metin.

    Returns:
        Normalize edilmiş metin (küçük harf, Türkçe normalize, noktalama temiz).
    """
    # Önce Türkçe büyük harfleri ASCII'ye çevir (İ → i, Ğ → g, vb.)
    text = text.translate(_TR_UPPER_MAP)
    text = text.lower()
    text = text.translate(_TR_LOWER_MAP)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fingerprint(text: str) -> str:
    """SHA-256 metin parmak izi.

    Args:
        text: Metin.

    Returns:
        Hex hash (ilk 32 karakter).
    """
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def extract_ngrams(text: str, n: int = 3) -> set[str]:
    """N-gram çıkarma.

    Args:
        text: Normalize edilmiş metin.
        n: N-gram boyutu.

    Returns:
        N-gram kümesi.
    """
    words = text.split()
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


def remove_stop_words(text: str, stop_words: set[str]) -> str:
    """Stop word'leri çıkar.

    Args:
        text: Metin.
        stop_words: Çıkarılacak kelimeler.

    Returns:
        Filtrelenmiş metin.
    """
    words = text.split()
    filtered = [w for w in words if w not in stop_words]
    return " ".join(filtered)


# ---------------------------------------------------------------------------
# Similarity Metrics
# ---------------------------------------------------------------------------


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard benzerlik katsayısı.

    Args:
        set_a: İlk küme.
        set_b: İkinci küme.

    Returns:
        Benzerlik [0.0, 1.0].
    """
    if not set_a and not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# Copy Risk Result
# ---------------------------------------------------------------------------


class RiskLevel:
    """Risk seviye sabitleri."""

    SAFE = "safe"          # < 0.30
    LOW = "low"            # 0.30 - 0.50
    MEDIUM = "medium"      # 0.50 - 0.70
    HIGH = "high"          # 0.70 - 0.85
    CRITICAL = "critical"  # > 0.85


@dataclass
class CopyRiskResult:
    """Kontaminasyon tespit sonucu."""

    risk_score: float = 0.0  # [0.0, 1.0]
    risk_level: str = RiskLevel.SAFE
    exact_match: bool = False
    nearest_match_id: str = ""
    nearest_match_score: float = 0.0
    method: str = ""  # fingerprint, ngram, semantic
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_safe(self) -> bool:
        """Risk kabul edilebilir mi?"""
        return self.risk_score < 0.70

    def to_dict(self) -> dict[str, Any]:
        """Dict dönüşümü."""
        return {
            "risk_score": round(self.risk_score, 4),
            "risk_level": self.risk_level,
            "exact_match": self.exact_match,
            "nearest_match_id": self.nearest_match_id,
            "nearest_match_score": round(self.nearest_match_score, 4),
            "method": self.method,
            "is_safe": self.is_safe,
        }


def classify_risk(score: float) -> str:
    """Risk skorundan seviye belirle.

    Args:
        score: Risk skoru [0.0, 1.0].

    Returns:
        Risk seviyesi string.
    """
    if score >= 0.85:
        return RiskLevel.CRITICAL
    if score >= 0.70:
        return RiskLevel.HIGH
    if score >= 0.50:
        return RiskLevel.MEDIUM
    if score >= 0.30:
        return RiskLevel.LOW
    return RiskLevel.SAFE


# ---------------------------------------------------------------------------
# Copy Risk Detector
# ---------------------------------------------------------------------------


class CopyRiskDetector:
    """Çok katmanlı kopya risk tespit sistemi.

    Kullanım:
        detector = CopyRiskDetector()

        # Mevcut soru bankasını yükle
        detector.add_reference("q001", "Bir torbada 3 kirmizi top vardir...")
        detector.add_reference("q002", "Asagidaki fonksiyonun limiti...")

        # Yeni soru kontrol et
        result = detector.check("Bir torbada 3 kirmizi ve 2 mavi top vardir...")
        print(result.risk_level)  # "medium" or "high"
    """

    def __init__(self, config: CopyRiskConfig | None = None) -> None:
        self.config = config or CopyRiskConfig()
        self._fingerprints: dict[str, str] = {}  # hash → question_id
        self._ngrams: dict[str, set[str]] = {}   # question_id → ngrams
        self._texts: dict[str, str] = {}          # question_id → normalized text

    def add_reference(self, question_id: str, text: str) -> None:
        """Referans soruyu veritabanına ekle.

        Args:
            question_id: Soru ID.
            text: Soru metni.
        """
        normalized = normalize_text(text)
        cleaned = remove_stop_words(normalized, self.config.stop_words)
        fp = fingerprint(text)
        ngrams = extract_ngrams(cleaned, self.config.ngram_size)

        self._fingerprints[fp] = question_id
        self._ngrams[question_id] = ngrams
        self._texts[question_id] = normalized

    def check(self, text: str) -> CopyRiskResult:
        """Yeni sorunun kopya riskini kontrol et.

        3 aşamalı kontrol:
        1. Exact match (fingerprint)
        2. Near-duplicate (n-gram Jaccard)
        3. Semantic similarity (varsa embedding)

        Args:
            text: Kontrol edilecek soru metni.

        Returns:
            CopyRiskResult.
        """
        # Stage 1: Fingerprint exact match
        fp = fingerprint(text)
        if fp in self._fingerprints:
            match_id = self._fingerprints[fp]
            return CopyRiskResult(
                risk_score=1.0,
                risk_level=RiskLevel.CRITICAL,
                exact_match=True,
                nearest_match_id=match_id,
                nearest_match_score=1.0,
                method="fingerprint",
            )

        # Stage 2: N-gram similarity
        normalized = normalize_text(text)
        cleaned = remove_stop_words(normalized, self.config.stop_words)
        new_ngrams = extract_ngrams(cleaned, self.config.ngram_size)

        best_score = 0.0
        best_id = ""

        for qid, ref_ngrams in self._ngrams.items():
            sim = jaccard_similarity(new_ngrams, ref_ngrams)
            if sim > best_score:
                best_score = sim
                best_id = qid

        risk_score = best_score
        risk_level = classify_risk(risk_score)

        return CopyRiskResult(
            risk_score=risk_score,
            risk_level=risk_level,
            exact_match=False,
            nearest_match_id=best_id,
            nearest_match_score=best_score,
            method="ngram",
            details={
                "ngram_size": self.config.ngram_size,
                "reference_count": len(self._ngrams),
            },
        )

    @property
    def reference_count(self) -> int:
        """Referans soru sayısı."""
        return len(self._ngrams)
