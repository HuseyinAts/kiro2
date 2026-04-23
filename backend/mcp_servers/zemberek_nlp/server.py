"""
Zemberek NLP MCP Server
Main FastMCP server exposing 8 Turkish NLP tools

Tools:
1. zemberek_analyze - Morphological analysis
2. zemberek_lemmatize - Lemmatization
3. zemberek_spell_check - Spell checking
4. zemberek_tokenize - Tokenization
5. zemberek_ner - Named Entity Recognition
6. zemberek_segment_sentences - Sentence segmentation
7. zemberek_normalize - Text normalization
8. zemberek_health - Health check
"""

import asyncio
import logging

import httpx
from fastmcp import FastMCP

from .cache.redis_cache import ZemberekCache, close_cache, get_cache
from .config import get_config
from .tools import (
    HealthHandler,
    LemmatizationHandler,
    MorphologyHandler,
    NERHandler,
    NormalizationHandler,
    SegmentationHandler,
    SpellCheckHandler,
    TokenizationHandler,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zemberek_nlp")

# Initialize FastMCP server
mcp = FastMCP("Zemberek NLP")

# Global state
_http_client: httpx.AsyncClient | None = None
_cache: ZemberekCache | None = None
_config = get_config()


async def get_http_client() -> httpx.AsyncClient:
    """Get or create HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=_config.http_timeout,
            limits=httpx.Limits(max_connections=_config.max_connections),
        )
    return _http_client


async def get_cache_instance() -> ZemberekCache | None:
    """Get or create cache instance"""
    global _cache
    if _cache is None and _config.cache_enabled:
        _cache = await get_cache()
    return _cache


async def cleanup():
    """Cleanup resources"""
    global _http_client, _cache
    if _http_client:
        await _http_client.aclose()
        _http_client = None
    if _cache:
        await close_cache()
        _cache = None


# =============================================================================
# Tool 1: Morphological Analysis (REQ-1)
# =============================================================================


@mcp.tool()
async def zemberek_analyze(text: str) -> str:
    """
    Perform morphological analysis on Turkish text.

    Analyzes each word to extract:
    - Root (kok)
    - Lemma (sozluk formu)
    - Part of speech (isim, fiil, etc.)
    - Suffixes (ekler)
    - Proper noun detection

    Args:
        text: Turkish text to analyze

    Returns:
        JSON with morphological analysis for each word

    Example:
        >>> zemberek_analyze("Kitapları okudum")
        {
            "text": "Kitapları okudum",
            "word_analyses": [
                {"word": "Kitapları", "analyses": [...]},
                {"word": "okudum", "analyses": [...]}
            ],
            "total_words": 2
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = MorphologyHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_analyze] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 2: Lemmatization (REQ-2)
# =============================================================================


@mcp.tool()
async def zemberek_lemmatize(text: str, batch: bool = False) -> str:
    """
    Extract lemmas (root forms) from Turkish text.

    For each word, returns:
    - Original word
    - Lemma (root form)
    - Part of speech
    - Verb infinitive form (-mek/-mak)
    - Noun singular nominative

    Args:
        text: Turkish text to lemmatize
        batch: Enable batch mode for higher throughput (>= 1000 words/sec)

    Returns:
        JSON with lemmas for each word

    Example:
        >>> zemberek_lemmatize("Kitapları okuyordum")
        {
            "text": "Kitapları okuyordum",
            "lemmas": [
                {"word": "Kitapları", "lemma": "kitap"},
                {"word": "okuyordum", "lemma": "okumak"}
            ]
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = LemmatizationHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text, batch=batch)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_lemmatize] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 3: Spell Check (REQ-3)
# =============================================================================


@mcp.tool()
async def zemberek_spell_check(text: str) -> str:
    """
    Check spelling of Turkish text and suggest corrections.

    For each word, provides:
    - Correctness status
    - Suggestions (edit distance <= 2)
    - Diacritic error detection (i/ı, s/ş, g/ğ)

    Args:
        text: Turkish text to check

    Returns:
        JSON with spell check results

    Example:
        >>> zemberek_spell_check("Turkce metni kontrol et")
        {
            "text": "Turkce metni kontrol et",
            "words": [
                {"word": "Turkce", "is_correct": false, "suggestions": ["Türkçe"]},
                ...
            ],
            "accuracy": 0.75
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = SpellCheckHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_spell_check] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 4: Tokenization (REQ-4)
# =============================================================================


@mcp.tool()
async def zemberek_tokenize(text: str, use_subword: bool = False) -> str:
    """
    Tokenize Turkish text into words and punctuation.

    Handles:
    - Word boundaries
    - Punctuation (sentence-final vs mid-word)
    - Abbreviations (Dr., vb.)
    - Numbers (1.000.000)
    - URLs and emails
    - BPE subword tokenization (when use_subword=true) (REQ-4.6)

    Args:
        text: Turkish text to tokenize
        use_subword: If true, also perform BPE subword tokenization using BERTurk

    Returns:
        JSON with tokens (and subword_tokens if use_subword=true)

    Example:
        >>> zemberek_tokenize("Dr. Ahmet'e 1.000 TL verdim.")
        {
            "tokens": ["Dr.", "Ahmet'e", "1.000", "TL", "verdim", "."],
            "token_count": 6
        }

        >>> zemberek_tokenize("Turkiye guzel", use_subword=True)
        {
            "tokens": ["Turkiye", "guzel"],
            "token_count": 2,
            "subword_tokens": ["Turki", "##ye", "guzel"],
            "subword_token_count": 3
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = TokenizationHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text, use_subword=use_subword)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_tokenize] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 5: Named Entity Recognition (REQ-5)
# =============================================================================


@mcp.tool()
async def zemberek_ner(text: str) -> str:
    """
    Extract named entities from Turkish text.

    Detects:
    - PERSON (kisi isimleri)
    - LOCATION (konum/yer isimleri)
    - ORGANIZATION (kurulus isimleri)

    Args:
        text: Turkish text for NER

    Returns:
        JSON with detected entities

    Example:
        >>> zemberek_ner("Ahmet Yilmaz Istanbul'da Koc Holding'de calisiyor")
        {
            "entities": [
                {"text": "Ahmet Yilmaz", "type": "PERSON"},
                {"text": "Istanbul", "type": "LOCATION"},
                {"text": "Koc Holding", "type": "ORGANIZATION"}
            ]
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = NERHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_ner] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 6: Sentence Segmentation (REQ-6)
# =============================================================================


@mcp.tool()
async def zemberek_segment_sentences(text: str) -> str:
    """
    Segment Turkish text into sentences.

    Handles:
    - Standard sentence endings (. ! ?)
    - Abbreviations (Dr., vb.)
    - Quotations
    - Ellipsis (...)
    - Dialog

    Args:
        text: Turkish text to segment

    Returns:
        JSON with sentences

    Example:
        >>> zemberek_segment_sentences("Merhaba! Nasilsin? Iyiyim.")
        {
            "sentences": ["Merhaba!", "Nasilsin?", "Iyiyim."],
            "sentence_count": 3
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = SegmentationHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_segment_sentences] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 7: Normalization (REQ-7)
# =============================================================================


@mcp.tool()
async def zemberek_normalize(text: str) -> str:
    """
    Normalize Turkish text from informal to formal.

    Handles:
    - Informal to formal ("naber" -> "ne haber")
    - Repeated characters ("çoooook" -> "çok")
    - Emoji/emoticon to text
    - Slang detection
    - Turkish case rules (I/İ, i/ı)

    Args:
        text: Turkish text to normalize

    Returns:
        JSON with normalized text and changes

    Example:
        >>> zemberek_normalize("mrb naber? :)")
        {
            "original": "mrb naber? :)",
            "normalized": "merhaba ne haber? (gulümseme)",
            "changes": [...]
        }
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = NormalizationHandler(client, cache, _config)

    try:
        result = await handler.execute(text=text)
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_normalize] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Tool 8: Health Check (REQ-8.6)
# =============================================================================


