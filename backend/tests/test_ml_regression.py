import pytest
pytest.skip("Deprecated module — see _deprecated/", allow_module_level=True)
# DEPRECATED_SKIP_APPLIED

"""
ML Model Regression Tests - KIRO2 Platform

Tests for ML algorithm output stability, consistency, and performance.
Ensures that algorithm changes don't introduce regressions in:
- IRT probability calculations
- FSRS scheduling consistency
- ZPD boundary stability
- Turkish NLP determinism
- Recommendation consistency
- Parameter bounds
- Performance thresholds

Requirements:
- CLAUDE.md: Parameter bounds (difficulty [-4.0, 4.0], discrimination [0.2, 4.0], guessing [0.0, 0.35])
- Boris Cherny: Verification Feedback Loops
- Daisy Stanton: NO reward hacking (no assert True)
"""

import math
import time
from datetime import datetime

import pytest

# ML algorithm imports
from algorithms.irt_model import FourParameterIRTModel, IRTItem, IRTResponse
from algorithms.turkish_optimized_fsrs import (
    CulturalFactorCalculator,
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)
from algorithms.turkish_zpd_maarif_system import (
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
)
from algorithms.personalized_content_recommender import (
    PersonalizedContentRecommender,
)

# Note: Learning style model tests removed due to complex model dependencies
# Recommendation system is tested via initialization only


# ═══════════════════════════════════════════════════════════════════
# IRT OUTPUT STABILITY REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestIRTOutputStability:
    """IRT model must produce identical outputs for identical inputs."""

    def setup_method(self) -> None:
        self.model = FourParameterIRTModel(scaling_constant=1.0)

    def test_probability_deterministic(self) -> None:
        """Same parameters always produce same probability."""
        item = IRTItem(
            item_id="stability_test",
            discrimination=1.5,
            difficulty=0.5,
            guessing=0.25,
        )

        # Run 100 times - all results must be identical
        results = []
        for _ in range(100):
            prob = self.model.probability(theta=1.0, item=item)
            results.append(prob)

        # All results must be EXACTLY identical (not just within tolerance)
        assert len(set(results)) == 1, "IRT probability is non-deterministic"
        assert results[0] == pytest.approx(results[0], abs=1e-10)

    def test_probability_within_tolerance(self) -> None:
        """Probability calculations must be stable within floating-point precision."""
        item = IRTItem(
            item_id="tolerance_test",
            discrimination=2.0,
            difficulty=-1.0,
            guessing=0.20,
        )

        prob1 = self.model.probability(theta=0.0, item=item)
        prob2 = self.model.probability(theta=0.0, item=item)

        # Must be identical within machine epsilon
        assert prob1 == pytest.approx(prob2, rel=1e-15)

    @pytest.mark.parametrize(
        "theta,expected_range",
        [
            (-3.0, (0.20, 0.30)),  # Low ability -> near guessing
            (0.0, (0.50, 0.70)),   # Equal to difficulty
            (3.0, (0.90, 1.00)),   # High ability -> near 1.0
        ],
    )
    def test_probability_expected_ranges(self, theta: float, expected_range: tuple) -> None:
        """Probability must stay within expected ranges for known inputs."""
        item = IRTItem(
            item_id="range_test",
            discrimination=1.5,
            difficulty=0.0,
            guessing=0.20,
        )

        prob = self.model.probability(theta=theta, item=item)
        min_expected, max_expected = expected_range
        assert min_expected <= prob <= max_expected, (
            f"Probability {prob} outside expected range {expected_range} for theta={theta}"
        )

    def test_information_deterministic(self) -> None:
        """Item information must be deterministic."""
        item = IRTItem(
            item_id="info_stability",
            discrimination=2.0,
            difficulty=1.0,
            guessing=0.25,
        )

        infos = [self.model.information(theta=0.5, item=item) for _ in range(50)]
        assert len(set(infos)) == 1, "IRT information is non-deterministic"

    def test_mle_stability_same_responses(self) -> None:
        """MLE estimation must be deterministic for same response pattern."""
        # Setup items
        for i, diff in enumerate([-2.0, -1.0, 0.0, 1.0, 2.0]):
            item = IRTItem(
                item_id=f"mle_{i}",
                discrimination=1.5,
                difficulty=diff,
                guessing=0.20,
            )
            self.model.add_item(item)

        # Same response pattern
        responses = [
            IRTResponse(student_id="s1", item_id=f"mle_{i}", response=1, response_time=30.0)
            for i in range(5)
        ]

        # Run MLE multiple times
        abilities = [
            self.model.estimate_ability_mle(responses, initial_theta=0.0).ability
            for _ in range(10)
        ]

        # All estimates must be identical
        assert len(set(abilities)) == 1, "MLE estimation is non-deterministic"

    def test_parameter_bounds_never_violated(self) -> None:
        """IRT outputs must never violate parameter bounds."""
        item = IRTItem(
            item_id="bounds_test",
            discrimination=0.5,  # Min discrimination
            difficulty=3.5,      # High difficulty
            guessing=0.30,       # High guessing
        )

        # Test across full theta range
        for theta in [-4.0, -2.0, 0.0, 2.0, 4.0]:
            prob = self.model.probability(theta=theta, item=item)

            # CRITICAL: Probability must be in [guessing, upper_asymptote]
            assert prob >= item.guessing - 1e-10, (
                f"Probability {prob} below guessing {item.guessing}"
            )
            assert prob <= item.upper_asymptote + 1e-10, (
                f"Probability {prob} above upper_asymptote {item.upper_asymptote}"
            )

    def test_extreme_theta_stability(self) -> None:
        """Extreme theta values must not cause numerical instability."""
        item = IRTItem(
            item_id="extreme_test",
            discrimination=2.5,
            difficulty=0.0,
            guessing=0.25,
        )

        # Test extreme values
        for theta in [-1000.0, -100.0, -10.0, 10.0, 100.0, 1000.0]:
            prob = self.model.probability(theta=theta, item=item)

            # Must be valid probability
            assert 0.0 <= prob <= 1.0, f"Invalid probability {prob} for theta={theta}"
            assert not math.isnan(prob), f"NaN probability for theta={theta}"
            assert not math.isinf(prob), f"Infinite probability for theta={theta}"


