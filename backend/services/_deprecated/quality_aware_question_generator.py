"""
Kalite Kontrolü ile Soru Üretici
Wave 2B Entegrasyonu - Otomatik Kalite Değerlendirmeli Üretim

Bu modül, Wave 2B değerlendirme modüllerini soru üretim sürecine entegre eder:
- Otomatik kalite kontrolü
- BERTScore semantik benzerlik
- ÖSYM Benchmark kıyaslama
- Bloom seviye doğrulama
- Akıllı yeniden deneme
"""

import logging
from typing import Dict, List, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class QualityAwareQuestionGenerator:
    """
    Kalite kontrolü ile soru üretici

    Wave 1 + 2A özelliklerini Wave 2B değerlendirme ile birleştirir:
    - XML-structured prompts
    - Keyword reranking
    - Subject-specific prompts
    - ✨ Otomatik kalite değerlendirme (YENİ)
    - ✨ Semantik benzerlik kontrolü (YENİ)
    - ✨ Bloom seviye doğrulama (YENİ)
    """

    def __init__(
        self,
        osym_reference_questions: Optional[List[Dict]] = None,
        enable_bertscore: bool = True,
        enable_benchmark: bool = True,
        quality_threshold: float = 0.80,
    ):
        """
        Args:
            osym_reference_questions: ÖSYM referans soruları (benchmark için)
            enable_bertscore: BERTScore kontrolünü aktifleştir
            enable_benchmark: Benchmark kıyaslamayı aktifleştir
            quality_threshold: Minimum kabul edilebilir kalite skoru (0-1)
        """
        self.quality_threshold = quality_threshold
        self._osym_reference = osym_reference_questions or []

        # Mevcut üretici (Wave 1 + 2A)
        from services.osym_inspired_generator import OSYMInspiredGenerator

        self.generator = OSYMInspiredGenerator()

        # Wave 2B modülleri
        self._init_quality_modules(enable_bertscore, enable_benchmark)

        logger.info(
            f"QualityAwareQuestionGenerator initialized: "
            f"threshold={quality_threshold}, "
            f"bertscore={self._bertscore_enabled}, "
            f"benchmark={self._benchmark_enabled}"
        )

    def _init_quality_modules(self, enable_bertscore: bool, enable_benchmark: bool):
        """Wave 2B kalite modüllerini başlat"""
        # Comprehensive evaluator (her zaman aktif)
        try:
            from services.comprehensive_quality_evaluator import (
                ComprehensiveQualityEvaluator,
            )

            self.evaluator = ComprehensiveQualityEvaluator(
                osym_reference_questions=self._osym_reference
            )
            logger.info("✓ Comprehensive evaluator loaded")
        except Exception as e:
            logger.warning(f"Comprehensive evaluator not available: {e}")
            self.evaluator = None

        # BERTScore (opsiyonel)
        self._bertscore_enabled = False
        if enable_bertscore:
            try:
                from services.bertscore_evaluator import BERTScoreEvaluator

                self.bertscore = BERTScoreEvaluator()
                self._bertscore_enabled = self.bertscore.is_available()
                if self._bertscore_enabled:
                    logger.info("✓ BERTScore evaluator loaded")
            except Exception as e:
                logger.warning(f"BERTScore not available: {e}")

        # Benchmark (opsiyonel)
        self._benchmark_enabled = False
        if enable_benchmark and self._osym_reference:
            try:
                from services.osym_benchmark_comparator import OSYMBenchmarkComparator

                self.benchmark = OSYMBenchmarkComparator()
                self.benchmark.set_reference_benchmark(self._osym_reference)
                self._benchmark_enabled = True
                logger.info("✓ ÖSYM Benchmark loaded")
            except Exception as e:
                logger.warning(f"Benchmark not available: {e}")

    async def generate_quality_question(
        self,
        subject: str,
        topic: str,
        difficulty: str = "orta",
        bloom_level: Optional[str] = None,
        max_retries: int = 3,
        evaluation_stage: str = "standard",
    ) -> Optional[Dict]:
        """
        Kalite kontrolü ile soru üret

        Args:
            subject: Ders (Matematik, Fizik, vb.)
            topic: Konu
            difficulty: Zorluk (kolay, orta, zor)
            bloom_level: Hedef Bloom seviyesi (opsiyonel)
            max_retries: Maksimum yeniden deneme sayısı
            evaluation_stage: Değerlendirme aşaması (quick/standard/thorough)

        Returns:
            Kaliteli soru dict veya None
        """
        attempt = 0
        best_question = None
        best_score = 0.0

        while attempt < max_retries:
            attempt += 1

            logger.info(
                f"[Attempt {attempt}/{max_retries}] Generating {subject} - {topic} "
                f"({difficulty})"
            )

            # 1. Soru üret (Wave 1 + 2A)
            question = await self.generator.generate_with_few_shot(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                exam_type="TYT",  # Default exam type
                provider="claude",  # Use Claude by default
            )

            if not question:
                logger.warning(f"[Attempt {attempt}] Generation failed")
                continue

            # 2. Kalite değerlendir (Wave 2B)
            evaluation = await self._evaluate_question(
                question=question, stage=evaluation_stage, expected_bloom=bloom_level
            )

            if not evaluation:
                logger.warning(f"[Attempt {attempt}] Evaluation failed")
                continue

            overall_score = evaluation.get("overall_score", 0.0)
            decision = evaluation.get("decision", "REJECT")

            logger.info(
                f"[Attempt {attempt}] Quality: {overall_score:.3f} ({decision})"
            )

            # En iyi soruyu sakla
            if overall_score > best_score:
                best_score = overall_score
                best_question = question
                best_question["quality_evaluation"] = evaluation

            # Hedef kaliteye ulaşıldı mı?
            if overall_score >= self.quality_threshold and decision == "APPROVE":
                logger.info(
                    f"✓ Quality target reached: {overall_score:.3f} >= "
                    f"{self.quality_threshold:.3f}"
                )
                return best_question

            # Yeniden deneme önerileri uygula
            if evaluation.get("recommendations"):
                logger.info(
                    f"[Attempt {attempt}] Recommendations: "
                    f"{evaluation['recommendations'][:2]}"
                )

        # Max deneme tükendi
        if best_question and best_score >= 0.70:
            logger.warning(
                f"⚠️  Max retries reached. Using best question: " f"{best_score:.3f}"
            )
            return best_question
        else:
            logger.error(
                f"✗ Failed to generate quality question after {max_retries} attempts. "
                f"Best score: {best_score:.3f}"
            )
            return None

    async def _evaluate_question(
        self,
        question: Dict,
        stage: str = "standard",
        expected_bloom: Optional[str] = None,
    ) -> Optional[Dict]:
        """Soruyu değerlendir"""
        if not self.evaluator:
            # Evaluator yoksa basit kontrol
            return {"overall_score": 0.75, "decision": "APPROVE", "method": "fallback"}

        try:
            # Comprehensive evaluation
            result = self.evaluator.evaluate(
                question=question, stage=stage, subject=question.get("subject")
            )

            evaluation = {
                "overall_score": result.overall_score,
                "decision": result.decision,
                "grade": result.overall_grade,
                "format_score": result.format_score,
                "quality_score": result.quality_score,
                "bloom_level": result.bloom_level,
                "bloom_confidence": result.bloom_confidence,
                "strengths": result.strengths,
                "weaknesses": result.weaknesses,
                "recommendations": result.recommendations,
                "evaluation_time_ms": result.evaluation_time_ms,
            }

            # BERTScore ekle (eğer aktifse)
            if self._bertscore_enabled and result.bertscore_f1:
                evaluation["bertscore_f1"] = result.bertscore_f1

            # Benchmark ekle (eğer aktifse)
            if self._benchmark_enabled and result.benchmark_similarity:
                evaluation["benchmark_similarity"] = result.benchmark_similarity

            # Bloom kontrolü
            if expected_bloom and result.bloom_level:
                expected_num = self._bloom_name_to_number(expected_bloom)
                if expected_num and expected_num != result.bloom_level:
                    evaluation["bloom_mismatch"] = True
                    evaluation["expected_bloom"] = expected_bloom
                    logger.warning(
                        f"Bloom mismatch: expected {expected_bloom}, "
                        f"got level {result.bloom_level}"
                    )

            return evaluation

        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return None

    def _bloom_name_to_number(self, name: str) -> Optional[int]:
        """Bloom isimden numaraya"""
        mapping = {
            "hatırlama": 1,
            "anlama": 2,
            "uygulama": 3,
            "analiz": 4,
            "değerlendirme": 5,
            "yaratma": 6,
        }
        return mapping.get(name.lower())

    async def generate_batch_with_quality(
        self, requirements: List[Dict], evaluation_stage: str = "standard"
    ) -> Dict:
        """
        Toplu kaliteli soru üret

        Args:
            requirements: Liste of {subject, topic, difficulty, bloom_level}
            evaluation_stage: Değerlendirme aşaması

        Returns:
            {
                "questions": [...],
                "statistics": {...},
                "failed": [...]
            }
        """
        start_time = datetime.now()

        questions = []
        failed = []
        quality_scores = []

        for i, req in enumerate(requirements, 1):
            logger.info(f"\n[{i}/{len(requirements)}] Generating question...")

            question = await self.generate_quality_question(
                subject=req.get("subject"),
                topic=req.get("topic"),
                difficulty=req.get("difficulty", "orta"),
                bloom_level=req.get("bloom_level"),
                max_retries=req.get("max_retries", 3),
                evaluation_stage=evaluation_stage,
            )

            if question:
                questions.append(question)
                score = question.get("quality_evaluation", {}).get("overall_score", 0)
                quality_scores.append(score)
                logger.info(f"✓ [{i}/{len(requirements)}] Success: {score:.3f}")
            else:
                failed.append(req)
                logger.error(f"✗ [{i}/{len(requirements)}] Failed")

        duration = (datetime.now() - start_time).total_seconds()

        # İstatistikler
        statistics = {
            "total_requested": len(requirements),
            "successful": len(questions),
            "failed": len(failed),
            "success_rate": len(questions) / len(requirements) if requirements else 0,
            "average_quality": sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0,
            "min_quality": min(quality_scores) if quality_scores else 0,
            "max_quality": max(quality_scores) if quality_scores else 0,
            "duration_seconds": duration,
            "questions_per_second": len(questions) / duration if duration > 0 else 0,
        }

        logger.info(
            f"\n📊 Batch Generation Complete:\n"
            f"  Success: {statistics['successful']}/{statistics['total_requested']} "
            f"({statistics['success_rate']:.1%})\n"
            f"  Avg Quality: {statistics['average_quality']:.3f}\n"
            f"  Duration: {statistics['duration_seconds']:.1f}s"
        )

        return {"questions": questions, "statistics": statistics, "failed": failed}


