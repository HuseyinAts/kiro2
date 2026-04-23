"""
Redis Cache Manager - Performance Optimization

DEPRECATED: Bu dosya geriye uyumluluk için korunuyor.
Tüm implementasyon core/cache/cache_manager.py'ye taşındı.
"""

# Re-export everything from the new location for backwards compatibility
from core.cache.cache_manager import (
    CacheManager,
    CacheService,
    ConnectionMetrics,
    ConnectionStatus,
    cache_content,
    cache_exam_results,
    cache_learning_style,
    cache_manager,
    cache_recommendations,
    cache_result,
)

__all__ = [
    "CacheManager",
    "CacheService",
    "ConnectionMetrics",
    "ConnectionStatus",
    "cache_content",
    "cache_exam_results",
    "cache_learning_style",
    "cache_manager",
    "cache_recommendations",
    "cache_result",
]
