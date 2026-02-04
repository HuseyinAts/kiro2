"""
Comprehensive Quality Evaluator Pipeline
Wave 2B - Integration: Complete Question Quality Assessment

Purpose:
- Unified pipeline for all quality evaluation methods
- Multi-stage evaluation (fast → thorough)
- Combines: Format, Quality, BERTScore, Bloom, ÖSYM Benchmark
- Provides actionable recommendations

Based on: SORU_URETIM_DEGERLENDIRME_CERCEVESI.md

Evaluation Stages:
1. Quick (< 100ms): Format validation, basic quality
2. Standard (< 2s): + Bloom classification, length check
3. Thorough (< 10s): + BERTScore comparison
4. Complete (< 30s): + ÖSYM benchmark analysis, full report

Thresholds:
- Overall score ≥ 0.90: Excellent (auto-approve)
- Overall score ≥ 0.80: Good (approve with minor notes)
- Overall score ≥ 0.70: Acceptable (manual review recommended)
- Overall score < 0.70: Needs improvement (reject or revise)
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a question"""

    # Overall assessment
    overall_score: float = 0.0  # 0-1
    overall_grade: str = ""  # Excellent/Good/Acceptable/Needs Improvement
    decision: str = ""  # APPROVE/REVIEW/REJECT

    # Component scores (0-1 each)
    format_score: float = 0.0
    quality_score: float = 0.0
    bloom_score: float = 0.0
    bertscore_f1: Optional[float] = None
    benchmark_similarity: Optional[float] = None

    # Detailed results
    format_issues: List[str] = field(default_factory=list)
    quality_issues: List[str] = field(default_factory=list)
    bloom_level: Optional[int] = None
    bloom_confidence: Optional[float] = None

    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    # Metadata
    evaluation_stage: str = "unknown"
    evaluation_time_ms: float = 0.0
    evaluated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ComprehensiveQualityEvaluator:
    """
    Comprehensive quality evaluation pipeline

    Integrates all evaluation modules:
    - Format validation
    - Quality scoring
    - Bloom classification
    - BERTScore semantic similarity
    - ÖSYM benchmark comparison
    """

    def __init__(self, osym_reference_questions: Optional[List[Dict]] = None):
        """
        Initialize evaluator

        Args:
            osym_reference_questions: ÖSYM questions for benchmark and BERTScore
        """
        self.logger = logger
        self._osym_questions = osym_reference_questions or []

        # Initialize all sub-evaluators
        self._init_evaluators()

    def _init_evaluators(self):
        """Initialize all evaluation modules"""
        # 1. BERTScore evaluator
        try:
            from services.bertscore_evaluator import BERTScoreEvaluator

            self.bertscore_evaluator = BERTScoreEvaluator()
            self._bertscore_available = self.bertscore_evaluator.is_available()
        except Exception as e:
            logger.warning(f"BERTScore evaluator not available: {e}")
            self.bertscore_evaluator = None
            self._bertscore_available = False

        # 2. ÖSYM Benchmark comparator
        try:
            from services.osym_benchmark_comparator import OSYMBenchmarkComparator

            self.benchmark_comparator = OSYMBenchmarkComparator()
            if self._osym_questions:
                self.benchmark_comparator.set_reference_benchmark(self._osym_questions)
                self._benchmark_available = True
            else:
                self._benchmark_available = False
                logger.warning("No ÖSYM reference questions provided for benchmark")
        except Exception as e:
            logger.warning(f"Benchmark comparator not available: {e}")
            self.benchmark_comparator = None
            self._benchmark_available = False

        # 3. Enhanced Bloom classifier
        try:
            from services.enhanced_bloom_classifier import EnhancedBloomClassifier

            self.bloom_classifier = EnhancedBloomClassifier()
            self._bloom_available = True
        except Exception as e:
            logger.warning(f"Bloom classifier not available: {e}")
            self.bloom_classifier = None
            self._bloom_available = False

        # 4. Existing quality scorer (if available)
        try:
            from services.question_quality_scorer import QuestionQualityScorer

            self.quality_scorer = QuestionQualityScorer()
            self._quality_scorer_available = True
        except Exception as e:
            logger.warning(f"Quality scorer not available: {e}")
            self.quality_scorer = None
            self._quality_scorer_available = False

        logger.info(
            f"Evaluator initialized: "
            f"BERTScore={self._bertscore_available}, "
            f"Benchmark={self._benchmark_available}, "
            f"Bloom={self._bloom_available}, "
            f"Quality={self._quality_scorer_available}"
        )

    def evaluate(
        self, question: Dict, stage: str = "standard", subject: Optional[str] = None
    ) -> EvaluationResult:
        """
        Evaluate question quality

        Args:
            question: Question dict with keys:
                - question_text or metin (str, required)
                - difficulty or zorluk (str, optional)
                - subject or konu (str, optional)
                - correct_answer or dogru_cevap (str, optional)
                - choices or secenekler (list, optional)
            stage: Evaluation thoroughness:
                - "quick": Format + basic quality (~100ms)
                - "standard": + Bloom + length (~2s)
                - "thorough": + BERTScore (~10s)
                - "complete": + Full benchmark (~30s)
            subject: Subject for subject-specific validation

        Returns:
            EvaluationResult with comprehensive assessment
        """
        import time

        start_time = time.time()

        result = EvaluationResult(evaluation_stage=stage)

        # Extract question text
        question_text = question.get("question_text") or question.get("metin") or ""
        if not question_text:
            result.overall_score = 0.0
            result.overall_grade = "Invalid"
            result.decision = "REJECT"
            result.weaknesses.append("No question text found")
            return result

        # Stage 1: Format validation (ALWAYS)
        result.format_score, result.format_issues = self._validate_format(question)

        if result.format_score < 0.5:
            # Critical format issues
            result.overall_score = result.format_score
            result.overall_grade = "Needs Improvement"
            result.decision = "REJECT"
            result.weaknesses.append("Critical format issues")
            return result

        # Stage 2: Quality scoring (if available)
        if self._quality_scorer_available:
            quality_result = self.quality_scorer.score(question)
            result.quality_score = quality_result.get("overall_score", 0.0)
            result.quality_issues = quality_result.get("issues", [])
        else:
            result.quality_score = 0.8  # Default if scorer not available

        if stage == "quick":
            result.overall_score = (result.format_score + result.quality_score) / 2
            result = self._finalize_result(result)
            result.evaluation_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 3: Bloom classification (STANDARD+)
        if self._bloom_available:
            bloom_pred = self.bloom_classifier.classify(
                question_text, method="ensemble"
            )
            result.bloom_level = bloom_pred.level
            result.bloom_confidence = bloom_pred.confidence
            result.bloom_score = bloom_pred.confidence  # Use confidence as score

            # Check if Bloom level matches expected (if provided)
            expected_bloom = question.get("bloom_level") or question.get(
                "bloom_seviyesi"
            )
            if expected_bloom:
                expected_num = self._bloom_name_to_number(expected_bloom)
                if expected_num and expected_num != bloom_pred.level:
                    result.weaknesses.append(
                        f"Bloom level mismatch: Expected {expected_bloom}, "
                        f"Got {bloom_pred.level_name}"
                    )

        # Length validation
        length_score, length_issues = self._validate_length(question_text, subject)
        if length_issues:
            result.weaknesses.extend(length_issues)

        if stage == "standard":
            scores = [result.format_score, result.quality_score]
            if result.bloom_score:
                scores.append(result.bloom_score)
            scores.append(length_score)
            result.overall_score = sum(scores) / len(scores)
            result = self._finalize_result(result)
            result.evaluation_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 4: BERTScore comparison (THOROUGH+)
        if self._bertscore_available and self._osym_questions:
            # Find most similar ÖSYM question
            pool_texts = [
                q.get("question_text") or q.get("metin") or ""
                for q in self._osym_questions
                if q.get("question_text") or q.get("metin")
            ]

            if pool_texts:
                matches = self.bertscore_evaluator.find_best_match(
                    question_text, pool_texts[:100], top_k=1  # Limit to 100 for speed
                )

                if matches:
                    result.bertscore_f1 = matches[0]["f1_score"]

                    # Interpret BERTScore
                    if result.bertscore_f1 >= 0.85:
                        result.strengths.append(
                            f"Excellent semantic similarity to ÖSYM (F1={result.bertscore_f1:.3f})"
                        )
                    elif result.bertscore_f1 >= 0.80:
                        result.strengths.append(
                            f"Good semantic similarity to ÖSYM (F1={result.bertscore_f1:.3f})"
                        )
                    elif result.bertscore_f1 < 0.75:
                        result.weaknesses.append(
                            f"Low semantic similarity to ÖSYM (F1={result.bertscore_f1:.3f})"
                        )

        if stage == "thorough":
            scores = [result.format_score, result.quality_score, length_score]
            if result.bloom_score:
                scores.append(result.bloom_score)
            if result.bertscore_f1:
                scores.append(result.bertscore_f1)
            result.overall_score = sum(scores) / len(scores)
            result = self._finalize_result(result)
            result.evaluation_time_ms = (time.time() - start_time) * 1000
            return result

        # Stage 5: Full benchmark comparison (COMPLETE)
        if self._benchmark_available:
            comparison = self.benchmark_comparator.compare_against_benchmark([question])
            result.benchmark_similarity = comparison.overall_similarity

            # Add benchmark insights
            if comparison.overall_similarity >= 0.85:
                result.strengths.append(
                    f"Excellent ÖSYM benchmark match ({comparison.overall_similarity:.3f})"
                )
            elif comparison.overall_similarity < 0.75:
                result.weaknesses.append(
                    f"Low ÖSYM benchmark match ({comparison.overall_similarity:.3f})"
                )

            # Add specific recommendations from benchmark
            result.recommendations.extend(comparison.recommendations)

        # Calculate final overall score
        scores = [result.format_score, result.quality_score, length_score]
        if result.bloom_score:
            scores.append(result.bloom_score)
        if result.bertscore_f1:
            scores.append(result.bertscore_f1)
        if result.benchmark_similarity:
            scores.append(result.benchmark_similarity)

        result.overall_score = sum(scores) / len(scores)
        result = self._finalize_result(result)
        result.evaluation_time_ms = (time.time() - start_time) * 1000

        return result

    def _validate_format(self, question: Dict) -> Tuple[float, List[str]]:
        """
        Validate question format

        Returns:
            (score, issues)
        """
        score = 1.0
        issues = []

        # Required fields
        if not (question.get("question_text") or question.get("metin")):
            score -= 0.5
            issues.append("Missing question text")

        # Check for choices
        choices = question.get("choices") or question.get("secenekler") or []
        if not choices or len(choices) < 4:
            score -= 0.2
            issues.append(f"Insufficient choices (need 4-5, got {len(choices)})")

        # Check for correct answer
        if not (question.get("correct_answer") or question.get("dogru_cevap")):
            score -= 0.2
            issues.append("Missing correct answer")

        return max(0.0, score), issues

    def _validate_length(
        self, question_text: str, subject: Optional[str] = None
    ) -> Tuple[float, List[str]]:
        """
        Validate question length against ÖSYM standards

        Returns:
            (score, issues)
        """
        length = len(question_text)
        issues = []

        # Subject-specific targets (from subject_specific_prompts.py)
        targets = {
            "Kimya": (141, 263),  # ±30% from 202
            "Matematik": (272, 504),  # ±30% from 388
            "Fizik": (317, 589),  # ±30% from 453
            "Biyoloji": (204, 378),  # ±30% from 291
            "Türkçe": (462, 858),  # ±30% from 660
        }

        # Get target for subject or use general range
        if subject and subject in targets:
            min_len, max_len = targets[subject]
        else:
            min_len, max_len = 200, 600  # General range

        # Check length
        if length < min_len:
            deviation = (min_len - length) / min_len
            score = 1.0 - deviation
            issues.append(f"Question too short ({length} chars, min {min_len})")
        elif length > max_len:
            deviation = (length - max_len) / max_len
            score = 1.0 - deviation
            issues.append(f"Question too long ({length} chars, max {max_len})")
        else:
            score = 1.0  # Perfect

        return max(0.0, score), issues

    def _bloom_name_to_number(self, name: str) -> Optional[int]:
        """Convert Bloom level name to number"""
        mapping = {
            "hatırlama": 1,
            "anlama": 2,
            "uygulama": 3,
            "analiz": 4,
            "değerlendirme": 5,
            "yaratma": 6,
            "bilgi": 1,
            "kavrama": 2,
            "sentez": 5,
        }
        return mapping.get(name.lower())

    def _finalize_result(self, result: EvaluationResult) -> EvaluationResult:
        """
        Finalize evaluation result with grade and decision

        Args:
            result: Partial result

        Returns:
            Complete result with grade and decision
        """
        # Determine grade
        if result.overall_score >= 0.90:
            result.overall_grade = "Excellent"
            result.decision = "APPROVE"
        elif result.overall_score >= 0.80:
            result.overall_grade = "Good"
            result.decision = "APPROVE"
        elif result.overall_score >= 0.70:
            result.overall_grade = "Acceptable"
            result.decision = "REVIEW"
        elif result.overall_score >= 0.60:
            result.overall_grade = "Marginal"
            result.decision = "REVIEW"
        else:
            result.overall_grade = "Needs Improvement"
            result.decision = "REJECT"

        # Generate recommendations based on issues
        if result.format_issues:
            result.recommendations.append(
                "Fix format issues: " + ", ".join(result.format_issues)
            )

        if result.quality_issues:
            result.recommendations.append(
                "Address quality issues: " + ", ".join(result.quality_issues[:3])
            )

        if result.bloom_confidence and result.bloom_confidence < 0.7:
            result.recommendations.append(
                "Low Bloom classification confidence - review cognitive level clarity"
            )

        # Add strengths if high scores
        if result.format_score >= 0.95:
            result.strengths.append("Perfect format compliance")

        if result.quality_score >= 0.90:
            result.strengths.append("High quality content")

        return result

    def evaluate_batch(self, questions: List[Dict], stage: str = "standard") -> Dict:
        """
        Evaluate multiple questions

        Args:
            questions: List of question dicts
            stage: Evaluation stage

        Returns:
            Dict with individual results and aggregate statistics
        """
        results = []
        for question in questions:
            result = self.evaluate(question, stage=stage)
            results.append(result)

        # Calculate aggregate statistics
        scores = [r.overall_score for r in results]
        decisions = [r.decision for r in results]

        aggregate = {
            "total_questions": len(questions),
            "mean_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "approved": sum(1 for d in decisions if d == "APPROVE"),
            "review": sum(1 for d in decisions if d == "REVIEW"),
            "rejected": sum(1 for d in decisions if d == "REJECT"),
            "approval_rate": sum(1 for d in decisions if d == "APPROVE")
            / len(decisions)
            if decisions
            else 0,
            "results": [r.to_dict() for r in results],
        }

        return aggregate


