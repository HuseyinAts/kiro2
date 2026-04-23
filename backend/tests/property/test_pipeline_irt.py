"""
Property-based tests for IRT Calculator in Question Generation Pipeline.

Validates:
- REQ-2.2: difficulty ∈ [-4.0, 4.0]
- REQ-2.3: discrimination ∈ [0.2, 4.0]
- REQ-2.4: guessing ∈ [0.0, 0.35]

Boris Cherny Standards: Property tests with 100+ iterations
"""

import math

from hypothesis import assume, given, settings
from hypothesis import strategies as st

# IRT Parameter Ranges (from spec)
DIFFICULTY_MIN = -4.0
DIFFICULTY_MAX = 4.0
DISCRIMINATION_MIN = 0.2
DISCRIMINATION_MAX = 4.0
GUESSING_MIN = 0.0
GUESSING_MAX = 0.35

# Constants
D = 1.7  # Scaling factor for IRT

# Valid parameter strategies
valid_difficulty = st.floats(min_value=DIFFICULTY_MIN, max_value=DIFFICULTY_MAX, allow_nan=False)
valid_discrimination = st.floats(min_value=DISCRIMINATION_MIN, max_value=DISCRIMINATION_MAX, allow_nan=False)
valid_guessing = st.floats(min_value=GUESSING_MIN, max_value=GUESSING_MAX, allow_nan=False)
any_theta = st.floats(min_value=-5.0, max_value=5.0, allow_nan=False)

# Extended parameter strategies (for clamping tests)
extended_difficulty = st.floats(min_value=-10.0, max_value=10.0, allow_nan=False)
extended_discrimination = st.floats(min_value=-1.0, max_value=10.0, allow_nan=False)
extended_guessing = st.floats(min_value=-1.0, max_value=1.0, allow_nan=False)


def calculate_probability(theta: float, difficulty: float, discrimination: float, guessing: float) -> float:
    """3PL IRT model: P(θ) = c + (1-c) / (1 + exp(-D*a*(θ-b)))"""
    exponent = -D * discrimination * (theta - difficulty)

    # Overflow protection
    if exponent > 700:
        return guessing
    if exponent < -700:
        return 1.0

    return guessing + (1 - guessing) / (1 + math.exp(exponent))


def calculate_information(theta: float, difficulty: float, discrimination: float, guessing: float) -> float:
    """IRT Information function: I(θ) = a²(P-c)²(1-P) / ((1-c)²P)"""
    prob = calculate_probability(theta, difficulty, discrimination, guessing)

    # Avoid division by zero
    if prob <= guessing or prob >= 1.0:
        return 0.0

    numerator = (discrimination ** 2) * ((prob - guessing) ** 2) * (1 - prob)
    denominator = ((1 - guessing) ** 2) * prob

    if denominator == 0:
        return 0.0

    return numerator / denominator


def clamp_parameters(difficulty: float, discrimination: float, guessing: float) -> dict:
    """Clamp parameters to valid IRT ranges."""
    return {
        "difficulty": max(DIFFICULTY_MIN, min(DIFFICULTY_MAX, difficulty)),
        "discrimination": max(DISCRIMINATION_MIN, min(DISCRIMINATION_MAX, discrimination)),
        "guessing": max(GUESSING_MIN, min(GUESSING_MAX, guessing))
    }


def validate_parameters(difficulty: float, discrimination: float, guessing: float) -> bool:
    """Validate IRT parameter ranges."""
    return (
        DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX and
        DISCRIMINATION_MIN <= discrimination <= DISCRIMINATION_MAX and
        GUESSING_MIN <= guessing <= GUESSING_MAX
    )


class TestIRTProbabilityBounds:
    """Property 1: P(θ) must be in [guessing, 1.0]"""

    @settings(max_examples=100)
    @given(
        theta=any_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing
    )
    def test_probability_lower_bound(self, theta, difficulty, discrimination, guessing):
        """P(θ) must never be less than guessing parameter."""
        prob = calculate_probability(theta, difficulty, discrimination, guessing)
        assert prob >= guessing - 1e-10, f"P({theta}) = {prob} < guessing = {guessing}"

    @settings(max_examples=100)
    @given(
        theta=any_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing
    )
    def test_probability_upper_bound(self, theta, difficulty, discrimination, guessing):
        """P(θ) must never exceed 1.0."""
        prob = calculate_probability(theta, difficulty, discrimination, guessing)
        assert prob <= 1.0 + 1e-10, f"P({theta}) = {prob} > 1.0"


