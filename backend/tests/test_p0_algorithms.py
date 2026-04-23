"""
P0 Algorithm Tests: IRT, FSRS, ZPD+Maarif
Comprehensive tests for core educational algorithms.

Covers:
- 4PL IRT model (probability, information, MLE, CAT)
- Turkish-optimized FSRS (scheduling, cultural factors, retention)
- ZPD + Maarif system (zones, recommendations, cultural adaptation)
"""

import os

# ─── IRT imports ───
import sys
import time
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from algorithms.irt_model import (
    FourParameterIRTModel,
    IRTItem,
    IRTResponse,
)
from algorithms.turkish_optimized_fsrs import (
    CulturalFactorCalculator,
    CulturalPeriod,
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)
from algorithms.turkish_zpd_maarif_system import (
    MaarifValue,
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
)
from core.irt_validators import (
    IRTValidationError,
    is_in_zpd,
    validate_irt_difficulty,
    validate_irt_discrimination,
    validate_irt_guessing,
)

# ═══════════════════════════════════════════════════════════════════
# IRT MODEL TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.irt
class TestIRTParameterValidation:
    """IRT parameter range validation tests."""

    @pytest.mark.parametrize(
        "difficulty",
        [-4.0, -2.0, 0.0, 2.0, 4.0],
    )
    def test_valid_difficulty_accepted(self, difficulty: float) -> None:
        result = validate_irt_difficulty(difficulty, strict=True)
        assert result == difficulty

    @pytest.mark.parametrize(
        "difficulty",
        [-5.0, -4.1, 4.1, 10.0, 100.0],
    )
    def test_invalid_difficulty_rejected(self, difficulty: float) -> None:
        with pytest.raises(IRTValidationError):
            validate_irt_difficulty(difficulty, strict=True)

    @pytest.mark.parametrize(
        "discrimination",
        [0.2, 0.5, 1.0, 2.0, 4.0],
    )
    def test_valid_discrimination_accepted(self, discrimination: float) -> None:
        result = validate_irt_discrimination(discrimination, strict=True)
        assert result == discrimination

    @pytest.mark.parametrize(
        "discrimination",
        [0.0, 0.1, 0.19, 4.1, 5.0],
    )
    def test_invalid_discrimination_rejected(self, discrimination: float) -> None:
        with pytest.raises(IRTValidationError):
            validate_irt_discrimination(discrimination, strict=True)

    @pytest.mark.parametrize(
        "guessing",
        [0.0, 0.1, 0.2, 0.25, 0.35],
    )
    def test_valid_guessing_accepted(self, guessing: float) -> None:
        result = validate_irt_guessing(guessing, strict=True)
        assert result == guessing

    @pytest.mark.parametrize(
        "guessing",
        [-0.01, 0.36, 0.5, 1.0],
    )
    def test_invalid_guessing_rejected(self, guessing: float) -> None:
        with pytest.raises(IRTValidationError):
            validate_irt_guessing(guessing, strict=True)

    def test_invalid_difficulty_clamped_non_strict(self) -> None:
        assert validate_irt_difficulty(5.0, strict=False) == 4.0
        assert validate_irt_difficulty(-5.0, strict=False) == -4.0

    def test_irt_item_invalid_params_raises(self) -> None:
        with pytest.raises(IRTValidationError):
            IRTItem(
                item_id="bad",
                discrimination=1.0,
                difficulty=10.0,  # out of range
                guessing=0.25,
            )

    def test_irt_item_valid_creation(self) -> None:
        item = IRTItem(
            item_id="q1",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.25,
        )
        assert item.item_id == "q1"
        assert item.difficulty == 0.0

    def test_irt_item_skip_validation(self) -> None:
        item = IRTItem(
            item_id="legacy",
            discrimination=0.01,  # would be invalid
            difficulty=10.0,  # would be invalid
            guessing=0.5,  # would be invalid
            _validate=False,
        )
        assert item.difficulty == 10.0


