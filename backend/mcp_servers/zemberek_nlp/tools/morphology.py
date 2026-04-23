"""
Morphological Analysis Tool (REQ-1)
Turkce kelime yapisi analizi - kok, ek, tip bilgileri

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import logging
from typing import Any

from .base import BaseToolHandler

logger = logging.getLogger(__name__)


class MorphologyHandler(BaseToolHandler):
    """Morphological analysis tool handler"""

    tool_name = "morphology"

    async def _call_jpype(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Perform morphological analysis using JPype bridge.

        Args:
            text: Turkish text to analyze

        Returns:
            MorphologyResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        words = text.split()
        word_analyses: list[dict[str, Any]] = []

        for word in words:
            try:
                # Call JPype bridge (async)
                analyses = await self.bridge.analyze_word_async(word)

                processed_analyses = []
                for i, analysis in enumerate(analyses):
                    # Calculate confidence based on position
                    confidence = 1.0 - (i * 0.1) if i < 10 else 0.1

                    # Detect proper nouns from POS
                    pos = analysis.get("pos", "")
                    is_proper_noun = "Prop" in str(pos) or "Noun,Prop" in str(pos)

                    processed_analyses.append({
                        "root": analysis.get("root", word),
                        "lemma": analysis.get("lemma", word),
                        "pos": str(pos),
                        "suffixes": analysis.get("suffixes", []),
                        "morphemes": analysis.get("suffixes", []),  # Same as suffixes in Zemberek
                        "formatted": analysis.get("formatted", ""),
                        "is_proper_noun": is_proper_noun,
                        "confidence": round(confidence, 2),
                    })

                word_analyses.append({
                    "word": word,
                    "analyses": processed_analyses,
                    "analysis_count": len(processed_analyses),
                })

            except Exception as e:
                logger.warning(f"[Morphology] JPype error for '{word}': {e}")
                word_analyses.append({
                    "word": word,
                    "analyses": [],
                    "analysis_count": 0,
                    "error": str(e),
                })

        return {
            "text": text,
            "word_analyses": word_analyses,
            "total_words": len(words),
        }

    async def _call_backend(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Perform morphological analysis on Turkish text

        Args:
            text: Turkish text to analyze

        Returns:
            MorphologyResult as dictionary
        """
        words = text.split()
        word_analyses: list[dict[str, Any]] = []

        for word in words:
            try:
                # Call backend for each word
                response = await self._post("/analyze", {"word": word})

                analyses = []
                for i, analysis in enumerate(response.get("analyses", [])):
                    # Calculate confidence based on position
                    # First analysis is most likely
                    confidence = 1.0 - (i * 0.1) if i < 10 else 0.1

                    # Detect proper nouns from POS
                    pos = analysis.get("pos", "")
                    is_proper_noun = "Prop" in pos or "Noun,Prop" in pos

                    analyses.append({
                        "root": self._extract_root(analysis),
                        "lemma": analysis.get("lemma", word),
                        "pos": pos,
                        "suffixes": self._extract_suffixes(analysis),
                        "morphemes": analysis.get("morphemes", []),
                        "formatted": analysis.get("formatted", ""),
                        "is_proper_noun": is_proper_noun,
                        "confidence": round(confidence, 2),
                    })

                word_analyses.append({
                    "word": word,
                    "analyses": analyses,
                    "analysis_count": len(analyses),
                })

            except Exception as e:
                logger.warning(f"[Morphology] Error analyzing '{word}': {e}")
                # Return empty analysis for failed words
                word_analyses.append({
                    "word": word,
                    "analyses": [],
                    "analysis_count": 0,
                    "error": str(e),
                })

        return {
            "text": text,
            "word_analyses": word_analyses,
            "total_words": len(words),
        }

    def _extract_root(self, analysis: dict[str, Any]) -> str:
        """Extract root from analysis"""
        lemma = analysis.get("lemma", "")
        morphemes = analysis.get("morphemes", [])

        if morphemes:
            # First morpheme is usually the root
            return morphemes[0]
        return lemma

    def _extract_suffixes(self, analysis: dict[str, Any]) -> list[str]:
        """Extract suffixes from morphemes"""
        morphemes = analysis.get("morphemes", [])
        if len(morphemes) > 1:
            # All morphemes except the first (root) are suffixes
            return morphemes[1:]
        return []
