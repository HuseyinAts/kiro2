"""
Question Classifier - ML-based Domain Detection
REQ-7.1: Soru siniflandirma ve domain tespiti
Teknofest 2025 - KIRO2 YKS Platformu

SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2) kullanarak
sorulari domain'lere siniflandirir.

Multi-domain detection threshold: 0.6
"""

import logging
from dataclasses import dataclass

import numpy as np

from ..domain_experts.base_domain_agent import DomainType

logger = logging.getLogger(__name__)

# Domain keywords for classification
# Extended from services/subject_relevance_scorer.py
DOMAIN_KEYWORDS: dict[DomainType, dict[str, list[str]]] = {
    DomainType.MATEMATIK: {
        "core": [
            "matematik", "sayı", "fonksiyon", "türev", "integral",
            "limit", "geometri", "cebir", "denklem", "eşitsizlik",
            "polinom", "logaritma", "üslü", "köklü", "matris",
        ],
        "topics": [
            "cebir", "geometri", "analiz", "olasılık", "istatistik",
            "trigonometri", "permütasyon", "kombinasyon", "faktöriyel",
            "toplam", "çarpım", "bölme", "çıkarma", "toplama",
            "eğim", "teğet", "türev", "integral", "alan hesabı",
        ],
    },
    DomainType.FIZIK: {
        "core": [
            "fizik", "kuvvet", "hareket", "enerji", "elektrik",
            "manyetizma", "ışık", "ses", "dalga", "newton",
            "joule", "watt", "volt", "amper", "ohm",
        ],
        "topics": [
            "mekanik", "elektrik", "optik", "termodinamik", "akustik",
            "hız", "ivme", "kütle", "ağırlık", "sürtünme",
            "potansiyel", "kinetik", "iş", "güç", "momentum",
            "basınç", "sıcaklık", "ısı", "genleşme",
        ],
    },
    DomainType.TURKCE: {
        "core": [
            "türkçe", "dil", "gramer", "edebiyat", "metin",
            "yazım", "sözcük", "cümle", "paragraf", "anlam",
            "fiil", "isim", "sıfat", "zarf", "edat",
        ],
        "topics": [
            "dilbilgisi", "edebiyat", "anlam bilgisi", "noktalama",
            "yazım kuralları", "eş anlamlı", "zıt anlamlı", "mecaz",
            "özne", "yüklem", "nesne", "tümleç", "edat",
            "bağlaç", "ünlem", "zamir", "belirteç",
        ],
    },
    DomainType.SOSYAL: {
        "core": [
            "tarih", "coğrafya", "felsefe", "din kültürü", "osmanlı",
            "cumhuriyet", "atatürk", "inkılap", "devlet", "toplum",
            "harita", "iklim", "nüfus", "ekonomi", "kültür",
        ],
        "topics": [
            "tarih", "coğrafya", "felsefe", "din kültürü",
            "osmanlı tarihi", "türk tarihi", "dünya tarihi",
            "fiziki coğrafya", "beşeri coğrafya", "ekonomik coğrafya",
            "etik", "mantık", "bilgi felsefesi", "varlık felsefesi",
        ],
    },
    DomainType.BIYOLOJI: {
        "core": [
            "biyoloji", "hücre", "canlı", "doku", "organ",
            "sistem", "genetik", "dna", "rna", "gen",
            "kromozom", "protein", "enzim", "vitamin",
        ],
        "topics": [
            "hücre", "genetik", "ekoloji", "anatomi",
            "mitokondri", "kloroplast", "ribozom", "çekirdek",
            "fotosentez", "solunum", "sindirim", "dolaşım",
            "boşaltım", "sinir sistemi", "endokrin sistem",
        ],
    },
    DomainType.YABANCI_DIL: {
        "core": [
            "english", "ingilizce", "grammar", "vocabulary",
            "reading", "writing", "speaking", "listening",
            "verb", "noun", "adjective", "adverb",
        ],
        "topics": [
            "grammar", "vocabulary", "reading", "writing",
            "tense", "modal", "passive", "conditional",
            "preposition", "conjunction", "article", "pronoun",
            "comprehension", "essay", "paragraph", "sentence",
        ],
    },
}

# Multi-domain detection threshold
MULTI_DOMAIN_THRESHOLD = 0.6