# Example usage
if __name__ == "__main__":
    # Sample ÖSYM questions for reference
    osym_questions = [
        {
            "question_text": "Bir elementin atom numarası 17'dir. Bu elementin değerlik elektron sayısı kaçtır?",
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
            "subject": "Kimya",
        },
        {
            "question_text": "İki vektörün skaler çarpımı için hangi formül kullanılır?",
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
            "subject": "Matematik",
        },
    ]

    # Initialize evaluator
    evaluator = ComprehensiveQualityEvaluator(osym_reference_questions=osym_questions)

    # Test question
    test_question = {
        "question_text": "25 gramındaki bir maddenin mol sayısı 0.5 mol ise, bu maddenin mol kütlesi kaç g/mol'dür?",
        "choices": ["A) 25", "B) 50", "C) 12.5", "D) 100", "E) 75"],
        "correct_answer": "B",
        "difficulty": "Orta",
        "bloom_level": "Uygulama",
        "subject": "Kimya",
    }

    # Evaluate at different stages
    print("=" * 60)
    print("COMPREHENSIVE QUALITY EVALUATION")
    print("=" * 60)

    for stage in ["quick", "standard", "thorough"]:
        print(f"\n📊 {stage.upper()} Evaluation:")
        result = evaluator.evaluate(test_question, stage=stage)
        print(f"  Overall Score: {result.overall_score:.3f} ({result.overall_grade})")
        print(f"  Decision: {result.decision}")
        print(f"  Evaluation Time: {result.evaluation_time_ms:.0f}ms")

        if result.strengths:
            print(f"  ✓ Strengths: {', '.join(result.strengths[:2])}")
        if result.weaknesses:
            print(f"  ✗ Weaknesses: {', '.join(result.weaknesses[:2])}")
        if result.bloom_level:
            print(
                f"  Bloom: Level {result.bloom_level} (confidence={result.bloom_confidence:.2f})"
            )

    print("\n" + "=" * 60)
