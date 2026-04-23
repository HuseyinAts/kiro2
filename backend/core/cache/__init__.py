"""
Cache Module - API Response Time Optimization

Bu modül, Redis tabanlı caching utilities sağlar.
Query caching, response caching ve cache invalidation destekler.

Author: Kiro AI
Date: 2026-01-14
Requirements: REQ-5.4
"""

# Import from local cache_manager.py module
# Bu import'lar 456+ dosyada kullanılıyor
from .cache_manager import (
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
from .query_cache import (
    QueryCache,
    QueryCacheWarmer,
    cached_query,
    get_query_cache,
    init_query_cache,
)

__all__ = [
    # Query cache
    "QueryCache",
    "QueryCacheWarmer",
    "cached_query",
    "get_query_cache",
    "init_query_cache",
    # Redis cache manager
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
