"""
Feature Flags ve Configuration Management System

Bu modül, video öneri sisteminin dinamik konfigürasyonunu ve
A/B testing altyapısını sağlar.

Requirements: 8.10
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class FeatureFlag(Enum):
    """Feature flag tanımları"""

    # Video Discovery Features
    SEMANTIC_SEARCH = "semantic_search"
    ADVANCED_SEARCH = "advanced_search"
    HYBRID_SEARCH = "hybrid_search"

    # Filtering Features
    TURKISH_CONTENT_FILTER = "turkish_content_filter"
    RELEVANCE_FILTER = "relevance_filter"
    DIFFICULTY_FILTER = "difficulty_filter"

    # Cache Features
    MULTI_LAYER_CACHE = "multi_layer_cache"
    CACHE_WARMING = "cache_warming"
    AGGRESSIVE_CACHING = "aggressive_caching"

    # Performance Features
    PARALLEL_DISCOVERY = "parallel_discovery"
    CIRCUIT_BREAKER = "circuit_breaker"
    RATE_LIMITING = "rate_limiting"

    # Quality Features
    QUALITY_SCORING = "quality_scoring"
    TRUSTED_CHANNELS_BOOST = "trusted_channels_boost"

    # Monitoring Features
    DETAILED_LOGGING = "detailed_logging"
    METRICS_COLLECTION = "metrics_collection"

    # Experimental Features
    AI_RELEVANCE_SCORING = "ai_relevance_scoring"
    PERSONALIZED_RANKING = "personalized_ranking"


class Environment(Enum):
    """Deployment environment"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class QualityThresholds:
    """
    Video kalite eşik değerleri

    Bu değerler video filtreleme ve skorlama için kullanılır.
    """

    # Language Detection Thresholds
    min_language_score: float = 0.8  # Minimum Türkçe güven skoru
    turkish_char_weight: float = 0.3  # Türkçe karakter ağırlığı

    # Relevance Thresholds
    min_relevance_score: float = 0.7  # Minimum konu alakalılık skoru
    keyword_match_weight: float = 0.6  # Ana konu eşleşme ağırlığı
    subtopic_match_weight: float = 0.4  # Alt konu eşleşme ağırlığı

    # Difficulty Matching Thresholds
    min_difficulty_match: float = 0.5  # Minimum zorluk uyum skoru
    difficulty_tolerance: int = 1  # ±1 seviye toleransı

    # Overall Quality Thresholds
    min_overall_score: float = 0.7  # Minimum genel kalite skoru
    language_weight: float = 0.3  # Dil skoru ağırlığı
    relevance_weight: float = 0.5  # Alakalılık skoru ağırlığı
    difficulty_weight: float = 0.2  # Zorluk uyum ağırlığı

    # Video Quality Thresholds
    min_view_count: int = 100  # Minimum izlenme sayısı
    min_video_duration_seconds: int = 60  # Minimum video süresi (1 dakika)
    max_video_duration_seconds: int = 3600  # Maximum video süresi (1 saat)

    # Channel Trust Thresholds
    trusted_channel_boost: float = 0.1  # Güvenilir kanal bonus skoru
    min_channel_subscriber_count: int = 1000  # Minimum abone sayısı

    def to_dict(self) -> dict[str, Any]:
        """Threshold'ları dictionary'e çevir"""
        return {
            "language": {
                "min_score": self.min_language_score,
                "turkish_char_weight": self.turkish_char_weight,
            },
            "relevance": {
                "min_score": self.min_relevance_score,
                "keyword_weight": self.keyword_match_weight,
                "subtopic_weight": self.subtopic_match_weight,
            },
            "difficulty": {
                "min_match": self.min_difficulty_match,
                "tolerance": self.difficulty_tolerance,
            },
            "overall": {
                "min_score": self.min_overall_score,
                "language_weight": self.language_weight,
                "relevance_weight": self.relevance_weight,
                "difficulty_weight": self.difficulty_weight,
            },
            "video_quality": {
                "min_views": self.min_view_count,
                "min_duration": self.min_video_duration_seconds,
                "max_duration": self.max_video_duration_seconds,
            },
            "channel_trust": {
                "boost": self.trusted_channel_boost,
                "min_subscribers": self.min_channel_subscriber_count,
            },
        }


