"""
OSYM Scoring Tests (K-06).

Tests for ÖSYM (Turkish National Exam Board) scoring rules.
YKS (Yükseköğretim Kurumları Sınavı) uses: Net = Correct - (Wrong / 4)
"""
import sys
from pathlib import Path
from typing import Dict

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))


def calculate_net(correct: int, wrong: int, empty: int) -> float:
    """
    Calculate net score using ÖSYM formula.

    Args:
        correct: Number of correct answers.
        wrong: Number of wrong answers.
        empty: Number of empty answers (not answered).

    Returns:
        Net score: correct - (wrong / 4)
    """
    return correct - (wrong / 4.0)


def calculate_subject_net(correct: int, wrong: int, empty: int) -> float:
    """Calculate net score for a subject."""
    return calculate_net(correct, wrong, empty)


class TestTYTNetCalculation:
    """Test TYT (Basic Proficiency Test) net calculations."""

    def test_tyt_net_calculation(self):
        """TYT: 80 correct, 20 wrong, 20 empty → net = 75.0."""
        correct = 80
        wrong = 20
        empty = 20

        net = calculate_net(correct, wrong, empty)

        # Net = 80 - (20 / 4) = 80 - 5 = 75
        assert net == 75.0

        # Total questions
        total = correct + wrong + empty
        assert total == 120  # TYT has 120 questions


class TestAYTNetCalculation:
    """Test AYT (Field Proficiency Test) net calculations."""

    def test_ayt_net_calculation(self):
        """AYT: 40 correct, 10 wrong, 110 empty → net = 37.5."""
        correct = 40
        wrong = 10
        empty = 110

        net = calculate_net(correct, wrong, empty)

        # Net = 40 - (10 / 4) = 40 - 2.5 = 37.5
        assert net == 37.5


class TestNegativeNet:
    """Test negative net scores."""

    def test_negative_net_allowed(self):
        """0 correct, 120 wrong → net = -30.0."""
        correct = 0
        wrong = 120
        empty = 0

        net = calculate_net(correct, wrong, empty)

        # Net = 0 - (120 / 4) = -30
        assert net == -30.0


class TestEmptyAnswers:
    """Test empty (unanswered) questions."""

    def test_empty_answers_neutral(self):
        """Empty answers should not affect net score."""
        # All correct, some empty
        net1 = calculate_net(correct=40, wrong=0, empty=80)
        assert net1 == 40.0

        # All empty
        net2 = calculate_net(correct=0, wrong=0, empty=120)
        assert net2 == 0.0


class TestWrongAnswerPenalty:
    """Test wrong answer penalty (1/4 per wrong)."""

    def test_four_wrong_equals_one_right(self):
        """4 wrong answers reduce net by 1."""
        # 5 correct, 4 wrong
        net1 = calculate_net(correct=5, wrong=4, empty=0)
        assert net1 == 4.0  # 5 - 1 = 4

        # 5 correct, 0 wrong
        net2 = calculate_net(correct=5, wrong=0, empty=0)
        assert net2 == 5.0

        # Difference should be exactly 1
        assert net2 - net1 == 1.0


class TestSubjectNetCalculation:
    """Test net calculation per subject."""

    def test_subject_net_calculation(self):
        """Türkçe: 30 correct, 5 wrong, 5 empty → net = 28.75."""
        correct = 30
        wrong = 5
        empty = 5

        net = calculate_subject_net(correct, wrong, empty)

        # Net = 30 - (5 / 4) = 30 - 1.25 = 28.75
        assert net == 28.75

        # Total questions in Türkçe section
        total = correct + wrong + empty
        assert total == 40  # TYT Türkçe has 40 questions


class TestPerfectScore:
    """Test perfect scores (all correct)."""

    def test_all_correct_max_net(self):
        """All correct → net = number of questions."""
        # TYT total: 120 questions
        net = calculate_net(correct=120, wrong=0, empty=0)

        assert net == 120.0


class TestWorstScore:
    """Test worst possible scores (all wrong)."""

    def test_all_wrong_min_net(self):
        """All wrong → net = -30.0 for 120 questions."""
        # All 120 questions wrong
        net = calculate_net(correct=0, wrong=120, empty=0)

        # Net = 0 - (120 / 4) = -30
        assert net == -30.0


# Helper for future integration with actual OSYM service
class OSYMScoreCalculator:
    """
    Helper class for OSYM score calculations.

    This can be moved to a service layer when needed.
    """

    TYT_QUESTIONS = 120
    AYT_QUESTIONS = 80  # Varies by field

    SUBJECT_QUESTIONS = {
        "turkce": 40,
        "matematik": 40,
        "sosyal": 20,
        "fen": 20,
    }

    @staticmethod
    def calculate_net(correct: int, wrong: int, empty: int) -> float:
        """Calculate net score."""
        return correct - (wrong / 4.0)

    @staticmethod
    def calculate_tyt_total(subject_nets: Dict[str, float]) -> float:
        """Calculate total TYT net from subject nets."""
        return sum(subject_nets.values())

    @staticmethod
    def validate_answer_counts(correct: int, wrong: int, empty: int, total: int) -> bool:
        """Validate that answer counts sum to total questions."""
        return (correct + wrong + empty) == total


def test_osym_calculator_helper():
    """Test OSYM calculator helper class."""
    calculator = OSYMScoreCalculator()

    # Test net calculation
    net = calculator.calculate_net(correct=80, wrong=20, empty=20)
    assert net == 75.0

    # Test validation
    valid = calculator.validate_answer_counts(
        correct=80, wrong=20, empty=20, total=120
    )
    assert valid is True

    invalid = calculator.validate_answer_counts(
        correct=80, wrong=20, empty=20, total=100
    )
    assert invalid is False

    # Test TYT total
    subject_nets = {
        "turkce": 35.0,
        "matematik": 30.0,
        "sosyal": 15.0,
        "fen": 18.0,
    }
    tyt_total = calculator.calculate_tyt_total(subject_nets)
    assert tyt_total == 98.0