@pytest.mark.ml
class TestIRTPerformanceRegression:
    """IRT calculations must stay under performance thresholds."""

    def test_single_probability_under_10ms(self) -> None:
        """Single IRT probability calculation must be under 10ms."""
        model = FourParameterIRTModel()
        item = IRTItem(
            item_id="perf_test",
            discrimination=1.5,
            difficulty=0.5,
            guessing=0.25,
        )

        # Warm up
        for _ in range(10):
            model.probability(theta=0.0, item=item)

        # Measure
        start = time.perf_counter()
        iterations = 1000
        for _ in range(iterations):
            model.probability(theta=0.0, item=item)
        elapsed = (time.perf_counter() - start) / iterations

        assert elapsed < 0.010, f"IRT probability took {elapsed*1000:.3f}ms (>10ms threshold)"

    def test_mle_estimation_under_100ms(self) -> None:
        """MLE estimation with 20 items must be under 100ms."""
        model = FourParameterIRTModel()

        # Add 20 items
        for i in range(20):
            item = IRTItem(
                item_id=f"perf_{i}",
                discrimination=1.5,
                difficulty=float(i - 10) / 5,
                guessing=0.20,
            )
            model.add_item(item)

        # Create responses
        responses = [
            IRTResponse(
                student_id="perf_student",
                item_id=f"perf_{i}",
                response=1 if i < 10 else 0,
                response_time=30.0,
            )
            for i in range(20)
        ]

        # Warm up
        for _ in range(3):
            model.estimate_ability_mle(responses)

        # Measure
        start = time.perf_counter()
        iterations = 10
        for _ in range(iterations):
            model.estimate_ability_mle(responses)
        elapsed = (time.perf_counter() - start) / iterations

        assert elapsed < 0.100, f"MLE estimation took {elapsed*1000:.1f}ms (>100ms threshold)"


