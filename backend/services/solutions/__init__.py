"""
Solutions Sub-Module - Alternative Solutions Service Components

This module contains refactored components from the original
alternative_solutions_service.py (2300+ lines).

Struktur:
- comparison.py - Solution comparison logic
- fastest.py - Fastest solution analysis
- voting.py - Voting and statistics

Usage:
    from services.solutions import (
        SolutionComparisonMixin,
        FastestSolutionMixin,
        SolutionVotingMixin,
    )

Author: KIRO2 Team
Date: 2025-01-24
"""

from .comparison import SolutionComparisonMixin
from .fastest import FastestSolutionMixin
from .voting import SolutionVotingMixin

__all__ = [
    "SolutionComparisonMixin",
    "FastestSolutionMixin",
    "SolutionVotingMixin",
]
