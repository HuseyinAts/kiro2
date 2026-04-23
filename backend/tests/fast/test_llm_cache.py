"""
Tests for LLM Cache System
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from core.llm_cache import (
    CacheEntry,
    LLMCache,
    LLMCacheConfig,
    LLMCacheStats,
    cached_llm,
    get_llm_cache,
)


class TestLLMCacheConfig:
    """Test LLM Cache Configuration"""

    def test_default_config(self):
        """Test default configuration values"""
        config = LLMCacheConfig()

        assert config.redis_url == "redis://localhost:6379/0"
        assert config.default_ttl == 3600
        assert config.long_ttl == 86400
        assert config.max_prompt_length == 4000
        assert config.enable_compression is True
        assert config.turkish_normalization is True
        assert config.key_prefix == "kiro2:llm"

    def test_custom_config(self):
        """Test custom configuration"""
        config = LLMCacheConfig(
            redis_url="redis://custom:6379/1", default_ttl=7200, key_prefix="custom:llm"
        )

        assert config.redis_url == "redis://custom:6379/1"
        assert config.default_ttl == 7200
        assert config.key_prefix == "custom:llm"


class TestCacheEntry:
    """Test Cache Entry Model"""

    def test_cache_entry_creation(self):
        """Test creating cache entry"""
        entry = CacheEntry(
            response="Test response",
            prompt_hash="abc123",
            model="gpt-4",
            timestamp=datetime.now(),
            token_count=100,
            cost=0.002,
        )

        assert entry.response == "Test response"
        assert entry.prompt_hash == "abc123"
        assert entry.model == "gpt-4"
        assert entry.token_count == 100
        assert entry.cost == 0.002

    def test_cache_entry_with_metadata(self):
        """Test cache entry with metadata"""
        entry = CacheEntry(
            response="Response",
            prompt_hash="hash",
            model="claude",
            timestamp=datetime.now(),
            metadata={"user_id": 123, "session": "abc"},
        )

        assert entry.metadata["user_id"] == 123
        assert entry.metadata["session"] == "abc"


class TestLLMCacheStats:
    """Test Cache Statistics"""

    def test_initial_stats(self):
        """Test initial statistics"""
        stats = LLMCacheStats()

        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.hit_ratio == 0.0
        assert stats.miss_ratio == 1.0

    def test_hit_ratio_calculation(self):
        """Test hit ratio calculation"""
        stats = LLMCacheStats(total_requests=100, cache_hits=75, cache_misses=25)

        assert stats.hit_ratio == 0.75
        assert stats.miss_ratio == 0.25

    def test_cost_tracking(self):
        """Test cost tracking"""
        stats = LLMCacheStats(total_tokens_saved=10000, total_cost_saved=5.50)

        assert stats.total_tokens_saved == 10000
        assert stats.total_cost_saved == 5.50


class TestLLMCache:
    """Test LLM Cache Implementation"""

    @pytest.fixture
    def cache_config(self):
        """Create test cache config"""
        return LLMCacheConfig(redis_url="redis://localhost:6379/0", default_ttl=3600)

    @pytest.fixture
    def llm_cache(self, cache_config):
        """Create LLM cache instance"""
        return LLMCache(config=cache_config)

    def test_cache_initialization(self, llm_cache):
        """Test cache initialization"""
        assert llm_cache.config is not None
        assert llm_cache.stats is not None
        assert llm_cache._redis_available is False
        assert len(llm_cache._memory_cache) == 0

    def test_normalize_prompt_basic(self, llm_cache):
        """Test basic prompt normalization"""
        prompt = "  What is 2+2?  "
        normalized = llm_cache._normalize_prompt(prompt)

        assert normalized == "What is 2+2?"

    def test_normalize_prompt_turkish(self, llm_cache):
        """Test Turkish character normalization"""
        prompt = "İstanbul'da hava nasıl?"
        normalized = llm_cache._normalize_prompt(prompt)

        # Should normalize İ to i
        assert "istanbul" in normalized.lower()

    def test_normalize_prompt_truncation(self, llm_cache):
        """Test prompt truncation for long prompts"""
        long_prompt = "A" * 5000
        normalized = llm_cache._normalize_prompt(long_prompt)

        assert len(normalized) == llm_cache.config.max_prompt_length

    def test_generate_cache_key_basic(self, llm_cache):
        """Test cache key generation"""
        key = llm_cache._generate_cache_key(prompt="What is AI?", model="gpt-4")

        assert key.startswith("kiro2:llm:gpt-4:")
        assert len(key) > 20  # Has hash component

    def test_generate_cache_key_consistency(self, llm_cache):
        """Test cache key consistency"""
        key1 = llm_cache._generate_cache_key(prompt="Test prompt", model="gpt-4")
        key2 = llm_cache._generate_cache_key(prompt="Test prompt", model="gpt-4")

        assert key1 == key2

    def test_generate_cache_key_with_kwargs(self, llm_cache):
        """Test cache key with additional parameters"""
        key1 = llm_cache._generate_cache_key(
            prompt="Test", model="gpt-4", temperature=0.7
        )
        key2 = llm_cache._generate_cache_key(
            prompt="Test", model="gpt-4", temperature=0.9
        )

        # Different temperature should create different keys
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_miss(self, llm_cache):
        """Test cache miss"""
        result = await llm_cache.get(prompt="Never cached before", model="gpt-4")

        assert result is None
        assert llm_cache.stats.cache_misses == 1
        assert llm_cache.stats.cache_hits == 0

    @pytest.mark.asyncio
    async def test_memory_cache_set_and_get(self, llm_cache):
        """Test memory cache set and get"""
        prompt = "What is 2+2?"
        response = "4"

        # Set in cache
        success = await llm_cache.set(
            prompt=prompt, response=response, model="gpt-4", token_count=50, cost=0.001
        )

        assert success is True
        assert len(llm_cache._memory_cache) == 1

        # Get from cache
        cached_response = await llm_cache.get(prompt=prompt, model="gpt-4")

        assert cached_response == response
        assert llm_cache.stats.cache_hits == 1

    @pytest.mark.asyncio
    async def test_memory_cache_lru_eviction(self, llm_cache):
        """Test LRU eviction in memory cache"""
        llm_cache._memory_cache_max_size = 3

        # Add 4 items (should trigger eviction)
        for i in range(4):
            await llm_cache.set(
                prompt=f"Prompt {i}", response=f"Response {i}", model="gpt-4"
            )

        # Should only have 3 items (max size)
        assert len(llm_cache._memory_cache) == 3

    @pytest.mark.asyncio
    async def test_redis_cache_with_mock(self, llm_cache):
        """Test Redis caching with mock"""
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        llm_cache.redis_client = mock_redis
        llm_cache._redis_available = True

        # Set value
        await llm_cache.set(
            prompt="Test prompt", response="Test response", model="gpt-4", ttl=3600
        )

        # Verify Redis was called
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats(self, llm_cache):
        """Test getting cache statistics"""
        # Simulate some cache activity
        llm_cache.stats.total_requests = 100
        llm_cache.stats.cache_hits = 75
        llm_cache.stats.cache_misses = 25
        llm_cache.stats.total_tokens_saved = 5000
        llm_cache.stats.total_cost_saved = 2.50

        stats = await llm_cache.get_stats()

        assert stats["total_requests"] == 100
        assert stats["cache_hits"] == 75
        assert stats["cache_misses"] == 25
        assert stats["hit_ratio"] == 0.75
        assert stats["total_tokens_saved"] == 5000
        assert stats["total_cost_saved"] == 2.50

    @pytest.mark.asyncio
    async def test_clear_all(self, llm_cache):
        """Test clearing entire cache"""
        # Add some items
        await llm_cache.set("Prompt 1", "Response 1", "gpt-4")
        await llm_cache.set("Prompt 2", "Response 2", "gpt-4")

        assert len(llm_cache._memory_cache) == 2

        # Clear all
        success = await llm_cache.clear_all()

        assert success is True
        assert len(llm_cache._memory_cache) == 0


class TestCachedLLMDecorator:
    """Test cached_llm decorator"""

    @pytest.mark.asyncio
    async def test_decorator_basic(self):
        """Test basic decorator functionality"""
        mock_cache = LLMCache()

        call_count = 0

        @cached_llm(ttl=3600, model="gpt-4", cache_instance=mock_cache)
        async def generate_response(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Generated: {prompt}"

        # First call - should execute function
        result1 = await generate_response("Test prompt")
        assert call_count == 1
        assert result1 == "Generated: Test prompt"

        # Second call - should use cache
        result2 = await generate_response("Test prompt")
        assert call_count == 1  # Should not increment
        assert result2 == "Generated: Test prompt"

    @pytest.mark.asyncio
    async def test_decorator_different_prompts(self):
        """Test decorator with different prompts"""
        mock_cache = LLMCache()

        call_count = 0

        @cached_llm(ttl=3600, model="gpt-4", cache_instance=mock_cache)
        async def generate_response(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Generated: {prompt}"

        # Different prompts should execute function
        result1 = await generate_response("Prompt 1")
        result2 = await generate_response("Prompt 2")

        assert call_count == 2
        assert result1 == "Generated: Prompt 1"
        assert result2 == "Generated: Prompt 2"


class TestGlobalCacheInstance:
    """Test global cache instance management"""

    @pytest.mark.asyncio
    async def test_get_llm_cache_singleton(self):
        """Test global cache instance is singleton"""
        cache1 = await get_llm_cache()
        cache2 = await get_llm_cache()

        # Should return same instance
        assert cache1 is cache2


# Integration test example (requires Redis)
@pytest.mark.skipif(True, reason="Requires running Redis")
class TestLLMCacheIntegration:
    """Integration tests requiring actual Redis"""

    @pytest.mark.asyncio
    async def test_redis_integration(self):
        """Test actual Redis integration"""
        cache = LLMCache()
        initialized = await cache.initialize()

        if not initialized:
            pytest.skip("Redis not available")

        # Test set and get
        await cache.set(
            prompt="Integration test prompt",
            response="Integration test response",
            model="gpt-4",
            ttl=60,
        )

        result = await cache.get(prompt="Integration test prompt", model="gpt-4")

        assert result == "Integration test response"

        # Cleanup
        await cache.close()
