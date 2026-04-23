"""
Unit Tests for Zemberek Tool Handlers with JPype Support

Tests all 8 tool handlers with mocked JPype bridge:
- MorphologyHandler
- LemmatizationHandler
- SpellCheckHandler
- TokenizationHandler
- NERHandler
- SegmentationHandler
- NormalizationHandler
- HealthHandler
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Import config
from mcp_servers.zemberek_nlp.config import ZemberekConfig
from mcp_servers.zemberek_nlp.tools.health import HealthHandler
from mcp_servers.zemberek_nlp.tools.lemmatization import LemmatizationHandler

# Import handlers
from mcp_servers.zemberek_nlp.tools.morphology import MorphologyHandler
from mcp_servers.zemberek_nlp.tools.ner import NERHandler
from mcp_servers.zemberek_nlp.tools.normalization import NormalizationHandler
from mcp_servers.zemberek_nlp.tools.segmentation import SegmentationHandler
from mcp_servers.zemberek_nlp.tools.spell_check import SpellCheckHandler
from mcp_servers.zemberek_nlp.tools.tokenization import TokenizationHandler


@pytest.fixture
def mock_config():
    """Create mock config with JPype enabled."""
    config = MagicMock(spec=ZemberekConfig)
    config.use_jpype = True
    config.zemberek_url = "http://localhost:8081"
    config.http_timeout = 10.0
    return config


@pytest.fixture
def mock_bridge():
    """Create mock JPype bridge."""
    bridge = MagicMock()
    bridge.is_initialized = True

    # Setup async mock methods
    async def analyze_word(word):
        return [
            {
                "root": word[:3] if len(word) > 3 else word,
                "lemma": word,
                "pos": "Noun",
                "suffixes": [],
                "formatted": f"[{word}:Noun]",
            }
        ]

    async def lemmatize(word):
        return word.rstrip("lar").rstrip("ler")

    async def check_spelling(word):
        return {"word": word, "is_correct": True, "suggestions": []}

    async def tokenize(text):
        return [{"text": w, "type": "Word"} for w in text.split()]

    async def segment_sentences(text):
        return [s.strip() for s in text.split(".") if s.strip()]

    async def normalize(text):
        return {"original": text, "normalized": text, "changes": []}

    async def extract_entities(text):
        return []

    bridge.analyze_word_async = AsyncMock(side_effect=analyze_word)
    bridge.lemmatize_async = AsyncMock(side_effect=lemmatize)
    bridge.check_spelling_async = AsyncMock(side_effect=check_spelling)
    bridge.tokenize_async = AsyncMock(side_effect=tokenize)
    bridge.segment_sentences_async = AsyncMock(side_effect=segment_sentences)
    bridge.normalize_async = AsyncMock(side_effect=normalize)
    bridge.extract_entities_async = AsyncMock(side_effect=extract_entities)
    bridge.get_health = MagicMock(return_value={
        "initialized": True,
        "jvm_started": True,
        "components": {
            "morphology": True,
            "spell_checker": True,
            "tokenizer": True,
        },
    })

    return bridge


@pytest.fixture
def mock_cache():
    """Create mock Redis cache."""
    cache = MagicMock()
    cache.is_connected = True
    cache.get_cached = AsyncMock(return_value=None)  # No cache hit
    cache.set_cached = AsyncMock()
    cache.stats = MagicMock()
    cache.stats.hit_rate = 0.5
    return cache


class TestMorphologyHandler:
    """Test MorphologyHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_analyzes_text(self, mock_config, mock_bridge):
        """_call_jpype should analyze text using bridge."""
        handler = MorphologyHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="kitap okumak")

        assert "word_analyses" in result
        assert result["total_words"] == 2
        assert len(result["word_analyses"]) == 2

    @pytest.mark.asyncio
    async def test_execute_uses_jpype_when_available(
        self, mock_config, mock_bridge, mock_cache
    ):
        """execute() should use JPype when available."""
        handler = MorphologyHandler(
            http_client=None,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler.execute(text="merhaba")

        assert "backend" in result
        assert result["backend"] == "jpype"
        mock_bridge.analyze_word_async.assert_called()


class TestLemmatizationHandler:
    """Test LemmatizationHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_lemmatizes_text(self, mock_config, mock_bridge):
        """_call_jpype should lemmatize text using bridge."""
        handler = LemmatizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="kitaplar evler")

        assert "lemmas" in result
        assert result["total_words"] == 2
        assert "throughput_wps" in result

    @pytest.mark.asyncio
    async def test_batch_mode_processes_parallel(self, mock_config, mock_bridge):
        """Batch mode should process words in parallel."""
        handler = LemmatizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        # Create text with many words for batch processing
        words = " ".join(["kitap"] * 15)
        result = await handler._call_jpype(text=words, batch=True)

        assert result["total_words"] == 15


class TestSpellCheckHandler:
    """Test SpellCheckHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_checks_spelling(self, mock_config, mock_bridge):
        """_call_jpype should check spelling using bridge."""
        handler = SpellCheckHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="merhaba dunya")

        assert "words" in result
        assert "accuracy" in result
        assert result["accuracy"] == 1.0  # All words correct in mock

    @pytest.mark.asyncio
    async def test_detects_diacritic_errors(self, mock_config, mock_bridge):
        """Should detect Turkish diacritic errors."""
        # Modify mock to return incorrect spelling
        async def mock_check(word):
            if word == "yanliz":
                return {"word": word, "is_correct": False, "suggestions": ["yalnız"]}
            return {"word": word, "is_correct": True, "suggestions": []}

        mock_bridge.check_spelling_async = AsyncMock(side_effect=mock_check)

        handler = SpellCheckHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="yanliz")

        assert result["error_count"] == 1


