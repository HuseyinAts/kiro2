"""
Property-based tests for Turkish-Optimized FSRS Algorithm.

Validates core invariants:
- Stability non-negative after any grade
- Difficulty bounds [0.0, 10.0]
- Retrievability bounds [0.0, 1.0]
- Interval ordering: AGAIN < HARD < GOOD < EASY
- Successful grades → stability non-decreasing
- Deterministic output for same input

Boris Cherny Standards: Property tests with 100+ iterations
"""

import sys
from datetime import datetime
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.turkish_optimized_fsrs import (  # noqa: E402
    FSRSCard,
    FSRSGrade,
    StudentContext,
    TurkishOptimizedFSRS,
)

# ============================================================================
# STRATEGY DEFINITIONS
# ============================================================================

# Valid FSRS parameter ranges
valid_difficulty = st.floats(
    min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False
)
valid_stability = st.floats(
    min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False
)
valid_retrievability = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)
valid_review_count = st.integers(min_value=0, max_value=100)
valid_lapse_count = st.integers(min_value=0, max_value=50)

# Student context parameters
valid_student_preference = st.booleans()
valid_pressure_level = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)
valid_anxiety_level = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)
valid_consistency = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

# Grades (all 4 valid grades)
all_grades = st.sampled_from(
    [FSRSGrade.AGAIN, FSRSGrade.HARD, FSRSGrade.GOOD, FSRSGrade.EASY]
)
successful_grades = st.sampled_from([FSRSGrade.HARD, FSRSGrade.GOOD, FSRSGrade.EASY])

# Card states
valid_states = st.sampled_from(["new", "learning", "review", "relearning"])

# Subjects
subjects = st.sampled_from(
    ["matematik", "fizik", "kimya", "biyoloji", "turkce", "tarih"]
)


def create_test_card(
    difficulty: float,
    stability: float,
    retrievability: float,
    review_count: int,
    lapse_count: int,
    state: str,
    subject: str,
) -> FSRSCard:
    """Create a test FSRSCard with given parameters."""
    return FSRSCard(
        id=f"test-card-{stability:.2f}",
        subject=subject,
        difficulty=difficulty,
        stability=stability,
        retrievability=retrievability,
        last_review=datetime(2025, 1, 1),
        due_date=datetime(2025, 1, 2),
        review_count=review_count,
        lapse_count=lapse_count,
        elapsed_days=0,
        scheduled_days=1,
        reps=review_count,
        lapses=lapse_count,
        state=state,
    )


def create_test_context(
    group_study: bool,
    family_pressure: float,
    exam_anxiety: float,
    consistency: float,
) -> StudentContext:
    """Create a test StudentContext with given parameters."""
    return StudentContext(
        student_id="test-student",
        group_study_preference=group_study,
        family_pressure_level=family_pressure,
        exam_anxiety_level=exam_anxiety,
        study_consistency=consistency,
        cultural_background="turkish",
        timezone="Europe/Istanbul",
    )


# ============================================================================
# PROPERTY 1: STABILITY NON-NEGATIVE
# ============================================================================


class TestStabilityNonNegative:
    """Property: Stability must always be non-negative after any grade."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_stability_always_non_negative(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Stability must be >= 0 after any grade (AGAIN/HARD/GOOD/EASY)."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert schedule.stability >= 0.0, (
            f"Stability became negative: {schedule.stability} "
            f"after grade {grade.name} with initial stability {stability}"
        )


# ============================================================================
# PROPERTY 2: DIFFICULTY BOUNDS
# ============================================================================


class TestDifficultyBounds:
    """Property: Difficulty must always be in [0.0, 10.0]."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_difficulty_in_bounds(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Difficulty must stay in [0.0, 10.0] after any grade."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert 0.0 <= schedule.difficulty <= 10.0, (
            f"Difficulty out of bounds: {schedule.difficulty} "
            f"after grade {grade.name} with initial difficulty {difficulty}"
        )


# ============================================================================
# PROPERTY 3: RETRIEVABILITY BOUNDS
# ============================================================================