@dataclass
class DomainClassification:
    """
    Soru siniflandirma sonucu

    Attributes:
        primary_domain: Ana domain
        primary_confidence: Ana domain guven skoru [0, 1]
        secondary_domain: Ikincil domain (multi-domain sorular)
        secondary_confidence: Ikincil guven skoru
        is_multi_domain: Birden fazla domain gerektirir mi?
        all_scores: Tum domain skorlari
    """

    primary_domain: DomainType
    primary_confidence: float
    secondary_domain: DomainType | None = None
    secondary_confidence: float | None = None
    is_multi_domain: bool = False
    all_scores: dict[DomainType, float] = None

    def __post_init__(self):
        if self.all_scores is None:
            self.all_scores = {}

        # Validate confidence bounds
        if not 0.0 <= self.primary_confidence <= 1.0:
            raise ValueError(
                f"primary_confidence must be in [0, 1], got {self.primary_confidence}"
            )
        if self.secondary_confidence is not None:
            if not 0.0 <= self.secondary_confidence <= 1.0:
                raise ValueError(
                    f"secondary_confidence must be in [0, 1], got {self.secondary_confidence}"
                )


class QuestionClassifier:
    """
    ML-based Question Domain Classifier (REQ-7.1)

    SentenceTransformer kullanarak sorulari domain'lere siniflandirir.
    Multi-domain detection: threshold >= 0.6

    Attributes:
        model: SentenceTransformer modeli
        domain_embeddings: Her domain icin ortalama embedding
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """
        QuestionClassifier olustur

        Args:
            model_name: SentenceTransformer model adi
        """
        self.model_name = model_name
        self._model = None
        self._domain_embeddings: dict[DomainType, np.ndarray] = {}
        self._initialized = False

        # Try to load the model
        self._initialize()

    def _initialize(self):
        """Model ve domain embedding'lerini yukle"""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)

            # Pre-compute domain embeddings
            self._compute_domain_embeddings()
            self._initialized = True
            logger.info("QuestionClassifier initialized successfully")

        except ImportError:
            logger.warning(
                "sentence-transformers not available, using keyword-based fallback"
            )
        except Exception as e:
            logger.error(f"Failed to initialize QuestionClassifier: {e}")

    def _compute_domain_embeddings(self):
        """Her domain icin ortalama embedding hesapla"""
        if self._model is None:
            return

        for domain, keywords in DOMAIN_KEYWORDS.items():
            # Combine core and topic keywords
            all_keywords = keywords["core"] + keywords.get("topics", [])
            keyword_text = " ".join(all_keywords)

            # Compute embedding
            embedding = self._model.encode(keyword_text)
            self._domain_embeddings[domain] = embedding

            logger.debug(f"Computed embedding for {domain.value}")

    def classify(self, question: str) -> DomainClassification:
        """
        Soruyu siniflandir

        Args:
            question: Soru metni

        Returns:
            DomainClassification: Siniflandirma sonucu
        """
        if not question or not question.strip():
            # Empty question - return default
            return DomainClassification(
                primary_domain=DomainType.MATEMATIK,
                primary_confidence=0.0,
                is_multi_domain=False,
            )

        question_lower = question.lower()

        # Use semantic classification if available
        if self._initialized and self._model is not None:
            return self._classify_semantic(question, question_lower)
        return self._classify_keyword(question_lower)

    def _classify_semantic(
        self, question: str, question_lower: str
    ) -> DomainClassification:
        """
        Semantic similarity kullanarak siniflandir

        Args:
            question: Soru metni (orijinal)
            question_lower: Soru metni (lowercase)

        Returns:
            DomainClassification: Siniflandirma sonucu
        """
        # Compute question embedding
        question_embedding = self._model.encode(question)

        # Calculate similarity with each domain
        scores: dict[DomainType, float] = {}
        for domain, domain_embedding in self._domain_embeddings.items():
            similarity = self._cosine_similarity(question_embedding, domain_embedding)
            # Normalize to [0, 1]
            scores[domain] = (similarity + 1) / 2

        # Apply keyword boost
        scores = self._apply_keyword_boost(scores, question_lower)

        # Sort by score
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        primary_domain, primary_confidence = sorted_domains[0]

        # Check for multi-domain
        is_multi_domain = False
        secondary_domain = None
        secondary_confidence = None

        if len(sorted_domains) > 1:
            second_domain, second_score = sorted_domains[1]
            if second_score >= MULTI_DOMAIN_THRESHOLD:
                is_multi_domain = True
                secondary_domain = second_domain
                secondary_confidence = second_score

        result = DomainClassification(
            primary_domain=primary_domain,
            primary_confidence=primary_confidence,
            secondary_domain=secondary_domain,
            secondary_confidence=secondary_confidence,
            is_multi_domain=is_multi_domain,
            all_scores=scores,
        )

        logger.info(
            f"Classified question to {primary_domain.value} "
            f"(confidence: {primary_confidence:.2f}, multi-domain: {is_multi_domain})"
        )

        return result

    def _classify_keyword(self, question_lower: str) -> DomainClassification:
        """
        Keyword-based fallback siniflandirma

        Args:
            question_lower: Soru metni (lowercase)

        Returns:
            DomainClassification: Siniflandirma sonucu
        """
        scores: dict[DomainType, float] = {}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = 0.0
            all_keywords = keywords["core"] + keywords.get("topics", [])
            total_keywords = len(all_keywords)

            if total_keywords > 0:
                matches = sum(1 for kw in all_keywords if kw in question_lower)
                score = matches / total_keywords

            scores[domain] = score

        # Normalize scores
        max_score = max(scores.values()) if scores else 0
        if max_score > 0:
            scores = {d: s / max_score for d, s in scores.items()}

        # Sort by score
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        primary_domain, primary_confidence = sorted_domains[0]

        # Check for multi-domain
        is_multi_domain = False
        secondary_domain = None
        secondary_confidence = None

        if len(sorted_domains) > 1:
            second_domain, second_score = sorted_domains[1]
            if second_score >= MULTI_DOMAIN_THRESHOLD:
                is_multi_domain = True
                secondary_domain = second_domain
                secondary_confidence = second_score

        return DomainClassification(
            primary_domain=primary_domain,
            primary_confidence=primary_confidence,
            secondary_domain=secondary_domain,
            secondary_confidence=secondary_confidence,
            is_multi_domain=is_multi_domain,
            all_scores=scores,
        )

    def _apply_keyword_boost(
        self, scores: dict[DomainType, float], question_lower: str
    ) -> dict[DomainType, float]:
        """
        Keyword eslesmelerine gore skorlari boost et

        Args:
            scores: Mevcut semantic skorlar
            question_lower: Soru metni (lowercase)

        Returns:
            Boost edilmis skorlar
        """
        boosted_scores = dict(scores)
        boost_factor = 0.15  # %15 boost per strong keyword match

        for domain, keywords in DOMAIN_KEYWORDS.items():
            core_keywords = keywords["core"]
            # Count strong matches (exact word boundary)
            strong_matches = sum(
                1 for kw in core_keywords if f" {kw} " in f" {question_lower} "
            )

            if strong_matches > 0:
                boost = min(strong_matches * boost_factor, 0.3)  # Max %30 boost
                boosted_scores[domain] = min(1.0, boosted_scores[domain] + boost)

        return boosted_scores

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Cosine similarity hesapla

        Args:
            a: Birinci vektorArgs:
            b: Ikinci vektor

        Returns:
            Cosine similarity [-1, 1]
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return float(dot_product / (norm_a * norm_b))

    def get_domain_for_subject(self, subject: str) -> DomainType | None:
        """
        Subject string'den DomainType'a donustur

        Args:
            subject: Ders adi (e.g., "matematik", "fizik")

        Returns:
            DomainType veya None
        """
        subject_lower = subject.lower().strip()

        mapping = {
            "matematik": DomainType.MATEMATIK,
            "mat": DomainType.MATEMATIK,
            "fizik": DomainType.FIZIK,
            "fiz": DomainType.FIZIK,
            "kimya": DomainType.FIZIK,  # Kimya fizik agent'ina yonlendirilir
            "türkçe": DomainType.TURKCE,
            "turkce": DomainType.TURKCE,
            "edebiyat": DomainType.TURKCE,
            "tarih": DomainType.SOSYAL,
            "coğrafya": DomainType.SOSYAL,
            "cografya": DomainType.SOSYAL,
            "felsefe": DomainType.SOSYAL,
            "din kültürü": DomainType.SOSYAL,
            "sosyal": DomainType.SOSYAL,
            "biyoloji": DomainType.BIYOLOJI,
            "bio": DomainType.BIYOLOJI,
            "ingilizce": DomainType.YABANCI_DIL,
            "english": DomainType.YABANCI_DIL,
            "yabancı dil": DomainType.YABANCI_DIL,
            "yabanci dil": DomainType.YABANCI_DIL,
        }

        return mapping.get(subject_lower)


# Global instance
_classifier_instance: QuestionClassifier | None = None


def get_question_classifier() -> QuestionClassifier:
    """Global QuestionClassifier instance'ini al"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = QuestionClassifier()
    return _classifier_instance
