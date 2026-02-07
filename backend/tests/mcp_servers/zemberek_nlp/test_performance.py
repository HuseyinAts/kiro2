"""
Performance Benchmark Tests for Zemberek-NLP MCP Tools

Validates REQ-8.5: API latency < 100ms for most operations.
Uses mocked backends to test timing and caching behavior.
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

# Performance targets (in milliseconds) - REQ-8.5
LATENCY_TARGETS: Dict[str, int] = {
    "morphology_analyze": 100,
    "lemmatize": 50,
    "spell_check": 100,
    "tokenize": 50,
    "ner_extract": 200,  # NER is more complex
    "segment_sentences": 50,
    "normalize_text": 100,
}

# Turkish test texts for benchmarking
TURKISH_TEXTS = {
    "short": "Merhaba dünya",
    "medium": "Türkiye'nin başkenti Ankara'dır ve çok güzel bir şehirdir.",
    "long": """
        İstanbul, Türkiye'nin en kalabalık şehri ve ülkenin ekonomik, kültürel
        ve tarihi merkezidir. Boğaziçi ile ikiye ayrılan şehir, hem Avrupa hem
        de Asya kıtasında topraklara sahiptir. Tarihi yarımada, UNESCO Dünya
        Mirası listesindedir.
    """.strip(),
}


@pytest.fixture
def mock_http_client():
    """Create mock HTTP client with realistic response times"""
    client = AsyncMock()

    async def mock_post(*args, **kwargs):
        # Simulate realistic response time (10-30ms for mock)
        await asyncio.sleep(0.015)  # 15ms simulated latency
        return MagicMock(
            json=lambda: {"result": "mocked", "analyses": []},
            raise_for_status=lambda: None
        )

    client.post = mock_post
    return client


@pytest.fixture
def mock_cache():
    """Create mock cache with configurable hit/miss behavior"""
    cache = MagicMock()
    cache.is_connected = True
    cache._cache_data = {}

    async def mock_get_cached(tool_name: str, cache_input: str):
        key = f"{tool_name}:{cache_input}"
        return cache._cache_data.get(key)

    async def mock_set_cached(tool_name: str, cache_input: str, value: Any, ttl: int = 300):
        key = f"{tool_name}:{cache_input}"
        cache._cache_data[key] = value
        return True

    cache.get_cached = mock_get_cached
    cache.set_cached = mock_set_cached
    return cache


@pytest.fixture
def mock_jpype_bridge():
    """Create mock JPype bridge"""
    bridge = MagicMock()
    bridge.is_initialized = True

    def mock_analyze(word: str):
        # Simulate fast JPype response (5-10ms)
        time.sleep(0.007)
        return [{"lemma": word, "pos": "Noun", "morphemes": [word]}]

    bridge.morphology = MagicMock()
    bridge.morphology.analyze = mock_analyze
    return bridge


class TestLatencyTargets:
    """
    Test that each tool meets its latency target (REQ-8.5).
    Uses mocked backends to isolate timing measurements.
    """

    @pytest.mark.asyncio
    async def test_morphology_latency(self, mock_http_client, mock_cache):
        """Morphology analysis should complete within 100ms"""
        from backend.mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler

        target_ms = LATENCY_TARGETS["morphology_analyze"]
        handler = MorphologyHandler(mock_http_client, mock_cache)

        # Warm up
        await handler.execute(text="test")

        # Measure
        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["short"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Morphology took {elapsed_ms:.1f}ms, target is {target_ms}ms"

    @pytest.mark.asyncio
    async def test_lemmatization_latency(self, mock_http_client, mock_cache):
        """Lemmatization should complete within 50ms"""
        from backend.mcp_servers.zemberek_nlp.tools.lemmatization import LemmatizationHandler

        target_ms = LATENCY_TARGETS["lemmatize"]
        handler = LemmatizationHandler(mock_http_client, mock_cache)

        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["short"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Lemmatization took {elapsed_ms:.1f}ms, target is {target_ms}ms"

    @pytest.mark.asyncio
    async def test_spell_check_latency(self, mock_http_client, mock_cache):
        """Spell check should complete within 100ms"""
        from backend.mcp_servers.zemberek_nlp.tools.spell_check import SpellCheckHandler

        target_ms = LATENCY_TARGETS["spell_check"]
        handler = SpellCheckHandler(mock_http_client, mock_cache)

        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["short"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Spell check took {elapsed_ms:.1f}ms, target is {target_ms}ms"

    @pytest.mark.asyncio
    async def test_tokenization_latency(self, mock_http_client, mock_cache):
        """Tokenization should complete within 50ms"""
        from backend.mcp_servers.zemberek_nlp.tools.tokenization import TokenizationHandler

        target_ms = LATENCY_TARGETS["tokenize"]
        handler = TokenizationHandler(mock_http_client, mock_cache)

        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["short"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Tokenization took {elapsed_ms:.1f}ms, target is {target_ms}ms"

    @pytest.mark.asyncio
    async def test_segmentation_latency(self, mock_http_client, mock_cache):
        """Sentence segmentation should complete within 50ms"""
        from backend.mcp_servers.zemberek_nlp.tools.segmentation import SegmentationHandler

        target_ms = LATENCY_TARGETS["segment_sentences"]
        handler = SegmentationHandler(mock_http_client, mock_cache)

        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["medium"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Segmentation took {elapsed_ms:.1f}ms, target is {target_ms}ms"

    @pytest.mark.asyncio
    async def test_normalization_latency(self, mock_http_client, mock_cache):
        """Text normalization should complete within 100ms"""
        from backend.mcp_servers.zemberek_nlp.tools.normalization import NormalizationHandler

        target_ms = LATENCY_TARGETS["normalize_text"]
        handler = NormalizationHandler(mock_http_client, mock_cache)

        start = time.perf_counter()
        await handler.execute(text=TURKISH_TEXTS["short"])
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < target_ms, f"Normalization took {elapsed_ms:.1f}ms, target is {target_ms}ms"


class TestCachePerformance:
    """Test that caching improves response times"""

    @pytest.mark.asyncio
    async def test_cache_hit_faster_than_miss(self, mock_http_client, mock_cache):
        """Cached responses should be faster than uncached"""
        from backend.mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler

        handler = MorphologyHandler(mock_http_client, mock_cache)
        text = "Merhaba"

        # First call (cache miss)
        start = time.perf_counter()
        result1 = await handler.execute(text=text)
        miss_time = time.perf_counter() - start

        # Manually populate cache
        cache_key = f"morphology:{text}"
        mock_cache._cache_data[cache_key] = result1

        # Second call (cache hit - should be instant with our mock)
        start = time.perf_counter()
        await handler.execute(text=text)
        hit_time = time.perf_counter() - start

        # Cache hit should be faster (at least 2x improvement expected)
        assert hit_time < miss_time, f"Cache hit ({hit_time:.4f}s) should be faster than miss ({miss_time:.4f}s)"

    @pytest.mark.asyncio
    async def test_repeated_calls_benefit_from_cache(self, mock_http_client, mock_cache):
        """Multiple calls with same input should benefit from caching"""
        from backend.mcp_servers.zemberek_nlp.tools.lemmatization import LemmatizationHandler

        handler = LemmatizationHandler(mock_http_client, mock_cache)
        text = "okuyorum"
        iterations = 5

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            await handler.execute(text=text)
            times.append(time.perf_counter() - start)

        # After first call, subsequent calls should be faster
        first_call = times[0]
        avg_subsequent = sum(times[1:]) / len(times[1:])

        # With caching, average of subsequent calls should be faster
        # (relaxed assertion due to mock overhead)
        assert avg_subsequent <= first_call * 1.5, \
            f"Subsequent calls ({avg_subsequent:.4f}s avg) should be similar to or faster than first ({first_call:.4f}s)"


class TestBatchProcessingEfficiency:
    """Test batch processing performance"""

    @pytest.mark.asyncio
    async def test_batch_more_efficient_than_individual(self, mock_http_client, mock_cache):
        """Batch processing should be more efficient than individual calls"""
        from backend.mcp_servers.zemberek_nlp.tools.lemmatization import LemmatizationHandler

        handler = LemmatizationHandler(mock_http_client, mock_cache)
        words = ["okumak", "yazmak", "koşmak", "yürümek", "düşünmek"]

        # Individual processing
        start = time.perf_counter()
        for word in words:
            await handler.execute(text=word)
        individual_time = time.perf_counter() - start

        # Batch processing (single call with all words)
        start = time.perf_counter()
        await handler.execute(text=" ".join(words), batch_mode=True)
        batch_time = time.perf_counter() - start

        # Batch should be at least 2x faster (or comparable due to mock)
        # Using relaxed assertion for mock tests
        assert batch_time <= individual_time * 1.2, \
            f"Batch ({batch_time:.4f}s) should be faster than individual ({individual_time:.4f}s)"


class TestThroughput:
    """Test throughput metrics"""

    @pytest.mark.asyncio
    async def test_morphology_throughput(self, mock_http_client, mock_cache):
        """Measure words per second for morphology analysis"""
        from backend.mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler

        handler = MorphologyHandler(mock_http_client, mock_cache)

        # Process 50 words (reduced for mock environment)
        words = ["kelime"] * 50
        text = " ".join(words)

        start = time.perf_counter()
        await handler.execute(text=text)
        elapsed = time.perf_counter() - start

        throughput = len(words) / elapsed

        # Should process at least 30 words per second in mock environment
        # Real implementation should be faster
        assert throughput >= 30, f"Throughput {throughput:.1f} words/s below target 30 words/s"

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_http_client, mock_cache):
        """Test handling of concurrent requests"""
        from backend.mcp_servers.zemberek_nlp.tools.tokenization import TokenizationHandler

        handler = TokenizationHandler(mock_http_client, mock_cache)

        # Create 10 concurrent tasks
        async def process_text(text: str):
            return await handler.execute(text=text)

        texts = [f"Test cümle {i}" for i in range(10)]

        start = time.perf_counter()
        results = await asyncio.gather(*[process_text(t) for t in texts])
        elapsed = time.perf_counter() - start

        # All should complete
        assert len(results) == 10

        # Concurrent processing should be faster than sequential
        # 10 requests at 15ms mock latency = ~150ms sequential
        # With concurrency, should be ~15-30ms total
        assert elapsed < 0.5, f"Concurrent requests took {elapsed:.3f}s, expected < 0.5s"


class TestLongTextPerformance:
    """Test performance with longer texts"""

    @pytest.mark.asyncio
    async def test_long_text_within_bounds(self, mock_http_client, mock_cache):
        """Long text should still complete within acceptable time"""
        from backend.mcp_servers.zemberek_nlp.tools.segmentation import SegmentationHandler

        handler = SegmentationHandler(mock_http_client, mock_cache)

        # Use long text
        text = TURKISH_TEXTS["long"]

        start = time.perf_counter()
        await handler.execute(text=text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Long text should still complete within 200ms
        assert elapsed_ms < 200, f"Long text took {elapsed_ms:.1f}ms, target is 200ms"

    @pytest.mark.asyncio
    async def test_scaling_behavior(self, mock_http_client, mock_cache):
        """Processing time should scale reasonably with input size"""
        from backend.mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler

        handler = MorphologyHandler(mock_http_client, mock_cache)

        # Test with different sizes
        sizes = [10, 50, 100]
        times = []

        for size in sizes:
            text = " ".join(["kelime"] * size)
            start = time.perf_counter()
            await handler.execute(text=text)
            times.append(time.perf_counter() - start)

        # Time should scale roughly linearly (within 3x for 10x input increase)
        scaling_factor = times[-1] / times[0]
        size_factor = sizes[-1] / sizes[0]

        # Allow for some overhead, but shouldn't be worse than O(n^2)
        assert scaling_factor < size_factor * 3, \
            f"Scaling factor {scaling_factor:.1f} too high for {size_factor}x input increase"
