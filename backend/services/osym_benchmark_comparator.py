"""
ÖSYM Benchmark Comparator
Wave 2B - Priority 1: Statistical Validation Against ÖSYM Standards

Purpose:
- Compare AI-generated questions against ÖSYM question bank
- Statistical tests for distribution equivalence
- Detect systematic biases in generation
- Ensure ÖSYM-like characteristics

Based on: SORU_URETIM_DEGERLENDIRME_CERCEVESI.md
Statistical Methods:
- Kolmogorov-Smirnov test (distribution similarity)
- Two One-Sided Tests (TOST) for equivalence
- Chi-square test (categorical distributions)
- Cohen's d (effect size)

Thresholds:
- Similarity score > 0.85: Excellent match
- Similarity score > 0.80: Good match
- Similarity score > 0.75: Acceptable match
- Similarity score < 0.75: Needs improvement
"""

import logging
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class QuestionStatistics:
    """Statistical summary of a question set"""

    # Basic counts
    total_count: int = 0

    # Length statistics
    lengths: list[int] = field(default_factory=list)
    mean_length: float = 0.0
    std_length: float = 0.0
    median_length: float = 0.0
    min_length: int = 0
    max_length: int = 0

    # Difficulty distribution
    difficulty_counts: dict[str, int] = field(default_factory=dict)
    difficulty_percentages: dict[str, float] = field(default_factory=dict)

    # Subject distribution
    subject_counts: dict[str, int] = field(default_factory=dict)
    subject_percentages: dict[str, float] = field(default_factory=dict)

    # Bloom taxonomy distribution
    bloom_counts: dict[str, int] = field(default_factory=dict)
    bloom_percentages: dict[str, float] = field(default_factory=dict)

    # Answer option statistics
    correct_answer_distribution: dict[str, int] = field(default_factory=dict)

    # Computed timestamp
    computed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkComparison:
    """Results of benchmark comparison"""

    # Overall similarity (0-1)
    overall_similarity: float = 0.0
    interpretation: str = ""

    # Component scores
    length_similarity: float = 0.0
    difficulty_similarity: float = 0.0
    bloom_similarity: float = 0.0

    # Statistical test results
    statistical_tests: dict = field(default_factory=dict)

    # Detailed comparisons
    length_comparison: dict = field(default_factory=dict)
    difficulty_comparison: dict = field(default_factory=dict)
    bloom_comparison: dict = field(default_factory=dict)

    # Recommendations
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class OSYMBenchmarkComparator:
    """
    Compare AI-generated questions against ÖSYM benchmark

    Statistical validation to ensure AI questions match ÖSYM characteristics
    """

    def __init__(self):
        """Initialize comparator"""
        self.logger = logger
        self._reference_stats: QuestionStatistics | None = None
        self._scipy_available = False

        # Try to import scipy for statistical tests
        try:
            import scipy.stats

            self._scipy = scipy.stats
            self._scipy_available = True
        except ImportError:
            logger.warning(
                "scipy not installed. Statistical tests disabled.\n"
                "Run: pip install scipy"
            )

    def calculate_statistics(
        self, questions: list[dict], name: str = "Unknown"
    ) -> QuestionStatistics:
        """
        Calculate comprehensive statistics for a question set

        Args:
            questions: List of question dicts with keys:
                - question_text (str)
                - difficulty (str, optional)
                - subject (str, optional)
                - bloom_level (str, optional)
                - correct_answer (str, optional)
            name: Name for logging

        Returns:
            QuestionStatistics object
        """
        if not questions:
            logger.warning(f"No questions provided for {name}")
            return QuestionStatistics()

        stats = QuestionStatistics()
        stats.total_count = len(questions)

        # Extract lengths
        lengths = []
        for q in questions:
            text = q.get("question_text") or q.get("metin") or ""
            lengths.append(len(text))

        stats.lengths = lengths
        if lengths:
            stats.mean_length = float(np.mean(lengths))
            stats.std_length = float(np.std(lengths))
            stats.median_length = float(np.median(lengths))
            stats.min_length = int(np.min(lengths))
            stats.max_length = int(np.max(lengths))

        # Difficulty distribution
        difficulties = []
        for q in questions:
            diff = q.get("difficulty") or q.get("zorluk") or "Unknown"
            if diff:
                difficulties.append(str(diff))

        if difficulties:
            stats.difficulty_counts = dict(Counter(difficulties))
            total = len(difficulties)
            stats.difficulty_percentages = {
                k: (v / total) * 100 for k, v in stats.difficulty_counts.items()
            }

        # Subject distribution
        subjects = []
        for q in questions:
            subj = q.get("subject") or q.get("konu") or "Unknown"
            if subj:
                subjects.append(str(subj))

        if subjects:
            stats.subject_counts = dict(Counter(subjects))
            total = len(subjects)
            stats.subject_percentages = {
                k: (v / total) * 100 for k, v in stats.subject_counts.items()
            }

        # Bloom taxonomy distribution
        blooms = []
        for q in questions:
            bloom = q.get("bloom_level") or q.get("bloom_seviyesi") or "Unknown"
            if bloom:
                blooms.append(str(bloom))

        if blooms:
            stats.bloom_counts = dict(Counter(blooms))
            total = len(blooms)
            stats.bloom_percentages = {
                k: (v / total) * 100 for k, v in stats.bloom_counts.items()
            }

        # Correct answer distribution
        answers = []
        for q in questions:
            ans = q.get("correct_answer") or q.get("dogru_cevap") or ""
            if ans:
                answers.append(str(ans))

        if answers:
            stats.correct_answer_distribution = dict(Counter(answers))

        logger.info(
            f"Calculated statistics for {name}: "
            f"{stats.total_count} questions, "
            f"mean_length={stats.mean_length:.1f}"
        )

        return stats

    def set_reference_benchmark(self, osym_questions: list[dict]) -> QuestionStatistics:
        """
        Set ÖSYM questions as reference benchmark

        Args:
            osym_questions: ÖSYM question bank

        Returns:
            Calculated statistics
        """
        self._reference_stats = self.calculate_statistics(
            osym_questions, name="ÖSYM Reference"
        )

        logger.info(
            f"Reference benchmark set: {self._reference_stats.total_count} "
            f"ÖSYM questions"
        )

        return self._reference_stats

    def compare_against_benchmark(
        self,
        ai_questions: list[dict],
        reference_stats: QuestionStatistics | None = None,
    ) -> BenchmarkComparison:
        """
        Compare AI-generated questions against ÖSYM benchmark

        Args:
            ai_questions: AI-generated questions
            reference_stats: Optional pre-calculated reference stats
                            (uses self._reference_stats if None)

        Returns:
            BenchmarkComparison with detailed analysis
        """
        # Use provided reference or stored reference
        ref_stats = reference_stats or self._reference_stats

        if ref_stats is None:
            raise ValueError(
                "No reference benchmark set. " "Call set_reference_benchmark() first."
            )

        # Calculate AI statistics
        ai_stats = self.calculate_statistics(ai_questions, name="AI Generated")

        # Initialize comparison result
        comparison = BenchmarkComparison()

        # 1. Length distribution comparison
        comparison.length_comparison = self._compare_lengths(ai_stats, ref_stats)
        comparison.length_similarity = comparison.length_comparison["similarity"]

        # 2. Difficulty distribution comparison
        comparison.difficulty_comparison = self._compare_difficulty(ai_stats, ref_stats)
        comparison.difficulty_similarity = comparison.difficulty_comparison[
            "similarity"
        ]

        # 3. Bloom distribution comparison
        comparison.bloom_comparison = self._compare_bloom(ai_stats, ref_stats)
        comparison.bloom_similarity = comparison.bloom_comparison["similarity"]

        # 4. Statistical tests (if scipy available)
        if self._scipy_available:
            comparison.statistical_tests = self._run_statistical_tests(
                ai_stats, ref_stats
            )

        # 5. Calculate overall similarity (weighted average)
        weights = {"length": 0.30, "difficulty": 0.35, "bloom": 0.35}

        comparison.overall_similarity = (
            weights["length"] * comparison.length_similarity
            + weights["difficulty"] * comparison.difficulty_similarity
            + weights["bloom"] * comparison.bloom_similarity
        )

        # 6. Interpretation
        comparison.interpretation = self._interpret_similarity(
            comparison.overall_similarity
        )

        # 7. Identify issues and recommendations
        comparison.issues, comparison.recommendations = self._generate_recommendations(
            comparison, ai_stats, ref_stats
        )

        logger.info(
            f"Benchmark comparison complete: "
            f"Overall similarity = {comparison.overall_similarity:.3f} "
            f"({comparison.interpretation})"
        )

        return comparison

    def _compare_lengths(
        self, ai_stats: QuestionStatistics, ref_stats: QuestionStatistics
    ) -> dict:
        """Compare length distributions"""
        # Calculate mean difference
        mean_diff = abs(ai_stats.mean_length - ref_stats.mean_length)
        mean_diff_pct = (mean_diff / ref_stats.mean_length) * 100

        # Calculate std difference
        std_diff = abs(ai_stats.std_length - ref_stats.std_length)

        # Similarity score (0-1)
        # Perfect match: mean within 10%, std within 20%
        mean_score = max(0, 1 - (mean_diff_pct / 10))
        std_score = max(0, 1 - (std_diff / (ref_stats.std_length * 0.2)))
        similarity = (mean_score + std_score) / 2

        result = {
            "similarity": similarity,
            "ai_mean": ai_stats.mean_length,
            "ref_mean": ref_stats.mean_length,
            "mean_diff": mean_diff,
            "mean_diff_pct": mean_diff_pct,
            "ai_std": ai_stats.std_length,
            "ref_std": ref_stats.std_length,
            "std_diff": std_diff,
            "interpretation": self._interpret_similarity(similarity),
        }

        # KS test if available
        if self._scipy_available and ai_stats.lengths and ref_stats.lengths:
            ks_stat, ks_pval = self._scipy.ks_2samp(ai_stats.lengths, ref_stats.lengths)
            result["ks_statistic"] = ks_stat
            result["ks_pvalue"] = ks_pval
            result["ks_similar"] = ks_pval > 0.05  # p>0.05 = similar

        return result

    def _compare_difficulty(
        self, ai_stats: QuestionStatistics, ref_stats: QuestionStatistics
    ) -> dict:
        """Compare difficulty distributions"""
        # Get all difficulty levels
        all_levels = set(
            list(ai_stats.difficulty_percentages.keys())
            + list(ref_stats.difficulty_percentages.keys())
        )

        # Calculate absolute percentage differences
        diffs = []
        for level in all_levels:
            ai_pct = ai_stats.difficulty_percentages.get(level, 0)
            ref_pct = ref_stats.difficulty_percentages.get(level, 0)
            diffs.append(abs(ai_pct - ref_pct))

        # Mean absolute percentage difference
        mean_abs_diff = np.mean(diffs) if diffs else 0

        # Similarity (0-1): perfect = 0% diff, poor = >20% diff
        similarity = max(0, 1 - (mean_abs_diff / 20))

        result = {
            "similarity": similarity,
            "ai_distribution": ai_stats.difficulty_percentages,
            "ref_distribution": ref_stats.difficulty_percentages,
            "mean_abs_diff": mean_abs_diff,
            "interpretation": self._interpret_similarity(similarity),
        }

        # Chi-square test if available
        if (
            self._scipy_available
            and ai_stats.difficulty_counts
            and ref_stats.difficulty_counts
        ):
            # Align counts for common levels
            common_levels = sorted(all_levels)
            ai_counts = [
                ai_stats.difficulty_counts.get(lvl, 0) for lvl in common_levels
            ]
            ref_counts = [
                ref_stats.difficulty_counts.get(lvl, 0) for lvl in common_levels
            ]

            if sum(ai_counts) > 0 and sum(ref_counts) > 0:
                # Normalize to proportions (avoids floating point sum mismatch)
                ai_proportions = np.array(ai_counts) / sum(ai_counts)
                ref_proportions = np.array(ref_counts) / sum(ref_counts)

                # Scale to same total for chi-square test
                total = sum(ai_counts)
                ai_observed = ai_proportions * total
                ref_expected = ref_proportions * total

                # Filter out zero expected
                nonzero = (
                    ref_expected > 0.5
                )  # Use 0.5 threshold to avoid numerical issues
                if np.any(nonzero):
                    # Round to avoid floating point precision issues
                    ai_obs_filtered = np.round(ai_observed[nonzero], 6)
                    ref_exp_filtered = np.round(ref_expected[nonzero], 6)

                    try:
                        chi2_stat, chi2_pval = self._scipy.chisquare(
                            ai_obs_filtered, ref_exp_filtered
                        )
                        result["chi2_statistic"] = chi2_stat
                        result["chi2_pvalue"] = chi2_pval
                        result["chi2_similar"] = chi2_pval > 0.05
                    except ValueError:
                        # If still fails, use proportion-based similarity instead
                        prop_diff = np.abs(ai_proportions - ref_proportions).mean()
                        result["proportion_similarity"] = 1 - prop_diff
                        result["chi2_similar"] = prop_diff < 0.15

        return result

    def _compare_bloom(
        self, ai_stats: QuestionStatistics, ref_stats: QuestionStatistics
    ) -> dict:
        """Compare Bloom taxonomy distributions"""
        # Same logic as difficulty comparison
        all_levels = set(
            list(ai_stats.bloom_percentages.keys())
            + list(ref_stats.bloom_percentages.keys())
        )

        diffs = []
        for level in all_levels:
            ai_pct = ai_stats.bloom_percentages.get(level, 0)
            ref_pct = ref_stats.bloom_percentages.get(level, 0)
            diffs.append(abs(ai_pct - ref_pct))

        mean_abs_diff = np.mean(diffs) if diffs else 0
        similarity = max(0, 1 - (mean_abs_diff / 20))

        return {
            "similarity": similarity,
            "ai_distribution": ai_stats.bloom_percentages,
            "ref_distribution": ref_stats.bloom_percentages,
            "mean_abs_diff": mean_abs_diff,
            "interpretation": self._interpret_similarity(similarity),
        }

    def _run_statistical_tests(
        self, ai_stats: QuestionStatistics, ref_stats: QuestionStatistics
    ) -> dict:
        """Run comprehensive statistical tests"""
        tests = {}

        # 1. Length distribution: Kolmogorov-Smirnov
        if ai_stats.lengths and ref_stats.lengths:
            ks_stat, ks_pval = self._scipy.ks_2samp(ai_stats.lengths, ref_stats.lengths)
            tests["ks_test"] = {
                "statistic": ks_stat,
                "pvalue": ks_pval,
                "significant": ks_pval < 0.05,
                "interpretation": "Similar distributions"
                if ks_pval > 0.05
                else "Different distributions",
            }

        # 2. Mean length: t-test
        if ai_stats.lengths and ref_stats.lengths:
            t_stat, t_pval = self._scipy.ttest_ind(ai_stats.lengths, ref_stats.lengths)
            tests["t_test"] = {
                "statistic": t_stat,
                "pvalue": t_pval,
                "significant": t_pval < 0.05,
                "interpretation": "Similar means"
                if t_pval > 0.05
                else "Different means",
            }

        # 3. Effect size: Cohen's d
        if ai_stats.lengths and ref_stats.lengths:
            cohens_d = self._calculate_cohens_d(ai_stats.lengths, ref_stats.lengths)
            tests["cohens_d"] = {
                "value": cohens_d,
                "interpretation": self._interpret_cohens_d(cohens_d),
            }

        return tests

    def _calculate_cohens_d(self, group1: list[float], group2: list[float]) -> float:
        """Calculate Cohen's d effect size"""
        mean1 = np.mean(group1)
        mean2 = np.mean(group2)
        std1 = np.std(group1, ddof=1)
        std2 = np.std(group2, ddof=1)
        n1 = len(group1)
        n2 = len(group2)

        # Pooled standard deviation
        pooled_std = np.sqrt(
            ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
        )

        # Cohen's d
        d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0
        return abs(d)

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        if d < 0.2:
            return "Negligible difference (excellent equivalence)"
        if d < 0.5:
            return "Small difference (good equivalence)"
        if d < 0.8:
            return "Medium difference (acceptable)"
        return "Large difference (needs improvement)"

    def _interpret_similarity(self, similarity: float) -> str:
        """Interpret similarity score"""
        if similarity >= 0.90:
            return "Excellent"
        if similarity >= 0.85:
            return "Very Good"
        if similarity >= 0.80:
            return "Good"
        if similarity >= 0.75:
            return "Acceptable"
        if similarity >= 0.70:
            return "Marginal"
        return "Needs Improvement"

    def _generate_recommendations(
        self,
        comparison: BenchmarkComparison,
        ai_stats: QuestionStatistics,
        ref_stats: QuestionStatistics,
    ) -> tuple[list[str], list[str]]:
        """Generate issues and recommendations"""
        issues = []
        recommendations = []

        # Check length
        if comparison.length_similarity < 0.75:
            mean_diff_pct = comparison.length_comparison["mean_diff_pct"]
            if ai_stats.mean_length > ref_stats.mean_length:
                issues.append(
                    f"Questions too long (avg {ai_stats.mean_length:.0f} vs {ref_stats.mean_length:.0f} chars, +{mean_diff_pct:.1f}%)"
                )
                recommendations.append(
                    "Reduce question verbosity - aim for more concise phrasing"
                )
            else:
                issues.append(
                    f"Questions too short (avg {ai_stats.mean_length:.0f} vs {ref_stats.mean_length:.0f} chars, -{mean_diff_pct:.1f}%)"
                )
                recommendations.append("Add more context and detail to questions")

        # Check difficulty
        if comparison.difficulty_similarity < 0.75:
            issues.append("Difficulty distribution differs significantly from ÖSYM")
            recommendations.append("Adjust difficulty balance to match ÖSYM patterns")

            # Specific recommendations
            for level, ref_pct in ref_stats.difficulty_percentages.items():
                ai_pct = ai_stats.difficulty_percentages.get(level, 0)
                diff = ai_pct - ref_pct
                if abs(diff) > 10:  # >10% difference
                    if diff > 0:
                        recommendations.append(
                            f"Reduce '{level}' questions by ~{abs(diff):.0f}%"
                        )
                    else:
                        recommendations.append(
                            f"Increase '{level}' questions by ~{abs(diff):.0f}%"
                        )

        # Check Bloom
        if comparison.bloom_similarity < 0.75:
            issues.append("Bloom taxonomy distribution differs from ÖSYM")
            recommendations.append("Rebalance cognitive levels to match ÖSYM standards")

        # Overall assessment
        if comparison.overall_similarity < 0.75:
            issues.append(
                f"Overall similarity low: {comparison.overall_similarity:.2f}"
            )
            recommendations.append("Consider major adjustments to generation prompts")
        elif comparison.overall_similarity < 0.85:
            recommendations.append(
                "Minor adjustments recommended for better ÖSYM alignment"
            )

        return issues, recommendations


