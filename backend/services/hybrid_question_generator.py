"""
Hibrit Soru Üretim Sistemi
ÖSYM-Guided AI Question Generation with Multi-Method Support

Bu modül:
1. ÖSYM examples kullanarak few-shot generation
2. IRT parametreli kalite kontrolü
3. Türkçe morfoloji analizi
4. Multi-model ensemble
5. Progressive learning pipeline

Research-backed implementation (2024 best practices)
"""

import asyncio
import logging
from datetime import datetime

# Existing services
from services.osym_inspired_generator import OSYMInspiredGenerator
from services.soru_bankasi_service import SoruBankasiServisi

logger = logging.getLogger(__name__)


class HybridQuestionGenerator:
    """
    Hibrit soru üretim sistemi

    Methods:
    1. osym_guided: Few-shot with 3 ÖSYM examples (recommended)
    2. ensemble: Multi-model generation, pick best
    3. progressive: Fine-tuned if available, else few-shot

    Features:
    - ÖSYM quality compliance
    - IRT parameter validation
    - Turkish morphology check
    - Automatic quality scoring
    - ✨ Wave 2B quality evaluation (NEW)
    """

    def __init__(
        self,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        enable_wave2b: bool = False,
        wave2b_threshold: float = 0.80,
        osym_reference_questions: list[dict] | None = None,
    ):
        # Initialize generators
        self.osym_generator = OSYMInspiredGenerator(
            openai_api_key=openai_api_key, anthropic_api_key=anthropic_api_key
        )

        # Initialize IRT & question bank service
        self.soru_bankasi = SoruBankasiServisi()

        # Quality thresholds
        self.quality_thresholds = {
            "min_osym_compliance": 0.75,
            "min_overall_quality": 0.70,
            "min_irt_discrimination": 0.5,
            "max_irt_difficulty_deviation": 1.5,
        }

        # Wave 2B integration (NEW)
        self.enable_wave2b = enable_wave2b
        self.wave2b_threshold = wave2b_threshold
        self._wave2b_evaluator = None

        if enable_wave2b:
            self._init_wave2b(osym_reference_questions)

    def _init_wave2b(self, osym_reference: list[dict] | None = None):
        """Initialize Wave 2B quality evaluator"""
        try:
            from services.comprehensive_quality_evaluator import (
                ComprehensiveQualityEvaluator,
            )

            self._wave2b_evaluator = ComprehensiveQualityEvaluator(
                osym_reference_questions=osym_reference
            )
            logger.info(
                f"✓ Wave 2B evaluator initialized (threshold: {self.wave2b_threshold})"
            )
        except Exception as e:
            logger.warning(f"Wave 2B evaluator not available: {e}")
            self.enable_wave2b = False

    async def generate_osym_quality_question(
        self,
        subject: str,
        topic: str,
        difficulty: str = "orta",
        exam_type: str = "TYT",
        provider: str = "claude",
        validate: bool = True,
        enable_retry: bool = True,  # NEW: Enable retry for short questions
    ) -> dict:
        """
        METHOD 1: ÖSYM-Guided Generation with Retry Logic

        Pipeline:
        1. RAG: Get 3 similar ÖSYM questions
        2. Style Analysis: Analyze ÖSYM patterns
        3. Few-Shot Generation: AI generates with examples
        4. LENGTH VALIDATION & RETRY: If too short (esp. Chemistry), retry with stricter prompt
        5. IRT Validation: Calculate IRT parameters
        6. Quality Scoring: Multi-metric evaluation

        Args:
            subject: Ders adı (Matematik, Fizik, vb.)
            topic: Konu başlığı
            difficulty: Zorluk (kolay, orta, zor)
            exam_type: Sınav tipi (TYT, AYT, YDT)
            provider: AI provider (claude, openai)
            validate: Kalite kontrolü yap mı?
            enable_retry: Enable retry logic for length validation (esp. Chemistry)

        Returns:
            Dict: Generated question with quality metrics
        """

        # Get subject config for length validation
        from services.subject_specific_prompts import get_subject_config

        subject_config = get_subject_config(subject)

        # Retry configuration
        max_retries = 2 if enable_retry else 0

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(
                        f"[RETRY] Attempt {attempt + 1}/{max_retries + 1} for {subject} - {topic}"
                    )

                # Generate question
                result = await self._generate_single_attempt(
                    subject, topic, difficulty, exam_type, provider, validate
                )

                # Length validation (especially critical for Chemistry)
                stem_length = len(result.get("stem", ""))

                if subject_config:
                    min_acceptable = subject_config.min_length
                    max_acceptable = subject_config.max_length

                    # Check if length is acceptable
                    if min_acceptable <= stem_length <= max_acceptable:
                        logger.info(
                            f"[LENGTH OK] {stem_length} chars (target: {min_acceptable}-{max_acceptable})"
                        )
                        return result  # Success!

                    # If too short and we have retries left
                    if stem_length < min_acceptable and attempt < max_retries:
                        deviation = (
                            (min_acceptable - stem_length) / min_acceptable
                        ) * 100
                        logger.warning(
                            f"[LENGTH FAIL - TOO SHORT] {stem_length} chars < {min_acceptable} min "
                            f"({deviation:.0f}% below target). Retrying..."
                        )
                        continue  # Retry

                    # If too long (no retry, but warn)
                    if stem_length > max_acceptable:
                        deviation = (
                            (stem_length - max_acceptable) / max_acceptable
                        ) * 100
                        logger.warning(
                            f"[LENGTH WARNING - TOO LONG] {stem_length} chars > {max_acceptable} max "
                            f"({deviation:.0f}% above target). Accepting anyway."
                        )

                    # Last attempt or other length issue
                    if attempt == max_retries:
                        logger.warning(
                            f"[LAST ATTEMPT] Using question with {stem_length} chars (target: {min_acceptable}-{max_acceptable})"
                        )
                        return result

                else:
                    # No subject config, accept any result
                    return result

            except Exception as e:
                if attempt == max_retries:
                    raise  # Re-raise on last attempt
                logger.warning(f"[RETRY] Attempt {attempt + 1} failed: {e}")
                continue

        # Should not reach here - all attempts failed
        raise Exception(
            f"Failed to generate question after {max_retries + 1} attempts for {subject} - {topic}"
        )

    async def _generate_single_attempt(
        self,
        subject: str,
        topic: str,
        difficulty: str = "orta",
        exam_type: str = "TYT",
        provider: str = "claude",
        validate: bool = True,
    ) -> dict:
        """
        Internal method: Single generation attempt without retry logic
        """
        try:
            logger.info(
                f"[HYBRID] Generating ÖSYM-guided question: {subject} - {topic}"
            )

            # Step 1: RAG - Get similar ÖSYM questions
            logger.info("[RAG] Retrieving 3 ÖSYM examples...")
            osym_examples = await self.osym_generator.get_similar_osym_questions(
                subject=subject, exam_type=exam_type, count=3
            )

            if not osym_examples:
                logger.warning(f"[WARNING] No ÖSYM examples found for {subject}")
                # Fallback: Continue without examples (zero-shot)

            # Step 2: Style Analysis
            logger.info("[STYLE] Analyzing ÖSYM style patterns...")
            style_guide = await self.osym_generator.analyze_osym_style(
                subject=subject, exam_type=exam_type
            )

            # Step 3: Few-Shot Generation with AI (OPTION A: Pass style_guide)
            logger.info(f"[AI] Generating question with {provider}...")
            ai_question = await self.osym_generator.generate_with_few_shot(
                subject=subject,
                topic=topic,
                exam_type=exam_type,
                difficulty=difficulty,
                provider=provider,
                style_guide=style_guide,  # OPTION A: Use database average
            )

            # Step 4: IRT Parameter Calculation
            logger.info("[IRT] Calculating IRT parameters...")
            irt_params = await self._calculate_irt_params(
                question_text=ai_question["stem"],
                difficulty=difficulty,
                subject=subject,
            )

            # Step 5: Turkish Morphology Analysis
            logger.info("[MORPH] Analyzing Turkish morphology...")
            morphology = await self._analyze_turkish_morphology(ai_question["stem"])

            # Step 6: Quality Scoring
            logger.info("[QUALITY] Calculating quality score...")
            quality_score = self._calculate_quality_score(
                ai_question=ai_question,
                style_guide=style_guide,
                irt_params=irt_params,
                morphology=morphology,
            )

            # Step 7: Validation (optional)
            if validate:
                is_valid = self._validate_question(quality_score)
                if not is_valid:
                    logger.warning("[QUALITY] Question did not pass validation")
                    quality_score["is_valid"] = False
                else:
                    quality_score["is_valid"] = True

            # Step 7.5: Wave 2B Evaluation (NEW)
            wave2b_evaluation = None
            if self.enable_wave2b and self._wave2b_evaluator:
                logger.info("[WAVE2B] Running advanced quality evaluation...")
                wave2b_evaluation = await self._run_wave2b_evaluation(
                    question_dict={
                        "question_text": ai_question["stem"],
                        "subject": subject,
                        "difficulty": difficulty,
                    }
                )

                if wave2b_evaluation:
                    logger.info(
                        f"[WAVE2B] Score: {wave2b_evaluation['overall_score']:.3f}, "
                        f"Decision: {wave2b_evaluation['decision']}"
                    )

                    # Update validation status based on Wave 2B
                    if wave2b_evaluation["decision"] == "REJECT":
                        quality_score["is_valid"] = False
                        quality_score["issues"].append("Wave 2B: Question rejected")
                    elif wave2b_evaluation["decision"] == "REVIEW":
                        quality_score["issues"].append(
                            "Wave 2B: Manual review recommended"
                        )

            # Step 8: Compile final result
            result = {
                # Question content
                "stem": ai_question["stem"],
                "options": ai_question["options"],
                "correct_answer": ai_question["correct_answer"],
                "explanation": ai_question["explanation"],
                # Metadata
                "subject": subject,
                "topic": topic,
                "difficulty": difficulty,
                "exam_type": exam_type,
                # Generation info
                "generation_method": "osym_guided_hybrid",
                "provider": provider,
                "osym_examples_used": len(osym_examples),
                # Quality metrics
                "osym_compliance_score": quality_score["osym_compliance"],
                "quality_score": quality_score["overall"],
                "grammar_score": quality_score.get("grammar_quality", 0.85),
                # IRT parameters
                "irt_difficulty": irt_params["difficulty"],
                "irt_discrimination": irt_params["discrimination"],
                "irt_guessing": irt_params["guessing"],
                # Turkish morphology
                "morphology_complexity": morphology["complexity"],
                "readability_score": morphology["readability"],
                # Validation
                "is_valid": quality_score.get("is_valid", True),
                "validation_issues": quality_score.get("issues", []),
                # Wave 2B Evaluation (NEW)
                "wave2b_enabled": self.enable_wave2b,
                "wave2b_evaluation": wave2b_evaluation if wave2b_evaluation else None,
                # Timestamps
                "created_at": datetime.now().isoformat(),
            }

            logger.info(
                f"[SUCCESS] Question generated! "
                f"Quality: {quality_score['overall']:.2f}, "
                f"ÖSYM: {quality_score['osym_compliance']:.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate question: {e}", exc_info=True)
            raise

    async def generate_ensemble(
        self, subject: str, topic: str, difficulty: str = "orta", exam_type: str = "TYT"
    ) -> dict:
        """
        METHOD 2: Multi-Model Ensemble

        Generate with 3 different methods, pick best:
        1. Claude + ÖSYM Few-Shot
        2. GPT-4 + ÖSYM Few-Shot
        3. Fine-tuned model (if available)

        Args:
            subject, topic, difficulty, exam_type

        Returns:
            Best quality question from 3 candidates
        """

        try:
            logger.info("[ENSEMBLE] Starting multi-model generation...")

            # Generate with Claude
            logger.info("[ENSEMBLE] Generating with Claude...")
            claude_question = await self.generate_osym_quality_question(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                exam_type=exam_type,
                provider="claude",
                validate=False,
            )

            # Generate with GPT-4
            logger.info("[ENSEMBLE] Generating with GPT-4...")
            gpt4_question = await self.generate_osym_quality_question(
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                exam_type=exam_type,
                provider="openai",
                validate=False,
            )

            # TODO: Add fine-tuned model generation when available
            # finetuned_question = await self.generate_with_finetuned(...)

            # Compare quality scores
            candidates = [
                {"question": claude_question, "source": "claude"},
                {"question": gpt4_question, "source": "gpt4"},
            ]

            # Pick best based on quality score
            best = max(candidates, key=lambda x: x["question"]["quality_score"])

            logger.info(
                f"[ENSEMBLE] Best model: {best['source']} "
                f"(quality: {best['question']['quality_score']:.2f})"
            )

            # Add ensemble metadata
            best_question = best["question"]
            best_question["generation_method"] = "ensemble"
            best_question["winning_provider"] = best["source"]
            best_question["candidates_evaluated"] = len(candidates)

            return best_question

        except Exception as e:
            logger.error(f"[ERROR] Ensemble generation failed: {e}", exc_info=True)
            # Fallback to single model
            return await self.generate_osym_quality_question(
                subject=subject, topic=topic, difficulty=difficulty, exam_type=exam_type
            )

    async def generate_progressive(
        self, subject: str, topic: str, difficulty: str = "orta", exam_type: str = "TYT"
    ) -> dict:
        """
        METHOD 3: Progressive Learning

        Try fine-tuned model first, fallback to few-shot

        Future implementation when fine-tuned model is ready
        """

        # TODO: Check if fine-tuned model exists
        has_finetuned_model = False

        if has_finetuned_model:
            logger.info("[PROGRESSIVE] Using fine-tuned model...")
            # return await self.generate_with_finetuned(...)
        else:
            logger.info("[PROGRESSIVE] Fallback to ÖSYM-guided generation...")
            return await self.generate_osym_quality_question(
                subject=subject, topic=topic, difficulty=difficulty, exam_type=exam_type
            )

    async def _calculate_irt_params(
        self, question_text: str, difficulty: str, subject: str
    ) -> dict[str, float]:
        """
        IRT parametrelerini hesapla

        Uses existing SoruBankasiServisi IRT calculator
        """
        try:
            irt_params = await self.soru_bankasi._hesapla_irt_parametreleri(
                zorluk=difficulty, konu=subject
            )

            return {
                "difficulty": irt_params["difficulty"],
                "discrimination": irt_params["discrimination"],
                "guessing": irt_params["guessing"],
            }

        except Exception as e:
            logger.error(f"[ERROR] IRT calculation failed: {e}", exc_info=True)
            # Default IRT parameters
            return {"difficulty": 0.0, "discrimination": 1.0, "guessing": 0.25}

    async def _analyze_turkish_morphology(self, text: str) -> dict[str, float]:
        """
        Türkçe morfoloji analizi

        Uses existing SoruBankasiServisi morphology analyzer
        """
        try:
            complexity = await self.soru_bankasi._hesapla_morfoloji_karmasikligi(text)
            readability = await self.soru_bankasi._hesapla_okunabilirlik(text)

            return {"complexity": complexity, "readability": readability}

        except Exception as e:
            logger.error(f"[ERROR] Morphology analysis failed: {e}", exc_info=True)
            return {"complexity": 0.5, "readability": 0.5}

    def _calculate_quality_score(
        self, ai_question: dict, style_guide: dict, irt_params: dict, morphology: dict
    ) -> dict[str, float]:
        """
        Multi-metric quality scoring

        Metrics:
        1. ÖSYM style compliance (0-1)
        2. IRT quality (0-1)
        3. Grammar quality (0-1)
        4. Morphology appropriateness (0-1)
        5. Readability (0-1)
        """

        # 1. ÖSYM Style Compliance
        stem_length = len(ai_question["stem"])
        target_length = style_guide.get("avg_stem_length", 600)

        # Length deviation (penalize if too far from ÖSYM average)
        length_deviation = abs(stem_length - target_length) / target_length
        osym_compliance = max(0, 1.0 - length_deviation)

        # Bonus: If within ±20% of target, full score
        if abs(stem_length - target_length) / target_length < 0.2:
            osym_compliance = 1.0

        # 2. IRT Quality
        # Good discrimination = 1.0-2.0 range
        discrimination = irt_params["discrimination"]
        irt_quality = min(1.0, max(0.0, (discrimination - 0.5) / 1.5))

        # 3. Grammar Quality (placeholder - needs actual Turkish NLP)
        # For now, assume good grammar (future: integrate Zemberek)
        grammar_quality = 0.85

        # 4. Morphology Appropriateness
        # Moderate complexity is good (0.4-0.7 range)
        complexity = morphology["complexity"]
        if 0.4 <= complexity <= 0.7:
            morphology_quality = 1.0
        else:
            morphology_quality = 1.0 - abs(complexity - 0.55) / 0.45

        # 5. Readability
        readability = morphology["readability"]

        # Overall Quality (weighted average)
        overall = (
            osym_compliance * 0.30
            + irt_quality * 0.25
            + grammar_quality * 0.20
            + morphology_quality * 0.15
            + readability * 0.10
        )

        # Collect issues
        issues = []
        if osym_compliance < 0.75:
            issues.append(f"Length deviation: {length_deviation:.1%} from ÖSYM average")
        if irt_quality < 0.5:
            issues.append(f"Low IRT discrimination: {discrimination:.2f}")
        if complexity < 0.3:
            issues.append("Too simple morphology")
        elif complexity > 0.8:
            issues.append("Too complex morphology")

        return {
            "overall": round(overall, 2),
            "osym_compliance": round(osym_compliance, 2),
            "irt_quality": round(irt_quality, 2),
            "grammar_quality": round(grammar_quality, 2),
            "morphology_quality": round(morphology_quality, 2),
            "readability": round(readability, 2),
            "issues": issues,
        }

    def _validate_question(self, quality_score: dict) -> bool:
        """
        Validate question against quality thresholds

        Returns:
            True if passes all thresholds, False otherwise
        """

        # Check thresholds
        if (
            quality_score["osym_compliance"]
            < self.quality_thresholds["min_osym_compliance"]
        ):
            return False

        if quality_score["overall"] < self.quality_thresholds["min_overall_quality"]:
            return False

        # All checks passed
        return True

    async def _run_wave2b_evaluation(self, question_dict: dict) -> dict | None:
        """
        Run Wave 2B comprehensive quality evaluation

        Args:
            question_dict: {question_text, subject, difficulty}

        Returns:
            Wave 2B evaluation result or None if failed
        """
        if not self._wave2b_evaluator:
            return None

        try:
            # Run comprehensive evaluation
            result = self._wave2b_evaluator.evaluate(
                question=question_dict,
                stage="standard",  # standard evaluation for generation
            )

            return {
                "overall_score": result.overall_score,
                "overall_grade": result.overall_grade,
                "decision": result.decision,
                "bloom_level": result.bloom_level,
                "bloom_confidence": result.bloom_confidence,
                "format_score": result.format_score,
                "quality_score": result.quality_score,
                "bertscore_f1": result.bertscore_f1
                if hasattr(result, "bertscore_f1")
                else None,
                "benchmark_similarity": result.benchmark_similarity
                if hasattr(result, "benchmark_similarity")
                else None,
                "strengths": result.strengths[:3],  # Top 3
                "weaknesses": result.weaknesses[:3],  # Top 3
                "recommendations": result.recommendations[:3],  # Top 3
            }

        except Exception as e:
            logger.error(f"Wave 2B evaluation failed: {e}", exc_info=True)
            return None


# ==================== USAGE EXAMPLE ====================


async def example_usage():
    """
    Örnek kullanım
    """

    # Initialize with API keys
    generator = HybridQuestionGenerator(
        anthropic_api_key="your-anthropic-key", openai_api_key="your-openai-key"
    )

    # Method 1: ÖSYM-Guided (Recommended)
    question = await generator.generate_osym_quality_question(
        subject="Matematik",
        topic="Türev Alma Kuralları",
        difficulty="orta",
        exam_type="TYT",
        provider="claude",
    )

    print("Generated Question:")
    print(f"Stem: {question['stem']}")
    print(f"Quality Score: {question['quality_score']}")
    print(f"ÖSYM Compliance: {question['osym_compliance_score']}")

    # Method 2: Ensemble (Best Quality)
    best_question = await generator.generate_ensemble(
        subject="Fizik", topic="Newton Kanunları", difficulty="zor"
    )

    print(f"\nBest Model: {best_question['winning_provider']}")
    print(f"Quality: {best_question['quality_score']}")


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
