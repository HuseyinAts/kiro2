"""
Unit Tests for Zemberek NLP Redis Cache
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCacheKeyGeneration:
    """Tests for cache key generation"""

    def test_basic_key_generation(self):
        """Test basic cache key generation"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import (
            generate_cache_key,
        )

        key = generate_cache_key("zemberek", "morphology", "test input")

        assert key.startswith("zemberek:morphology:")
        assert len(key) > len("zemberek:morphology:")

    def test_deterministic_keys(self):
        """Test cache keys are deterministic"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import (
            generate_cache_key,
        )

        key1 = generate_cache_key("zemberek", "morphology", "same input")
        key2 = generate_cache_key("zemberek", "morphology", "same input")

        assert key1 == key2

    def test_different_inputs_different_keys(self):
        """Test different inputs produce different keys"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import (
            generate_cache_key,
        )

        key1 = generate_cache_key("zemberek", "morphology", "input one")
        key2 = generate_cache_key("zemberek", "morphology", "input two")

        assert key1 != key2

    def test_case_normalization(self):
        """Test case normalization in key generation"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import (
            generate_cache_key,
        )

        key1 = generate_cache_key("zemberek", "morphology", "Test Input")
        key2 = generate_cache_key("zemberek", "morphology", "test input")

        assert key1 == key2  # Should be normalized to same key

    def test_whitespace_normalization(self):
        """Test whitespace normalization"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import (
            generate_cache_key,
        )

        key1 = generate_cache_key("zemberek", "morphology", "  test input  ")
        key2 = generate_cache_key("zemberek", "morphology", "test input")

        assert key1 == key2


class TestCacheStats:
    """Tests for cache statistics"""

    def test_initial_stats(self):
        """Test initial cache stats"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import CacheStats

        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.errors == 0
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import CacheStats

        stats = CacheStats()
        stats.hits = 80
        stats.misses = 20

        assert stats.hit_rate == 0.8

    def test_to_dict(self):
        """Test stats to dictionary conversion"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import CacheStats

        stats = CacheStats()
        stats.hits = 10
        stats.misses = 5

        stats_dict = stats.to_dict()

        assert "hits" in stats_dict
        assert "misses" in stats_dict
        assert "hit_rate" in stats_dict
        assert stats_dict["hits"] == 10


class TestZemberekCache:
    """Tests for ZemberekCache class"""

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test cache when disabled"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import ZemberekCache

        with patch("backend.mcp_servers.zemberek_nlp.cache.redis_cache.get_config") as mock_config:
            mock_config.return_value = MagicMock(cache_enabled=False)
            cache = ZemberekCache()

            result = await cache.connect()

            assert result is False
            assert cache.is_connected is False

    @pytest.mark.asyncio
    async def test_get_cached_when_disconnected(self):
        """Test get_cached returns None when disconnected"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import ZemberekCache

        cache = ZemberekCache()
        cache._connected = False

        result = await cache.get_cached("morphology", "test")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_cached_when_disconnected(self):
        """Test set_cached returns False when disconnected"""
        from backend.mcp_servers.zemberek_nlp.cache.redis_cache import ZemberekCache

        cache = ZemberekCache()
        cache._connected = False

        result = await cache.set_cached("morphology", "test", {"data": "value"})

        assert result is False


class TestTTLConfiguration:
    """Tests for TTL configuration"""

    def test_default_ttl(self):
        """Test default TTL values"""
        from backend.mcp_servers.zemberek_nlp.config import CACHE_TTL, get_ttl

        # Morphology should have 1 hour TTL
        assert CACHE_TTL["morphology"] == 3600

        # Unknown tool should get default
        assert get_ttl("unknown_tool") == 3600

    def test_tool_specific_ttl(self):
        """Test tool-specific TTL values"""
        from backend.mcp_servers.zemberek_nlp.config import get_ttl

        # Spell check has shorter TTL
        assert get_ttl("spell_check") == 1800

        # NER has shorter TTL
        assert get_ttl("ner") == 1800