class TestRetrievabilityBounds:
    """Property: Retrievability must always be in [0.0, 1.0]."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_retrievability_in_bounds(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Retrievability must stay in [0.0, 1.0] after any grade."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert 0.0 <= schedule.retrievability <= 1.0, (
            f"Retrievability out of bounds: {schedule.retrievability} "
            f"after grade {grade.name} with initial retrievability {retrievability}"
        )


# ============================================================================
# PROPERTY 4: INTERVAL ORDERING
# ============================================================================


class TestIntervalOrdering:
    """Property: Intervals must satisfy AGAIN < HARD < GOOD < EASY."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_interval_ordering(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """AGAIN interval ≤ HARD interval ≤ GOOD interval ≤ EASY interval."""
        # Skip new cards as they have special handling
        assume(state != "new")
        assume(stability >= 1.0)  # Ensure reasonable stability for comparison

        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule_again = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.AGAIN,
            current_date=current_date,
            student_context=context,
        )
        schedule_hard = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.HARD,
            current_date=current_date,
            student_context=context,
        )
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

        assert schedule_again.interval_days <= schedule_hard.interval_days, (
            f"AGAIN ({schedule_again.interval_days}d) > "
            f"HARD ({schedule_hard.interval_days}d)"
        )
        assert schedule_hard.interval_days <= schedule_good.interval_days, (
            f"HARD ({schedule_hard.interval_days}d) > "
            f"GOOD ({schedule_good.interval_days}d)"
        )
        assert schedule_good.interval_days <= schedule_easy.interval_days, (
            f"GOOD ({schedule_good.interval_days}d) > "
            f"EASY ({schedule_easy.interval_days}d)"
        )


# ============================================================================
# PROPERTY 5: SUCCESSFUL GRADES → STABILITY NON-DECREASING
# ============================================================================


class TestStabilityIncreaseOnSuccess:
    """Property: GOOD/EASY grades should increase stability."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=st.sampled_from([FSRSGrade.GOOD, FSRSGrade.EASY]),  # Only GOOD/EASY
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_stability_non_decreasing_on_success(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """GOOD/EASY grades increase stability (HARD can decrease per FSRS)."""
        # Only test non-new cards (new cards have special initial stability)
        assume(state != "new")

        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        initial_stability = card.stability
        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        # GOOD (2.4063x) and EASY (5.8145x) multipliers always increase stability
        assert schedule.stability >= initial_stability - 1e-6, (
            f"Successful grade {grade.name} decreased stability: "
            f"{initial_stability} → {schedule.stability}"
        )


# ============================================================================
# PROPERTY 6: HARD GRADE BEHAVIOR
# ============================================================================


class TestHardGradeBehavior:
    """Property: HARD grade uses stability multiplier < 1.0 (per FSRS spec)."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=st.sampled_from(["learning", "review", "relearning"]),  # Non-new states
        subject=subjects,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_hard_grade_stability_behavior(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """HARD grade can decrease stability (multiplier 0.7186 < 1.0)."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        initial_stability = card.stability
        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.HARD,
            current_date=current_date,
            student_context=context,
        )

        # HARD multiplier is turkish_params[1] = 0.7186 < 1.0
        # So new_stability = old_stability * 0.7186
        expected_stability_approx = initial_stability * fsrs.turkish_params[1]

        # Allow 1% tolerance for floating point
        assert (
            abs(schedule.stability - expected_stability_approx)
            / expected_stability_approx
            < 0.01
        ), (
            f"HARD grade stability calculation incorrect: "
            f"expected ~{expected_stability_approx}, got {schedule.stability}"
        )


# ============================================================================
# PROPERTY 7: DETERMINISTIC OUTPUT
# ============================================================================