@dataclass
class PerformanceConfig:
    """
    Performance tuning parametreleri
    """

    # Cache Configuration
    cache_ttl_seconds: int = 3600  # 1 hour
    memory_cache_size: int = 100  # LRU cache size
    cache_warming_enabled: bool = True

    # Parallel Processing
    max_parallel_searches: int = 3  # Maksimum paralel arama sayısı
    search_timeout_seconds: int = 5  # Arama timeout süresi

    # Rate Limiting
    requests_per_minute_per_ip: int = 10
    requests_per_minute_per_user: int = 20
    youtube_api_quota_limit: int = 10000  # Günlük quota

    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    circuit_breaker_success_threshold: int = 2

    # Response Time Targets
    target_p95_response_time_ms: int = 3000  # 3 saniye
    target_p99_response_time_ms: int = 5000  # 5 saniye

    # Video Discovery
    max_videos_per_subject: int = 5
    max_total_videos: int = 15

    def to_dict(self) -> dict[str, Any]:
        """Config'i dictionary'e çevir"""
        return {
            "cache": {
                "ttl_seconds": self.cache_ttl_seconds,
                "memory_size": self.memory_cache_size,
                "warming_enabled": self.cache_warming_enabled,
            },
            "parallel": {
                "max_searches": self.max_parallel_searches,
                "timeout_seconds": self.search_timeout_seconds,
            },
            "rate_limiting": {
                "per_ip": self.requests_per_minute_per_ip,
                "per_user": self.requests_per_minute_per_user,
                "youtube_quota": self.youtube_api_quota_limit,
            },
            "circuit_breaker": {
                "failure_threshold": self.circuit_breaker_failure_threshold,
                "timeout_seconds": self.circuit_breaker_timeout_seconds,
                "success_threshold": self.circuit_breaker_success_threshold,
            },
            "targets": {
                "p95_ms": self.target_p95_response_time_ms,
                "p99_ms": self.target_p99_response_time_ms,
            },
            "discovery": {
                "max_per_subject": self.max_videos_per_subject,
                "max_total": self.max_total_videos,
            },
        }


@dataclass
class ABTestVariant:
    """
    A/B test varyantı
    """

    name: str
    description: str
    traffic_percentage: float  # 0-100 arası
    config_overrides: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def __post_init__(self):
        """Validation"""
        if not 0 <= self.traffic_percentage <= 100:
            raise ValueError("Traffic percentage must be between 0 and 100")


@dataclass
class ABTest:
    """
    A/B test tanımı
    """

    test_id: str
    name: str
    description: str
    variants: list[ABTestVariant]
    start_date: datetime
    end_date: datetime | None = None
    enabled: bool = True

    def __post_init__(self):
        """Validation"""
        total_traffic = sum(v.traffic_percentage for v in self.variants)
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(
                f"Total traffic percentage must be 100, got {total_traffic}"
            )

    def get_variant_for_user(self, user_id: str) -> ABTestVariant:
        """
        Kullanıcı için variant belirle (consistent hashing)
        """
        import hashlib

        # User ID'yi hash'le
        hash_value = int(
            hashlib.md5(
                f"{self.test_id}:{user_id}".encode(), usedforsecurity=False
            ).hexdigest(),
            16,
        )
        percentage = (hash_value % 100) + 1  # 1-100 arası

        # Variant belirle
        cumulative = 0
        for variant in self.variants:
            cumulative += variant.traffic_percentage
            if percentage <= cumulative:
                return variant

        # Fallback (olmamalı ama güvenlik için)
        return self.variants[0]


