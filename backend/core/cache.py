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
    cache_manager,
    cache_result,
    cache_learning_style,
    cache_exam_results,
    cache_recommendations,
    cache_content,
)

__all__ = [
    "CacheManager",
    "CacheService",
    "ConnectionMetrics",
    "ConnectionStatus",
    "cache_manager",
    "cache_result",
    "cache_learning_style",
    "cache_exam_results",
    "cache_recommendations",
    "cache_content",
]