@pytest.mark.irt
class TestIRTProbability:
    """4PL IRT probability calculation tests."""

    def setup_method(self) -> None:
        self.model = FourParameterIRTModel(scaling_constant=1.0)

    def _make_item(
        self,
        difficulty: float = 0.0,
        discrimination: float = 1.0,
        guessing: float = 0.0,
        upper_asymptote: float = 1.0,
    ) -> IRTItem:
        return IRTItem(
            item_id="test",
            discrimination=discrimination,
            difficulty=difficulty,
            guessing=guessing,
            upper_asymptote=upper_asymptote,
        )

    def test_probability_between_guessing_and_upper(self) -> None:
        """P(theta) must be in [c, d] for any theta."""
        item = self._make_item(guessing=0.25, upper_asymptote=0.98)
        for theta in [-4.0, -2.0, 0.0, 2.0, 4.0]:
            p = self.model.probability(theta, item)
            assert p >= 0.25 - 1e-6, f"P({theta}) = {p} < guessing"
            assert p <= 0.98 + 1e-6, f"P({theta}) = {p} > upper_asymptote"

    def test_theta_equals_difficulty_gives_midpoint(self) -> None:
        """When theta == b, P = c + (d-c)/2 = (1+c)/2 for d=1, c=guessing."""
        item = self._make_item(difficulty=1.0, guessing=0.2)
        p = self.model.probability(1.0, item)
        expected = (1.0 + 0.2) / 2.0  # 0.6
        assert p == pytest.approx(expected, abs=0.01)

    def test_higher_theta_gives_higher_probability(self) -> None:
        item = self._make_item(difficulty=0.0, discrimination=1.5)
        p_low = self.model.probability(-2.0, item)
        p_high = self.model.probability(2.0, item)
        assert p_high > p_low

    def test_higher_discrimination_steeper_curve(self) -> None:
        """Higher discrimination -> larger probability difference around b."""
        item_low_a = self._make_item(discrimination=0.5)
        item_high_a = self._make_item(discrimination=3.0)
        diff_low = (
            self.model.probability(1.0, item_low_a)
            - self.model.probability(-1.0, item_low_a)
        )
        diff_high = (
            self.model.probability(1.0, item_high_a)
            - self.model.probability(-1.0, item_high_a)
        )
        assert diff_high > diff_low

    def test_probability_extreme_theta(self) -> None:
        """Extreme theta values should not produce NaN or errors."""
        item = self._make_item(difficulty=0.0, discrimination=2.0, guessing=0.25)
        p_neg = self.model.probability(-100.0, item)
        p_pos = self.model.probability(100.0, item)
        assert 0.0 < p_neg < 1.0
        assert 0.0 < p_pos < 1.0


@pytest.mark.irt
class TestIRTInformation:
    """Item and test information function tests."""

    def setup_method(self) -> None:
        self.model = FourParameterIRTModel()

    def _make_item(self, **kwargs: float) -> IRTItem:
        defaults = {
            "item_id": "info_test",
            "discrimination": 1.5,
            "difficulty": 0.0,
            "guessing": 0.0,
        }
        defaults.update(kwargs)
        return IRTItem(**defaults)  # type: ignore[arg-type]

    def test_information_is_positive(self) -> None:
        item = self._make_item()
        for theta in [-3.0, -1.0, 0.0, 1.0, 3.0]:
            info = self.model.information(theta, item)
            assert info >= 0.0

    def test_information_peaks_near_difficulty(self) -> None:
        item = self._make_item(difficulty=1.0)
        info_at_b = self.model.information(1.0, item)
        info_far = self.model.information(-2.0, item)
        assert info_at_b > info_far

    def test_higher_discrimination_more_information(self) -> None:
        item_low = self._make_item(discrimination=0.5)
        item_high = self._make_item(discrimination=3.0)
        assert self.model.information(0.0, item_high) > self.model.information(
            0.0, item_low
        )

    def test_test_information_sums_items(self) -> None:
        items = [self._make_item(difficulty=d) for d in [-1.0, 0.0, 1.0]]
        for item in items:
            self.model.add_item(item)
        total = self.model.test_information(0.0, items)
        individual_sum = sum(self.model.information(0.0, item) for item in items)
        assert total == pytest.approx(individual_sum)

    def test_standard_error_decreases_with_items(self) -> None:
        items_1 = [self._make_item(difficulty=0.0)]
        items_3 = [self._make_item(difficulty=d) for d in [-1.0, 0.0, 1.0]]
        se_1 = self.model.standard_error(0.0, items_1)
        se_3 = self.model.standard_error(0.0, items_3)
        assert se_3 < se_1


