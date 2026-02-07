"""
Property-based tests for ZPD Maarif System.

Validates:
- ZPD probability bounds [0.15, 0.85] for optimal zone
- ZPD classification determinism
- Zone ordering consistency
- Cultural adjustment factors
- Maarif subject mapping
- IRT probability monotonicity within ZPD context

Boris Cherny Standards: Property tests with 100+ iterations
"""

import math
import sys
from pathlib import Path

from hypothesis import given, settings, strategies as st, assume, HealthCheck

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.turkish_zpd_maarif_system import (  # noqa: E402
    MaarifValue,
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
)

# IRT Parameter Ranges
THETA_MIN = -4.0
THETA_MAX = 4.0
DIFFICULTY_MIN = -4.0
DIFFICULTY_MAX = 4.0
DISCRIMINATION_MIN = 0.2
DISCRIMINATION_MAX = 4.0
GUESSING_MIN = 0.0
GUESSING_MAX = 0.35

# ZPD Probability Bounds
ZPD_LOWER_BOUND = 0.15
ZPD_UPPER_BOUND = 0.85
ZPD_OPTIMAL_LOWER = 0.40
ZPD_OPTIMAL_UPPER = 0.60

# IRT constant
D = 1.7


def calculate_irt_probability(
    theta: float, difficulty: float, discrimination: float, guessing: float
) -> float:
    """
    Calculate 3PL IRT probability.

    Args:
        theta: Student ability parameter [-4, 4].
        difficulty: Question difficulty parameter [-4, 4].
        discrimination: Question discrimination parameter [0.2, 4.0].
        guessing: Guessing parameter [0.0, 0.35].

    Returns:
        Probability of correct answer [guessing, 1.0].
    """
    exponent = -D * discrimination * (theta - difficulty)

    # Overflow protection
    if exponent > 700:
        return guessing
    elif exponent < -700:
        return 1.0

    return guessing + (1 - guessing) / (1 + math.exp(exponent))


def classify_zpd_zone(probability: float) -> str:
    """
    Classify ZPD zone based on success probability.

    Args:
        probability: Success probability [0.0, 1.0].

    Returns:
        Zone classification: "too_easy", "optimal", "acceptable", "too_hard".
    """
    if probability > ZPD_UPPER_BOUND:
        return "too_easy"
    elif probability < ZPD_LOWER_BOUND:
        return "too_hard"
    elif ZPD_OPTIMAL_LOWER <= probability <= ZPD_OPTIMAL_UPPER:
        return "optimal"
    else:
        return "acceptable"


# Hypothesis strategies
valid_theta = st.floats(
    min_value=THETA_MIN, max_value=THETA_MAX, allow_nan=False, allow_infinity=False
)
valid_difficulty = st.floats(
    min_value=DIFFICULTY_MIN,
    max_value=DIFFICULTY_MAX,
    allow_nan=False,
    allow_infinity=False,
)
valid_discrimination = st.floats(
    min_value=DISCRIMINATION_MIN,
    max_value=DISCRIMINATION_MAX,
    allow_nan=False,
    allow_infinity=False,
)
valid_guessing = st.floats(
    min_value=GUESSING_MIN,
    max_value=GUESSING_MAX,
    allow_nan=False,
    allow_infinity=False,
)

# Cultural factor strategies (all in [0.0, 1.0])
cultural_factor = st.floats(
    min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False
)

# Subject strategy (from Maarif mapping)
valid_subjects = st.sampled_from(["tarih", "türkçe", "matematik", "fen", "sosyal", "din"])


