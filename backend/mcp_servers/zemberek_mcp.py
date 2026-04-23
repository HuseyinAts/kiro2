"""
Zemberek NLP MCP Server
Model Context Protocol wrapper for Zemberek HTTP service
"""

import os

import httpx
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("Zemberek NLP")

ZEMBEREK_URL = os.getenv("ZEMBEREK_SERVICE_URL", "http://localhost:8081")


@mcp.tool()
async def tokenize_turkish_text(text: str) -> list[str]:
    """
    Tokenize Turkish text into words and punctuation.

    Args:
        text: Turkish text to tokenize

    Returns:
        List of tokens (words and punctuation)

    Example:
        >>> tokenize_turkish_text("Merhaba dünya, nasılsınız?")
        ["Merhaba", "dünya", ",", "nasılsınız", "?"]
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEMBEREK_URL}/tokenize", json={"text": text}, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("tokens", [])
    except Exception as e:
        return [f"Error: {e!s}"]


@mcp.tool()
async def normalize_turkish_text(text: str) -> str:
    """
    Normalize Turkish text (fix spelling, convert informal to formal).

    Args:
        text: Turkish text to normalize

    Returns:
        Normalized text

    Example:
        >>> normalize_turkish_text("mrb nasılsn")
        "Merhaba nasılsın"
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEMBEREK_URL}/normalize", json={"text": text}, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("normalized", text)
    except Exception as e:
        return f"Error: {e!s}"


@mcp.tool()
async def analyze_turkish_word(word: str) -> str:
    """
    Perform morphological analysis of a Turkish word.

    Args:
        word: Single Turkish word to analyze

    Returns:
        Morphological analysis with lemma, POS tag, and morphemes

    Example:
        >>> analyze_turkish_word("okuyordum")
        "Lemma: oku, POS: Verb, Morphemes: [oku, yor, du, m]"
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEMBEREK_URL}/analyze", json={"word": word}, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            if data.get("analyses"):
                analysis = data["analyses"][0]
                lemma = analysis.get("lemma", "")
                pos = analysis.get("pos", "")
                morphemes = analysis.get("morphemes", [])
                return f"Lemma: {lemma}, POS: {pos}, Morphemes: {morphemes}"
            return "No analysis found"
    except Exception as e:
        return f"Error: {e!s}"


@mcp.tool()
async def extract_sentences(text: str) -> list[str]:
    """
    Extract sentences from Turkish text.

    Args:
        text: Turkish text containing multiple sentences

    Returns:
        List of sentences

    Example:
        >>> extract_sentences("İlk cümle. İkinci cümle! Üçüncü cümle?")
        ["İlk cümle.", "İkinci cümle!", "Üçüncü cümle?"]
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ZEMBEREK_URL}/sentences", json={"text": text}, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("sentences", [])
    except Exception as e:
        return [f"Error: {e!s}"]


@mcp.resource("zemberek://health")
async def zemberek_health() -> str:
    """Check Zemberek service health status"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ZEMBEREK_URL}/health", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return f"Status: {data.get('status')}, Available: {data.get('zemberek_available')}"
    except Exception as e:
        return f"Zemberek service unavailable: {e!s}"


if __name__ == "__main__":
    # Run MCP server with stdio transport (for IDE integration)
    mcp.run(transport="stdio")
