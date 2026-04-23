"""
Celdirici (Distractor) Uretim Sistemi
REQ-48.37-48.40: Plausible distractor generation, Common misconception database, Distractor quality scoring

Bu modul OSYM standartlarinda makul celdiriciler uretir ve
Turk ogrencilerin yaygın yaptigi hatalari kullanir.
"""

import json
import logging
from typing import Any

from models.curriculum import SubjectType

from .models import MISCONCEPTION_DATABASE, get_misconceptions

logger = logging.getLogger(__name__)


class DistractorGenerationSystem:
    """
    Celdirici (Distractor) Uretim Sistemi
    REQ-48.37-48.40: Plausible distractor generation, Common misconception database, Distractor quality scoring
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: LLM servisi
        """
        self.llm_service = llm_service

    @property
    def misconception_database(self) -> dict:
        """REQ-48.38: Common misconception database - Yaygın kavram yanılgıları veritabanı"""
        return MISCONCEPTION_DATABASE

    async def generate_distractors(
        self,
        correct_answer: str,
        question_context: str,
        subject: SubjectType,
        topic: str,
        count: int = 3,
    ) -> list[dict[str, Any]]:
        """
        REQ-48.37: Plausible distractor generation - Makul celdiriciler uretmek

        Args:
            correct_answer: Dogru cevap
            question_context: Soru baglami
            subject: Ders
            topic: Konu
            count: Uretilecek celdirici sayisi

        Returns:
            Celdirici listesi (her biri quality_score ile)
        """
        try:
            distractors = []

            # 1. Misconception-based distractors (yaygin hatalardan)
            misconception_distractors = self._generate_misconception_distractors(
                subject, topic, correct_answer, count=count // 2 + 1
            )
            distractors.extend(misconception_distractors)

            # 2. LLM-based distractors (AI ile uretilen)
            if self.llm_service and len(distractors) < count:
                llm_distractors = await self._generate_llm_distractors(
                    correct_answer,
                    question_context,
                    subject,
                    topic,
                    count - len(distractors),
                )
                distractors.extend(llm_distractors)

            # 3. Fallback: Basit varyasyonlar
            while len(distractors) < count:
                fallback_distractor = self._generate_fallback_distractor(
                    correct_answer, len(distractors)
                )
                distractors.append(fallback_distractor)

            # 4. Quality scoring - Her celdiriciyi skorla
            scored_distractors = []
            for distractor in distractors:
                score = self._score_distractor_quality(
                    distractor["text"], correct_answer, question_context
                )
                scored_distractors.append(
                    {
                        "text": distractor["text"],
                        "quality_score": score,
                        "generation_method": distractor.get("method", "unknown"),
                    }
                )

            # 5. En yuksek skorlu celdiricileri sec
            scored_distractors.sort(key=lambda x: x["quality_score"], reverse=True)

            # REQ-48.40: En yuksek skorlu 3 celdiriciyi kullanmak
            return scored_distractors[:count]

        except Exception as e:
            logger.error(f"Celdirici uretim hatasi: {e}")
            return self._generate_fallback_distractors(correct_answer, count)

    def _generate_misconception_distractors(
        self, subject: SubjectType, topic: str, correct_answer: str, count: int
    ) -> list[dict[str, str]]:
        """
        REQ-48.38: Common misconception database kullanarak celdirici uret
        """
        distractors = []
        misconceptions = get_misconceptions(subject.value, topic)

        for i, misconception in enumerate(misconceptions[:count]):
            distractors.append(
                {
                    "text": f"{chr(66+i)}) {misconception} (yaygin hata)",
                    "method": "misconception_based",
                }
            )

        return distractors

    async def _generate_llm_distractors(
        self,
        correct_answer: str,
        question_context: str,
        subject: SubjectType,
        topic: str,
        count: int,
    ) -> list[dict[str, str]]:
        """LLM ile celdirici uret"""
        try:
            prompt = f"""Sen bir OSYM soru hazirlama uzmanisin. Asagidaki soru icin {count} adet makul ama yanlis celdirici (distractor) uret:

SORU BAGLAMI: {question_context}
DOGRU CEVAP: {correct_answer}
DERS: {subject.value}
KONU: {topic}

CELDIRICI KRITERLERI:
1. Makul gorunmeli (plausible)
2. Ogrencilerin yapabilecegi yaygin hatalar olmali
3. Dogru cevapla karistirilabilir olmali
4. Tamamen sacma olmamali

CIKTI FORMATI (JSON):
{{
    "distractors": [
        "Celdirici 1",
        "Celdirici 2",
        ...
    ]
}}"""

            if self.llm_service:
                response = await self.llm_service.generate(
                    prompt, max_tokens=300, temperature=0.8
                )
                data = json.loads(response)
                return [
                    {"text": d, "method": "llm_generated"}
                    for d in data.get("distractors", [])
                ]

        except Exception as e:
            logger.error(f"LLM celdirici uretim hatasi: {e}")

        return []

    def _generate_fallback_distractor(
        self, correct_answer: str, index: int
    ) -> dict[str, str]:
        """Fallback celdirici uret"""
        return {
            "text": f"{chr(66+index)}) Alternatif cevap {index+1}",
            "method": "fallback",
        }

    def _generate_fallback_distractors(
        self, correct_answer: str, count: int
    ) -> list[dict[str, Any]]:
        """Fallback celdiriciler"""
        return [
            {
                "text": f"{chr(66+i)}) Alternatif cevap {i+1}",
                "quality_score": 0.5,
                "generation_method": "fallback",
            }
            for i in range(count)
        ]

    def _score_distractor_quality(
        self, distractor: str, correct_answer: str, question_context: str
    ) -> float:
        """
        REQ-48.39: Distractor quality scoring - Her celdiriciyi 0-100 arasi degerlendirmek

        Returns:
            Quality score (0.0 - 1.0)
        """
        score = 0.0

        # 1. Uzunluk benzerligi (dogru cevapla benzer uzunlukta olmali)
        len_distractor = len(distractor) if distractor else 1
        len_correct = len(correct_answer) if correct_answer else 1
        length_ratio = min(len_distractor, len_correct) / max(len_distractor, len_correct)
        score += length_ratio * 0.2

        # 2. Kelime benzerligi (bazi ortak kelimeler olmali ama cok fazla degil)
        distractor_words = set(distractor.lower().split()) if distractor else set()
        correct_words = set(correct_answer.lower().split()) if correct_answer else set()
        common_words = distractor_words & correct_words

        max_words = max(len(distractor_words), len(correct_words), 1)
        similarity = len(common_words) / max_words

        # Ideal benzerlik %30-60 arasi
        if 0.3 <= similarity <= 0.6:
            score += 0.3
        elif similarity < 0.3:
            score += similarity
        else:
            score += (1.0 - similarity) * 0.3

        # 3. Baglam uygunlugu (soru baglamiyla ilgili olmali)
        context_words = set(question_context.lower().split()) if question_context else set()
        if distractor_words:
            context_relevance = len(distractor_words & context_words) / len(distractor_words)
        else:
            context_relevance = 0
        score += context_relevance * 0.3

        # 4. Makulluk (cok kisa veya cok uzun olmamali)
        if 10 <= len(distractor) <= 200:
            score += 0.2

        return min(score, 1.0)
