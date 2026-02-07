"""
Property-based tests for Weighted Scoring in Question Generation Pipeline.

Validates:
- REQ-6.3: Weighted average calculation (Content 25%, Difficulty 20%, Distractor 20%, Compliance 20%, Language 15%)

Boris Cherny Standards: Property tests with 100+ iterations
"""

from hypothesis import given, strategies as st, settings, assume
from typing import Dict

# Stage weights from spec (sum = 1.0)
STAGE_WEIGHTS = {
    "content_generator": 0.25,
    "difficulty_calibration": 0.20,
    "distractor_generator": 0.20,
    "osym_compliance": 0.20,
    "language_qa": 0.15
}

# Valid score strategy
valid_score = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


def calculate_weighted_score(stage_scores: Dict[str, float]) -> float:
    """
    Calculate weighted average of stage scores.

    Formula: final_score = Σ(score_i × weight_i) / Σ(weight_i)
    """
    total_score = 0.0
    total_weight = 0.0

    for stage_name, score in stage_scores.items():
        weight = STAGE_WEIGHTS.get(stage_name, 0.0)
        total_score += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(total_score / total_weight, 4)


class TestWeightedScoreRange:
    """Property 1: Final score must be in [0.0, 1.0]"""

    @settings(max_examples=100)
    @given(
        content_score=valid_score,
        difficulty_score=valid_score,
        distractor_score=valid_score,
        compliance_score=valid_score,
        language_score=valid_score
    )
    def test_final_score_in_valid_range(
        self, content_score, difficulty_score, distractor_score, compliance_score, language_score
    ):
        """Final weighted score must always be between 0 and 1."""
        scores = {
            "content_generator": content_score,
            "difficulty_calibration": difficulty_score,
            "distractor_generator": distractor_score,
            "osym_compliance": compliance_score,
            "language_qa": language_score
        }

        final_score = calculate_weighted_score(scores)

        assert 0.0 <= final_score <= 1.0, f"Final score {final_score} not in [0, 1]"

    @settings(max_examples=100)
    @given(
        content_score=valid_score,
        difficulty_score=valid_score
    )
    def test_partial_scores_in_valid_range(self, content_score, difficulty_score):
        """Partial stage scores must also produce valid final score."""
        scores = {
            "content_generator": content_score,
            "difficulty_calibration": difficulty_score
        }

        final_score = calculate_weighted_score(scores)

        assert 0.0 <= final_score <= 1.0, f"Final score {final_score} not in [0, 1]"


class TestWeightedScoreWeightsSum:
    """Property 2: Weights must be properly normalized"""

    def test_weights_sum_to_one(self):
        """Stage weights must sum to 1.0."""
        total_weight = sum(STAGE_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 1e-10, f"Weights sum to {total_weight}, expected 1.0"

    @settings(max_examples=100)
    @given(uniform_score=valid_score)
    def test_uniform_scores_equal_final(self, uniform_score):
        """If all stage scores are equal, final score equals that score."""
        scores = {stage: uniform_score for stage in STAGE_WEIGHTS.keys()}

        final_score = calculate_weighted_score(scores)

        assert abs(final_score - uniform_score) < 1e-3, (
            f"Uniform scores {uniform_score} produced final score {final_score}"
        )


class TestMissingStagesHandled:
    """Property 3: Missing stages must not cause errors"""

    def test_empty_scores(self):
        """Empty scores dict should return 0."""
        final_score = calculate_weighted_score({})
        assert final_score == 0.0, f"Empty scores produced {final_score}"

    @settings(max_examples=100)
    @given(score=valid_score)
    def test_single_stage(self, score):
        """Single stage score should still produce valid result."""
        scores = {"content_generator": score}

        final_score = calculate_weighted_score(scores)

        assert 0.0 <= final_score <= 1.0, f"Single stage score {score} produced {final_score}"

    @settings(max_examples=100)
    @given(
        content_score=valid_score,
        unknown_score=valid_score
    )
    def test_unknown_stages_ignored(self, content_score, unknown_score):
        """Unknown stage names should be ignored (weight=0)."""
        scores = {
            "content_generator": content_score,
            "unknown_stage": unknown_score
        }

        final_score = calculate_weighted_score(scores)

        # Should only consider content_generator
        expected = content_score  # Since it's the only valid stage with weight
        assert abs(final_score - expected) < 1e-3, (
            f"Unknown stage affected score: expected {expected}, got {final_score}"
        )


class TestStageScoreContribution:
    """Property 4: Each stage must contribute according to its weight"""

    @settings(max_examples=100)
    @given(
        content_score=valid_score,
        difficulty_score=valid_score,
        distractor_score=valid_score,
        compliance_score=valid_score,
        language_score=valid_score
    )
    def test_weighted_contribution(
        self, content_score, difficulty_score, distractor_score, compliance_score, language_score
    ):
        """Final score must be weighted average of stage scores."""
        scores = {
            "content_generator": content_score,
            "difficulty_calibration": difficulty_score,
            "distractor_generator": distractor_score,
            "osym_compliance": compliance_score,
            "language_qa": language_score
        }

        final_score = calculate_weighted_score(scores)

        # Manual calculation
        expected = (
            content_score * 0.25 +
            difficulty_score * 0.20 +
            distractor_score * 0.20 +
            compliance_score * 0.20 +
            language_score * 0.15
        )

        assert abs(final_score - expected) < 1e-3, (
            f"Weighted average mismatch: expected {expected}, got {final_score}"
        )

    @settings(max_examples=100)
    @given(high_score=valid_score, low_score=valid_score)
    def test_higher_weight_more_impact(self, high_score, low_score):
        """Higher weighted stage should have more impact on final score."""
        assume(high_score > low_score + 0.1)  # Ensure meaningful difference

        # Content (25%) vs Language (15%)
        scores_content_high = {
            "content_generator": high_score,
            "language_qa": low_score
        }
        scores_content_low = {
            "content_generator": low_score,
            "language_qa": high_score
        }

        final_content_high = calculate_weighted_score(scores_content_high)
        final_content_low = calculate_weighted_score(scores_content_low)

        # Higher weight on high score should produce higher final
        assert final_content_high > final_content_low, (
            "Content (25%) with high score didn't beat Language (15%) with high score"
        )
