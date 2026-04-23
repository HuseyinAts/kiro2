"""
Zemberek NLP Cache Package
Redis-based caching with namespace support
"""

from .redis_cache import (
    ZemberekCache,
    generate_cache_key,
    get_cache,
)

__all__ = [
    "ZemberekCache",
    "generate_cache_key",
    "get_cache",
]
