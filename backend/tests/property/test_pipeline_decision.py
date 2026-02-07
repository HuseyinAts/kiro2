"""
Property-based tests for Decision Threshold Logic in Question Generation Pipeline.

Validates:
- REQ-6.4: score >= 0.85 → "approved"
- REQ-6.5: 0.70 <= score < 0.85 → "review"
- REQ-6.6: score < 0.70 → "rejected"

Boris Cherny Standards: Property tests with 100+ iterations
"""

from hypothesis import given, strategies as st, settings, assume
from typing import Literal

# Decision Thresholds from spec
APPROVAL_THRESHOLD = 0.85
REVIEW_THRESHOLD = 0.70

# Decision type
Decision = Literal["approved", "review", "rejected"]

# Score strategies for specific ranges
approved_score = st.floats(min_value=0.85, max_value=1.0, allow_nan=False)
review_score = st.floats(min_value=0.70, max_value=0.8499999, allow_nan=False)
rejected_score = st.floats(min_value=0.0, max_value=0.6999999, allow_nan=False)
any_score = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


def make_decision(score: float) -> Decision:
    """
    Make quality decision based on final score.

    Thresholds:
    - >= 0.85: approved
    - 0.70 - 0.84: review
    - < 0.70: rejected
    """
    if score >= APPROVAL_THRESHOLD:
        return "approved"
    elif score >= REVIEW_THRESHOLD:
        return "review"
    else:
        return "rejected"


def decision_to_rank(decision: Decision) -> int:
    """Convert decision to numeric rank for comparison."""
    ranks = {"rejected": 0, "review": 1, "approved": 2}
    return ranks[decision]


class TestDecisionThresholdApproved:
    """Property 1: score >= 0.85 must always result in 'approved'"""

    @settings(max_examples=100)
    @given(score=approved_score)
    def test_high_score_approved(self, score):
        """Scores >= 0.85 must be approved."""
        decision = make_decision(score)
        assert decision == "approved", f"Score {score} should be approved, got {decision}"

    def test_exact_threshold(self):
        """Exactly 0.85 must be approved."""
        decision = make_decision(0.85)
        assert decision == "approved", "0.85 should be approved"

    def test_perfect_score(self):
        """Perfect score (1.0) must be approved."""
        decision = make_decision(1.0)
        assert decision == "approved", "1.0 should be approved"


class TestDecisionThresholdReview:
    """Property 2: 0.70 <= score < 0.85 must always result in 'review'"""

    @settings(max_examples=100)
    @given(score=review_score)
    def test_mid_score_review(self, score):
        """Scores in [0.70, 0.85) must need review."""
        decision = make_decision(score)
        assert decision == "review", f"Score {score} should need review, got {decision}"

    def test_exact_lower_threshold(self):
        """Exactly 0.70 must be review."""
        decision = make_decision(0.70)
        assert decision == "review", "0.70 should be review"

    def test_just_below_approval(self):
        """Score just below approval must be review."""
        decision = make_decision(0.8499)
        assert decision == "review", "0.8499 should be review"


class TestDecisionThresholdRejected:
    """Property 3: score < 0.70 must always result in 'rejected'"""

    @settings(max_examples=100)
    @given(score=rejected_score)
    def test_low_score_rejected(self, score):
        """Scores < 0.70 must be rejected."""
        decision = make_decision(score)
        assert decision == "rejected", f"Score {score} should be rejected, got {decision}"

    def test_zero_score(self):
        """Zero score must be rejected."""
        decision = make_decision(0.0)
        assert decision == "rejected", "0.0 should be rejected"

    def test_just_below_review(self):
        """Score just below review threshold must be rejected."""
        decision = make_decision(0.6999)
        assert decision == "rejected", "0.6999 should be rejected"


class TestDecisionMonotonicity:
    """Property 4: Higher score must result in same or better decision"""

    @settings(max_examples=100)
    @given(score1=any_score, score2=any_score)
    def test_decision_improves_with_score(self, score1, score2):
        """Higher scores must not result in worse decisions."""
        assume(score1 < score2)  # Only test when score1 < score2

        decision1 = make_decision(score1)
        decision2 = make_decision(score2)

        rank1 = decision_to_rank(decision1)
        rank2 = decision_to_rank(decision2)

        assert rank2 >= rank1, (
            f"Score {score2} ({decision2}) should not be worse than "
            f"score {score1} ({decision1})"
        )

    @settings(max_examples=100)
    @given(score=any_score, delta=st.floats(min_value=0.01, max_value=0.5, allow_nan=False))
    def test_increasing_score_doesnt_worsen(self, score, delta):
        """Increasing score must not worsen decision."""
        assume(score + delta <= 1.0)

        decision_before = make_decision(score)
        decision_after = make_decision(score + delta)

        rank_before = decision_to_rank(decision_before)
        rank_after = decision_to_rank(decision_after)

        assert rank_after >= rank_before, (
            f"Increasing score from {score} to {score + delta} "
            f"worsened decision from {decision_before} to {decision_after}"
        )


class TestDecisionBoundaryTransitions:
    """Property 5: Boundary transitions must be correct"""

    def test_rejection_to_review_boundary(self):
        """Verify transition at 0.70 boundary."""
        assert make_decision(0.699) == "rejected"
        assert make_decision(0.70) == "review"
        assert make_decision(0.701) == "review"

    def test_review_to_approval_boundary(self):
        """Verify transition at 0.85 boundary."""
        assert make_decision(0.849) == "review"
        assert make_decision(0.85) == "approved"
        assert make_decision(0.851) == "approved"

    @settings(max_examples=100)
    @given(epsilon=st.floats(min_value=1e-6, max_value=0.01, allow_nan=False))
    def test_epsilon_above_rejection_threshold(self, epsilon):
        """Just above rejection threshold must be review."""
        score = REVIEW_THRESHOLD + epsilon
        if score < APPROVAL_THRESHOLD:
            decision = make_decision(score)
            assert decision == "review", f"Score {score} should be review"

    @settings(max_examples=100)
    @given(epsilon=st.floats(min_value=1e-6, max_value=0.01, allow_nan=False))
    def test_epsilon_above_review_threshold(self, epsilon):
        """Just above review threshold must be approved."""
        score = APPROVAL_THRESHOLD + epsilon
        if score <= 1.0:
            decision = make_decision(score)
            assert decision == "approved", f"Score {score} should be approved"