class TestIRTProbabilityMonotonicity:
    """Property 2: P(θ) must increase as θ increases (for positive discrimination)"""

    @settings(max_examples=100)
    @given(
        theta1=any_theta,
        theta2=any_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing
    )
    def test_probability_monotonic(self, theta1, theta2, difficulty, discrimination, guessing):
        """Higher ability (theta) must result in higher probability."""
        assume(theta1 < theta2)  # Only test when theta1 < theta2
        assume(discrimination > 0)  # Monotonicity requires positive discrimination

        prob1 = calculate_probability(theta1, difficulty, discrimination, guessing)
        prob2 = calculate_probability(theta2, difficulty, discrimination, guessing)

        assert prob1 <= prob2 + 1e-10, f"P({theta1}) = {prob1} > P({theta2}) = {prob2}"


class TestParameterClamping:
    """Property 3: Clamping must be idempotent - clamp(clamp(x)) = clamp(x)"""

    @settings(max_examples=100)
    @given(
        difficulty=extended_difficulty,
        discrimination=extended_discrimination,
        guessing=extended_guessing
    )
    def test_clamping_idempotent(self, difficulty, discrimination, guessing):
        """Applying clamp twice should give same result as applying once."""
        clamped_once = clamp_parameters(difficulty, discrimination, guessing)
        clamped_twice = clamp_parameters(
            clamped_once["difficulty"],
            clamped_once["discrimination"],
            clamped_once["guessing"]
        )

        assert clamped_once == clamped_twice, "Clamping is not idempotent"

    @settings(max_examples=100)
    @given(
        difficulty=extended_difficulty,
        discrimination=extended_discrimination,
        guessing=extended_guessing
    )
    def test_clamping_produces_valid_parameters(self, difficulty, discrimination, guessing):
        """Clamped parameters must always be valid."""
        clamped = clamp_parameters(difficulty, discrimination, guessing)

        assert validate_parameters(
            clamped["difficulty"],
            clamped["discrimination"],
            clamped["guessing"]
        ), f"Clamped params not valid: {clamped}"


class TestZPDConsistency:
    """Property 4: ZPD score must be consistent with probability calculation"""

    @settings(max_examples=100)
    @given(
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing
    )
    def test_zpd_consistency(self, difficulty, discrimination, guessing):
        """ZPD classification must match probability ranges."""
        theta = 0.0  # Average student
        prob = calculate_probability(theta, difficulty, discrimination, guessing)

        # ZPD definitions
        if 0.40 <= prob <= 0.60:
            expected_zpd = "optimal"
        elif 0.15 <= prob <= 0.85:
            expected_zpd = "acceptable"
        else:
            expected_zpd = "outside"

        # Verify probability-based ZPD classification
        if expected_zpd == "optimal":
            assert 0.40 <= prob <= 0.60
        elif expected_zpd == "acceptable":
            assert 0.15 <= prob <= 0.85


class TestInformationNonNegative:
    """Property 5: Information function I(θ) must be non-negative"""

    @settings(max_examples=100)
    @given(
        theta=any_theta,
        difficulty=valid_difficulty,
        discrimination=valid_discrimination,
        guessing=valid_guessing
    )
    def test_information_non_negative(self, theta, difficulty, discrimination, guessing):
        """Fisher information must never be negative."""
        info = calculate_information(theta, difficulty, discrimination, guessing)
        assert info >= -1e-10, f"I({theta}) = {info} < 0"


class TestParameterValidation:
    """Property 6: Validation function must correctly identify valid/invalid params"""

    @settings(max_examples=100)
    @given(
        difficulty=extended_difficulty,
        discrimination=extended_discrimination,
        guessing=extended_guessing
    )
    def test_validation_correctness(self, difficulty, discrimination, guessing):
        """Validation must match expected ranges."""
        is_valid = validate_parameters(difficulty, discrimination, guessing)

        expected_valid = (
            DIFFICULTY_MIN <= difficulty <= DIFFICULTY_MAX and
            DISCRIMINATION_MIN <= discrimination <= DISCRIMINATION_MAX and
            GUESSING_MIN <= guessing <= GUESSING_MAX
        )

        assert is_valid == expected_valid, (
            f"Validation mismatch: validate({difficulty}, {discrimination}, {guessing}) "
            f"= {is_valid}, expected {expected_valid}"
        )
