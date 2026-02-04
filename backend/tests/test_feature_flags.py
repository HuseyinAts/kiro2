"""
Unit tests for Feature Flags and Configuration Management
"""

import pytest
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from backend.core.feature_flags import (
    FeatureFlag,
    Environment,
    QualityThresholds,
    PerformanceConfig,
    ABTestVariant,
    ABTest,
    FeatureFlagManager,
)
from backend.core.config_utils import (
    is_feature_enabled,
    get_quality_thresholds,
    get_performance_config,
    get_ab_test_variant,
    get_config_for_user,
)


class TestQualityThresholds:
    """Quality thresholds tests"""

    def test_default_values(self):
        """Test default threshold values"""
        thresholds = QualityThresholds()

        assert thresholds.min_language_score == 0.8
        assert thresholds.min_relevance_score == 0.7
        assert thresholds.min_difficulty_match == 0.5
        assert thresholds.min_overall_score == 0.7

    def test_to_dict(self):
        """Test threshold serialization"""
        thresholds = QualityThresholds()
        data = thresholds.to_dict()

        assert "language" in data
        assert "relevance" in data
        assert "difficulty" in data
        assert "overall" in data
        assert data["language"]["min_score"] == 0.8


class TestPerformanceConfig:
    """Performance config tests"""

    def test_default_values(self):
        """Test default config values"""
        config = PerformanceConfig()

        assert config.cache_ttl_seconds == 3600
        assert config.memory_cache_size == 100
        assert config.max_parallel_searches == 3
        assert config.requests_per_minute_per_ip == 10

    def test_to_dict(self):
        """Test config serialization"""
        config = PerformanceConfig()
        data = config.to_dict()

        assert "cache" in data
        assert "parallel" in data
        assert "rate_limiting" in data
        assert data["cache"]["ttl_seconds"] == 3600


class TestABTestVariant:
    """A/B test variant tests"""

    def test_valid_variant(self):
        """Test valid variant creation"""
        variant = ABTestVariant(
            name="control", description="Control group", traffic_percentage=50.0
        )

        assert variant.name == "control"
        assert variant.traffic_percentage == 50.0
        assert variant.enabled is True

    def test_invalid_traffic_percentage(self):
        """Test invalid traffic percentage"""
        with pytest.raises(ValueError):
            ABTestVariant(
                name="test", description="Test", traffic_percentage=150.0  # Invalid
            )


class TestABTest:
    """A/B test tests"""

    def test_valid_ab_test(self):
        """Test valid A/B test creation"""
        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test description",
            variants=variants,
            start_date=datetime.now(),
        )

        assert ab_test.test_id == "test_1"
        assert len(ab_test.variants) == 2
        assert ab_test.enabled is True

    def test_invalid_traffic_total(self):
        """Test invalid traffic percentage total"""
        variants = [
            ABTestVariant("control", "Control", 40.0),
            ABTestVariant("treatment", "Treatment", 50.0),  # Total = 90
        ]

        with pytest.raises(ValueError):
            ABTest(
                test_id="test_1",
                name="Test 1",
                description="Test",
                variants=variants,
                start_date=datetime.now(),
            )

    def test_get_variant_for_user(self):
        """Test consistent variant assignment"""
        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test",
            variants=variants,
            start_date=datetime.now(),
        )

        # Same user should get same variant
        user_id = "user_123"
        variant1 = ab_test.get_variant_for_user(user_id)
        variant2 = ab_test.get_variant_for_user(user_id)

        assert variant1.name == variant2.name

    def test_variant_distribution(self):
        """Test variant distribution is roughly 50/50"""
        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test",
            variants=variants,
            start_date=datetime.now(),
        )

        # Test with 100 users
        control_count = 0
        treatment_count = 0

        for i in range(100):
            variant = ab_test.get_variant_for_user(f"user_{i}")
            if variant.name == "control":
                control_count += 1
            else:
                treatment_count += 1

        # Should be roughly 50/50 (allow 30-70 range)
        assert 30 <= control_count <= 70
        assert 30 <= treatment_count <= 70