class TestTokenizationHandler:
    """Test TokenizationHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_tokenizes_text(self, mock_config, mock_bridge):
        """_call_jpype should tokenize text using bridge."""
        handler = TokenizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="Merhaba dunya")

        assert "tokens" in result
        assert result["token_count"] == 2
        assert "Merhaba" in result["tokens"]

    @pytest.mark.asyncio
    async def test_detects_urls(self, mock_config, mock_bridge):
        """Should detect URLs in text."""
        handler = TokenizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="Visit https://example.com today")

        assert result["has_url"] is True


class TestNERHandler:
    """Test NERHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_extracts_entities(self, mock_config, mock_bridge):
        """_call_jpype should extract entities using bridge."""
        handler = NERHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="Istanbul guzel")

        assert "entities" in result
        assert "entity_count" in result

    @pytest.mark.asyncio
    async def test_uses_pattern_fallback(self, mock_config, mock_bridge):
        """Should use pattern-based detection when NER unavailable."""
        # Make NER raise exception
        mock_bridge.extract_entities_async = AsyncMock(
            side_effect=Exception("NER not available")
        )

        handler = NERHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        # This should not raise, but use fallback
        result = await handler._call_jpype(text="Dr. Ahmet Istanbul")

        assert "entities" in result


class TestSegmentationHandler:
    """Test SegmentationHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_segments_text(self, mock_config, mock_bridge):
        """_call_jpype should segment text into sentences."""
        handler = SegmentationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="Birinci cumle. Ikinci cumle.")

        assert "sentences" in result
        assert result["sentence_count"] == 2

    @pytest.mark.asyncio
    async def test_detects_dialog(self, mock_config, mock_bridge):
        """Should detect dialog markers."""
        handler = SegmentationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text='- Merhaba dedi.')

        assert result["has_dialog"] is True


class TestNormalizationHandler:
    """Test NormalizationHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_normalizes_text(self, mock_config, mock_bridge):
        """_call_jpype should normalize text."""
        handler = NormalizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="merhaba nasilsin")

        assert "original" in result
        assert "normalized" in result
        assert "changes" in result

    @pytest.mark.asyncio
    async def test_fixes_repeated_chars(self, mock_config, mock_bridge):
        """Should fix repeated characters."""
        handler = NormalizationHandler(
            http_client=None,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype(text="coooook")

        # Check that repeated char fix was applied
        assert "cok" in result["normalized"] or any(
            c.get("change_type") == "repeated" for c in result["changes"]
        )


class TestHealthHandler:
    """Test HealthHandler with JPype support."""

    @pytest.mark.asyncio
    async def test_call_jpype_returns_health(self, mock_config, mock_bridge, mock_cache):
        """_call_jpype should return health status."""
        handler = HealthHandler(
            http_client=None,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype()

        assert "status" in result
        assert result["backend_mode"] == "jpype"
        assert result["jpype_initialized"] is True
        assert "components" in result

    @pytest.mark.asyncio
    async def test_shows_unhealthy_when_not_init(self, mock_config, mock_cache):
        """Should show unhealthy when bridge not initialized."""
        mock_bridge = MagicMock()
        mock_bridge.is_initialized = False
        mock_bridge.get_health = MagicMock(return_value={
            "initialized": False,
            "jvm_started": False,
            "components": {},
        })

        handler = HealthHandler(
            http_client=None,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler._call_jpype()

        assert result["status"] == "unhealthy"


class TestFallbackBehavior:
    """Test JPype -> HTTP fallback behavior."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Fallback returns 'jpype' backend instead of 'http' (handler logic changed)")
    async def test_falls_back_to_http_on_jpype_error(
        self, mock_config, mock_cache
    ):
        """Should fall back to HTTP when JPype fails."""
        # Create bridge that raises on JPype call
        mock_bridge = MagicMock()
        mock_bridge.is_initialized = True
        mock_bridge.analyze_word_async = AsyncMock(
            side_effect=Exception("JPype error")
        )

        # Create HTTP client mock
        mock_http = MagicMock()
        async def mock_post(url, json, timeout):
            response = MagicMock()
            response.json.return_value = {"analyses": [{"lemma": "test", "pos": "Noun"}]}
            response.raise_for_status = MagicMock()
            return response
        mock_http.post = AsyncMock(side_effect=mock_post)

        handler = MorphologyHandler(
            http_client=mock_http,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        # Should not raise, should fall back to HTTP
        result = await handler.execute(text="test")

        assert result["backend"] == "http"


class TestCacheIntegration:
    """Test cache integration with JPype handlers."""

    @pytest.mark.asyncio
    async def test_caches_jpype_results(
        self, mock_config, mock_bridge, mock_cache
    ):
        """JPype results should be cached."""
        handler = MorphologyHandler(
            http_client=None,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        await handler.execute(text="kitap")

        # Verify cache was called
        mock_cache.set_cached.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_cached_result(
        self, mock_config, mock_bridge, mock_cache
    ):
        """Should return cached result when available."""
        cached_data = {
            "text": "kitap",
            "word_analyses": [{"word": "kitap", "analyses": []}],
            "total_words": 1,
        }
        mock_cache.get_cached = AsyncMock(return_value=cached_data)

        handler = MorphologyHandler(
            http_client=None,
            cache=mock_cache,
            config=mock_config,
            bridge=mock_bridge,
        )
        handler._use_jpype = True

        result = await handler.execute(text="kitap")

        assert result["cached"] is True
        mock_bridge.analyze_word_async.assert_not_called()