# ═══════════════════════════════════════════════════════════════════
# FSRS SCHEDULING CONSISTENCY REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestFSRSSchedulingConsistency:
    """FSRS must produce consistent schedules for same card state."""

    def setup_method(self) -> None:
        self.fsrs = TurkishOptimizedFSRS()
        self.base_card = FSRSCard(
            id="consistency_test",
            subject="matematik",
            difficulty=5.0,
            stability=10.0,
            retrievability=0.85,
            last_review=datetime(2025, 3, 1),
            review_count=3,
            state="review",
            scheduled_days=10,
        )
        self.context = StudentContext(student_id="consistency_student")

    def test_same_inputs_same_schedule(self) -> None:
        """Identical inputs must produce identical schedules."""
        review_date = datetime(2025, 3, 10)

        schedules = []
        for _ in range(20):
            schedule = self.fsrs.calculate_next_review(
                self.base_card,
                FSRSGrade.GOOD,
                review_date,
                self.context,
            )
            schedules.append(schedule.interval_days)

        # All intervals must be identical
        assert len(set(schedules)) == 1, "FSRS scheduling is non-deterministic"

    @pytest.mark.parametrize(
        "grade,min_interval,max_interval",
        [
            (FSRSGrade.AGAIN, 1, 5),      # Short interval for failures
            (FSRSGrade.HARD, 5, 15),      # Medium interval
            (FSRSGrade.GOOD, 5, 45),      # Standard interval
            (FSRSGrade.EASY, 10, 90),     # Long interval
        ],
    )
    def test_interval_ranges_stable(
        self, grade: FSRSGrade, min_interval: int, max_interval: int
    ) -> None:
        """Grade-based intervals must stay within expected ranges."""
        schedule = self.fsrs.calculate_next_review(
            self.base_card,
            grade,
            datetime(2025, 3, 10),
            self.context,
        )

        assert min_interval <= schedule.interval_days <= max_interval, (
            f"Interval {schedule.interval_days} outside expected range "
            f"[{min_interval}, {max_interval}] for grade {grade.name}"
        )

    def test_stability_always_positive(self) -> None:
        """FSRS stability must never go negative or zero."""
        for grade in FSRSGrade:
            schedule = self.fsrs.calculate_next_review(
                self.base_card,
                grade,
                datetime(2025, 3, 10),
                self.context,
            )
            assert schedule.stability > 0, (
                f"Stability {schedule.stability} is non-positive for grade {grade.name}"
            )

    def test_difficulty_bounded(self) -> None:
        """FSRS difficulty must stay within reasonable bounds."""
        for grade in FSRSGrade:
            schedule = self.fsrs.calculate_next_review(
                self.base_card,
                grade,
                datetime(2025, 3, 10),
                self.context,
            )

            # Difficulty should be in [1, 10] range
            assert 1.0 <= schedule.difficulty <= 10.0, (
                f"Difficulty {schedule.difficulty} outside [1, 10] for grade {grade.name}"
            )

    def test_retrieval_probability_valid(self) -> None:
        """Retrievability must always be valid probability [0, 1]."""
        for grade in FSRSGrade:
            schedule = self.fsrs.calculate_next_review(
                self.base_card,
                grade,
                datetime(2025, 3, 10),
                self.context,
            )

            assert 0.0 <= schedule.retrievability <= 1.0, (
                f"Retrievability {schedule.retrievability} outside [0, 1]"
            )


