"""
Consistency Checker

Bu modül, AI yanıtlarının önceki yanıtlarla tutarlılığını kontrol eder.

Features:
- Son 10 yanıt analizi
- Direct contradiction detection
- Semantic contradiction detection (embeddings)
- Contradiction type classification

Requirements: REQ-5.1 - REQ-5.6

Weight in total confidence: 30%
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from backend.consistency.response_history_manager import ResponseHistoryManager
from backend.validators.base_response_validator import (
    AgentResponse,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class Contradiction(BaseModel):
    """Çelişki modeli"""
    topic: str = Field(description="Çelişki konusu")
    current_statement: str = Field(description="Mevcut ifade")
    previous_statement: str = Field(description="Önceki ifade")
    previous_response_id: str = Field(description="Önceki yanıt ID'si")
    contradiction_type: str = Field(description="direct/semantic")
    confidence: float = Field(ge=0.0, le=1.0, description="Çelişki güveni")


class ConsistencyChecker:
    """
    AI yanıt tutarlılık kontrolcüsü.

    Önceki yanıtlarla karşılaştırarak çelişkileri tespit eder.
    """

    # Maksimum kontrol edilecek geçmiş yanıt sayısı
    MAX_HISTORY_CHECK = 10

    # Çelişki eşik değerleri
    DIRECT_CONTRADICTION_THRESHOLD = 0.85
    SEMANTIC_CONTRADICTION_THRESHOLD = 0.70

    # Türkçe olumsuzluk kelimeleri
    NEGATION_WORDS = [
        "değil", "değildir", "yok", "yoktur",
        "hayır", "asla", "hiç", "hiçbir",
        "olmaz", "olamaz", "yapılamaz", "edilemez",
    ]

    def __init__(
        self,
        history_manager: Optional[ResponseHistoryManager] = None,
        use_embeddings: bool = True,
    ):
        """
        Args:
            history_manager: Yanıt geçmişi yöneticisi
            use_embeddings: Embedding tabanlı çelişki tespiti kullan
        """
        self.history = history_manager or ResponseHistoryManager()
        self.use_embeddings = use_embeddings
        self._embedding_model = None

    async def check_consistency(
        self, response: AgentResponse
    ) -> ValidationResult:
        """
        Yanıtın önceki yanıtlarla tutarlılığını kontrol et.

        Args:
            response: Kontrol edilecek yanıt

        Returns:
            ValidationResult: Tutarlılık sonucu
        """
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        score = 1.0

        # Geçmiş yanıtları al
        previous_responses = await self.history.get_recent_responses(
            user_id=response.user_id,
            agent_type=response.agent_type,
            limit=self.MAX_HISTORY_CHECK,
        )

        if not previous_responses:
            # Geçmiş yok, tutarlılık kontrolü yapılamaz
            return ValidationResult(
                is_valid=True,
                score=1.0,
                errors=[],
                warnings=[],
                suggestions=[],
                metadata={
                    "consistency_checker": "ConsistencyChecker",
                    "responses_checked": 0,
                    "note": "no_history",
                },
            )

        # Çelişkileri tespit et
        contradictions: List[Contradiction] = []

        # 1. Direct contradiction detection
        direct_contradictions = await self._detect_direct_contradictions(
            response, previous_responses
        )
        contradictions.extend(direct_contradictions)

        # 2. Semantic contradiction detection
        if self.use_embeddings:
            semantic_contradictions = await self._detect_semantic_contradictions(
                response, previous_responses
            )
            contradictions.extend(semantic_contradictions)

        # Sonuçları işle
        for contradiction in contradictions:
            if contradiction.contradiction_type == "direct":
                errors.append(
                    f"Çelişki tespit edildi - Konu: {contradiction.topic}"
                )
                score -= 0.2
            else:
                warnings.append(
                    f"Dolaylı çelişki olabilir - Konu: {contradiction.topic}"
                )
                score -= 0.1

        # Öneriler
        if contradictions:
            suggestions.extend(
                self._generate_consistency_suggestions(contradictions)
            )

        # Skoru sınırla
        score = max(0.0, min(1.0, score))

        # Yanıtı geçmişe kaydet
        await self.history.save_response(response)

        return ValidationResult(
            is_valid=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            metadata={
                "consistency_checker": "ConsistencyChecker",
                "responses_checked": len(previous_responses),
                "contradictions_found": len(contradictions),
                "contradictions": [c.model_dump() for c in contradictions],
            },
        )

    async def _detect_direct_contradictions(
        self,
        current: AgentResponse,
        previous: List[AgentResponse],
    ) -> List[Contradiction]:
        """
        Doğrudan çelişkileri tespit et.

        Args:
            current: Mevcut yanıt
            previous: Önceki yanıtlar

        Returns:
            List[Contradiction]: Tespit edilen çelişkiler
        """
        contradictions = []

        # Mevcut yanıttan konuları çıkar
        current_topics = self._extract_topics(current.response_text)

        for prev_response in previous:
            # Önceki yanıttan konuları çıkar
            prev_topics = self._extract_topics(prev_response.response_text)

            # Ortak konuları bul
            common_topics = set(current_topics.keys()) & set(prev_topics.keys())

            for topic in common_topics:
                current_statement = current_topics[topic]
                prev_statement = prev_topics[topic]

                # Çelişki kontrolü
                is_contradiction, confidence = self._check_direct_contradiction(
                    current_statement, prev_statement
                )

                if is_contradiction and confidence >= self.DIRECT_CONTRADICTION_THRESHOLD:
                    contradictions.append(
                        Contradiction(
                            topic=topic,
                            current_statement=current_statement,
                            previous_statement=prev_statement,
                            previous_response_id=prev_response.response_id,
                            contradiction_type="direct",
                            confidence=confidence,
                        )
                    )

        return contradictions

    async def _detect_semantic_contradictions(
        self,
        current: AgentResponse,
        previous: List[AgentResponse],
    ) -> List[Contradiction]:
        """
        Semantik çelişkileri tespit et (embedding tabanlı).

        Args:
            current: Mevcut yanıt
            previous: Önceki yanıtlar

        Returns:
            List[Contradiction]: Tespit edilen çelişkiler
        """
        contradictions = []

        try:
            # Lazy loading for sentence-transformers
            if self._embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(
                    'paraphrase-multilingual-MiniLM-L12-v2'
                )

            import numpy as np

            # Mevcut yanıtın cümlelerini çıkar
            current_sentences = self._split_sentences(current.response_text)

            for prev_response in previous:
                prev_sentences = self._split_sentences(prev_response.response_text)

                if not current_sentences or not prev_sentences:
                    continue

                # Embedding hesapla
                current_embs = self._embedding_model.encode(current_sentences)
                prev_embs = self._embedding_model.encode(prev_sentences)

                # Her cümle çifti için çelişki kontrolü
                for i, curr_sent in enumerate(current_sentences):
                    for j, prev_sent in enumerate(prev_sentences):
                        # Benzerlik hesapla
                        similarity = float(
                            np.dot(current_embs[i], prev_embs[j]) / (
                                np.linalg.norm(current_embs[i]) *
                                np.linalg.norm(prev_embs[j])
                            )
                        )

                        # Yüksek benzerlik + farklı olumsuzluk = olası çelişki
                        if similarity > 0.7:
                            curr_negation = self._has_negation(curr_sent)
                            prev_negation = self._has_negation(prev_sent)

                            if curr_negation != prev_negation:
                                # Potansiyel semantik çelişki
                                topic = self._extract_main_topic(curr_sent)

                                if topic:
                                    contradictions.append(
                                        Contradiction(
                                            topic=topic,
                                            current_statement=curr_sent,
                                            previous_statement=prev_sent,
                                            previous_response_id=prev_response.response_id,
                                            contradiction_type="semantic",
                                            confidence=similarity * 0.8,
                                        )
                                    )

        except ImportError:
            logger.warning("sentence-transformers not available")
        except Exception as e:
            logger.error(f"Semantic contradiction detection error: {e}")

        return contradictions

    def _extract_topics(self, text: str) -> Dict[str, str]:
        """
        Metinden konu-ifade çiftlerini çıkar.

        Args:
            text: Metin

        Returns:
            Dict[str, str]: Konu -> ifade mapping
        """
        topics = {}
        sentences = self._split_sentences(text)

        for sentence in sentences:
            # Ana konuyu çıkar (ilk isim grubu)
            topic = self._extract_main_topic(sentence)
            if topic:
                topics[topic] = sentence

        return topics

    def _extract_main_topic(self, sentence: str) -> Optional[str]:
        """
        Cümleden ana konuyu çıkar.

        Args:
            sentence: Cümle

        Returns:
            str: Ana konu
        """
        # Basit konu çıkarma: ilk birkaç kelime
        words = sentence.split()

        if not words:
            return None

        # Stop words
        stop_words = {
            "ve", "veya", "ile", "için", "bu", "şu", "o",
            "bir", "de", "da", "den", "dan",
        }

        topic_words = []
        for word in words[:5]:
            word_clean = word.lower().strip('.,;:!?')
            if word_clean not in stop_words and len(word_clean) > 2:
                topic_words.append(word_clean)
                if len(topic_words) >= 3:
                    break

        return " ".join(topic_words) if topic_words else None

    def _split_sentences(self, text: str) -> List[str]:
        """
        Metni cümlelere ayır.

        Args:
            text: Metin

        Returns:
            List[str]: Cümle listesi
        """
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def _check_direct_contradiction(
        self,
        statement1: str,
        statement2: str,
    ) -> Tuple[bool, float]:
        """
        İki ifade arasında doğrudan çelişki var mı kontrol et.

        Args:
            statement1: İlk ifade
            statement2: İkinci ifade

        Returns:
            Tuple[bool, float]: (çelişki_var_mı, güven)
        """
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()

        # Olumsuzluk farkı kontrolü
        s1_negation = self._has_negation(s1_lower)
        s2_negation = self._has_negation(s2_lower)

        if s1_negation == s2_negation:
            # Aynı olumsuzluk durumu - çelişki yok
            return False, 0.0

        # Kelime benzerliği hesapla
        s1_words = set(s1_lower.split()) - set(self.NEGATION_WORDS)
        s2_words = set(s2_lower.split()) - set(self.NEGATION_WORDS)

        if not s1_words or not s2_words:
            return False, 0.0

        # Jaccard similarity
        intersection = len(s1_words & s2_words)
        union = len(s1_words | s2_words)

        similarity = intersection / union if union > 0 else 0

        # Yüksek benzerlik + farklı olumsuzluk = çelişki
        if similarity > 0.5:
            return True, similarity

        return False, 0.0

    def _has_negation(self, text: str) -> bool:
        """
        Metinde olumsuzluk var mı kontrol et.

        Args:
            text: Metin

        Returns:
            bool: Olumsuzluk var mı
        """
        text_lower = text.lower()
        return any(neg in text_lower for neg in self.NEGATION_WORDS)

    def _generate_consistency_suggestions(
        self,
        contradictions: List[Contradiction],
    ) -> List[str]:
        """
        Tutarlılık önerileri oluştur.

        Args:
            contradictions: Çelişki listesi

        Returns:
            List[str]: Öneri listesi
        """
        suggestions = []

        direct_count = sum(
            1 for c in contradictions
            if c.contradiction_type == "direct"
        )
        semantic_count = len(contradictions) - direct_count

        if direct_count > 0:
            suggestions.append(
                f"{direct_count} doğrudan çelişki tespit edildi. "
                "Önceki yanıtlarınızla tutarlı olun veya değişikliği açıklayın."
            )

        if semantic_count > 0:
            suggestions.append(
                f"{semantic_count} olası dolaylı çelişki tespit edildi. "
                "İfadelerinizi netleştirin."
            )

        # Spesifik konular için öneriler
        topics = set(c.topic for c in contradictions)
        if len(topics) <= 3:
            for topic in topics:
                suggestions.append(
                    f"'{topic}' konusunda tutarlı bir yaklaşım benimseyin."
                )

        return suggestions