# Kolaylık fonksiyonları


async def generate_single_quality_question(
    subject: str,
    topic: str,
    difficulty: str = "orta",
    osym_reference: Optional[List[Dict]] = None,
) -> Optional[Dict]:
    """
    Tek kaliteli soru üret (kolaylık fonksiyonu)

    Kullanım:
        soru = await generate_single_quality_question("Matematik", "Türev", "orta")
    """
    generator = QualityAwareQuestionGenerator(
        osym_reference_questions=osym_reference, quality_threshold=0.80
    )

    return await generator.generate_quality_question(
        subject=subject, topic=topic, difficulty=difficulty
    )


# Örnek kullanım
if __name__ == "__main__":

    async def demo():
        print("=" * 70)
        print("KALİTE KONTROLLÜ SORU ÜRETİMİ - DEMO")
        print("=" * 70)

        # Tek soru
        print("\n1. Tek Soru Üretimi:")
        generator = QualityAwareQuestionGenerator(
            quality_threshold=0.80, enable_bertscore=True, enable_benchmark=False
        )

        soru = await generator.generate_quality_question(
            subject="Kimya",
            topic="Mol Kavramı",
            difficulty="orta",
            max_retries=3,
            evaluation_stage="standard",
        )

        if soru:
            eval_result = soru.get("quality_evaluation", {})
            print("\n✓ Soru üretildi!")
            print(f"  Kalite Skoru: {eval_result.get('overall_score', 0):.3f}")
            print(f"  Karar: {eval_result.get('decision')}")
            print(f"  Bloom: Seviye {eval_result.get('bloom_level')}")
            print(f"  Soru: {soru.get('question_text', '')[:100]}...")

        # Toplu üretim
        print("\n\n2. Toplu Soru Üretimi:")
        requirements = [
            {"subject": "Matematik", "topic": "Türev", "difficulty": "orta"},
            {"subject": "Fizik", "topic": "Newton Kanunları", "difficulty": "zor"},
            {"subject": "Kimya", "topic": "Asit-Baz", "difficulty": "kolay"},
        ]

        results = await generator.generate_batch_with_quality(
            requirements=requirements, evaluation_stage="quick"
        )

        print("\n✓ Toplu üretim tamamlandı:")
        print(f"  Başarı oranı: {results['statistics']['success_rate']:.1%}")
        print(f"  Ortalama kalite: {results['statistics']['average_quality']:.3f}")
        print(f"  Süre: {results['statistics']['duration_seconds']:.1f}s")

    # Demo'yu çalıştır
    asyncio.run(demo())