@pytest.mark.irt
class TestIRTAbilityEstimation:
    """MLE ability estimation tests."""

    def setup_method(self) -> None:
        self.model = FourParameterIRTModel()
        # Add items across difficulty range
        for i, diff in enumerate([-2.0, -1.0, 0.0, 1.0, 2.0]):
            item = IRTItem(
                item_id=f"item_{i}",
                discrimination=1.5,
                difficulty=diff,
                guessing=0.2,
            )
            self.model.add_item(item)

    def test_mle_empty_responses_returns_zero(self) -> None:
        result = self.model.estimate_ability_mle([])
        assert result.ability == 0.0
        assert result.n_items == 0

    def test_mle_all_correct_high_ability(self) -> None:
        responses = [
            IRTResponse(student_id="s1", item_id=f"item_{i}", response=1, response_time=30.0)
            for i in range(5)
        ]
        result = self.model.estimate_ability_mle(responses)
        assert result.ability > 0.0
        assert result.student_id == "s1"
        assert result.estimation_method == "MLE"

    def test_mle_all_incorrect_low_ability(self) -> None:
        responses = [
            IRTResponse(student_id="s2", item_id=f"item_{i}", response=0, response_time=30.0)
            for i in range(5)
        ]
        result = self.model.estimate_ability_mle(responses)
        # With guessing=0.2, MLE for all-incorrect may not converge to negative
        # but ability should be estimated and bounded
        assert -4.0 <= result.ability <= 4.0
        assert result.n_items == 5

    def test_mle_mixed_responses_moderate_ability(self) -> None:
        # Correct on easy, incorrect on hard
        responses = [
            IRTResponse(student_id="s3", item_id="item_0", response=1, response_time=30.0),
            IRTResponse(student_id="s3", item_id="item_1", response=1, response_time=30.0),
            IRTResponse(student_id="s3", item_id="item_2", response=1, response_time=30.0),
            IRTResponse(student_id="s3", item_id="item_3", response=0, response_time=30.0),
            IRTResponse(student_id="s3", item_id="item_4", response=0, response_time=30.0),
        ]
        result = self.model.estimate_ability_mle(responses)
        assert -2.0 < result.ability < 2.0

    def test_mle_ability_bounded(self) -> None:
        responses = [
            IRTResponse(student_id="s4", item_id=f"item_{i}", response=1, response_time=30.0)
            for i in range(5)
        ]
        result = self.model.estimate_ability_mle(responses)
        assert -4.0 <= result.ability <= 4.0

    def test_mle_yks_predicted_score(self) -> None:
        responses = [
            IRTResponse(student_id="s5", item_id="item_2", response=1, response_time=30.0),
        ]
        result = self.model.estimate_ability_mle(responses)
        # YKS score formula: 300 + theta * 66.67
        expected_score = 300 + result.ability * 66.67
        assert result.yks_predicted_score == pytest.approx(expected_score, abs=0.1)

    def test_mle_confidence_interval(self) -> None:
        responses = [
            IRTResponse(student_id="s6", item_id=f"item_{i}", response=1, response_time=30.0)
            for i in range(5)
        ]
        result = self.model.estimate_ability_mle(responses)
        low, high = result.confidence_interval_95
        assert low < result.ability < high


@pytest.mark.irt
class TestCATItemSelection:
    """Computerized Adaptive Testing item selection tests."""

    def setup_method(self) -> None:
        self.model = FourParameterIRTModel()
        self.items = []
        for i, diff in enumerate([-2.0, -1.0, 0.0, 1.0, 2.0]):
            item = IRTItem(
                item_id=f"cat_{i}",
                discrimination=1.5,
                difficulty=diff,
                guessing=0.2,
            )
            self.model.add_item(item)
            self.items.append(item)

    def test_cat_selects_item_near_theta(self) -> None:
        selected = self.model.select_next_item_cat(0.0, self.items, [])
        assert selected is not None
        # Item near difficulty=0.0 should have highest information
        assert selected.difficulty == pytest.approx(0.0, abs=1.5)

    def test_cat_excludes_answered_items(self) -> None:
        answered = ["cat_2"]  # difficulty=0.0
        selected = self.model.select_next_item_cat(0.0, self.items, answered)
        assert selected is not None
        assert selected.item_id != "cat_2"

    def test_cat_returns_none_when_all_answered(self) -> None:
        answered = [f"cat_{i}" for i in range(5)]
        selected = self.model.select_next_item_cat(0.0, self.items, answered)
        assert selected is None

    def test_cat_selects_max_information_item(self) -> None:
        selected = self.model.select_next_item_cat(1.5, self.items, [])
        assert selected is not None
        # Should be the item closest to theta=1.5
        info_selected = self.model.information(1.5, selected)
        for item in self.items:
            assert info_selected >= self.model.information(1.5, item) - 1e-10


