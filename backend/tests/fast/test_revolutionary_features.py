"""
Fast unit tests for revolutionary features service
Tests: Dataclasses, Profile models
Coverage target: 40-60% of services.revolutionary_features_service
"""
import pytest
from dataclasses import asdict


class TestVARKProfile:
    """Test VARK profile dataclass"""

    def test_vark_profile_creation(self):
        """Test VARK profile can be created"""
        from services.revolutionary_features_service import VARKProfile

        profile = VARKProfile(
            visual=0.8, auditory=0.6, reading=0.7, kinesthetic=0.5, dominant="visual"
        )

        assert profile.visual == 0.8
        assert profile.auditory == 0.6
        assert profile.reading == 0.7
        assert profile.kinesthetic == 0.5
        assert profile.dominant == "visual"

    def test_vark_profile_to_dict(self):
        """Test VARK profile can be converted to dict"""
        from services.revolutionary_features_service import VARKProfile

        profile = VARKProfile(
            visual=0.8, auditory=0.6, reading=0.7, kinesthetic=0.5, dominant="visual"
        )

        profile_dict = asdict(profile)
        assert isinstance(profile_dict, dict)
        assert profile_dict["dominant"] == "visual"


class TestFelderProfile:
    """Test Felder-Silverman profile dataclass"""

    def test_felder_profile_creation(self):
        """Test Felder profile can be created"""
        from services.revolutionary_features_service import FelderProfile

        profile = FelderProfile(
            active_reflective=0.7,
            sensing_intuitive=0.6,
            visual_verbal=0.8,
            sequential_global=0.5,
            preferences=["active", "visual"],
        )

        assert profile.active_reflective == 0.7
        assert profile.sensing_intuitive == 0.6
        assert profile.visual_verbal == 0.8
        assert profile.sequential_global == 0.5
        assert len(profile.preferences) == 2


class TestHybridLearningProfile:
    """Test hybrid learning profile dataclass"""

    def test_hybrid_profile_creation(self):
        """Test hybrid profile can be created"""
        from services.revolutionary_features_service import (
            HybridLearningProfile,
            VARKProfile,
            FelderProfile,
        )

        vark = VARKProfile(0.8, 0.6, 0.7, 0.5, "visual")
        felder = FelderProfile(0.7, 0.6, 0.8, 0.5, ["active", "visual"])

        hybrid = HybridLearningProfile(
            student_id="student123",
            hybrid_code="VARK-V-FELDER-AV",
            vark_profile=vark,
            felder_profile=felder,
            confidence={"overall": 0.85},
            data_points_used=100,
            detection_date="2025-01-01",
            last_updated="2025-01-01",
        )

        assert hybrid.student_id == "student123"
        assert hybrid.hybrid_code == "VARK-V-FELDER-AV"
        assert hybrid.data_points_used == 100


class TestCulturalContext:
    """Test cultural context dataclass"""

    def test_cultural_context_creation(self):
        """Test cultural context can be created"""
        from services.revolutionary_features_service import CulturalContext

        context = CulturalContext(
            group_learning_preference=0.8,
            teacher_respect_level=0.9,
            family_involvement=0.7,
            peer_competition=0.6,
            authority_acceptance=0.8,
            collective_success=0.7,
            elder_wisdom_value=0.8,
            social_harmony=0.9,
        )

        assert context.teacher_respect_level == 0.9
        assert context.social_harmony == 0.9
        assert context.group_learning_preference == 0.8


class TestMaarifAlignment:
    """Test Maarif alignment dataclass"""

    def test_maarif_alignment_exists(self):
        """Test MaarifAlignment dataclass exists"""
        from services.revolutionary_features_service import MaarifAlignment

        assert MaarifAlignment is not None
