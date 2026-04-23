"""
StudyBuddyAgent Yanıt Doğrulayıcı

Bu modül, StudyBuddyAgent'ın verdiği cevapları doğrular.

Doğrulamalar:
1. Semantik ilgi (query-answer relevance)
2. Matematik doğruluğu (SymPy ile)
3. Tarihsel bilgi doğruluğu
4. Bilimsel doğruluk
5. Kaynak güvenilirliği

Requirements: REQ-2.1 - REQ-2.6
"""

import logging
import re
from typing import Any

from backend.validators.base_response_validator import (
    AgentResponse,
    BaseResponseValidator,
    ValidationResult,
)

logger = logging.getLogger(__name__)


# Güvenilir kaynak domain'leri
TRUSTED_DOMAINS = [
    "meb.gov.tr",
    "tuba.gov.tr",
    "tubitak.gov.tr",
    "wikipedia.org",
    "tr.wikipedia.org",
    "khanacademy.org",
    "tr.khanacademy.org",
    "eba.gov.tr",
    "yok.gov.tr",
    "osym.gov.tr",
]

# Konu keyword'leri
MATH_KEYWORDS = [
    "hesapla", "topla", "çıkar", "çarp", "böl", "kaç",
    "sonuç", "=", "+", "-", "*", "/", "^",
    "denklem", "eşitlik", "oran", "yüzde", "%",
    "karekök", "üs", "logaritma", "türev", "integral",
    "alan", "çevre", "hacim", "açı", "derece",
]

HISTORY_KEYWORDS = [
    "tarih", "yıl", "yüzyıl", "dönem", "savaş",
    "antlaşma", "padişah", "sultan", "imparatorluk",
    "cumhuriyet", "osmanlı", "atatürk", "kurtuluş",
    "inkılap", "devrim", "milli mücadele",
]

SCIENCE_KEYWORDS = [
    "atom", "molekül", "element", "bileşik",
    "hücre", "organ", "sistem", "canlı",
    "enerji", "kuvvet", "hareket", "hız",
    "ışık", "ses", "dalga", "elektrik",
    "reaksiyon", "bağ", "periyodik",
]