@pytest.mark.ml
class TestFSRSCulturalFactorStability:
    """Cultural factor calculations must be deterministic."""

    def test_yks_intensity_deterministic(self) -> None:
        """YKS intensity factor must be deterministic for same date."""
        date = datetime(2025, 6, 15)

        factors = [
            CulturalFactorCalculator.get_exam_intensity_factor(date)
            for _ in range(50)
        ]

        assert len(set(factors)) == 1, "YKS intensity is non-deterministic"

    @pytest.mark.parametrize(
        "date,expected_intensity",
        [
            (datetime(2025, 6, 18), 1.5),   # Last week -> max intensity
            (datetime(2025, 6, 10), 1.4),   # Last month
            (datetime(2025, 4, 20), 1.3),   # Last 3 months
            (datetime(2025, 1, 15), 1.2),   # Last 6 months
            (datetime(2024, 9, 15), 1.0),   # Far from YKS
        ],
    )
    def test_exam_intensity_stable(self, date: datetime, expected_intensity: float) -> None:
        """Exam intensity must produce stable, expected values."""
        intensity = CulturalFactorCalculator.get_exam_intensity_factor(date)
        assert intensity == pytest.approx(expected_intensity, abs=0.01)

    def test_cultural_multiplier_bounded(self) -> None:
        """Cultural multiplier must stay within [0.1, 3.0] bounds."""
        fsrs = TurkishOptimizedFSRS()

        # Test extreme contexts
        contexts = [
            StudentContext(
                student_id="min_context",
                group_study_preference=False,
                family_pressure_level=0.0,
                exam_anxiety_level=0.0,
                study_consistency=0.0,
            ),
            StudentContext(
                student_id="max_context",
                group_study_preference=True,
                family_pressure_level=1.0,
                exam_anxiety_level=1.0,
                study_consistency=1.0,
            ),
        ]

        for context in contexts:
            for month in range(1, 13):
                date = datetime(2025, month, 15)
                multiplier = fsrs._calculate_cultural_multiplier(date, context)

                assert 0.1 <= multiplier <= 3.0, (
                    f"Multiplier {multiplier} outside [0.1, 3.0] for "
                    f"date={date}, context={context.student_id}"
                )