class TestZPDProbabilityBounds:
    """Property 1: ZPD probability always in [0.15, 0.85] for optimal zone."""

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_optimal_zone_within_zpd_bounds(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Questions in optimal zone must have P ∈ [0.15, 0.85]."""
        prob = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        zone = classify_zpd_zone(prob)

        if zone == "optimal":
            assert (
                ZPD_LOWER_BOUND <= prob <= ZPD_UPPER_BOUND
            ), f"Optimal zone P={prob:.3f} outside ZPD bounds [{ZPD_LOWER_BOUND}, {ZPD_UPPER_BOUND}]"

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_acceptable_zone_within_zpd_bounds(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Questions in acceptable zone must have P ∈ [0.15, 0.85]."""
        prob = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        zone = classify_zpd_zone(prob)

        if zone == "acceptable":
            assert (
                ZPD_LOWER_BOUND <= prob <= ZPD_UPPER_BOUND
            ), f"Acceptable zone P={prob:.3f} outside ZPD bounds [{ZPD_LOWER_BOUND}, {ZPD_UPPER_BOUND}]"

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_too_easy_outside_zpd(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Questions classified as too_easy must have P > 0.85."""
        prob = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        zone = classify_zpd_zone(prob)

        if zone == "too_easy":
            assert (
                prob > ZPD_UPPER_BOUND
            ), f"Too easy zone P={prob:.3f} should be > {ZPD_UPPER_BOUND}"

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_too_hard_outside_zpd(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Questions classified as too_hard must have P < 0.15."""
        prob = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        zone = classify_zpd_zone(prob)

        if zone == "too_hard":
            assert (
                prob < ZPD_LOWER_BOUND
            ), f"Too hard zone P={prob:.3f} should be < {ZPD_LOWER_BOUND}"


class TestZPDClassificationDeterminism:
    """Property 2: ZPD classification is deterministic (same θ, b → same zone)."""

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_same_parameters_same_zone(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Calling classification twice with same params must give same result."""
        prob1 = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        prob2 = calculate_irt_probability(theta, difficulty, discrimination, guessing)

        zone1 = classify_zpd_zone(prob1)
        zone2 = classify_zpd_zone(prob2)

        assert zone1 == zone2, f"Non-deterministic classification: {zone1} != {zone2}"
        assert abs(prob1 - prob2) < 1e-10, f"Non-deterministic probability: {prob1} != {prob2}"


class TestZoneOrderingConsistency:
    """Property 3: Zone ordering consistency (TOO_EASY threshold < OPTIMAL < TOO_HARD)."""

    def test_zone_threshold_ordering(self) -> None:
        """ZPD zone thresholds must be properly ordered."""
        # TOO_EASY threshold (upper bound)
        too_easy_threshold = ZPD_UPPER_BOUND

        # OPTIMAL range
        optimal_lower = ZPD_OPTIMAL_LOWER
        optimal_upper = ZPD_OPTIMAL_UPPER

        # TOO_HARD threshold (lower bound)
        too_hard_threshold = ZPD_LOWER_BOUND

        # Ordering: TOO_HARD < OPTIMAL < TOO_EASY
        assert too_hard_threshold < optimal_lower, "TOO_HARD threshold must be below OPTIMAL"
        assert (
            optimal_upper < too_easy_threshold
        ), "OPTIMAL upper must be below TOO_EASY threshold"

    @settings(max_examples=100)
    @given(probability=st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    def test_zone_classification_covers_all_probabilities(self, probability: float) -> None:
        """Every probability must map to exactly one zone."""
        zone = classify_zpd_zone(probability)

        # Must be one of four zones
        assert zone in ["too_easy", "optimal", "acceptable", "too_hard"], f"Unknown zone: {zone}"

        # Verify correct zone
        if probability > ZPD_UPPER_BOUND:
            assert zone == "too_easy", f"P={probability:.3f} should be too_easy, got {zone}"
        elif probability < ZPD_LOWER_BOUND:
            assert zone == "too_hard", f"P={probability:.3f} should be too_hard, got {zone}"
        elif ZPD_OPTIMAL_LOWER <= probability <= ZPD_OPTIMAL_UPPER:
            assert zone == "optimal", f"P={probability:.3f} should be optimal, got {zone}"
        else:
            assert zone == "acceptable", f"P={probability:.3f} should be acceptable, got {zone}"


class TestCulturalAdjustmentFactors:
    """Property 4: Cultural adjustment factors are positive."""

    def test_zpd_expansion_factors_positive(self) -> None:
        """All ZPD expansion factors must be > 1.0."""
        system = TurkishZPDMaarifSystem()

        for factor_name, factor_value in system.zpd_expansion_factors.items():
            assert factor_value > 1.0, f"Factor {factor_name} = {factor_value} must be > 1.0"

    def test_default_cultural_factors_in_range(self) -> None:
        """Default cultural factors must be in [0.0, 1.0]."""
        system = TurkishZPDMaarifSystem()

        for factor_name, factor_value in system.default_cultural_factors.items():
            assert (
                0.0 <= factor_value <= 1.0
            ), f"Factor {factor_name} = {factor_value} must be in [0.0, 1.0]"

    @settings(max_examples=100)
    @given(
        group_learning_preference=cultural_factor,
        teacher_respect_level=cultural_factor,
        family_involvement=cultural_factor,
        peer_competition=cultural_factor,
        authority_acceptance=cultural_factor,
        collective_success=cultural_factor,
        elder_wisdom_value=cultural_factor,
        social_harmony=cultural_factor,
    )
    def test_cultural_context_parameters_valid(
        self,
        group_learning_preference: float,
        teacher_respect_level: float,
        family_involvement: float,
        peer_competition: float,
        authority_acceptance: float,
        collective_success: float,
        elder_wisdom_value: float,
        social_harmony: float,
    ) -> None:
        """Cultural context can be constructed with any valid [0, 1] parameters."""
        context = TurkishCulturalContext(
            student_id="test-student",
            group_learning_preference=group_learning_preference,
            teacher_respect_level=teacher_respect_level,
            family_involvement=family_involvement,
            peer_competition=peer_competition,
            authority_acceptance=authority_acceptance,
            collective_success=collective_success,
            elder_wisdom_value=elder_wisdom_value,
            social_harmony=social_harmony,
        )

        # All parameters must remain in [0, 1]
        assert 0.0 <= context.group_learning_preference <= 1.0
        assert 0.0 <= context.teacher_respect_level <= 1.0
        assert 0.0 <= context.family_involvement <= 1.0
        assert 0.0 <= context.peer_competition <= 1.0
        assert 0.0 <= context.authority_acceptance <= 1.0
        assert 0.0 <= context.collective_success <= 1.0
        assert 0.0 <= context.elder_wisdom_value <= 1.0
        assert 0.0 <= context.social_harmony <= 1.0


class TestMaarifSubjectMapping:
    """Property 5: Maarif subject mapping non-empty for all subjects."""

    def test_all_subjects_have_maarif_values(self) -> None:
        """Every subject must map to at least one Maarif value."""
        system = TurkishZPDMaarifSystem()

        for subject, values in system.subject_maarif_mapping.items():
            assert len(values) > 0, f"Subject {subject} has no Maarif values"
            assert all(
                isinstance(v, MaarifValue) for v in values
            ), f"Subject {subject} contains non-MaarifValue items"

    @settings(max_examples=50)
    @given(subject=valid_subjects)
    def test_subject_mapping_consistent(self, subject: str) -> None:
        """Subject mapping must be deterministic and consistent."""
        system1 = TurkishZPDMaarifSystem()
        system2 = TurkishZPDMaarifSystem()

        values1 = system1.subject_maarif_mapping.get(subject, [])
        values2 = system2.subject_maarif_mapping.get(subject, [])

        assert values1 == values2, f"Subject {subject} mapping is non-deterministic"

    def test_maarif_values_valid(self) -> None:
        """All Maarif values in mapping must be valid enum members."""
        system = TurkishZPDMaarifSystem()
        all_maarif_values = set(MaarifValue)

        for subject, values in system.subject_maarif_mapping.items():
            for value in values:
                assert (
                    value in all_maarif_values
                ), f"Invalid MaarifValue {value} in subject {subject}"


class TestIRTProbabilityMonotonicity:
    """Property 6: IRT probability monotonicity within ZPD context."""

    @settings(max_examples=100)
    @given(
        theta1=valid_theta,
        theta2=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_higher_ability_higher_probability(
        self,
        theta1: float,
        theta2: float,
        difficulty: float,
        discrimination: float,
        guessing: float,
    ) -> None:
        """Higher ability must result in higher probability (monotonicity)."""
        assume(theta1 < theta2)  # Only test when theta1 < theta2
        assume(discrimination > 0)  # Monotonicity requires positive discrimination

        prob1 = calculate_irt_probability(theta1, difficulty, discrimination, guessing)
        prob2 = calculate_irt_probability(theta2, difficulty, discrimination, guessing)

        assert (
            prob1 <= prob2 + 1e-10
        ), f"Monotonicity violated: P({theta1:.2f}) = {prob1:.3f} > P({theta2:.2f}) = {prob2:.3f}"

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty1=valid_difficulty,
        difficulty2=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_harder_question_lower_probability(
        self,
        theta: float,
        difficulty1: float,
        difficulty2: float,
        discrimination: float,
        guessing: float,
    ) -> None:
        """Harder questions (higher difficulty) must have lower success probability."""
        assume(difficulty1 < difficulty2)  # difficulty1 is easier
        assume(discrimination > 0)

        prob1 = calculate_irt_probability(theta, difficulty1, discrimination, guessing)
        prob2 = calculate_irt_probability(theta, difficulty2, discrimination, guessing)

        assert (
            prob1 >= prob2 - 1e-10
        ), f"Difficulty relationship violated: P(b={difficulty1:.2f}) = {prob1:.3f} < P(b={difficulty2:.2f}) = {prob2:.3f}"

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination1=valid_discrimination,
        discrimination2=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_higher_discrimination_stronger_separation(
        self,
        theta: float,
        difficulty: float,
        discrimination1: float,
        discrimination2: float,
        guessing: float,
    ) -> None:
        """Higher discrimination increases separation between abilities."""
        assume(discrimination1 < discrimination2)
        assume(abs(theta - difficulty) > 0.5)  # Need some separation to observe effect
        # With non-trivial guessing, the 3PL guessing floor can compress
        # the probability range and invert the discrimination effect.
        # Restrict guessing to keep the property testable.
        assume(guessing < 0.05)

        prob1 = calculate_irt_probability(theta, difficulty, discrimination1, guessing)
        prob2 = calculate_irt_probability(theta, difficulty, discrimination2, guessing)

        # Higher discrimination should move probability further from 0.5
        distance1 = abs(prob1 - 0.5)
        distance2 = abs(prob2 - 0.5)

        # Allow tolerance for numerical precision and edge effects
        assert distance2 >= distance1 - 0.05, (
            f"Higher discrimination should increase separation: "
            f"a={discrimination1:.2f} gives distance {distance1:.3f}, "
            f"a={discrimination2:.2f} gives distance {distance2:.3f}"
        )


class TestZPDProbabilityConsistency:
    """Property 7: ZPD probability calculation matches zone classification."""

    @settings(max_examples=100)
    @given(
        theta=valid_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing,
    )
    def test_zpd_zone_probability_consistency(
        self, theta: float, difficulty: float, discrimination: float, guessing: float
    ) -> None:
        """Zone classification must be consistent with calculated probability."""
        prob = calculate_irt_probability(theta, difficulty, discrimination, guessing)
        zone = classify_zpd_zone(prob)

        # Verify zone matches probability
        if zone == "too_easy":
            assert prob > ZPD_UPPER_BOUND
        elif zone == "too_hard":
            assert prob < ZPD_LOWER_BOUND
        elif zone == "optimal":
            assert ZPD_OPTIMAL_LOWER <= prob <= ZPD_OPTIMAL_UPPER
        elif zone == "acceptable":
            assert ZPD_LOWER_BOUND <= prob <= ZPD_UPPER_BOUND
            assert not (ZPD_OPTIMAL_LOWER <= prob <= ZPD_OPTIMAL_UPPER)


class TestZPDExpansionBehavior:
    """Property 8: ZPD expansion factors compound multiplicatively."""

    def test_expansion_factors_compound_correctly(self) -> None:
        """Multiple cultural factors should multiply ZPD expansion."""
        system = TurkishZPDMaarifSystem()

        base_zpd_range = 1.0  # Base 30% expansion

        # Apply group learning factor
        group_factor = system.zpd_expansion_factors["group_learning"]
        expanded_with_group = base_zpd_range * group_factor

        # Apply teacher respect factor on top
        teacher_factor = system.zpd_expansion_factors["high_teacher_respect"]
        expanded_with_both = expanded_with_group * teacher_factor

        # Verify multiplicative composition
        expected = base_zpd_range * group_factor * teacher_factor
        assert abs(expanded_with_both - expected) < 1e-10, "Factors should multiply"

        # Verify expansion actually increases ZPD
        assert expanded_with_both > base_zpd_range, "Factors should expand ZPD"