@mcp.tool()
async def zemberek_health() -> str:
    """
    Check health of Zemberek NLP service.

    Returns:
    - Service status (healthy/degraded/unhealthy)
    - Zemberek availability
    - Redis availability
    - HTTP backend availability
    - Cache hit rate
    - Uptime

    Returns:
        JSON with health information
    """
    client = await get_http_client()
    cache = await get_cache_instance()
    handler = HealthHandler(client, cache, _config)

    try:
        result = await handler.execute()
        return _format_result(result)
    except Exception as e:
        logger.error(f"[zemberek_health] Error: {e}")
        return f"Error: {e!s}"


# =============================================================================
# Resource: Health Status
# =============================================================================


@mcp.resource("zemberek://health")
async def health_resource() -> str:
    """Zemberek health status resource"""
    return await zemberek_health()


# =============================================================================
# Utility Functions
# =============================================================================


def _format_result(result: dict) -> str:
    """Format result dict as JSON string"""
    import json
    return json.dumps(result, indent=2, ensure_ascii=False)


# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """Run Zemberek NLP MCP server"""
    logger.info("[Zemberek NLP MCP] Starting server...")
    logger.info(f"[Zemberek NLP MCP] HTTP Backend: {_config.zemberek_url}")
    logger.info(f"[Zemberek NLP MCP] Redis: {_config.redis_host}:{_config.redis_port}")
    logger.info(f"[Zemberek NLP MCP] Cache enabled: {_config.cache_enabled}")

    try:
        mcp.run(transport="stdio")
    finally:
        # Cleanup on exit
        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
