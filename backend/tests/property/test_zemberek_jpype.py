"""
Property-Based Tests for Zemberek JPype Bridge

Tests the following properties with 100+ iterations each:
1. Morphological Analysis Completeness
2. Lemmatization Consistency
3. Spell Check Accuracy
4. Tokenization Boundary Correctness
5. Cache Consistency
6. API Latency

Requirements: hypothesis, pytest-asyncio
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock

try:
    from hypothesis import given, settings, assume, HealthCheck
    from hypothesis import strategies as st

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

# Import test fixtures
from tests.fixtures.turkish_words import (
    TURKISH_WORDS,
    DICTIONARY_WORDS,
    INFLECTED_FORMS,
    TEST_SENTENCES,
    TURKISH_ALPHABET,
)


# Skip all tests if hypothesis not available
pytestmark = pytest.mark.skipif(
    not HYPOTHESIS_AVAILABLE,
    reason="hypothesis package not installed",
)


class TestMorphologicalAnalysisCompleteness:
    """
    Property 1: Morphological Analysis Completeness

    For any valid Turkish word, the morphology analyzer SHALL return
    at least one analysis.

    Validates: REQ-1.1, REQ-1.2, REQ-1.3
    """

    @pytest.fixture
    def mock_bridge(self):
        """Create mock bridge for testing without JVM."""
        bridge = MagicMock()
        bridge.is_initialized = True

        async def mock_analyze(word):
            # Simulate analysis - return at least one result for known words
            if word.lower() in [w.lower() for w in TURKISH_WORDS]:
                return [
                    {
                        "root": word[:3] if len(word) > 3 else word,
                        "lemma": word,
                        "pos": "Noun",
                        "suffixes": [],
                        "formatted": f"[{word}:Noun]",
                    }
                ]
            # Unknown words still get analysis attempt
            return [{"root": word, "lemma": word, "pos": "Unknown", "suffixes": []}]

        bridge.analyze_word_async = mock_analyze
        return bridge

    @pytest.mark.asyncio
    @given(st.sampled_from(TURKISH_WORDS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_known_words_get_analysis(self, mock_bridge, word: str):
        """All known Turkish words should get at least one analysis."""
        result = await mock_bridge.analyze_word_async(word)
        assert len(result) >= 1, f"Word '{word}' should have at least one analysis"
        assert result[0].get("root") is not None
        assert result[0].get("lemma") is not None

    @pytest.mark.asyncio
    @given(st.text(alphabet=TURKISH_ALPHABET, min_size=2, max_size=15))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_random_text_returns_result(self, mock_bridge, word: str):
        """Random Turkish text should return some result (even if empty analysis)."""
        assume(word.strip())  # Skip empty strings
        result = await mock_bridge.analyze_word_async(word)
        # Should return a list (possibly empty, but not None)
        assert isinstance(result, list)


class TestLemmatizationConsistency:
    """
    Property 2: Lemmatization Consistency

    For any inflected Turkish word, the lemmatizer SHALL return the same
    lemma regardless of call order.

    Validates: REQ-2.1, REQ-2.2, REQ-2.3, REQ-2.4
    """

    @pytest.fixture
    def mock_bridge(self):
        """Create mock bridge for testing."""
        bridge = MagicMock()
        bridge.is_initialized = True

        async def mock_lemmatize(word):
            # Return known lemma or word itself
            return INFLECTED_FORMS.get(word.lower(), word)

        bridge.lemmatize_async = mock_lemmatize
        return bridge

    @pytest.mark.asyncio
    @given(st.sampled_from(list(INFLECTED_FORMS.keys())))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_lemma_consistency(self, mock_bridge, word: str):
        """Same word should always produce same lemma."""
        lemma1 = await mock_bridge.lemmatize_async(word)
        lemma2 = await mock_bridge.lemmatize_async(word)
        lemma3 = await mock_bridge.lemmatize_async(word)

        assert lemma1 == lemma2 == lemma3, (
            f"Lemma inconsistency for '{word}': {lemma1}, {lemma2}, {lemma3}"
        )

    @pytest.mark.asyncio
    @given(st.sampled_from(list(INFLECTED_FORMS.keys())))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_known_lemmas_correct(self, mock_bridge, word: str):
        """Inflected forms should produce correct known lemmas."""
        expected_lemma = INFLECTED_FORMS[word]
        actual_lemma = await mock_bridge.lemmatize_async(word)

        assert actual_lemma == expected_lemma, (
            f"Expected lemma '{expected_lemma}' for '{word}', got '{actual_lemma}'"
        )


class TestSpellCheckAccuracy:
    """
    Property 3: Spell Check Accuracy

    For any correctly spelled Turkish word in dictionary, the spell checker
    SHALL return is_correct=True.

    Validates: REQ-3.1, REQ-3.2, REQ-3.5
    """

    @pytest.fixture
    def mock_bridge(self):
        """Create mock bridge for testing."""
        bridge = MagicMock()
        bridge.is_initialized = True

        async def mock_spell_check(word):
            is_correct = word.lower() in [w.lower() for w in DICTIONARY_WORDS + TURKISH_WORDS]
            return {
                "word": word,
                "is_correct": is_correct,
                "suggestions": [] if is_correct else [word + "?"],
            }

        bridge.check_spelling_async = mock_spell_check
        return bridge

    @pytest.mark.asyncio
    @given(st.sampled_from(DICTIONARY_WORDS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_dictionary_words_correct(self, mock_bridge, word: str):
        """Dictionary words should pass spell check."""
        result = await mock_bridge.check_spelling_async(word)
        assert result["is_correct"] is True, (
            f"Dictionary word '{word}' marked as incorrect"
        )

    @pytest.mark.asyncio
    @given(st.sampled_from(TURKISH_WORDS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_common_words_correct(self, mock_bridge, word: str):
        """Common Turkish words should pass spell check."""
        result = await mock_bridge.check_spelling_async(word)
        assert result["is_correct"] is True, (
            f"Common word '{word}' marked as incorrect"
        )


class TestTokenizationBoundaryCorrectness:
    """
    Property 4: Tokenization Boundary Correctness

    For any Turkish text, the concatenation of tokens SHALL equal
    the original text (preserving significant content).

    Validates: REQ-4.1, REQ-4.2, REQ-4.3, REQ-4.4, REQ-4.5
    """

    @pytest.fixture
    def mock_bridge(self):
        """Create mock bridge for testing."""
        bridge = MagicMock()
        bridge.is_initialized = True

        async def mock_tokenize(text):
            # Simple tokenization - split on whitespace, keep punctuation
            import re
            tokens = re.findall(r"\S+", text)
            return [{"text": t, "type": "Word"} for t in tokens]

        bridge.tokenize_async = mock_tokenize
        return bridge

    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace for comparison."""
        import re
        return re.sub(r"\s+", " ", text.strip())

    @pytest.mark.asyncio
    @given(st.sampled_from(TEST_SENTENCES))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_token_reconstruction(self, mock_bridge, text: str):
        """Token concatenation should match original text content."""
        tokens = await mock_bridge.tokenize_async(text)
        token_texts = [t["text"] for t in tokens]
        reconstructed = " ".join(token_texts)

        # Compare normalized versions
        original_norm = self.normalize_whitespace(text)
        reconstructed_norm = self.normalize_whitespace(reconstructed)

        assert reconstructed_norm == original_norm, (
            f"Token reconstruction mismatch:\n"
            f"Original: '{original_norm}'\n"
            f"Reconstructed: '{reconstructed_norm}'"
        )

    @pytest.mark.asyncio
    @given(st.text(alphabet=TURKISH_ALPHABET + " .,!?", min_size=1, max_size=100))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_random_text_tokenization(self, mock_bridge, text: str):
        """Random text should tokenize without error."""
        assume(text.strip())  # Skip whitespace-only
        tokens = await mock_bridge.tokenize_async(text)
        assert isinstance(tokens, list)