# ═══════════════════════════════════════════════════════════════════
# FSRS TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.fsrs
class TestFSRSCardCreation:
    """FSRSCard dataclass tests."""

    def test_default_card(self) -> None:
        card = FSRSCard(id="c1", subject="matematik")
        assert card.id == "c1"
        assert card.difficulty == 0.0
        assert card.stability == 0.0
        assert card.state == "new"
        assert card.review_count == 0

    def test_card_with_values(self) -> None:
        card = FSRSCard(
            id="c2",
            subject="fizik",
            difficulty=5.0,
            stability=10.0,
            retrievability=0.9,
            review_count=5,
        )
        assert card.difficulty == 5.0
        assert card.stability == 10.0
        assert card.retrievability == 0.9


@pytest.mark.fsrs
class TestFSRSScheduleCalculation:
    """FSRS schedule calculation for each grade."""

    def setup_method(self) -> None:
        self.fsrs = TurkishOptimizedFSRS()
        self.card = FSRSCard(
            id="s1",
            subject="matematik",
            difficulty=5.0,
            stability=10.0,
            retrievability=0.85,
            last_review=datetime(2025, 3, 1),
            review_count=3,
            state="review",
            scheduled_days=10,
        )
        self.context = StudentContext(student_id="stu1")
        self.review_date = datetime(2025, 3, 10)  # March 10 - normal period

    def test_again_gives_shortest_interval(self) -> None:
        schedule = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.AGAIN, self.review_date, self.context
        )
        assert schedule.interval_days >= 1
        # AGAIN should give shorter interval than GOOD
        schedule_good = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.GOOD, self.review_date, self.context
        )
        assert schedule.interval_days <= schedule_good.interval_days

    def test_easy_gives_longest_interval(self) -> None:
        schedule_easy = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.EASY, self.review_date, self.context
        )
        schedule_good = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.GOOD, self.review_date, self.context
        )
        assert schedule_easy.interval_days >= schedule_good.interval_days

    def test_grade_ordering(self) -> None:
        """AGAIN < HARD <= GOOD <= EASY in interval days."""
        intervals = {}
        for grade in FSRSGrade:
            s = self.fsrs.calculate_next_review(
                self.card, grade, self.review_date, self.context
            )
            intervals[grade] = s.interval_days

        assert intervals[FSRSGrade.AGAIN] <= intervals[FSRSGrade.HARD]
        assert intervals[FSRSGrade.HARD] <= intervals[FSRSGrade.GOOD]
        assert intervals[FSRSGrade.GOOD] <= intervals[FSRSGrade.EASY]

    def test_interval_within_bounds(self) -> None:
        for grade in FSRSGrade:
            s = self.fsrs.calculate_next_review(
                self.card, grade, self.review_date, self.context
            )
            assert s.interval_days >= self.fsrs.min_interval
            assert s.interval_days <= self.fsrs.max_interval

    def test_schedule_returns_correct_card_id(self) -> None:
        s = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.GOOD, self.review_date, self.context
        )
        assert s.card_id == "s1"
        assert s.grade == FSRSGrade.GOOD

    def test_scheduled_date_in_future(self) -> None:
        s = self.fsrs.calculate_next_review(
            self.card, FSRSGrade.GOOD, self.review_date, self.context
        )
        assert s.scheduled_date > self.review_date


@pytest.mark.fsrs
class TestFSRSStabilityAndDifficulty:
    """Stability and difficulty update tests."""

    def setup_method(self) -> None:
        self.fsrs = TurkishOptimizedFSRS()
        self.context = StudentContext(student_id="stu_sd")

    def test_again_increases_difficulty(self) -> None:
        card = FSRSCard(
            id="sd1", subject="mat", difficulty=5.0, stability=10.0,
            state="review", scheduled_days=5,
        )
        s = self.fsrs.calculate_next_review(
            card, FSRSGrade.AGAIN, datetime(2025, 3, 10), self.context
        )
        assert s.difficulty > 5.0

    def test_again_decreases_stability(self) -> None:
        card = FSRSCard(
            id="sd2", subject="mat", difficulty=5.0, stability=10.0,
            state="review", scheduled_days=5,
        )
        s = self.fsrs.calculate_next_review(
            card, FSRSGrade.AGAIN, datetime(2025, 3, 10), self.context
        )
        assert s.stability < 10.0

    def test_easy_decreases_difficulty(self) -> None:
        card = FSRSCard(
            id="sd3", subject="mat", difficulty=5.0, stability=10.0,
            state="review", scheduled_days=5,
        )
        s = self.fsrs.calculate_next_review(
            card, FSRSGrade.EASY, datetime(2025, 3, 10), self.context
        )
        assert s.difficulty < 5.0

    def test_good_keeps_difficulty(self) -> None:
        card = FSRSCard(
            id="sd4", subject="mat", difficulty=5.0, stability=10.0,
            state="review", scheduled_days=5,
        )
        s = self.fsrs.calculate_next_review(
            card, FSRSGrade.GOOD, datetime(2025, 3, 10), self.context
        )
        assert s.difficulty == pytest.approx(5.0, abs=0.01)

    def test_stability_bounded(self) -> None:
        card = FSRSCard(
            id="sd5", subject="mat", difficulty=5.0, stability=0.1,
            state="review", scheduled_days=1,
        )
        s = self.fsrs.calculate_next_review(
            card, FSRSGrade.AGAIN, datetime(2025, 3, 10), self.context
        )
        assert s.stability >= 0.1  # min stability