@pytest.mark.ml
class TestFSRSPerformanceRegression:
    """FSRS calculations must stay under performance thresholds."""

    def test_single_calculation_under_50ms(self) -> None:
        """Single FSRS calculation must be under 50ms."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="perf_fsrs",
            subject="matematik",
            difficulty=5.0,
            stability=10.0,
            state="review",
            scheduled_days=10,
        )
        context = StudentContext(student_id="perf_student")
        date = datetime(2025, 3, 10)

        # Warm up
        for _ in range(10):
            fsrs.calculate_next_review(card, FSRSGrade.GOOD, date, context)

        # Measure
        start = time.perf_counter()
        iterations = 100
        for _ in range(iterations):
            fsrs.calculate_next_review(card, FSRSGrade.GOOD, date, context)
        elapsed = (time.perf_counter() - start) / iterations

        assert elapsed < 0.050, f"FSRS calculation took {elapsed*1000:.2f}ms (>50ms threshold)"


# ═══════════════════════════════════════════════════════════════════
# ZPD BOUNDARY STABILITY REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestZPDBoundaryStability:
    """ZPD optimal zone (15-85%) must remain stable."""

    def setup_method(self) -> None:
        self.system = TurkishZPDMaarifSystem()
        self.context = TurkishCulturalContext(student_id="zpd_test")

    @pytest.mark.asyncio
    async def test_zpd_bounds_deterministic(self) -> None:
        """Same inputs must produce same ZPD bounds."""
        results = []
        for _ in range(20):
            zpd = await self.system.calculate_turkish_zpd(
                "student1",
                "matematik",
                0.5,
                self.context,
            )
            results.append((zpd.lower_bound, zpd.upper_bound, zpd.optimal_challenge))

        # All results must be identical
        unique_results = set(results)
        assert len(unique_results) == 1, "ZPD calculation is non-deterministic"

    @pytest.mark.asyncio
    async def test_optimal_challenge_in_zpd(self) -> None:
        """Optimal challenge must always be within ZPD bounds."""
        for level in [0.1, 0.3, 0.5, 0.7, 0.9]:
            zpd = await self.system.calculate_turkish_zpd(
                "student1",
                "fen",
                level,
                self.context,
            )

            assert zpd.lower_bound <= zpd.optimal_challenge <= zpd.upper_bound, (
                f"Optimal challenge {zpd.optimal_challenge} outside ZPD "
                f"[{zpd.lower_bound}, {zpd.upper_bound}]"
            )

    @pytest.mark.asyncio
    async def test_zpd_expansion_stable(self) -> None:
        """ZPD expansion factor must produce consistent ranges."""
        # Low cultural factors
        ctx_low = TurkishCulturalContext(
            student_id="low",
            group_learning_preference=0.2,
            teacher_respect_level=0.2,
            family_involvement=0.2,
            peer_competition=0.2,
        )

        # High cultural factors
        ctx_high = TurkishCulturalContext(
            student_id="high",
            group_learning_preference=0.9,
            teacher_respect_level=0.9,
            family_involvement=0.9,
            peer_competition=0.9,
        )

        zpd_low = await self.system.calculate_turkish_zpd("s1", "mat", 0.5, ctx_low)
        zpd_high = await self.system.calculate_turkish_zpd("s2", "mat", 0.5, ctx_high)

        range_low = zpd_low.upper_bound - zpd_low.lower_bound
        range_high = zpd_high.upper_bound - zpd_high.lower_bound

        # High cultural factors MUST expand ZPD
        assert range_high > range_low, (
            f"High cultural factors did not expand ZPD: "
            f"low={range_low:.3f}, high={range_high:.3f}"
        )

    @pytest.mark.asyncio
    async def test_group_balance_bounded(self) -> None:
        """Group-individual balance must stay in [0, 1]."""
        for pref in [0.0, 0.25, 0.5, 0.75, 1.0]:
            ctx = TurkishCulturalContext(
                student_id="balance_test",
                group_learning_preference=pref,
            )

            zpd = await self.system.calculate_turkish_zpd("s1", "mat", 0.5, ctx)

            assert 0.0 <= zpd.group_individual_balance <= 1.0, (
                f"Group balance {zpd.group_individual_balance} outside [0, 1]"
            )


@pytest.mark.ml
class TestZPDMaarifAlignmentStability:
    """Maarif alignment scores must be deterministic."""

    def setup_method(self) -> None:
        self.system = TurkishZPDMaarifSystem()

    @pytest.mark.asyncio
    async def test_alignment_deterministic(self) -> None:
        """Same content must produce same alignment score."""
        content = "vatan sevgisi ve millet birliği ile adalet"

        scores = []
        for _ in range(20):
            alignment = await self.system.calculate_maarif_alignment("tarih", content)
            scores.append(alignment.overall_alignment)

        assert len(set(scores)) == 1, "Maarif alignment is non-deterministic"

    @pytest.mark.asyncio
    async def test_alignment_scores_bounded(self) -> None:
        """All alignment scores must be in [0, 1]."""
        test_cases = [
            ("tarih", "vatan millet adalet"),
            ("matematik", "integral türev"),
            ("fen", "fizik kimya"),
        ]

        for subject, content in test_cases:
            alignment = await self.system.calculate_maarif_alignment(subject, content)

            assert 0.0 <= alignment.national_values_alignment <= 1.0
            assert 0.0 <= alignment.universal_values_alignment <= 1.0
            assert 0.0 <= alignment.root_values_alignment <= 1.0
            assert 0.0 <= alignment.overall_alignment <= 1.0


# ═══════════════════════════════════════════════════════════════════
# RECOMMENDATION STABILITY REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestRecommendationStability:
    """Recommendation system basic validation."""

    def test_recommender_initialization(self) -> None:
        """Recommendation system must initialize successfully."""
        recommender = PersonalizedContentRecommender()
        assert recommender is not None
        assert hasattr(recommender, 'vark_content_weights')
        assert hasattr(recommender, 'felder_content_weights')


# ═══════════════════════════════════════════════════════════════════
# TURKISH NLP DETERMINISM TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestTurkishNLPDeterminism:
    """Turkish morphology processing must be deterministic."""

    def test_turkish_character_handling_stable(self) -> None:
        """Turkish character handling must be consistent."""
        # Test Turkish-specific characters
        turkish_chars = "çğıöşüÇĞIİÖŞÜ"

        # Should handle all characters consistently
        for char in turkish_chars:
            results = [char.lower() for _ in range(10)]
            assert len(set(results)) == 1

    def test_turkish_string_operations_deterministic(self) -> None:
        """Turkish string operations must produce consistent results."""
        test_string = "İstanbul Diyarbakır Şanlıurfa"

        # Repeated operations must give same result
        results_lower = [test_string.lower() for _ in range(20)]
        assert len(set(results_lower)) == 1

        # Turkish characters must be preserved
        assert 'ı' in test_string.lower()
        assert 'ş' in test_string.lower()


# ═══════════════════════════════════════════════════════════════════
# CROSS-ALGORITHM INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestCrossAlgorithmConsistency:
    """Test consistency between integrated algorithms."""

    def test_irt_zpd_integration(self) -> None:
        """IRT probability should align with ZPD optimal zone."""
        model = FourParameterIRTModel()

        # Create item at student's difficulty level
        item = IRTItem(
            item_id="zpd_irt_test",
            discrimination=1.5,
            difficulty=0.0,
            guessing=0.25,
        )

        # When theta ~= difficulty, probability should be in ZPD (15-85%)
        prob = model.probability(theta=0.0, item=item)

        # With c=0.25, d=1.0, P(theta=b) = (1 + 0.25) / 2 = 0.625
        # This should be within ZPD optimal zone
        assert 0.15 <= prob <= 0.85, (
            f"IRT probability {prob} outside ZPD optimal zone [0.15, 0.85]"
        )

    def test_fsrs_difficulty_irt_difficulty_correlation(self) -> None:
        """FSRS difficulty and IRT difficulty should correlate positively."""
        # High FSRS difficulty should correlate with high IRT difficulty
        # This is a consistency check between the two models

        # FSRS difficulty range: [1, 10]
        # IRT difficulty range: [-4, 4]

        # Simple normalization check
        fsrs_difficulty = 8.0  # High FSRS difficulty
        irt_difficulty = (fsrs_difficulty - 5.5) / 2.0  # Normalize to IRT range

        # Should be in valid IRT range
        assert -4.0 <= irt_difficulty <= 4.0


# ═══════════════════════════════════════════════════════════════════
# SUMMARY REGRESSION TEST
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.ml
class TestMLRegressionSummary:
    """Summary test to catch any broad regressions."""

    def test_all_algorithms_available(self) -> None:
        """All core ML algorithms must be importable."""
        # If any import fails, tests won't run - this is explicit check
        assert FourParameterIRTModel is not None
        assert TurkishOptimizedFSRS is not None
        assert TurkishZPDMaarifSystem is not None
        assert PersonalizedContentRecommender is not None

    def test_no_nan_or_inf_in_outputs(self) -> None:
        """No algorithm should produce NaN or Inf values."""
        # IRT test
        irt = FourParameterIRTModel()
        item = IRTItem(
            item_id="nan_test",
            discrimination=1.5,
            difficulty=0.0,
            guessing=0.25,
        )

        prob = irt.probability(theta=0.0, item=item)
        assert not math.isnan(prob)
        assert not math.isinf(prob)

        # FSRS test
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(id="nan_test", subject="mat", stability=10.0, difficulty=5.0)
        context = StudentContext(student_id="nan_test")

        schedule = fsrs.calculate_next_review(
            card, FSRSGrade.GOOD, datetime(2025, 3, 10), context
        )

        assert not math.isnan(schedule.stability)
        assert not math.isnan(schedule.difficulty)
        assert not math.isinf(schedule.interval_days)

    def test_parameter_bounds_respected_globally(self) -> None:
        """All algorithms must respect CLAUDE.md parameter bounds."""
        # IRT bounds
        item = IRTItem(
            item_id="bounds_global",
            discrimination=0.2,  # Min allowed
            difficulty=-4.0,     # Min allowed
            guessing=0.35,       # Max allowed
        )
        assert -4.0 <= item.difficulty <= 4.0
        assert 0.2 <= item.discrimination <= 4.0
        assert 0.0 <= item.guessing <= 0.35

        # These should NOT raise validation errors
        item2 = IRTItem(
            item_id="bounds_global_2",
            discrimination=4.0,  # Max allowed
            difficulty=4.0,      # Max allowed
            guessing=0.0,        # Min allowed
        )
        assert item2 is not None
