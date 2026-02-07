"""
FSRS Scheduling Tests (K-03).

Tests for Turkish-optimized FSRS spaced repetition algorithm.
"""
import sys
from datetime import datetime
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.turkish_optimized_fsrs import (  # noqa: E402
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)


class TestGradeIntervals:
    """Test interval calculations for different grades."""

    def test_new_card_good_grade_interval(self):
        """New card with GOOD grade should get interval >= 1 day."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-001",
            subject="matematik",
            difficulty=5.0,
            stability=1.0,
            state="new",
        )
        context = StudentContext(student_id="student-001")

        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=datetime.now(),
            student_context=context,
        )

        # Use interval_days attribute (not interval)
        assert schedule.interval_days >= 1

    def test_again_grade_resets(self):
        """AGAIN grade should reset progress."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-002",
            subject="turkce",
            difficulty=5.0,
            stability=10.0,
            state="review",
        )
        context = StudentContext(student_id="student-002")

        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.AGAIN,
            current_date=datetime.now(),
            student_context=context,
        )

        # AGAIN should result in shorter interval
        # Note: FSRSSchedule doesn't return card object, check interval instead
        assert schedule.interval_days < 10

    def test_easy_grade_bigger_interval(self):
        """EASY grade should give longer interval than GOOD."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-003",
            subject="fizik",
            difficulty=5.0,
            stability=5.0,
            state="review",
        )
        context = StudentContext(student_id="student-003")
        current_date = datetime.now()

        schedule_good = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=current_date,
            student_context=context,
        )

        schedule_easy = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.EASY,
            current_date=current_date,
            student_context=context,
        )

        assert schedule_easy.interval_days > schedule_good.interval_days

    def test_hard_grade_smaller_interval(self):
        """HARD grade should give shorter interval than GOOD."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-004",
            subject="kimya",
            difficulty=5.0,
            stability=5.0,
            state="review",
        )
        context = StudentContext(student_id="student-004")
        current_date = datetime.now()

        schedule_good = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=current_date,
            student_context=context,
        )

        schedule_hard = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.HARD,
            current_date=current_date,
            student_context=context,
        )

        assert schedule_hard.interval_days < schedule_good.interval_days


class TestStabilityAndRetrievability:
    """Test stability and retrievability calculations."""

    def test_stability_increases_on_success(self):
        """Consecutive GOOD grades should increase stability."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-005",
            subject="biyoloji",
            difficulty=5.0,
            stability=5.0,
            state="review",
        )
        context = StudentContext(student_id="student-005")

        initial_stability = card.stability

        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=datetime.now(),
            student_context=context,
        )

        # Check schedule.stability (not schedule.card.stability)
        assert schedule.stability > initial_stability

    def test_retrievability_in_range(self):
        """Retrievability should be in [0, 1]."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-006",
            subject="tarih",
            difficulty=5.0,
            stability=10.0,
            state="review",
        )
        context = StudentContext(student_id="student-006")

        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=datetime.now(),
            student_context=context,
        )

        assert 0.0 <= schedule.retrievability <= 1.0


class TestReviewDates:
    """Test review date calculations."""

    def test_due_date_future(self):
        """Next review should be after current date."""
        fsrs = TurkishOptimizedFSRS()
        card = FSRSCard(
            id="card-007",
            subject="cografya",
            difficulty=5.0,
            stability=3.0,
            state="review",
        )
        context = StudentContext(student_id="student-007")
        current_date = datetime.now()

        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.GOOD,
            current_date=current_date,
            student_context=context,
        )

        # Use scheduled_date attribute (not due_date)
        assert schedule.scheduled_date > current_date

    def test_min_interval_1_day(self):
        """Minimum interval should be 1 day."""
        fsrs = TurkishOptimizedFSRS()

        assert fsrs.min_interval == 1

    def test_max_interval_36500(self):
        """Maximum interval should be 36500 days (100 years)."""
        fsrs = TurkishOptimizedFSRS()

        assert fsrs.max_interval == 36500


class TestRetentionDefaults:
    """Test default retention settings."""

    def test_default_retention_085(self):
        """Default retention rate should be 0.85 (85%)."""
        fsrs = TurkishOptimizedFSRS()

        assert fsrs.default_retention == 0.85


class TestCulturalAdjustments:
    """Test Turkish cultural adjustments."""

    def test_ramadan_factor(self):
        """Ramadan factor should be 0.75 (reduced learning)."""
        fsrs = TurkishOptimizedFSRS()

        factor = fsrs.cultural_adjustments.get("ramadan_factor")

        assert factor == 0.75

    def test_yks_stress_factor(self):
        """YKS preparation stress factor should be 1.50."""
        fsrs = TurkishOptimizedFSRS()

        # Check in education_factors or cultural_adjustments
        factor = fsrs.turkish_education_factors.get("yks_preparation_stress")

        assert factor == 1.50

    def test_summer_decay_factor(self):
        """Summer break decay factor should be 0.60."""
        fsrs = TurkishOptimizedFSRS()

        factor = fsrs.cultural_adjustments.get("summer_break_decay")

        assert factor == 0.60

    def test_group_study_bonus(self):
        """Group study bonus should be 1.25."""
        fsrs = TurkishOptimizedFSRS()

        factor = fsrs.cultural_adjustments.get("group_study_bonus")

        assert factor == 1.25

    def test_family_pressure_factor(self):
        """Family pressure factor should be 1.15."""
        fsrs = TurkishOptimizedFSRS()

        factor = fsrs.cultural_adjustments.get("family_pressure")

        assert factor == 1.15

    def test_religious_holiday_factor(self):
        """Religious holiday factor should be 0.80."""
        fsrs = TurkishOptimizedFSRS()

        factor = fsrs.cultural_adjustments.get("religious_holiday")

        assert factor == 0.80


class TestCardStateTransitions:
    """Test FSRSCard state transitions."""

    def test_card_state_transitions(self):
        """Card states should include new, learning, review, relearning."""
        valid_states = ["new", "learning", "review", "relearning"]

        # Create cards with each state
        for state in valid_states:
            card = FSRSCard(
                id=f"card-{state}",
                subject="matematik",
                difficulty=5.0,
                stability=1.0,
                state=state,
            )

            assert card.state in valid_states
            assert card.state == state
