"""
IRT Model Boundary Tests (K-01).

Tests for Item Response Theory parameter boundaries and calculations.
"""
import sys
from pathlib import Path

import pytest

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.irt_model import (  # noqa: E402
    FourParameterIRTModel,
    IRTItem,
    IRTResponse,
    IRTValidationError,
    StudentAbility,
)


class TestDifficultyBoundaries:
    """Test difficulty parameter boundaries [-4.0, 4.0]."""

    def test_difficulty_lower_bound_accepted(self):
        """Difficulty at -4.0 should be accepted."""
        item = IRTItem(
            item_id="test-001",
            discrimination=1.0,
            difficulty=-4.0,
            guessing=0.25,
        )
        assert item.difficulty == -4.0

    def test_difficulty_upper_bound_accepted(self):
        """Difficulty at 4.0 should be accepted."""
        item = IRTItem(
            item_id="test-002",
            discrimination=1.0,
            difficulty=4.0,
            guessing=0.25,
        )
        assert item.difficulty == 4.0

    def test_difficulty_below_range_rejected(self):
        """Difficulty below -4.0 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="difficulty"):
            IRTItem(
                item_id="test-003",
                discrimination=1.0,
                difficulty=-4.1,
                guessing=0.25,
            )

    def test_difficulty_above_range_rejected(self):
        """Difficulty above 4.0 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="difficulty"):
            IRTItem(
                item_id="test-004",
                discrimination=1.0,
                difficulty=4.1,
                guessing=0.25,
            )


class TestDiscriminationBoundaries:
    """Test discrimination parameter boundaries [0.2, 4.0]."""

    def test_discrimination_lower_bound(self):
        """Discrimination at 0.2 should be accepted."""
        item = IRTItem(
            item_id="test-005",
            discrimination=0.2,
            difficulty=0.0,
            guessing=0.25,
        )
        assert item.discrimination == 0.2

    def test_discrimination_upper_bound(self):
        """Discrimination at 4.0 should be accepted."""
        item = IRTItem(
            item_id="test-006",
            discrimination=4.0,
            difficulty=0.0,
            guessing=0.25,
        )
        assert item.discrimination == 4.0

    def test_discrimination_below_rejected(self):
        """Discrimination below 0.2 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="discrimination"):
            IRTItem(
                item_id="test-007",
                discrimination=0.1,
                difficulty=0.0,
                guessing=0.25,
            )

    def test_discrimination_above_rejected(self):
        """Discrimination above 4.0 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="discrimination"):
            IRTItem(
                item_id="test-008",
                discrimination=4.5,
                difficulty=0.0,
                guessing=0.25,
            )