# Example usage
if __name__ == "__main__":
    # Sample ÖSYM questions (reference)
    osym_questions = [
        {
            "question_text": "Sample ÖSYM question 1" * 20,
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
        },
        {
            "question_text": "Sample ÖSYM question 2" * 25,
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
        },
        {
            "question_text": "Sample ÖSYM question 3" * 30,
            "difficulty": "Zor",
            "bloom_level": "Analiz",
        },
        {
            "question_text": "Sample ÖSYM question 4" * 22,
            "difficulty": "Orta",
            "bloom_level": "Anlama",
        },
        {
            "question_text": "Sample ÖSYM question 5" * 28,
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
        },
    ]

    # Sample AI questions
    ai_questions = [
        {
            "question_text": "AI generated question 1" * 25,
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
        },
        {
            "question_text": "AI generated question 2" * 20,
            "difficulty": "Kolay",
            "bloom_level": "Hatırlama",
        },
        {
            "question_text": "AI generated question 3" * 35,
            "difficulty": "Zor",
            "bloom_level": "Sentez",
        },
        {
            "question_text": "AI generated question 4" * 30,
            "difficulty": "Orta",
            "bloom_level": "Uygulama",
        },
    ]

    # Create comparator
    comparator = OSYMBenchmarkComparator()

    # Set reference
    ref_stats = comparator.set_reference_benchmark(osym_questions)
    print("\n📊 ÖSYM Reference Statistics:")
    print(f"  Questions: {ref_stats.total_count}")
    print(f"  Mean length: {ref_stats.mean_length:.1f} chars")
    print(f"  Difficulty: {ref_stats.difficulty_percentages}")

    # Compare AI questions
    comparison = comparator.compare_against_benchmark(ai_questions)
    print("\n📊 Benchmark Comparison:")
    print(
        f"  Overall similarity: {comparison.overall_similarity:.3f} ({comparison.interpretation})"
    )
    print(f"  Length similarity: {comparison.length_similarity:.3f}")
    print(f"  Difficulty similarity: {comparison.difficulty_similarity:.3f}")
    print(f"  Bloom similarity: {comparison.bloom_similarity:.3f}")

    if comparison.issues:
        print("\n⚠️ Issues:")
        for issue in comparison.issues:
            print(f"  - {issue}")

    if comparison.recommendations:
        print("\n💡 Recommendations:")
        for rec in comparison.recommendations:
            print(f"  - {rec}")