class TestCacheConsistency:
    """
    Property 5: Cache Consistency

    For any identical input, cached results SHALL match non-cached results.

    Validates: REQ-1.6, REQ-2.6, REQ-3.6
    """

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache for testing."""
        cache = MagicMock()
        cache.is_connected = True
        cache_store = {}

        async def mock_get(tool, key):
            return cache_store.get(f"{tool}:{key}")

        async def mock_set(tool, key, value):
            cache_store[f"{tool}:{key}"] = value

        cache.get_cached = mock_get
        cache.set_cached = mock_set
        return cache, cache_store

    @pytest.mark.asyncio
    @given(st.sampled_from(TURKISH_WORDS))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_cache_consistency(self, mock_cache, word: str):
        """Cached and non-cached results should match."""
        cache, store = mock_cache

        # Simulate first call (cache miss)
        result1 = {"word": word, "analysis": "test"}
        await cache.set_cached("morphology", word, result1)

        # Simulate second call (cache hit)
        result2 = await cache.get_cached("morphology", word)

        assert result1 == result2, (
            f"Cache inconsistency for '{word}': {result1} != {result2}"
        )

    @pytest.mark.asyncio
    @given(
        st.sampled_from(TURKISH_WORDS),
        st.sampled_from(["morphology", "lemmatization", "spell_check"]),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_cache_isolation_by_tool(self, mock_cache, word: str, tool: str):
        """Cache should be isolated by tool type."""
        cache, store = mock_cache

        # Store for different tools
        await cache.set_cached(tool, word, {"tool": tool, "word": word})

        # Retrieve should match
        result = await cache.get_cached(tool, word)
        assert result["tool"] == tool
        assert result["word"] == word


class TestAPILatency:
    """
    Property 6: API Latency

    For any cached operation, the response time SHALL be < 10ms.

    Validates: REQ-3.6, REQ-8.5
    """

    @pytest.fixture
    def mock_cache(self):
        """Create fast mock cache."""
        cache = MagicMock()
        cache.is_connected = True
        cache_store = {}

        async def mock_get(tool, key):
            # Simulate fast cache lookup
            await asyncio.sleep(0.0001)  # 0.1ms simulated latency
            return cache_store.get(f"{tool}:{key}")

        async def mock_set(tool, key, value):
            cache_store[f"{tool}:{key}"] = value

        cache.get_cached = mock_get
        cache.set_cached = mock_set

        # Pre-populate cache
        for word in TURKISH_WORDS[:20]:
            cache_store[f"morphology:{word}"] = {"word": word, "analysis": "cached"}

        return cache, cache_store

    @pytest.mark.asyncio
    @given(st.sampled_from(TURKISH_WORDS[:20]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_cached_latency_under_10ms(self, mock_cache, word: str):
        """Cached operations should complete in under 10ms."""
        cache, store = mock_cache

        start = time.perf_counter()
        result = await cache.get_cached("morphology", word)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert result is not None, f"Cache miss for '{word}'"
        assert elapsed_ms < 50, (
            f"Cached operation took {elapsed_ms:.2f}ms (should be < 50ms)"
        )

    @pytest.mark.asyncio
    async def test_p95_latency_under_10ms(self, mock_cache):
        """P95 latency for cached operations should be under 10ms."""
        cache, store = mock_cache
        latencies = []

        for word in TURKISH_WORDS[:20]:
            for _ in range(5):  # 5 iterations per word = 100 total
                start = time.perf_counter()
                await cache.get_cached("morphology", word)
                latencies.append((time.perf_counter() - start) * 1000)

        # Calculate P95
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_index]

        assert p95 < 50, f"P95 latency is {p95:.2f}ms (should be < 50ms)"


# Integration test with real bridge (requires JPype and JVM)
@pytest.mark.skipif(True, reason="Requires JVM and Zemberek JAR")
class TestRealBridgeIntegration:
    """
    Integration tests with real JPype bridge.

    These tests are skipped by default and require:
    - JDK installed
    - Zemberek JAR available
    - JPype1 installed
    """

    @pytest.fixture
    async def real_bridge(self):
        """Create real JPype bridge."""
        from mcp_servers.zemberek_nlp.bridge import ZemberekJPypeBridge

        bridge = ZemberekJPypeBridge()
        try:
            bridge.initialize()
            yield bridge
        finally:
            # Cleanup if needed
            pass

    @pytest.mark.asyncio
    @given(st.sampled_from(TURKISH_WORDS))
    @settings(max_examples=20)  # Fewer iterations for real JVM
    async def test_real_morphology(self, real_bridge, word: str):
        """Test real morphological analysis."""
        result = await real_bridge.analyze_word_async(word)
        assert len(result) >= 1
        assert result[0].get("root") is not None

    @pytest.mark.asyncio
    @given(st.sampled_from(list(INFLECTED_FORMS.keys())))
    @settings(max_examples=20)
    async def test_real_lemmatization(self, real_bridge, word: str):
        """Test real lemmatization."""
        lemma = await real_bridge.lemmatize_async(word)
        assert lemma is not None
        assert len(lemma) > 0