class TestFeatureFlagManager:
    """Feature flag manager tests"""

    def test_default_flags_production(self):
        """Test default flags for production"""
        manager = FeatureFlagManager(environment=Environment.PRODUCTION)

        # Stable features should be enabled
        assert manager.is_enabled(FeatureFlag.SEMANTIC_SEARCH) is True
        assert manager.is_enabled(FeatureFlag.TURKISH_CONTENT_FILTER) is True

        # Experimental features should be disabled
        assert manager.is_enabled(FeatureFlag.AI_RELEVANCE_SCORING) is False
        assert manager.is_enabled(FeatureFlag.PERSONALIZED_RANKING) is False

    def test_default_flags_development(self):
        """Test default flags for development"""
        manager = FeatureFlagManager(environment=Environment.DEVELOPMENT)

        # All features should be enabled in development
        for flag in FeatureFlag:
            assert manager.is_enabled(flag) is True

    def test_load_configuration_from_file(self):
        """Test loading configuration from file"""
        # Create temporary config file
        config_data = {
            "environment": "test",
            "feature_flags": {"semantic_search": False, "advanced_search": True},
            "quality_thresholds": {"language": {"min_score": 0.9}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            manager = FeatureFlagManager(
                environment=Environment.TEST, config_file=config_file
            )

            # Check loaded flags
            assert manager.is_enabled(FeatureFlag.SEMANTIC_SEARCH) is False
            assert manager.is_enabled(FeatureFlag.ADVANCED_SEARCH) is True

            # Check loaded thresholds
            thresholds = manager.get_quality_thresholds()
            assert thresholds.min_language_score == 0.9

        finally:
            Path(config_file).unlink()

    def test_save_configuration(self):
        """Test saving configuration to file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            manager = FeatureFlagManager(
                environment=Environment.TEST, config_file=config_file
            )

            # Modify configuration
            manager.flags[FeatureFlag.SEMANTIC_SEARCH] = False
            manager.quality_thresholds.min_language_score = 0.95

            # Save
            manager.save_configuration()

            # Load and verify
            with open(config_file, "r") as f:
                saved_config = json.load(f)

            assert saved_config["feature_flags"]["semantic_search"] is False
            assert saved_config["quality_thresholds"]["language"]["min_score"] == 0.95

        finally:
            Path(config_file).unlink()

    def test_get_ab_test_variant(self):
        """Test getting A/B test variant"""
        manager = FeatureFlagManager(environment=Environment.TEST)

        # Add A/B test
        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test",
            variants=variants,
            start_date=datetime.now() - timedelta(days=1),  # Started yesterday
            end_date=datetime.now() + timedelta(days=30),  # Ends in 30 days
            enabled=True,
        )

        manager.ab_tests["test_1"] = ab_test

        # Get variant
        variant = manager.get_ab_test_variant("test_1", "user_123")

        assert variant is not None
        assert variant.name in ["control", "treatment"]

    def test_ab_test_not_started(self):
        """Test A/B test that hasn't started yet"""
        manager = FeatureFlagManager(environment=Environment.TEST)

        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test",
            variants=variants,
            start_date=datetime.now() + timedelta(days=1),  # Starts tomorrow
            enabled=True,
        )

        manager.ab_tests["test_1"] = ab_test

        # Should return None (test not started)
        variant = manager.get_ab_test_variant("test_1", "user_123")
        assert variant is None

    def test_ab_test_ended(self):
        """Test A/B test that has ended"""
        manager = FeatureFlagManager(environment=Environment.TEST)

        variants = [
            ABTestVariant("control", "Control", 50.0),
            ABTestVariant("treatment", "Treatment", 50.0),
        ]

        ab_test = ABTest(
            test_id="test_1",
            name="Test 1",
            description="Test",
            variants=variants,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now() - timedelta(days=1),  # Ended yesterday
            enabled=True,
        )

        manager.ab_tests["test_1"] = ab_test

        # Should return None (test ended)
        variant = manager.get_ab_test_variant("test_1", "user_123")
        assert variant is None

    def test_get_config_summary(self):
        """Test getting configuration summary"""
        manager = FeatureFlagManager(environment=Environment.PRODUCTION)

        summary = manager.get_config_summary()

        assert "environment" in summary
        assert "enabled_features" in summary
        assert "disabled_features" in summary
        assert "quality_thresholds" in summary
        assert "performance_config" in summary
        assert summary["environment"] == "production"


class TestConfigUtils:
    """Config utility functions tests"""

    def test_is_feature_enabled(self):
        """Test is_feature_enabled utility"""
        # This will use the global manager
        # Just test that it doesn't crash
        result = is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH)
        assert isinstance(result, bool)

    def test_get_quality_thresholds(self):
        """Test get_quality_thresholds utility"""
        thresholds = get_quality_thresholds()
        assert isinstance(thresholds, QualityThresholds)
        assert thresholds.min_language_score > 0

    def test_get_performance_config(self):
        """Test get_performance_config utility"""
        config = get_performance_config()
        assert isinstance(config, PerformanceConfig)
        assert config.cache_ttl_seconds > 0

    def test_get_config_for_user(self):
        """Test get_config_for_user utility"""
        config = get_config_for_user("user_123")

        assert "quality_thresholds" in config
        assert "performance_config" in config
        assert "feature_flags" in config
        assert "ab_test_variants" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
