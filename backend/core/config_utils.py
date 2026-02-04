"""
Configuration Utility Functions

Feature flag ve configuration'a kolay erişim için yardımcı fonksiyonlar.
"""

from typing import Optional
from .feature_flags import (
    FeatureFlag,
    FeatureFlagManager,
    QualityThresholds,
    PerformanceConfig,
    ABTestVariant,
    get_feature_flag_manager,
)


def is_feature_enabled(flag: FeatureFlag) -> bool:
    """
    Feature flag aktif mi kontrol et

    Usage:
        if is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH):
            # Use semantic search
            pass
    """
    manager = get_feature_flag_manager()
    return manager.is_enabled(flag)


def get_quality_thresholds() -> QualityThresholds:
    """
    Quality threshold'ları al

    Usage:
        thresholds = get_quality_thresholds()
        if video.language_score >= thresholds.min_language_score:
            # Video passes language check
            pass
    """
    manager = get_feature_flag_manager()
    return manager.get_quality_thresholds()


def get_performance_config() -> PerformanceConfig:
    """
    Performance configuration'ı al

    Usage:
        config = get_performance_config()
        cache_ttl = config.cache_ttl_seconds
    """
    manager = get_feature_flag_manager()
    return manager.get_performance_config()


def get_ab_test_variant(test_id: str, user_id: str) -> Optional[ABTestVariant]:
    """
    Kullanıcı için A/B test varyantını al

    Usage:
        variant = get_ab_test_variant('relevance_scoring_v2', user_id)
        if variant and variant.name == 'treatment':
            # Use new algorithm
            pass
    """
    manager = get_feature_flag_manager()
    return manager.get_ab_test_variant(test_id, user_id)


def apply_ab_test_config(test_id: str, user_id: str, base_config: dict) -> dict:
    """
    A/B test varyantına göre config'i override et

    Usage:
        config = {'cache_ttl': 3600}
        config = apply_ab_test_config('cache_test', user_id, config)
    """
    variant = get_ab_test_variant(test_id, user_id)

    if variant and variant.config_overrides:
        # Apply overrides
        config = base_config.copy()
        config.update(variant.config_overrides)
        return config

    return base_config


def get_config_for_user(user_id: str) -> dict:
    """
    Kullanıcı için tam konfigürasyonu al (A/B test overrides dahil)

    Returns:
        {
            'quality_thresholds': {...},
            'performance_config': {...},
            'feature_flags': {...},
            'ab_test_variants': {...}
        }
    """
    manager = get_feature_flag_manager()

    # Base configuration
    config = {
        "quality_thresholds": manager.get_quality_thresholds().to_dict(),
        "performance_config": manager.get_performance_config().to_dict(),
        "feature_flags": {flag.value: manager.is_enabled(flag) for flag in FeatureFlag},
        "ab_test_variants": {},
    }

    # Apply A/B test overrides
    for test_id, ab_test in manager.ab_tests.items():
        if ab_test.enabled:
            variant = ab_test.get_variant_for_user(user_id)
            config["ab_test_variants"][test_id] = {
                "variant_name": variant.name,
                "overrides": variant.config_overrides,
            }

            # Apply overrides to config
            if variant.config_overrides:
                # Override feature flags
                for key, value in variant.config_overrides.items():
                    if key in config["feature_flags"]:
                        config["feature_flags"][key] = value
                    # Override other configs
                    elif key in config["performance_config"]:
                        config["performance_config"][key] = value

    return config


# Convenience functions for common checks


def should_use_semantic_search() -> bool:
    """Semantic search kullanılmalı mı?"""
    return is_feature_enabled(FeatureFlag.SEMANTIC_SEARCH)


def should_use_advanced_search() -> bool:
    """Advanced search kullanılmalı mı?"""
    return is_feature_enabled(FeatureFlag.ADVANCED_SEARCH)


def should_use_hybrid_search() -> bool:
    """Hybrid search kullanılmalı mı?"""
    return is_feature_enabled(FeatureFlag.HYBRID_SEARCH)


def should_filter_turkish_content() -> bool:
    """Türkçe içerik filtreleme yapılmalı mı?"""
    return is_feature_enabled(FeatureFlag.TURKISH_CONTENT_FILTER)


def should_use_multi_layer_cache() -> bool:
    """Multi-layer cache kullanılmalı mı?"""
    return is_feature_enabled(FeatureFlag.MULTI_LAYER_CACHE)


def should_enable_circuit_breaker() -> bool:
    """Circuit breaker aktif olmalı mı?"""
    return is_feature_enabled(FeatureFlag.CIRCUIT_BREAKER)


def should_enable_rate_limiting() -> bool:
    """Rate limiting aktif olmalı mı?"""
    return is_feature_enabled(FeatureFlag.RATE_LIMITING)


def should_collect_detailed_logs() -> bool:
    """Detaylı log toplama aktif olmalı mı?"""
    return is_feature_enabled(FeatureFlag.DETAILED_LOGGING)


def get_cache_ttl() -> int:
    """Cache TTL değerini al (saniye)"""
    config = get_performance_config()
    return config.cache_ttl_seconds


def get_max_parallel_searches() -> int:
    """Maksimum paralel arama sayısını al"""
    config = get_performance_config()
    return config.max_parallel_searches


def get_rate_limit_per_ip() -> int:
    """IP başına rate limit değerini al"""
    config = get_performance_config()
    return config.requests_per_minute_per_ip


def get_min_language_score() -> float:
    """Minimum dil skoru eşiğini al"""
    thresholds = get_quality_thresholds()
    return thresholds.min_language_score


def get_min_relevance_score() -> float:
    """Minimum alakalılık skoru eşiğini al"""
    thresholds = get_quality_thresholds()
    return thresholds.min_relevance_score


def get_min_overall_score() -> float:
    """Minimum genel kalite skoru eşiğini al"""
    thresholds = get_quality_thresholds()
    return thresholds.min_overall_score
