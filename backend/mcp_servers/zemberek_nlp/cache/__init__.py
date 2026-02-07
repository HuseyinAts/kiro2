"""
Zemberek NLP Cache Package
Redis-based caching with namespace support
"""

from .redis_cache import (
    ZemberekCache,
    get_cache,
    generate_cache_key,
)

__all__ = [
    "ZemberekCache",
    "get_cache",
    "generate_cache_key",
]