class FeatureFlagManager:
    """
    Feature flag ve configuration yönetimi
    """

    def __init__(
        self,
        environment: Environment = Environment.PRODUCTION,
        config_file: str | None = None,
    ):
        self.environment = environment
        self.config_file = config_file or self._get_default_config_file()

        # Default configurations
        self.flags: dict[FeatureFlag, bool] = self._get_default_flags()
        self.quality_thresholds = QualityThresholds()
        self.performance_config = PerformanceConfig()
        self.ab_tests: dict[str, ABTest] = {}

        # Load configuration
        self._load_configuration()

    def _get_default_config_file(self) -> str:
        """Default config dosya yolu"""
        base_dir = Path(__file__).parent.parent
        return str(base_dir / "config" / f"feature_flags_{self.environment.value}.json")

    def _get_default_flags(self) -> dict[FeatureFlag, bool]:
        """Environment'a göre default flag değerleri"""

        if self.environment == Environment.PRODUCTION:
            return {
                # Production: Stable features only
                FeatureFlag.SEMANTIC_SEARCH: True,
                FeatureFlag.ADVANCED_SEARCH: True,
                FeatureFlag.HYBRID_SEARCH: True,
                FeatureFlag.TURKISH_CONTENT_FILTER: True,
                FeatureFlag.RELEVANCE_FILTER: True,
                FeatureFlag.DIFFICULTY_FILTER: True,
                FeatureFlag.MULTI_LAYER_CACHE: True,
                FeatureFlag.CACHE_WARMING: True,
                FeatureFlag.AGGRESSIVE_CACHING: False,
                FeatureFlag.PARALLEL_DISCOVERY: True,
                FeatureFlag.CIRCUIT_BREAKER: True,
                FeatureFlag.RATE_LIMITING: True,
                FeatureFlag.QUALITY_SCORING: True,
                FeatureFlag.TRUSTED_CHANNELS_BOOST: True,
                FeatureFlag.DETAILED_LOGGING: False,
                FeatureFlag.METRICS_COLLECTION: True,
                FeatureFlag.AI_RELEVANCE_SCORING: False,  # Experimental
                FeatureFlag.PERSONALIZED_RANKING: False,  # Experimental
            }

        if self.environment == Environment.STAGING:
            return {
                # Staging: Test new features
                FeatureFlag.SEMANTIC_SEARCH: True,
                FeatureFlag.ADVANCED_SEARCH: True,
                FeatureFlag.HYBRID_SEARCH: True,
                FeatureFlag.TURKISH_CONTENT_FILTER: True,
                FeatureFlag.RELEVANCE_FILTER: True,
                FeatureFlag.DIFFICULTY_FILTER: True,
                FeatureFlag.MULTI_LAYER_CACHE: True,
                FeatureFlag.CACHE_WARMING: True,
                FeatureFlag.AGGRESSIVE_CACHING: True,
                FeatureFlag.PARALLEL_DISCOVERY: True,
                FeatureFlag.CIRCUIT_BREAKER: True,
                FeatureFlag.RATE_LIMITING: True,
                FeatureFlag.QUALITY_SCORING: True,
                FeatureFlag.TRUSTED_CHANNELS_BOOST: True,
                FeatureFlag.DETAILED_LOGGING: True,
                FeatureFlag.METRICS_COLLECTION: True,
                FeatureFlag.AI_RELEVANCE_SCORING: True,  # Test experimental
                FeatureFlag.PERSONALIZED_RANKING: True,  # Test experimental
            }

        # DEVELOPMENT or TEST
        return {
            # Development: All features enabled for testing
            flag: True
            for flag in FeatureFlag
        }

    def _load_configuration(self):
        """Configuration dosyasından ayarları yükle"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, encoding="utf-8") as f:
                    config = json.load(f)

                # Load feature flags
                if "feature_flags" in config:
                    for flag_name, enabled in config["feature_flags"].items():
                        try:
                            flag = FeatureFlag(flag_name)
                            self.flags[flag] = enabled
                        except ValueError:
                            print(f"Warning: Unknown feature flag '{flag_name}'")

                # Load quality thresholds
                if "quality_thresholds" in config:
                    self._load_quality_thresholds(config["quality_thresholds"])

                # Load performance config
                if "performance_config" in config:
                    self._load_performance_config(config["performance_config"])

                # Load A/B tests
                if "ab_tests" in config:
                    self._load_ab_tests(config["ab_tests"])

        except Exception as e:
            print(f"Warning: Failed to load configuration from {self.config_file}: {e}")
            print("Using default configuration")

    def _load_quality_thresholds(self, config: dict[str, Any]):
        """Quality threshold'ları yükle"""
        if "language" in config:
            self.quality_thresholds.min_language_score = config["language"].get(
                "min_score", self.quality_thresholds.min_language_score
            )
            self.quality_thresholds.turkish_char_weight = config["language"].get(
                "turkish_char_weight", self.quality_thresholds.turkish_char_weight
            )

        if "relevance" in config:
            self.quality_thresholds.min_relevance_score = config["relevance"].get(
                "min_score", self.quality_thresholds.min_relevance_score
            )
            self.quality_thresholds.keyword_match_weight = config["relevance"].get(
                "keyword_weight", self.quality_thresholds.keyword_match_weight
            )
            self.quality_thresholds.subtopic_match_weight = config["relevance"].get(
                "subtopic_weight", self.quality_thresholds.subtopic_match_weight
            )

        if "difficulty" in config:
            self.quality_thresholds.min_difficulty_match = config["difficulty"].get(
                "min_match", self.quality_thresholds.min_difficulty_match
            )
            self.quality_thresholds.difficulty_tolerance = config["difficulty"].get(
                "tolerance", self.quality_thresholds.difficulty_tolerance
            )

        if "overall" in config:
            self.quality_thresholds.min_overall_score = config["overall"].get(
                "min_score", self.quality_thresholds.min_overall_score
            )
            self.quality_thresholds.language_weight = config["overall"].get(
                "language_weight", self.quality_thresholds.language_weight
            )
            self.quality_thresholds.relevance_weight = config["overall"].get(
                "relevance_weight", self.quality_thresholds.relevance_weight
            )
            self.quality_thresholds.difficulty_weight = config["overall"].get(
                "difficulty_weight", self.quality_thresholds.difficulty_weight
            )

    def _load_performance_config(self, config: dict[str, Any]):
        """Performance config'i yükle"""
        if "cache" in config:
            self.performance_config.cache_ttl_seconds = config["cache"].get(
                "ttl_seconds", self.performance_config.cache_ttl_seconds
            )
            self.performance_config.memory_cache_size = config["cache"].get(
                "memory_size", self.performance_config.memory_cache_size
            )
            self.performance_config.cache_warming_enabled = config["cache"].get(
                "warming_enabled", self.performance_config.cache_warming_enabled
            )

        if "parallel" in config:
            self.performance_config.max_parallel_searches = config["parallel"].get(
                "max_searches", self.performance_config.max_parallel_searches
            )
            self.performance_config.search_timeout_seconds = config["parallel"].get(
                "timeout_seconds", self.performance_config.search_timeout_seconds
            )

        if "rate_limiting" in config:
            self.performance_config.requests_per_minute_per_ip = config[
                "rate_limiting"
            ].get("per_ip", self.performance_config.requests_per_minute_per_ip)
            self.performance_config.requests_per_minute_per_user = config[
                "rate_limiting"
            ].get("per_user", self.performance_config.requests_per_minute_per_user)

    def _load_ab_tests(self, config: list[dict[str, Any]]):
        """A/B test'leri yükle"""
        for test_config in config:
            try:
                variants = [
                    ABTestVariant(
                        name=v["name"],
                        description=v["description"],
                        traffic_percentage=v["traffic_percentage"],
                        config_overrides=v.get("config_overrides", {}),
                        enabled=v.get("enabled", True),
                    )
                    for v in test_config["variants"]
                ]

                ab_test = ABTest(
                    test_id=test_config["test_id"],
                    name=test_config["name"],
                    description=test_config["description"],
                    variants=variants,
                    start_date=datetime.fromisoformat(test_config["start_date"]),
                    end_date=datetime.fromisoformat(test_config["end_date"])
                    if test_config.get("end_date")
                    else None,
                    enabled=test_config.get("enabled", True),
                )

                self.ab_tests[ab_test.test_id] = ab_test

            except Exception as e:
                print(f"Warning: Failed to load A/B test: {e}")

    def is_enabled(self, flag: FeatureFlag) -> bool:
        """Feature flag aktif mi?"""
        return self.flags.get(flag, False)

    def get_quality_thresholds(self) -> QualityThresholds:
        """Quality threshold'ları al"""
        return self.quality_thresholds

    def get_performance_config(self) -> PerformanceConfig:
        """Performance config'i al"""
        return self.performance_config

    def get_ab_test_variant(self, test_id: str, user_id: str) -> ABTestVariant | None:
        """
        Kullanıcı için A/B test varyantını al
        """
        ab_test = self.ab_tests.get(test_id)

        if not ab_test or not ab_test.enabled:
            return None

        # Test süresi kontrolü
        now = datetime.now()
        if now < ab_test.start_date:
            return None
        if ab_test.end_date and now > ab_test.end_date:
            return None

        return ab_test.get_variant_for_user(user_id)

    def save_configuration(self):
        """Mevcut konfigürasyonu dosyaya kaydet"""
        config = {
            "environment": self.environment.value,
            "feature_flags": {
                flag.value: enabled for flag, enabled in self.flags.items()
            },
            "quality_thresholds": self.quality_thresholds.to_dict(),
            "performance_config": self.performance_config.to_dict(),
            "ab_tests": [
                {
                    "test_id": test.test_id,
                    "name": test.name,
                    "description": test.description,
                    "variants": [
                        {
                            "name": v.name,
                            "description": v.description,
                            "traffic_percentage": v.traffic_percentage,
                            "config_overrides": v.config_overrides,
                            "enabled": v.enabled,
                        }
                        for v in test.variants
                    ],
                    "start_date": test.start_date.isoformat(),
                    "end_date": test.end_date.isoformat() if test.end_date else None,
                    "enabled": test.enabled,
                }
                for test in self.ab_tests.values()
            ],
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def get_config_summary(self) -> dict[str, Any]:
        """Konfigürasyon özetini al"""
        return {
            "environment": self.environment.value,
            "enabled_features": [
                flag.value for flag, enabled in self.flags.items() if enabled
            ],
            "disabled_features": [
                flag.value for flag, enabled in self.flags.items() if not enabled
            ],
            "quality_thresholds": self.quality_thresholds.to_dict(),
            "performance_config": self.performance_config.to_dict(),
            "active_ab_tests": [
                {
                    "test_id": test.test_id,
                    "name": test.name,
                    "variants": len(test.variants),
                }
                for test in self.ab_tests.values()
                if test.enabled
            ],
        }


# Global instance
_feature_flag_manager: FeatureFlagManager | None = None


def get_feature_flag_manager() -> FeatureFlagManager:
    """Global feature flag manager instance'ını al"""
    global _feature_flag_manager

    if _feature_flag_manager is None:
        # Environment'ı environment variable'dan al
        env_name = os.getenv("ENVIRONMENT", "production").lower()
        try:
            environment = Environment(env_name)
        except ValueError:
            environment = Environment.PRODUCTION

        _feature_flag_manager = FeatureFlagManager(environment=environment)

    return _feature_flag_manager


def initialize_feature_flags(environment: Environment, config_file: str | None = None):
    """Feature flag manager'ı initialize et"""
    global _feature_flag_manager
    _feature_flag_manager = FeatureFlagManager(
        environment=environment, config_file=config_file
    )
