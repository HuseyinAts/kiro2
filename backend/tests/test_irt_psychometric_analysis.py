"""
Tests for IRT Psychometric Analysis Service
Task 57: IRT Parametreleri ve Psikometrik Analiz
"""

import numpy as np
import pytest

from services.irt_psychometric_analysis import (
    IRTParameters,
    IRTPsychometricAnalysis,
)


@pytest.fixture
def irt_service():
    """IRT Psychometric Analysis service fixture."""
    return IRTPsychometricAnalysis()


@pytest.fixture
def sample_params():
    """Sample IRT parameters."""
    return IRTParameters(a=1.2, b=0.5, c=0.25, d=1.0)


@pytest.fixture
def sample_responses():
    """Sample student responses for calibration."""
    np.random.seed(42)
    n_students = 250

    # Simulate student abilities
    theta_values = np.random.normal(0, 1, n_students)

    # Simulate responses based on 4PL model
    responses = []
    for theta in theta_values:
        # True parameters
        a, b, c, d = 1.0, 0.0, 0.25, 1.0
        prob = c + (d - c) / (1 + np.exp(-a * (theta - b)))
        is_correct = np.random.random() < prob

        responses.append(
            {
                "student_ability": theta,
                "is_correct": is_correct,
                "overall_score": (theta + 3) / 6,  # Normalize to 0-1
            }
        )

    return responses


# ==================== SUBTASK 57.1: 4 Parametreli IRT Model Tests ====================


class TestFourParameterIRTModel:
    """Tests for 4-parameter IRT model implementation."""

    # TODO: Implement test cases for 4PL IRT model
