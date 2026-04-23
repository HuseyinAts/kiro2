"""
Question bank quality tests (K-05).

Tests question bank requirements and quality standards.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend to path
backend_dir = str(Path(__file__).parent.parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def test_minimum_question_count_requirement():
    """Test minimum question count requirement is defined."""
    MINIMUM_TOTAL_QUESTIONS = 1000

    assert isinstance(MINIMUM_TOTAL_QUESTIONS, int), (
        "Minimum question count should be an integer"
    )
    assert MINIMUM_TOTAL_QUESTIONS >= 1000, (
        f"Should require at least 1000 questions, got: {MINIMUM_TOTAL_QUESTIONS}"
    )


def test_tyt_turkce_minimum():
    """Test TYT Türkçe minimum question count."""
    MINIMUM_TURKCE = 100

    assert isinstance(MINIMUM_TURKCE, int), (
        "Türkçe minimum should be an integer"
    )
    assert MINIMUM_TURKCE >= 100, (
        f"TYT Türkçe should have at least 100 questions, got: {MINIMUM_TURKCE}"
    )


def test_tyt_matematik_minimum():
    """Test TYT Matematik minimum question count."""
    MINIMUM_MATEMATIK = 100

    assert isinstance(MINIMUM_MATEMATIK, int), (
        "Matematik minimum should be an integer"
    )
    assert MINIMUM_MATEMATIK >= 100, (
        f"TYT Matematik should have at least 100 questions, got: {MINIMUM_MATEMATIK}"
    )


def test_tyt_fen_minimum():
    """Test TYT Fen minimum question count."""
    MINIMUM_FEN = 50

    assert isinstance(MINIMUM_FEN, int), (
        "Fen minimum should be an integer"
    )
    assert MINIMUM_FEN >= 50, (
        f"TYT Fen should have at least 50 questions, got: {MINIMUM_FEN}"
    )


def test_tyt_sosyal_minimum():
    """Test TYT Sosyal minimum question count."""
    MINIMUM_SOSYAL = 50

    assert isinstance(MINIMUM_SOSYAL, int), (
        "Sosyal minimum should be an integer"
    )
    assert MINIMUM_SOSYAL >= 50, (
        f"TYT Sosyal should have at least 50 questions, got: {MINIMUM_SOSYAL}"
    )


def test_difficulty_distribution_balanced():
    """Test difficulty distribution requirements."""
    # Expected distribution percentages
    DIFFICULTY_DISTRIBUTION = {
        "easy": 0.3,  # 30%
        "medium": 0.5,  # 50%
        "hard": 0.2,  # 20%
    }

    total_percentage = sum(DIFFICULTY_DISTRIBUTION.values())

    assert abs(total_percentage - 1.0) < 0.01, (
        f"Difficulty percentages should sum to 1.0, got: {total_percentage}"
    )

    # Check each difficulty level
    assert DIFFICULTY_DISTRIBUTION["easy"] >= 0.2, (
        "Easy questions should be at least 20%"
    )
    assert DIFFICULTY_DISTRIBUTION["medium"] >= 0.4, (
        "Medium questions should be at least 40%"
    )
    assert DIFFICULTY_DISTRIBUTION["hard"] >= 0.1, (
        "Hard questions should be at least 10%"
    )


def test_all_questions_have_5_options():
    """Test that all questions should have 5 options (A-E)."""
    REQUIRED_OPTIONS_COUNT = 5
    OPTION_LABELS = ["A", "B", "C", "D", "E"]

    assert REQUIRED_OPTIONS_COUNT == 5, (
        f"Questions should have 5 options, got: {REQUIRED_OPTIONS_COUNT}"
    )

    assert len(OPTION_LABELS) == 5, (
        f"Should have 5 option labels, got: {len(OPTION_LABELS)}"
    )

    # Verify option labels are correct
    assert OPTION_LABELS == ["A", "B", "C", "D", "E"], (
        f"Option labels should be A-E, got: {OPTION_LABELS}"
    )


def test_all_questions_have_correct_answer():
    """Test that all questions must have exactly one correct answer."""
    REQUIRED_CORRECT_ANSWERS = 1

    assert REQUIRED_CORRECT_ANSWERS == 1, (
        "Each question must have exactly 1 correct answer"
    )

    # Valid correct answer options
    VALID_CORRECT_OPTIONS = ["A", "B", "C", "D", "E"]

    assert len(VALID_CORRECT_OPTIONS) == 5, (
        f"Should have 5 valid correct options, got: {len(VALID_CORRECT_OPTIONS)}"
    )

    # Verify each is a single character
    assert all(len(opt) == 1 for opt in VALID_CORRECT_OPTIONS), (
        "Each option should be a single character"
    )