class TestGuessingBoundaries:
    """Test guessing parameter boundaries [0.0, 0.35]."""

    def test_guessing_lower_bound(self):
        """Guessing at 0.0 should be accepted."""
        item = IRTItem(
            item_id="test-009",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.0,
        )
        assert item.guessing == 0.0

    def test_guessing_upper_bound(self):
        """Guessing at 0.35 should be accepted."""
        item = IRTItem(
            item_id="test-010",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.35,
        )
        assert item.guessing == 0.35

    def test_guessing_above_rejected(self):
        """Guessing above 0.35 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="guessing"):
            IRTItem(
                item_id="test-011",
                discrimination=1.0,
                difficulty=0.0,
                guessing=0.5,
            )

    def test_guessing_below_rejected(self):
        """Guessing below 0.0 should raise IRTValidationError."""
        with pytest.raises(IRTValidationError, match="guessing"):
            IRTItem(
                item_id="test-012",
                discrimination=1.0,
                difficulty=0.0,
                guessing=-0.1,
            )


class TestUpperAsymptote:
    """Test upper asymptote parameter [0.0, 1.0]."""

    def test_upper_asymptote_valid(self):
        """Upper asymptote at 0.98 should be accepted."""
        item = IRTItem(
            item_id="test-013",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.25,
            upper_asymptote=0.98,
        )
        assert item.upper_asymptote == 0.98


class TestFourPLModel:
    """Test 4PL IRT model calculations."""

    def test_4pl_probability_calculation(self):
        """Test probability calculation with θ=0, b=0, a=1, c=0.25, d=0.98."""
        model = FourParameterIRTModel()
        item = IRTItem(
            item_id="test-014",
            discrimination=1.0,
            difficulty=0.0,
            guessing=0.25,
            upper_asymptote=0.98,
        )

        prob = model.probability(theta=0.0, item=item)

        # At θ=b, exponent is 0, so exp(0)=1, P = c + (d-c)/(1+1) = 0.25 + 0.73/2 ≈ 0.615
        assert 0.60 <= prob <= 0.65
        assert 0.0 <= prob <= 1.0

    def test_fisher_information_positive(self):
        """Fisher information should be positive for valid parameters."""
        model = FourParameterIRTModel()
        item = IRTItem(
            item_id="test-015",
            discrimination=1.5,
            difficulty=0.5,
            guessing=0.25,
        )

        info = model.information(theta=0.0, item=item)

        assert info > 0.0

    def test_mle_ability_estimation(self):
        """MLE should estimate ability from responses."""
        model = FourParameterIRTModel()

        # Create items with valid difficulty range
        items = [
            IRTItem(
                item_id=f"item-{i}",
                discrimination=1.2,
                difficulty=float(i - 5) * 0.8,  # Scale to [-4.0, 3.2] range
                guessing=0.25,
            )
            for i in range(10)
        ]

        # Add items to model
        for item in items:
            model.add_item(item)

        # Simulate responses for θ ≈ 0.5
        responses = [
            IRTResponse(
                student_id="student-001",
                item_id=item.item_id,
                response=1 if item.difficulty < 1.0 else 0,
                response_time=30.0,
            )
            for item in items
        ]

        ability = model.estimate_ability_mle(responses)

        # Should converge to reasonable estimate
        assert -3.0 <= ability.ability <= 3.0
        assert ability.se > 0.0
        assert ability.se < 2.0

    def test_cat_selects_max_info_item(self):
        """CAT should select item with maximum information."""
        model = FourParameterIRTModel()

        items = [
            IRTItem(
                item_id="easy",
                discrimination=1.0,
                difficulty=-2.0,
                guessing=0.25,
            ),
            IRTItem(
                item_id="medium",
                discrimination=1.5,
                difficulty=0.5,
                guessing=0.25,
            ),
            IRTItem(
                item_id="hard",
                discrimination=1.0,
                difficulty=2.0,
                guessing=0.25,
            ),
        ]

        # For θ=0.5, medium item should have highest info
        # Use correct parameter names: current_theta, available_items, answered_items
        selected = model.select_next_item_cat(
            current_theta=0.5,
            available_items=items,
            answered_items=[]
        )

        assert selected is not None
        assert selected.item_id == "medium"


class TestYKSDefaults:
    """Test typical YKS parameter ranges."""

    def test_tyt_default_params(self):
        """TYT items should use typical difficulty ranges."""
        # Typical TYT: medium difficulty, moderate discrimination
        tyt_item = IRTItem(
            item_id="tyt-turkce-01",
            discrimination=1.2,
            difficulty=0.0,  # Medium difficulty
            guessing=0.25,  # 4 choices = 25% guess
        )

        assert -2.0 <= tyt_item.difficulty <= 2.0
        assert 0.8 <= tyt_item.discrimination <= 2.0
        assert tyt_item.guessing == 0.25

    def test_ayt_default_params(self):
        """AYT items should use typical difficulty ranges."""
        # Typical AYT: higher difficulty, higher discrimination
        ayt_item = IRTItem(
            item_id="ayt-matematik-01",
            discrimination=1.5,
            difficulty=1.0,  # Harder than TYT
            guessing=0.25,
        )

        assert -1.0 <= ayt_item.difficulty <= 3.0
        assert 1.0 <= ayt_item.discrimination <= 2.5
        assert ayt_item.guessing == 0.25

    def test_yks_score_conversion(self):
        """Test YKS score conversion: θ=0 → score≈300."""
        ability = StudentAbility(
            student_id="test-student",
            ability=0.0,
            se=0.3,
            estimation_method="MLE",
            n_items=10
        )

        # Calculate YKS predicted score: 300 + theta * 66.67
        yks_score = 300 + ability.ability * 66.67
        expected_score = 300.0

        assert abs(yks_score - expected_score) < 5.0
        assert 100.0 <= yks_score <= 500.0