class StudyBuddyValidator(BaseResponseValidator):
    """
    StudyBuddyAgent yanıtlarını doğrulayan validator.

    Sohbet asistanının verdiği cevapların:
    - Soruyla ilgili olduğunu
    - Matematiksel hesaplamaların doğru olduğunu
    - Tarihsel bilgilerin doğru olduğunu
    - Bilimsel açıklamaların doğru olduğunu
    - Kaynakların güvenilir olduğunu

    kontrol eder.
    """

    # Relevance eşik değerleri
    HIGH_RELEVANCE_THRESHOLD = 0.85
    LOW_RELEVANCE_THRESHOLD = 0.70

    def __init__(
        self,
        weight: float = 0.30,
        use_embeddings: bool = True,
    ):
        """
        Args:
            weight: Validator ağırlığı (default: 0.30)
            use_embeddings: Embedding tabanlı relevance kullan
        """
        super().__init__(weight)
        self.use_embeddings = use_embeddings
        self._embedding_model = None

    def get_validator_name(self) -> str:
        return "StudyBuddyValidator"

    async def validate(self, response: AgentResponse) -> ValidationResult:
        """
        StudyBuddyAgent yanıtını doğrula.

        Args:
            response: Doğrulanacak agent yanıtı

        Returns:
            ValidationResult: Doğrulama sonucu
        """
        errors: list[str] = []
        warnings: list[str] = []
        suggestions: list[str] = []
        score = 1.0

        query = response.query
        answer = response.response_text
        sources = response.response_data.get("sources", [])

        # 1. Konu ilgisi kontrolü (REQ-2.1)
        relevance_score = await self._calculate_relevance(query, answer)

        if relevance_score < self.LOW_RELEVANCE_THRESHOLD:
            errors.append("Cevap soruyla ilgili değil")
            score -= 0.3
            suggestions.append(
                "Cevabı soruyla daha ilgili hale getirin"
            )
        elif relevance_score < self.HIGH_RELEVANCE_THRESHOLD:
            warnings.append("Cevap kısmen ilgili")
            score -= 0.1
            suggestions.append(
                "Cevabı soruya daha odaklı hale getirin"
            )

        # 2. Matematiksel doğruluk kontrolü (REQ-2.2)
        if self._is_math_question(query):
            math_result = await self._verify_math_answer(query, answer)
            if not math_result["is_correct"]:
                if math_result["confidence"] > 0.8:
                    errors.append(
                        f"Matematiksel hesaplama hatalı: {math_result['detail']}"
                    )
                    score -= 0.4
                else:
                    warnings.append(
                        f"Matematiksel hesaplama doğrulanamadı: {math_result['detail']}"
                    )
                    score -= 0.1
                suggestions.append("Hesaplamaları tekrar kontrol edin")

        # 3. Tarihsel bilgi kontrolü (REQ-2.3)
        if self._is_history_question(query):
            history_result = await self._verify_historical_facts(answer)
            for error in history_result["errors"]:
                errors.append(f"Tarihsel bilgi hatalı: {error}")
                score -= 0.3
            for warning in history_result["warnings"]:
                warnings.append(f"Tarihsel bilgi belirsiz: {warning}")
                score -= 0.1

        # 4. Bilimsel doğruluk kontrolü (REQ-2.4)
        if self._is_science_question(query):
            science_result = await self._verify_scientific_claims(answer)
            for error in science_result["errors"]:
                errors.append(f"Bilimsel açıklama hatalı: {error}")
                score -= 0.3
            for warning in science_result["warnings"]:
                warnings.append(f"Bilimsel açıklama belirsiz: {warning}")
                score -= 0.1

        # 5. Kaynak güvenilirliği kontrolü (REQ-2.5)
        if sources:
            source_result = self._check_source_reliability(sources)
            for unreliable in source_result["unreliable"]:
                warnings.append(f"Kaynak güvenilir değil: {unreliable}")
                score -= 0.1
            if source_result["unreliable"]:
                suggestions.append(
                    "Güvenilir akademik veya resmi kaynaklara başvurun"
                )

        # Skoru sınırla
        score = max(0.0, min(1.0, score))

        # Metadata oluştur
        metadata = {
            "validator": self.get_validator_name(),
            "relevance_score": relevance_score,
            "is_math_question": self._is_math_question(query),
            "is_history_question": self._is_history_question(query),
            "is_science_question": self._is_science_question(query),
            "source_count": len(sources),
        }

        return ValidationResult(
            is_valid=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata=metadata,
        )

    async def _calculate_relevance(
        self, query: str, answer: str
    ) -> float:
        """
        Query ve answer arasındaki semantik ilgiyi hesapla.

        Args:
            query: Kullanıcı sorusu
            answer: Agent cevabı

        Returns:
            float: Relevance skoru (0-1)
        """
        if self.use_embeddings:
            try:
                return await self._calculate_embedding_similarity(
                    query, answer
                )
            except Exception as e:
                logger.warning(f"Embedding similarity failed: {e}")

        # Fallback: Kelime tabanlı benzerlik
        return self._calculate_keyword_similarity(query, answer)

    async def _calculate_embedding_similarity(
        self, text1: str, text2: str
    ) -> float:
        """
        Embedding tabanlı semantik benzerlik hesapla.

        Args:
            text1: İlk metin
            text2: İkinci metin

        Returns:
            float: Cosine similarity (0-1)
        """
        try:
            # Lazy loading for sentence-transformers
            if self._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )

            import numpy as np

            emb1 = self._embedding_model.encode(text1)
            emb2 = self._embedding_model.encode(text2)

            # Cosine similarity
            similarity = float(
                np.dot(emb1, emb2) / (
                    np.linalg.norm(emb1) * np.linalg.norm(emb2)
                )
            )

            # Normalize to 0-1
            return (similarity + 1) / 2

        except ImportError:
            logger.warning("sentence-transformers not available")
            return self._calculate_keyword_similarity(text1, text2)

    def _calculate_keyword_similarity(
        self, query: str, answer: str
    ) -> float:
        """
        Kelime tabanlı basit benzerlik hesapla.

        Args:
            query: Soru
            answer: Cevap

        Returns:
            float: Benzerlik skoru (0-1)
        """
        # Türkçe stop words
        stop_words = {
            "ve", "veya", "ile", "için", "bu", "şu", "o",
            "bir", "mi", "mı", "mu", "mü", "ne", "nasıl",
            "neden", "niçin", "hangi", "kaç", "kim",
            "de", "da", "den", "dan", "dır", "dir",
        }

        def tokenize(text: str) -> set:
            words = re.findall(r'\b\w+\b', text.lower())
            return {w for w in words if w not in stop_words and len(w) > 2}

        query_words = tokenize(query)
        answer_words = tokenize(answer)

        if not query_words:
            return 0.5  # Neutral score

        # Jaccard similarity
        intersection = len(query_words & answer_words)
        union = len(query_words | answer_words)

        if union == 0:
            return 0.5

        return intersection / union

    def _is_math_question(self, query: str) -> bool:
        """Matematik sorusu mu kontrol et"""
        query_lower = query.lower()
        return any(kw in query_lower for kw in MATH_KEYWORDS)

    def _is_history_question(self, query: str) -> bool:
        """Tarih sorusu mu kontrol et"""
        query_lower = query.lower()
        return any(kw in query_lower for kw in HISTORY_KEYWORDS)

    def _is_science_question(self, query: str) -> bool:
        """Fen/bilim sorusu mu kontrol et"""
        query_lower = query.lower()
        return any(kw in query_lower for kw in SCIENCE_KEYWORDS)

    async def _verify_math_answer(
        self, query: str, answer: str
    ) -> dict[str, Any]:
        """
        Matematiksel cevabı doğrula.

        Args:
            query: Soru
            answer: Cevap

        Returns:
            Dict: Doğrulama sonucu
        """
        try:
            from sympy import simplify
            from sympy.parsing.sympy_parser import parse_expr

            # Sayısal değerleri çıkar
            answer_numbers = self._extract_numbers(answer)

            if not answer_numbers:
                return {
                    "is_correct": True,
                    "confidence": 0.3,
                    "detail": "Sayısal değer bulunamadı",
                }

            # Matematiksel ifadeleri çıkar ve doğrula
            query_expr = self._extract_math_expression(query)
            answer_expr = self._extract_math_expression(answer)

            if query_expr and answer_expr:
                try:
                    q_parsed = parse_expr(query_expr)
                    a_parsed = parse_expr(answer_expr)

                    # Basit aritmetik kontrolü
                    if simplify(q_parsed - a_parsed) == 0:
                        return {
                            "is_correct": True,
                            "confidence": 0.95,
                            "detail": "İfadeler eşit",
                        }
                except Exception:
                    pass

            # Basit hesaplama kontrolü
            if "=" in query or "kaç" in query.lower():
                expected = self._calculate_simple_expression(query)
                if expected is not None:
                    # En yakın cevap numarasını kontrol et
                    for num in answer_numbers:
                        if abs(float(num) - expected) < 0.01:
                            return {
                                "is_correct": True,
                                "confidence": 0.9,
                                "detail": f"Beklenen: {expected}",
                            }
                    return {
                        "is_correct": False,
                        "confidence": 0.85,
                        "detail": f"Beklenen: {expected}, Bulunan: {answer_numbers}",
                    }

            return {
                "is_correct": True,
                "confidence": 0.5,
                "detail": "Otomatik doğrulama yapılamadı",
            }

        except ImportError:
            logger.warning("sympy not available for math verification")
            return {
                "is_correct": True,
                "confidence": 0.3,
                "detail": "SymPy mevcut değil",
            }
        except Exception as e:
            logger.warning(f"Math verification error: {e}")
            return {
                "is_correct": True,
                "confidence": 0.3,
                "detail": str(e),
            }

    def _extract_numbers(self, text: str) -> list[str]:
        """Metinden sayıları çıkar"""
        # Ondalık ve tam sayılar
        pattern = r'-?\d+(?:[.,]\d+)?'
        return re.findall(pattern, text)

    def _extract_math_expression(self, text: str) -> str | None:
        """Metinden matematiksel ifadeyi çıkar"""
        # Basit aritmetik ifadeler
        pattern = r'[\d\s\+\-\*\/\(\)\^\.]+[=][\d\s\+\-\*\/\(\)\^\.]*'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0].replace(' ', '')
        return None

    def _calculate_simple_expression(self, text: str) -> float | None:
        """Basit aritmetik ifadeyi hesapla"""
        try:
            # Sayıları ve operatörleri çıkar
            pattern = r'(\d+(?:\.\d+)?)\s*([+\-*/])\s*(\d+(?:\.\d+)?)'
            match = re.search(pattern, text)

            if match:
                a, op, b = match.groups()
                a, b = float(a), float(b)

                if op == '+':
                    return a + b
                if op == '-':
                    return a - b
                if op == '*':
                    return a * b
                if op == '/' and b != 0:
                    return a / b

            return None
        except Exception:
            return None

    async def _verify_historical_facts(
        self, answer: str
    ) -> dict[str, Any]:
        """
        Tarihsel bilgileri doğrula.

        Args:
            answer: Doğrulanacak cevap

        Returns:
            Dict: Doğrulama sonucu
        """
        errors = []
        warnings = []

        # Tarih formatlarını çıkar
        year_pattern = r'\b(1[0-9]{3}|20[0-2][0-9])\b'
        years = re.findall(year_pattern, answer)

        # Bilinen tarihsel hataları kontrol et
        known_facts = {
            "cumhuriyet": 1923,
            "kurtuluş savaşı": (1919, 1923),
            "osmanlı kuruluş": 1299,
            "istanbul fethi": 1453,
            "birinci dünya savaşı": (1914, 1918),
            "ikinci dünya savaşı": (1939, 1945),
        }

        answer_lower = answer.lower()

        for fact, year_info in known_facts.items():
            if fact in answer_lower:
                if isinstance(year_info, tuple):
                    start, end = year_info
                    mentioned_years = [
                        int(y) for y in years
                        if start - 5 <= int(y) <= end + 5
                    ]
                    if not mentioned_years:
                        warnings.append(
                            f"'{fact}' için tarih bilgisi eksik veya hatalı"
                        )
                elif str(year_info) not in years:
                    # Yakın bir tarih var mı kontrol et
                    close_years = [
                        y for y in years
                        if abs(int(y) - year_info) <= 2
                    ]
                    if not close_years:
                        warnings.append(
                            f"'{fact}' için beklenen tarih: {year_info}"
                        )

        return {
            "errors": errors,
            "warnings": warnings,
        }

    async def _verify_scientific_claims(
        self, answer: str
    ) -> dict[str, Any]:
        """
        Bilimsel iddiaları doğrula.

        Args:
            answer: Doğrulanacak cevap

        Returns:
            Dict: Doğrulama sonucu
        """
        errors = []
        warnings = []

        # Bilinen bilimsel sabitler ve gerçekler
        scientific_facts = {
            "ışık hızı": ("299792458", "m/s"),
            "su kaynama noktası": ("100", "derece"),
            "su donma noktası": ("0", "derece"),
            "yerçekimi ivmesi": ("9.8", "m/s"),
            "avogadro sayısı": ("6.022", "10^23"),
            "pi sayısı": ("3.14", ""),
        }

        answer_lower = answer.lower()

        for concept, (value, unit) in scientific_facts.items():
            if concept in answer_lower:
                if value not in answer:
                    # Yaklaşık değer kontrolü
                    numbers = self._extract_numbers(answer)
                    try:
                        expected = float(value.replace(",", "."))
                        close_match = any(
                            abs(float(n.replace(",", ".")) - expected) / expected < 0.1
                            for n in numbers
                        )
                        if not close_match and numbers:
                            warnings.append(
                                f"'{concept}' için beklenen değer: ~{value} {unit}"
                            )
                    except ValueError:
                        pass

        return {
            "errors": errors,
            "warnings": warnings,
        }

    def _check_source_reliability(
        self, sources: list[str]
    ) -> dict[str, Any]:
        """
        Kaynakların güvenilirliğini kontrol et.

        Args:
            sources: Kaynak URL'leri veya isimleri

        Returns:
            Dict: Güvenilirlik sonucu
        """
        reliable = []
        unreliable = []

        for source in sources:
            source_lower = source.lower()

            # URL kontrolü
            is_trusted = any(
                domain in source_lower
                for domain in TRUSTED_DOMAINS
            )

            # Akademik kaynak kontrolü
            academic_indicators = [
                ".edu", ".gov", "üniversite", "university",
                "akademik", "bilimsel", "araştırma",
            ]
            is_academic = any(
                ind in source_lower
                for ind in academic_indicators
            )

            if is_trusted or is_academic:
                reliable.append(source)
            else:
                # Şüpheli kaynak patternleri
                suspicious_patterns = [
                    "blog", "forum", "sosyal medya",
                    "twitter", "facebook", "instagram",
                ]
                is_suspicious = any(
                    pattern in source_lower
                    for pattern in suspicious_patterns
                )

                if is_suspicious:
                    unreliable.append(source)
                else:
                    reliable.append(source)  # Benefit of doubt

        return {
            "reliable": reliable,
            "unreliable": unreliable,
        }