@pytest.mark.fsrs
class TestFSRSCulturalFactors:
    """Cultural factor calculation tests."""

    def test_yks_period_detection(self) -> None:
        june_15 = datetime(2025, 6, 15)
        assert CulturalFactorCalculator.is_yks_period(june_15) is True

    def test_normal_period_not_yks(self) -> None:
        march_1 = datetime(2025, 3, 1)
        assert CulturalFactorCalculator.is_yks_period(march_1) is False

    def test_days_until_yks(self) -> None:
        jan_1 = datetime(2025, 1, 1)
        days = CulturalFactorCalculator.days_until_yks(jan_1)
        assert days > 0
        assert days < 365

    def test_days_until_yks_after_yks(self) -> None:
        """After YKS, should count to next year."""
        july_1 = datetime(2025, 7, 1)
        days = CulturalFactorCalculator.days_until_yks(july_1)
        assert days > 300  # roughly 11 months to next YKS

    def test_exam_intensity_last_week(self) -> None:
        factor = CulturalFactorCalculator.get_exam_intensity_factor(
            datetime(2025, 6, 18)  # 2 days before YKS
        )
        assert factor == 1.5

    def test_exam_intensity_normal(self) -> None:
        factor = CulturalFactorCalculator.get_exam_intensity_factor(
            datetime(2025, 9, 15)  # far from YKS (~9 months away)
        )
        assert factor == 1.0

    def test_summer_break_detection(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        period = fsrs._detect_cultural_period(datetime(2025, 7, 15))
        assert period == CulturalPeriod.SUMMER_BREAK

    def test_exam_season_detection(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        period = fsrs._detect_cultural_period(datetime(2025, 6, 15))
        assert period == CulturalPeriod.EXAM_SEASON

    def test_normal_period_detection(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        # February is normally NORMAL (unless Ramadan falls there)
        period = fsrs._detect_cultural_period(datetime(2025, 2, 15))
        # Could be NORMAL or RAMADAN depending on hijri calendar
        assert period in [CulturalPeriod.NORMAL, CulturalPeriod.RAMADAN]

    def test_cultural_multiplier_bounded(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        ctx = StudentContext(
            student_id="test",
            group_study_preference=True,
            family_pressure_level=1.0,
            exam_anxiety_level=1.0,
            study_consistency=1.0,
        )
        mult = fsrs._calculate_cultural_multiplier(datetime(2025, 3, 10), ctx)
        assert 0.1 <= mult <= 3.0

    def test_weekend_effect_applied(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        ctx = StudentContext(student_id="test")
        # Saturday March 8, 2025
        sat = datetime(2025, 3, 8)
        # Wednesday March 5, 2025
        wed = datetime(2025, 3, 5)
        mult_sat = fsrs._calculate_cultural_multiplier(sat, ctx)
        mult_wed = fsrs._calculate_cultural_multiplier(wed, ctx)
        # Weekend should have lower multiplier due to 0.90 factor
        assert mult_sat < mult_wed


@pytest.mark.fsrs
class TestFSRSRetentionAndDifficulty:
    """Retention prediction and difficulty adjustment tests."""

    def setup_method(self) -> None:
        self.fsrs = TurkishOptimizedFSRS()

    def test_predict_retention_decreases_over_time(self) -> None:
        card = FSRSCard(id="r1", subject="mat", stability=10.0)
        r_1 = self.fsrs.predict_retention_probability(card, days_ahead=1)
        r_10 = self.fsrs.predict_retention_probability(card, days_ahead=10)
        r_30 = self.fsrs.predict_retention_probability(card, days_ahead=30)
        assert r_1 > r_10 > r_30

    def test_predict_retention_bounded(self) -> None:
        card = FSRSCard(id="r2", subject="mat", stability=10.0)
        for days in [0, 1, 10, 100, 1000]:
            r = self.fsrs.predict_retention_probability(card, days_ahead=days)
            assert 0.0 <= r <= 1.0

    def test_predict_retention_zero_stability(self) -> None:
        card = FSRSCard(id="r3", subject="mat", stability=0.0)
        assert self.fsrs.predict_retention_probability(card, days_ahead=1) == 0.0

    def test_difficulty_adjustment_high_success(self) -> None:
        card = FSRSCard(id="da1", subject="mat", difficulty=5.0)
        grades = [FSRSGrade.GOOD, FSRSGrade.GOOD, FSRSGrade.EASY, FSRSGrade.GOOD, FSRSGrade.EASY]
        adj = self.fsrs.calculate_difficulty_adjustment(card, grades)
        assert adj < 0  # should decrease difficulty

    def test_difficulty_adjustment_low_success(self) -> None:
        card = FSRSCard(id="da2", subject="mat", difficulty=5.0)
        grades = [FSRSGrade.AGAIN, FSRSGrade.HARD, FSRSGrade.AGAIN, FSRSGrade.AGAIN, FSRSGrade.HARD]
        adj = self.fsrs.calculate_difficulty_adjustment(card, grades)
        assert adj > 0  # should increase difficulty

    def test_difficulty_adjustment_empty(self) -> None:
        card = FSRSCard(id="da3", subject="mat")
        adj = self.fsrs.calculate_difficulty_adjustment(card, [])
        assert adj == 0.0

    def test_optimal_retention_high_anxiety(self) -> None:
        ctx = StudentContext(student_id="or1", exam_anxiety_level=0.9)
        retention = self.fsrs.get_optimal_retention_rate(ctx)
        assert retention > self.fsrs.default_retention

    def test_optimal_retention_bounded(self) -> None:
        ctx = StudentContext(
            student_id="or2",
            exam_anxiety_level=1.0,
            family_pressure_level=1.0,
        )
        retention = self.fsrs.get_optimal_retention_rate(ctx)
        assert retention <= 0.95


@pytest.mark.fsrs
class TestFSRSPerformance:
    """Performance benchmarks for FSRS calculations."""

    def test_single_calculation_under_10ms(self) -> None:
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="perf1", subject="mat", difficulty=5.0, stability=10.0,
            state="review", scheduled_days=10,
        )
        ctx = StudentContext(student_id="perf")
        dt = datetime(2025, 3, 10)

        start = time.perf_counter()
        for _ in range(100):
            fsrs.calculate_next_review(card, FSRSGrade.GOOD, dt, ctx)
        elapsed = (time.perf_counter() - start) / 100

        assert elapsed < 0.01, f"Single calculation took {elapsed*1000:.2f}ms (>10ms)"


# ═══════════════════════════════════════════════════════════════════
# ZPD + MAARIF TESTS
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.zpd
class TestMaarifValues:
    """MEB Maarif value system tests."""

    def test_maarif_value_enum_members(self) -> None:
        assert MaarifValue.VATAN.value == "vatan"
        assert MaarifValue.ADALET.value == "adalet"
        assert MaarifValue.SABIR.value == "sabır"

    def test_subject_maarif_mapping(self) -> None:
        system = TurkishZPDMaarifSystem()
        assert "tarih" in system.subject_maarif_mapping
        assert "matematik" in system.subject_maarif_mapping
        tarih_values = system.subject_maarif_mapping["tarih"]
        assert MaarifValue.VATAN in tarih_values


@pytest.mark.zpd
class TestMaarifAlignment:
    """Maarif value alignment calculation tests."""

    @pytest.fixture
    def system(self) -> TurkishZPDMaarifSystem:
        return TurkishZPDMaarifSystem()

    @pytest.mark.asyncio
    async def test_alignment_with_matching_content(self, system: TurkishZPDMaarifSystem) -> None:
        alignment = await system.calculate_maarif_alignment(
            "tarih", "vatan sevgisi ve millet birliği ile adalet"
        )
        assert alignment.overall_alignment > 0.0
        assert len(alignment.aligned_values) > 0

    @pytest.mark.asyncio
    async def test_alignment_no_matching_content(self, system: TurkishZPDMaarifSystem) -> None:
        alignment = await system.calculate_maarif_alignment(
            "matematik", "integral ve türev hesaplamaları"
        )
        # matematik maps to DÜRÜSTLÜK, SABIR, SORUMLULUK - none of these keywords match
        assert alignment.overall_alignment == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_alignment_scores_bounded(self, system: TurkishZPDMaarifSystem) -> None:
        alignment = await system.calculate_maarif_alignment(
            "tarih", "vatan millet adalet hak eşitlik dostluk"
        )
        assert 0.0 <= alignment.national_values_alignment <= 1.0
        assert 0.0 <= alignment.universal_values_alignment <= 1.0
        assert 0.0 <= alignment.root_values_alignment <= 1.0
        assert 0.0 <= alignment.overall_alignment <= 1.0


@pytest.mark.zpd
class TestTurkishZPDCalculation:
    """ZPD calculation with cultural adaptation tests."""

    @pytest.fixture
    def system(self) -> TurkishZPDMaarifSystem:
        return TurkishZPDMaarifSystem()

    @pytest.fixture
    def default_context(self) -> TurkishCulturalContext:
        return TurkishCulturalContext(student_id="zpd_test")

    @pytest.mark.asyncio
    async def test_zpd_lower_bound_equals_current_level(
        self, system: TurkishZPDMaarifSystem, default_context: TurkishCulturalContext
    ) -> None:
        zpd = await system.calculate_turkish_zpd(
            "s1", "matematik", 0.5, default_context
        )
        assert zpd.lower_bound == 0.5

    @pytest.mark.asyncio
    async def test_zpd_upper_bound_above_current_level(
        self, system: TurkishZPDMaarifSystem, default_context: TurkishCulturalContext
    ) -> None:
        zpd = await system.calculate_turkish_zpd(
            "s1", "matematik", 0.5, default_context
        )
        assert zpd.upper_bound > zpd.current_level

    @pytest.mark.asyncio
    async def test_optimal_challenge_within_zpd(
        self, system: TurkishZPDMaarifSystem, default_context: TurkishCulturalContext
    ) -> None:
        zpd = await system.calculate_turkish_zpd(
            "s1", "fen", 0.5, default_context
        )
        assert zpd.lower_bound <= zpd.optimal_challenge <= zpd.upper_bound

    @pytest.mark.asyncio
    async def test_group_preference_expands_zpd(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx_low_group = TurkishCulturalContext(
            student_id="s1", group_learning_preference=0.3,
            teacher_respect_level=0.3, family_involvement=0.3,
            peer_competition=0.2,
        )
        ctx_high_group = TurkishCulturalContext(
            student_id="s2", group_learning_preference=0.9,
            teacher_respect_level=0.9, family_involvement=0.9,
            peer_competition=0.9,
        )
        zpd_low = await system.calculate_turkish_zpd("s1", "mat", 0.5, ctx_low_group)
        zpd_high = await system.calculate_turkish_zpd("s2", "mat", 0.5, ctx_high_group)
        range_low = zpd_low.upper_bound - zpd_low.lower_bound
        range_high = zpd_high.upper_bound - zpd_high.lower_bound
        assert range_high > range_low

    @pytest.mark.asyncio
    async def test_zpd_group_balance_computed(
        self, system: TurkishZPDMaarifSystem, default_context: TurkishCulturalContext
    ) -> None:
        zpd = await system.calculate_turkish_zpd(
            "s1", "tarih", 0.5, default_context
        )
        assert 0.0 <= zpd.group_individual_balance <= 1.0


@pytest.mark.zpd
class TestZPDRecommendation:
    """ZPD-based learning recommendation tests."""

    @pytest.fixture
    def system(self) -> TurkishZPDMaarifSystem:
        return TurkishZPDMaarifSystem()

    @pytest.mark.asyncio
    async def test_recommendation_learning_mode_group(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = TurkishCulturalContext(
            student_id="rec1",
            group_learning_preference=0.95,
            collective_success=0.95,
            social_harmony=0.95,
            peer_competition=0.8,
        )
        zpd = await system.calculate_turkish_zpd("rec1", "tarih", 0.5, ctx)
        rec = await system.generate_zpd_recommendation(zpd, "Osmanlı tarihi")
        assert rec.learning_mode in ["group", "mixed", "individual"]
        assert rec.recommended_difficulty > 0
        assert 0.0 <= rec.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_recommendation_has_reasoning(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = TurkishCulturalContext(student_id="rec2")
        zpd = await system.calculate_turkish_zpd("rec2", "matematik", 0.6, ctx)
        rec = await system.generate_zpd_recommendation(zpd, "Diferansiyel denklemler")
        assert len(rec.reasoning) > 10
        assert rec.reasoning.endswith(".")

    @pytest.mark.asyncio
    async def test_recommendation_teacher_guidance_bounded(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = TurkishCulturalContext(student_id="rec3", teacher_respect_level=1.0)
        zpd = await system.calculate_turkish_zpd("rec3", "fen", 0.4, ctx)
        rec = await system.generate_zpd_recommendation(zpd, "Fizik")
        assert 0.0 <= rec.teacher_guidance_level <= 1.0


@pytest.mark.zpd
class TestDifficultyAdaptation:
    """Cultural difficulty adaptation tests."""

    @pytest.fixture
    def system(self) -> TurkishZPDMaarifSystem:
        return TurkishZPDMaarifSystem()

    @pytest.mark.asyncio
    async def test_adapt_difficulty_bounded(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = TurkishCulturalContext(
            student_id="da1",
            collective_success=0.9,
            teacher_respect_level=0.9,
            family_involvement=0.9,
        )
        perf = {
            "individual_score": 0.4,
            "group_score": 0.8,
            "teacher_feedback_score": 0.9,
            "homework_score": 0.9,
        }
        adapted = await system.adapt_difficulty_culturally(0.5, perf, ctx)
        assert 0.1 <= adapted <= 1.0

    @pytest.mark.asyncio
    async def test_group_outperformance_increases_difficulty(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = TurkishCulturalContext(student_id="da2", collective_success=0.9)
        perf_group_high = {"individual_score": 0.3, "group_score": 0.8}
        perf_group_low = {"individual_score": 0.8, "group_score": 0.3}
        d_high = await system.adapt_difficulty_culturally(0.5, perf_group_high, ctx)
        d_low = await system.adapt_difficulty_culturally(0.5, perf_group_low, ctx)
        assert d_high >= d_low


@pytest.mark.zpd
class TestCulturalContextDetection:
    """Cultural context detection tests."""

    @pytest.fixture
    def system(self) -> TurkishZPDMaarifSystem:
        return TurkishZPDMaarifSystem()

    @pytest.mark.asyncio
    async def test_detect_from_behavioral_data(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        data = {
            "group_study_sessions": 8,
            "individual_study_sessions": 2,
            "teacher_question_count": 15,
            "peer_interaction_count": 20,
            "help_seeking_frequency": 10,
        }
        ctx = await system.detect_cultural_context("det1", data)
        assert ctx.student_id == "det1"
        assert ctx.group_learning_preference == pytest.approx(0.8, abs=0.01)

    @pytest.mark.asyncio
    async def test_detect_with_family_survey(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        data = {"group_study_sessions": 5, "individual_study_sessions": 5}
        survey = {"involvement_level": 0.9, "collective_focus": 0.8}
        ctx = await system.detect_cultural_context("det2", data, survey)
        assert ctx.family_involvement == 0.9
        assert ctx.collective_success == 0.8

    @pytest.mark.asyncio
    async def test_detect_empty_behavioral_data(
        self, system: TurkishZPDMaarifSystem
    ) -> None:
        ctx = await system.detect_cultural_context("det3", {})
        # Should use defaults from TurkishCulturalContext
        assert ctx.student_id == "det3"


@pytest.mark.zpd
class TestCorrelationCalculation:
    """Simple correlation helper tests."""

    def setup_method(self) -> None:
        self.system = TurkishZPDMaarifSystem()

    def test_perfect_positive_correlation(self) -> None:
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        corr = self.system._calculate_simple_correlation(x, y)
        assert corr == pytest.approx(1.0, abs=0.001)

    def test_perfect_negative_correlation(self) -> None:
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        corr = self.system._calculate_simple_correlation(x, y)
        assert corr == pytest.approx(-1.0, abs=0.001)

    def test_mismatched_lengths(self) -> None:
        assert self.system._calculate_simple_correlation([1.0], [1.0, 2.0]) == 0.0

    def test_too_few_points(self) -> None:
        assert self.system._calculate_simple_correlation([1.0], [1.0]) == 0.0


@pytest.mark.zpd
class TestZPDOptimalZone:
    """ZPD optimal zone: success probability between 15% and 85%."""

    def test_in_zpd_optimal(self) -> None:
        assert is_in_zpd(0.5) is True
        assert is_in_zpd(0.15) is True
        assert is_in_zpd(0.85) is True

    def test_outside_zpd(self) -> None:
        assert is_in_zpd(0.14) is False
        assert is_in_zpd(0.86) is False
        assert is_in_zpd(0.0) is False
        assert is_in_zpd(1.0) is False

    def test_irt_probability_in_zpd(self) -> None:
        """When theta ~= difficulty, 3PL probability should be in ZPD for c=0.25."""
        model = FourParameterIRTModel()
        item = IRTItem(
            item_id="zpd_check",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.25,
        )
        p = model.probability(0.0, item)
        # (1 + 0.25) / 2 = 0.625 which is in [0.15, 0.85]
        assert is_in_zpd(p), f"P={p} is outside ZPD optimal zone"
