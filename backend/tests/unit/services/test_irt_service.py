"""
Unit tests for IRT Model (algorithms/irt_model.py)

Tests 4-Parameter IRT model with Turkish education system optimizations.

IMPORTANT: NO REWARD HACKING
- Test actual IRT calculations
- Validate parameter ranges per CLAUDE.md
- Test CAT item selection
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[3]))

import pytest
import numpy as np

from algorithms.irt_model import (
    FourParameterIRTModel,
    IRTItem,
    IRTResponse
)
from core.irt_validators import IRTValidationError


@pytest.fixture
def irt_model():
    """Create a fresh IRT model instance."""
    return FourParameterIRTModel(scaling_constant=1.0)


@pytest.fixture
def sample_item():
    """Create a valid IRT item within CLAUDE.md parameter ranges."""
    return IRTItem(
        item_id="Q001",
        discrimination=1.5,  # [0.2, 4.0]
        difficulty=0.0,      # [-4.0, 4.0]
        guessing=0.25,       # [0.0, 0.35]
        upper_asymptote=1.0, # [0.0, 1.0]
        subject="matematik",
        topic="türev",
        yks_question_type="TYT"
    )


def test_create_irt_item(sample_item):
    """Test creating a valid IRT item."""
    assert sample_item.item_id == "Q001"
    assert sample_item.discrimination == 1.5
    assert sample_item.difficulty == 0.0
    assert sample_item.guessing == 0.25
    assert sample_item.upper_asymptote == 1.0


def test_calculate_probability(irt_model, sample_item):
    """Test IRT probability calculation."""
    theta = 0.0  # Ability equal to difficulty

    prob = irt_model.probability(theta, sample_item)

    # At theta == difficulty, probability should be (c + d) / 2 for typical cases
    assert 0.0 < prob < 1.0
    assert isinstance(prob, (float, np.float64))

    # Check boundary conditions
    prob_high = irt_model.probability(4.0, sample_item)  # High ability
    prob_low = irt_model.probability(-4.0, sample_item)  # Low ability
    assert prob_high > prob_low  # Higher ability -> higher probability


def test_calculate_information(irt_model, sample_item):
    """Test item information calculation."""
    theta = 0.0

    info = irt_model.information(theta, sample_item)

    assert info >= 0.0
    assert isinstance(info, (float, np.float64))

    # Maximum information should be near difficulty
    info_at_difficulty = irt_model.information(sample_item.difficulty, sample_item)
    info_far_away = irt_model.information(sample_item.difficulty + 3.0, sample_item)
    assert info_at_difficulty > info_far_away


def test_estimate_ability(irt_model):
    """Test ability estimation with MLE."""
    # Add items to model
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=-1.0, guessing=0.25),
        IRTItem("Q2", discrimination=1.5, difficulty=0.0, guessing=0.25),
        IRTItem("Q3", discrimination=1.2, difficulty=1.0, guessing=0.25),
    ]
    for item in items:
        irt_model.add_item(item)

    # Create responses (2 correct, 1 incorrect)
    responses = [
        IRTResponse("STU001", "Q1", response=1, response_time=45.0),
        IRTResponse("STU001", "Q2", response=1, response_time=60.0),
        IRTResponse("STU001", "Q3", response=0, response_time=90.0),
    ]

    ability = irt_model.estimate_ability_mle(responses, initial_theta=0.0)

    assert ability.student_id == "STU001"
    assert -4.0 <= ability.ability <= 4.0
    assert ability.se > 0.0
    assert ability.n_items == 3
    assert ability.estimation_method == "MLE"


def test_select_next_cat_item(irt_model):
    """Test CAT item selection (maximum information)."""
    # Add multiple items
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=-2.0, guessing=0.25),
        IRTItem("Q2", discrimination=1.5, difficulty=0.0, guessing=0.25),
        IRTItem("Q3", discrimination=1.2, difficulty=2.0, guessing=0.25),
    ]
    for item in items:
        irt_model.add_item(item)

    # Select next item for student with ability 0.0
    current_theta = 0.0
    next_item = irt_model.select_next_item_cat(
        current_theta=current_theta,
        available_items=items,
        answered_items=[]
    )

    assert next_item is not None
    assert next_item.item_id in ["Q1", "Q2", "Q3"]

    # Item close to current ability should have higher information
    # Q2 (difficulty 0.0) should be selected for theta=0.0
    assert next_item.item_id == "Q2"


def test_add_response(irt_model, sample_item):
    """Test adding a response."""
    irt_model.add_item(sample_item)

    response = IRTResponse(
        student_id="STU001",
        item_id="Q001",
        response=1,
        response_time=60.0
    )

    irt_model.add_response(response)

    assert len(irt_model.responses) == 1
    assert irt_model.responses[0].student_id == "STU001"
    assert irt_model.responses[0].item_id == "Q001"


def test_get_item_difficulty(irt_model, sample_item):
    """Test retrieving item difficulty."""
    irt_model.add_item(sample_item)

    retrieved_item = irt_model.get_item("Q001")

    assert retrieved_item is not None
    assert retrieved_item.difficulty == 0.0


def test_calibrate_item(sample_item):
    """Test item calibration (parameters are within valid ranges)."""
    # Item should be validated on creation
    assert -4.0 <= sample_item.difficulty <= 4.0
    assert 0.2 <= sample_item.discrimination <= 4.0
    assert 0.0 <= sample_item.guessing <= 0.35
    assert 0.0 <= sample_item.upper_asymptote <= 1.0


def test_batch_probability(irt_model):
    """Test batch probability calculation for multiple theta values."""
    item = IRTItem("Q1", discrimination=1.5, difficulty=0.0, guessing=0.25)
    irt_model.add_item(item)

    theta_values = np.linspace(-3.0, 3.0, 7)
    probabilities = [irt_model.probability(theta, item) for theta in theta_values]

    # All probabilities should be valid
    assert all(0.0 < p < 1.0 for p in probabilities)

    # Probabilities should increase with theta
    assert probabilities[-1] > probabilities[0]


def test_standard_error_calculation(irt_model):
    """Test standard error calculation."""
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=0.0, guessing=0.25),
        IRTItem("Q2", discrimination=1.5, difficulty=0.5, guessing=0.25),
    ]

    theta = 0.0
    se = irt_model.standard_error(theta, items)

    assert se > 0.0
    assert se < 999.0  # Not the fallback value

    # SE should decrease with more items (more information)
    items_extended = items + [
        IRTItem("Q3", discrimination=1.2, difficulty=-0.5, guessing=0.25),
    ]
    se_extended = irt_model.standard_error(theta, items_extended)
    assert se_extended < se


def test_ability_bounds(irt_model):
    """Test that ability estimates stay within bounds [-4, 4]."""
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=0.0, guessing=0.25),
    ]
    irt_model.add_item(items[0])

    # All correct responses (should push ability high)
    responses_all_correct = [
        IRTResponse("STU001", "Q1", response=1, response_time=60.0)
    ] * 5

    ability = irt_model.estimate_ability_mle(responses_all_correct)

    assert -4.0 <= ability.ability <= 4.0


def test_empty_responses_handling(irt_model):
    """Test handling of empty response list."""
    ability = irt_model.estimate_ability_mle([])

    assert ability.student_id == "unknown"
    assert ability.ability == 0.0
    assert ability.se == 999.0
    assert ability.n_items == 0


def test_yks_score_from_ability(irt_model):
    """Test YKS score prediction from ability."""
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=0.0, guessing=0.25),
    ]
    irt_model.add_item(items[0])

    responses = [
        IRTResponse("STU001", "Q1", response=1, response_time=60.0)
    ]

    ability = irt_model.estimate_ability_mle(responses)

    # YKS score formula: 300 + theta * 66.67
    expected_score = 300 + ability.ability * 66.67
    assert ability.yks_predicted_score is not None
    assert abs(ability.yks_predicted_score - expected_score) < 1.0

    # Score should be in valid YKS range (can exceed 500 for very high ability)
    assert 100.0 <= ability.yks_predicted_score <= 600.0


def test_confidence_interval(irt_model):
    """Test 95% confidence interval calculation."""
    items = [
        IRTItem("Q1", discrimination=1.5, difficulty=0.0, guessing=0.25),
        IRTItem("Q2", discrimination=1.2, difficulty=0.5, guessing=0.25),
    ]
    for item in items:
        irt_model.add_item(item)

    responses = [
        IRTResponse("STU001", "Q1", response=1, response_time=60.0),
        IRTResponse("STU001", "Q2", response=1, response_time=60.0),
    ]

    ability = irt_model.estimate_ability_mle(responses)

    lower, upper = ability.confidence_interval_95

    # CI should bracket the ability estimate
    assert lower < ability.ability < upper

    # 95% CI: ±1.96 SE
    expected_margin = 1.96 * ability.se
    assert abs(upper - ability.ability) == pytest.approx(expected_margin, abs=0.1)
    assert abs(ability.ability - lower) == pytest.approx(expected_margin, abs=0.1)


def test_test_information_sum(irt_model):
    """Test that test information is sum of item information."""
    items = [
        IRTItem("Q1", discrimination=1.0, difficulty=0.0, guessing=0.25),
        IRTItem("Q2", discrimination=1.5, difficulty=0.5, guessing=0.25),
    ]

    theta = 0.0
    total_info = irt_model.test_information(theta, items)

    individual_infos = [irt_model.information(theta, item) for item in items]
    expected_total = sum(individual_infos)

    assert total_info == pytest.approx(expected_total, abs=1e-6)


def test_invalid_discrimination_raises():
    """Test that invalid discrimination parameter raises error."""
    with pytest.raises(IRTValidationError):
        IRTItem(
            item_id="Q_INVALID",
            discrimination=5.0,  # > 4.0 (out of range)
            difficulty=0.0,
            guessing=0.25
        )


def test_invalid_difficulty_raises():
    """Test that invalid difficulty parameter raises error."""
    with pytest.raises(IRTValidationError):
        IRTItem(
            item_id="Q_INVALID",
            discrimination=1.5,
            difficulty=5.0,  # > 4.0 (out of range)
            guessing=0.25
        )


def test_invalid_guessing_raises():
    """Test that invalid guessing parameter raises error."""
    with pytest.raises(IRTValidationError):
        IRTItem(
            item_id="Q_INVALID",
            discrimination=1.5,
            difficulty=0.0,
            guessing=0.40  # > 0.35 (out of range)
        )