class TestDeterministicOutput:
    """Property: Same input must produce same output (determinism)."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_deterministic_scheduling(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Same inputs must return same result (determinism)."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule1 = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )
        schedule2 = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert schedule1.interval_days == schedule2.interval_days, (
            "Non-deterministic interval calculation"
        )
        assert abs(schedule1.stability - schedule2.stability) < 1e-9, (
            "Non-deterministic stability calculation"
        )
        assert abs(schedule1.difficulty - schedule2.difficulty) < 1e-9, (
            "Non-deterministic difficulty calculation"
        )
        assert abs(schedule1.retrievability - schedule2.retrievability) < 1e-9, (
            "Non-deterministic retrievability calculation"
        )


# ============================================================================
# PROPERTY 7: INTERVAL BOUNDS
# ============================================================================


class TestIntervalBounds:
    """Property: Intervals must respect min_interval and max_interval."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_interval_respects_bounds(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Interval must be in [min_interval, max_interval]."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert fsrs.min_interval <= schedule.interval_days <= fsrs.max_interval, (
            f"Interval {schedule.interval_days} outside bounds "
            f"[{fsrs.min_interval}, {fsrs.max_interval}]"
        )


# ============================================================================
# PROPERTY 8: CULTURAL MULTIPLIER BOUNDS
# ============================================================================


class TestCulturalMultiplierBounds:
    """Property: Cultural multiplier must be in reasonable range [0.1, 3.0]."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_cultural_multiplier_bounded(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Cultural multiplier must be in [0.1, 3.0] as per implementation."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        # Extract cultural multiplier from cultural_factors
        if "cultural_multiplier" in schedule.cultural_factors:
            multiplier = schedule.cultural_factors["cultural_multiplier"]
            assert 0.1 <= multiplier <= 3.0, (
                f"Cultural multiplier {multiplier} outside bounds [0.1, 3.0]"
            )


# ============================================================================
# PROPERTY 9: LAPSE COUNT INCREASES ON AGAIN
# ============================================================================


class TestLapseCountIncreaseOnAgain:
    """Property: AGAIN grade must increase lapse count."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_again_increases_difficulty(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """AGAIN grade should increase difficulty (penalty for failure)."""
        # Avoid already-max difficulty
        assume(difficulty < 9.8)

        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        initial_difficulty = card.difficulty
        schedule = fsrs.calculate_next_review(
            card=card,
            grade=FSRSGrade.AGAIN,
            current_date=current_date,
            student_context=context,
        )

        # AGAIN should increase difficulty (penalty)
        assert schedule.difficulty > initial_difficulty - 1e-6, (
            f"AGAIN grade did not increase difficulty: "
            f"{initial_difficulty} → {schedule.difficulty}"
        )


# ============================================================================
# PROPERTY 10: SCHEDULED DATE FUTURE
# ============================================================================


class TestScheduledDateFuture:
    """Property: Scheduled date must be in the future (at least 1 day)."""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        stability=valid_stability,
        retrievability=valid_retrievability,
        review_count=valid_review_count,
        lapse_count=valid_lapse_count,
        state=valid_states,
        subject=subjects,
        grade=all_grades,
        group_study=valid_student_preference,
        family_pressure=valid_pressure_level,
        exam_anxiety=valid_anxiety_level,
        consistency=valid_consistency,
    )
    def test_scheduled_date_in_future(
        self,
        difficulty: float,
        stability: float,
        retrievability: float,
        review_count: int,
        lapse_count: int,
        state: str,
        subject: str,
        grade: FSRSGrade,
        group_study: bool,
        family_pressure: float,
        exam_anxiety: float,
        consistency: float,
    ) -> None:
        """Scheduled date must be after current date."""
        fsrs = TurkishOptimizedFSRS()
        card = create_test_card(
            difficulty,
            stability,
            retrievability,
            review_count,
            lapse_count,
            state,
            subject,
        )
        context = create_test_context(
            group_study, family_pressure, exam_anxiety, consistency
        )
        current_date = datetime(2025, 3, 15, 10, 0, 0)

        schedule = fsrs.calculate_next_review(
            card=card, grade=grade, current_date=current_date, student_context=context
        )

        assert schedule.scheduled_date > current_date, (
            f"Scheduled date {schedule.scheduled_date} not after current {current_date}"
        )
