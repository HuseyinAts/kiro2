"""
ZPD Boundary Tests (K-02).

Tests for Zone of Proximal Development and Maarif values.
Exercises real TurkishZPDMaarifSystem engine — no literal-only assertions.
"""

import sys
from pathlib import Path

import pytest

# Add backend directory to path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))

from algorithms.turkish_zpd_maarif_system import (  # noqa: E402
    MaarifValue,
    TurkishCulturalContext,
    TurkishZPDMaarifSystem,
)

# ── Helper ──────────────────────────────────────────────────────────────────


def _make_system_and_context(student_id: str = "test-001"):
    system = TurkishZPDMaarifSystem()
    context = TurkishCulturalContext(student_id=student_id)
    return system, context


# ── ZPD Range Tests (async — exercises calculate_turkish_zpd) ───────────────


class TestZPDProbabilityBoundaries:
    """Test ZPD range via the real calculate_turkish_zpd engine."""

    @pytest.mark.asyncio
    async def test_zpd_range_has_bounds(self):
        """System should return ZPD range with lower/upper bounds."""
        system, ctx = _make_system_and_context()
        zpd = await system.calculate_turkish_zpd(
            student_id="test-001",
            subject="matematik",
            current_level=0.5,
            cultural_context=ctx,
        )
        assert hasattr(zpd, "lower_bound")
        assert hasattr(zpd, "upper_bound")
        assert zpd.lower_bound < zpd.upper_bound

    @pytest.mark.asyncio
    async def test_zpd_lower_bound_reasonable(self):
        """Lower bound should be non-negative and at or below current level."""
        system, ctx = _make_system_and_context("test-002")
        zpd = await system.calculate_turkish_zpd(
            student_id="test-002",
            subject="matematik",
            current_level=0.5,
            cultural_context=ctx,
        )
        assert zpd.lower_bound >= 0.0
        assert zpd.lower_bound <= 0.5

    @pytest.mark.asyncio
    async def test_zpd_upper_bound_above_current(self):
        """Upper bound should extend beyond current level."""
        system, ctx = _make_system_and_context("test-003")
        zpd = await system.calculate_turkish_zpd(
            student_id="test-003",
            subject="matematik",
            current_level=0.5,
            cultural_context=ctx,
        )
        assert zpd.upper_bound > 0.5

    @pytest.mark.asyncio
    async def test_zpd_optimal_challenge_in_range(self):
        """Optimal challenge should be within ZPD range."""
        system, ctx = _make_system_and_context("test-004")
        zpd = await system.calculate_turkish_zpd(
            student_id="test-004",
            subject="matematik",
            current_level=0.5,
            cultural_context=ctx,
        )
        assert zpd.lower_bound <= zpd.optimal_challenge <= zpd.upper_bound

    @pytest.mark.asyncio
    async def test_zpd_valid_at_low_level(self):
        """ZPD should produce a valid range at low skill level."""
        system, ctx = _make_system_and_context("test-low")
        zpd = await system.calculate_turkish_zpd(
            student_id="test-low",
            subject="matematik",
            current_level=0.1,
            cultural_context=ctx,
        )
        assert zpd.lower_bound < zpd.upper_bound

    @pytest.mark.asyncio
    async def test_zpd_valid_at_high_level(self):
        """ZPD should produce a valid range at high skill level."""
        system, ctx = _make_system_and_context("test-high")
        zpd = await system.calculate_turkish_zpd(
            student_id="test-high",
            subject="matematik",
            current_level=0.9,
            cultural_context=ctx,
        )
        assert zpd.lower_bound < zpd.upper_bound

    @pytest.mark.asyncio
    @pytest.mark.parametrize("subject", ["matematik", "fizik", "tarih", "turkce"])
    async def test_zpd_works_for_subjects(self, subject):
        """ZPD should work for different YKS subjects."""
        system, ctx = _make_system_and_context(f"test-{subject}")
        zpd = await system.calculate_turkish_zpd(
            student_id=f"test-{subject}",
            subject=subject,
            current_level=0.5,
            cultural_context=ctx,
        )
        assert zpd.lower_bound < zpd.upper_bound, f"ZPD invalid for {subject}"


# ── Maarif Values (sync) ───────────────────────────────────────────────────


class TestMaarifValues:
    """Test Maarif (educational values) system."""

    def test_maarif_values_count(self):
        """Should have at least 14 Maarif values."""
        values = list(MaarifValue)
        assert len(values) >= 14

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
        assert hasattr(system, "subject_maarif_mapping")
        tarih_values = system.subject_maarif_mapping.get("tarih", [])
        assert MaarifValue.VATAN in tarih_values
        assert MaarifValue.MILLET in tarih_values
        assert MaarifValue.ADALET in tarih_values


# ── Expansion Factors (sync) ───────────────────────────────────────────────


class TestZPDExpansionFactors:
    """Test ZPD expansion factors for Turkish cultural context."""

    def test_group_learning_expansion(self):
        system = TurkishZPDMaarifSystem()
        assert system.zpd_expansion_factors.get("group_learning") == 1.20

    def test_teacher_respect_expansion(self):
        system = TurkishZPDMaarifSystem()
        assert system.zpd_expansion_factors.get("high_teacher_respect") == 1.15

    def test_family_support_expansion(self):
        system = TurkishZPDMaarifSystem()
        assert system.zpd_expansion_factors.get("family_support") == 1.10

    def test_maarif_alignment_expansion(self):
        system = TurkishZPDMaarifSystem()
        assert system.zpd_expansion_factors.get("maarif_alignment") == 1.25


# ── Cultural Context Defaults (sync) ──────────────────────────────────────


class TestCulturalContext:
    """Test Turkish cultural context defaults."""

    def test_default_cultural_factors(self):
        context = TurkishCulturalContext(student_id="test-student-001")
        assert context.group_learning_preference == 0.8
        assert context.teacher_respect_level == 0.9
        assert context.family_involvement == 0.7
        assert 0.0 <= context.group_learning_preference <= 1.0
        assert 0.0 <= context.teacher_respect_level <= 1.0
        assert 0.0 <= context.family_involvement <= 1.0
