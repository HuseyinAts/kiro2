"""
Learning Path Configuration Module

Centralized configuration for all learning path components.
Consolidates scattered configs from core/, strategies/, integrations/.

Teknofest 2025 - Eğitim Eylemci Projesi
"""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class LearningPathConfig:
    """
    Centralized configuration for learning path system.

    All settings are immutable and loaded from environment variables.
    Uses dataclass(frozen=True) for thread-safety and caching.

    Configuration Groups:
        - Cache settings (Redis + in-memory)
        - Rate limits
        - Circuit breaker settings
        - Search settings
        - TTL settings
    """

    # ==================== CACHE SETTINGS ====================

    # Redis connection
    CACHE_REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # L1 Cache (in-memory LRU cache)
    CACHE_L1_MAX_SIZE: int = int(os.getenv("LEARNING_PATH_CACHE_L1_SIZE", "20"))

    # Default TTL for cached items (seconds)
    CACHE_DEFAULT_TTL: int = int(os.getenv("LEARNING_PATH_CACHE_TTL", "300"))

    # Completion data TTL (15 minutes)
    CACHE_COMPLETION_TTL: int = 900

    # Profile cache TTL (30 minutes)
    PROFILE_CACHE_TTL: int = 1800

    # Resource cache TTL (1 hour)
    RESOURCE_CACHE_TTL: int = 3600

    # Path cache TTL (10 minutes)
    PATH_CACHE_TTL: int = 600

    # ==================== RATE LIMITS (per minute) ====================

    # Profile creation (light operation)
    RATE_LIMIT_CREATE_PROFILE: str = "10/minute"

    # Path creation (expensive AI operation)
    RATE_LIMIT_CREATE_PATH: str = "5/minute"

    # Resource search (moderate operation)
    RATE_LIMIT_SEARCH_RESOURCES: str = "30/minute"

    # Default rate limit for all other operations
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # Assessment generation (expensive AI operation)
    RATE_LIMIT_CREATE_ASSESSMENT: str = "8/minute"

    # Profile update (moderate operation)
    RATE_LIMIT_UPDATE_PROFILE: str = "15/minute"

    # ==================== IN-MEMORY CACHE SETTINGS ====================

    # TTLCache settings for student profiles
    PROFILE_CACHE_MAXSIZE: int = 1000

    # Resource cache max size
    RESOURCE_CACHE_MAXSIZE: int = 500

    # Path cache max size
    PATH_CACHE_MAXSIZE: int = 200

    # ==================== CIRCUIT BREAKER SETTINGS ====================

    # Number of failures before circuit opens
    CB_FAILURE_THRESHOLD: int = 5

    # Seconds to wait before attempting recovery
    CB_RECOVERY_TIMEOUT: int = 30

    # Max retry attempts for failed operations
    CB_MAX_RETRY_ATTEMPTS: int = 3

    # ==================== SEARCH SETTINGS ====================

    # Maximum number of resources returned per search
    MAX_RESOURCES_PER_SEARCH: int = 20

    # Default video duration for estimates (minutes)
    DEFAULT_VIDEO_DURATION: int = 10

    # Maximum search results to cache
    MAX_SEARCH_RESULTS_CACHE: int = 100

    # Search timeout (seconds)
    SEARCH_TIMEOUT: int = 30

    # ==================== LEARNING PATH GENERATION SETTINGS ====================

    # Default number of phases in learning path
    DEFAULT_PATH_PHASES: int = 4

    # Minimum resources per phase
    MIN_RESOURCES_PER_PHASE: int = 2

    # Maximum resources per phase
    MAX_RESOURCES_PER_PHASE: int = 8

    # Default study time per day (minutes)
    DEFAULT_STUDY_TIME_DAILY: int = 120

    # ==================== IRT/ZPD SETTINGS ====================

    # Optimal success probability range for ZPD
    ZPD_SUCCESS_PROB_MIN: float = 0.15
    ZPD_SUCCESS_PROB_MAX: float = 0.85

    # IRT difficulty range
    IRT_DIFFICULTY_MIN: float = -4.0
    IRT_DIFFICULTY_MAX: float = 4.0

    # IRT discrimination range
    IRT_DISCRIMINATION_MIN: float = 0.2
    IRT_DISCRIMINATION_MAX: float = 4.0

    # IRT guessing parameter range
    IRT_GUESSING_MIN: float = 0.0
    IRT_GUESSING_MAX: float = 0.35

    # ==================== LOGGING SETTINGS ====================

    # Enable verbose logging
    ENABLE_VERBOSE_LOGGING: bool = os.getenv("LEARNING_PATH_VERBOSE_LOGGING", "false").lower() == "true"

    # Log cache hits/misses
    LOG_CACHE_OPERATIONS: bool = os.getenv("LOG_CACHE_OPERATIONS", "false").lower() == "true"

    # ==================== FEATURE FLAGS ====================

    # Enable Redis caching (fallback to in-memory if disabled)
    ENABLE_REDIS_CACHE: bool = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"

    # Enable circuit breaker
    ENABLE_CIRCUIT_BREAKER: bool = os.getenv("ENABLE_CIRCUIT_BREAKER", "true").lower() == "true"

    # Enable resource ranking
    ENABLE_RESOURCE_RANKING: bool = os.getenv("ENABLE_RESOURCE_RANKING", "true").lower() == "true"

    # Enable learning style detection
    ENABLE_LEARNING_STYLE_DETECTION: bool = os.getenv("ENABLE_LEARNING_STYLE_DETECTION", "true").lower() == "true"

    # ==================== API KEYS ====================

    # YouTube Data API v3 key
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")


@lru_cache(maxsize=1)
def get_learning_path_config() -> LearningPathConfig:
    """
    Get singleton instance of LearningPathConfig.

    Uses lru_cache to ensure only one instance exists.
    Thread-safe and efficient.

    Returns:
        LearningPathConfig: Frozen configuration instance

    Example:
        >>> config = get_learning_path_config()
        >>> config.CACHE_REDIS_URL
        'redis://localhost:6379/0'
        >>> config.RATE_LIMIT_CREATE_PATH
        '5/minute'
    """
    return LearningPathConfig()


# Convenience aliases for backward compatibility
config = get_learning_path_config()

__all__ = [
    "LearningPathConfig",
    "get_learning_path_config",
    "config",
]
