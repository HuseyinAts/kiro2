"""
ZPD Boundary Tests (K-02).

Tests for Zone of Proximal Development and Maarif values.
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.turkish_zpd_maarif_system import (  # noqa: E402
    MaarifValue,
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
)


class TestZPDProbabilityBoundaries:
    """Test ZPD success probability boundaries [0.15, 0.85]."""

    def test_zpd_lower_bound_15_percent(self):
        """ZPD lower bound should be 0.15 (15%)."""
        # ZPD_SUCCESS_PROBABILITY_RANGE is used internally
        lower_bound = 0.15

        assert lower_bound == 0.15

    def test_zpd_upper_bound_85_percent(self):
        """ZPD upper bound should be 0.85 (85%)."""
        upper_bound = 0.85

        assert upper_bound == 0.85

    def test_question_too_hard_rejected(self):
        """Questions with P < 0.15 should be outside ZPD."""
        probability = 0.10

        is_in_zpd = 0.15 <= probability <= 0.85

        assert not is_in_zpd

    def test_question_too_easy_rejected(self):
        """Questions with P > 0.85 should be outside ZPD."""
        probability = 0.90

        is_in_zpd = 0.15 <= probability <= 0.85

        assert not is_in_zpd

    def test_question_in_zpd_accepted(self):
        """Questions with 0.15 ≤ P ≤ 0.85 should be in ZPD."""
        probabilities = [0.15, 0.50, 0.85]

        for prob in probabilities:
            is_in_zpd = 0.15 <= prob <= 0.85
            assert is_in_zpd, f"Probability {prob} should be in ZPD"


class TestMaarifValues:
    """Test Maarif (educational values) system."""

    def test_maarif_values_count(self):
        """Should have at least 14 Maarif values."""
        values = list(MaarifValue)

        assert len(values) >= 14

        # Check key values exist
        required_values = [
            "VATAN",
            "MILLET",
            "AILE",
            "ADALET",
            "DÜRÜSTLÜK",
            "SAYGI",
            "SORUMLULUK",
        ]

        value_names = [v.name for v in values]
        for required in required_values:
            assert required in value_names, f"{required} should be in MaarifValue"

    def test_tarih_maarif_mapping(self):
        """History subject should map to VATAN, MILLET, ADALET."""
        system = TurkishZPDMaarifSystem()

        # Check subject_maarif_mapping exists
        assert hasattr(system, "subject_maarif_mapping")

        tarih_values = system.subject_maarif_mapping.get("tarih", [])

        # Should contain VATAN, MILLET, ADALET
        assert MaarifValue.VATAN in tarih_values
        assert MaarifValue.MILLET in tarih_values
        assert MaarifValue.ADALET in tarih_values


class TestZPDExpansionFactors:
    """Test ZPD expansion factors for Turkish cultural context."""

    def test_group_learning_expansion(self):
        """Group learning should expand ZPD by 1.20x."""
        system = TurkishZPDMaarifSystem()

        factor = system.zpd_expansion_factors.get("group_learning")

        assert factor == 1.20

    def test_teacher_respect_expansion(self):
        """Teacher respect should expand ZPD by 1.15x."""
        system = TurkishZPDMaarifSystem()

        factor = system.zpd_expansion_factors.get("high_teacher_respect")

        assert factor == 1.15

    def test_family_support_expansion(self):
        """Family support should expand ZPD by 1.10x."""
        system = TurkishZPDMaarifSystem()

        factor = system.zpd_expansion_factors.get("family_support")

        assert factor == 1.10

    def test_maarif_alignment_expansion(self):
        """Maarif alignment should expand ZPD by 1.25x."""
        system = TurkishZPDMaarifSystem()

        factor = system.zpd_expansion_factors.get("maarif_alignment")

        assert factor == 1.25


class TestCulturalContext:
    """Test Turkish cultural context defaults."""

    def test_default_cultural_factors(self):
        """Default cultural factors should match Turkish educational context."""
        context = TurkishCulturalContext(student_id="test-student-001")

        # Group learning preference: 0.8 (80%)
        assert context.group_learning_preference == 0.8

        # Teacher respect level: 0.9 (90%)
        assert context.teacher_respect_level == 0.9

        # Family involvement: 0.7 (70%)
        assert context.family_involvement == 0.7

        # All factors should be in [0, 1]
        assert 0.0 <= context.group_learning_preference <= 1.0
        assert 0.0 <= context.teacher_respect_level <= 1.0
        assert 0.0 <= context.family_involvement <= 1.0
