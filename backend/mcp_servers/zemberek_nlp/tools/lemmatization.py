"""
Lemmatization Tool (REQ-2)
Turkce kelime koklerini bulma - batch destekli

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import asyncio
import logging
import time
from typing import Any

from .base import BaseToolHandler
from core.turkish_nlp_utils import normalize_tr

logger = logging.getLogger(__name__)


class LemmatizationHandler(BaseToolHandler):
    """Lemmatization tool handler"""

    tool_name = "lemmatization"

    async def _call_jpype(
        self, text: str, batch: bool = False, **kwargs
    ) -> dict[str, Any]:
        """
        Extract lemmas using JPype bridge.

        Args:
            text: Turkish text to lemmatize
            batch: Enable batch mode for parallel processing

        Returns:
            BatchLemmaResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        start_time = time.perf_counter()
        words = text.split()

        if batch and len(words) > 10:
            # True batch mode with parallel processing
            lemmas = await self._lemmatize_batch_jpype(words)
        else:
            # Sequential processing
            lemmas = await self._lemmatize_sequential_jpype(words)

        elapsed_seconds = time.perf_counter() - start_time
        throughput = len(words) / elapsed_seconds if elapsed_seconds > 0 else 0

        return {
            "text": text,
            "lemmas": lemmas,
            "total_words": len(words),
            "throughput_wps": round(throughput, 2),
        }

    async def _lemmatize_sequential_jpype(
        self, words: list[str]
    ) -> list[dict[str, Any]]:
        """Lemmatize words sequentially using JPype bridge."""
        lemmas = []

        for word in words:
            try:
                lemma = await self.bridge.lemmatize_async(word)
                analyses = await self.bridge.analyze_word_async(word)

                # Get POS from first analysis
                pos = None
                is_verb = False
                is_noun = False

                if analyses:
                    pos = str(analyses[0].get("pos", ""))
                    is_verb = "Verb" in pos
                    is_noun = "Noun" in pos and not is_verb

                # For verbs, ensure infinitive form
                if is_verb and not lemma.endswith(("mek", "mak")):
                    lemma = self._get_infinitive(lemma)

                confidence = 1.0 if len(analyses) <= 1 else 0.9

                lemmas.append({
                    "word": word,
                    "lemma": lemma,
                    "pos": pos,
                    "is_verb": is_verb,
                    "is_noun": is_noun,
                    "confidence": confidence,
                })

            except Exception as e:
                logger.warning(f"[Lemmatization] JPype error for '{word}': {e}")
                lemmas.append({
                    "word": word,
                    "lemma": word,
                    "pos": None,
                    "is_verb": False,
                    "is_noun": False,
                    "confidence": 0.0,
                    "error": str(e),
                })

        return lemmas

    async def _lemmatize_batch_jpype(
        self, words: list[str], batch_size: int = 50
    ) -> list[dict[str, Any]]:
        """
        Lemmatize words in parallel batches using JPype bridge.

        Args:
            words: List of words to lemmatize
            batch_size: Number of words per batch

        Returns:
            List of lemma results
        """
        # Split into batches
        batches = [
            words[i : i + batch_size] for i in range(0, len(words), batch_size)
        ]

        # Process batches in parallel
        tasks = [
            self._process_batch_jpype(batch) for batch in batches
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        lemmas = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"[Lemmatization] Batch error: {result}")
            else:
                lemmas.extend(result)

        return lemmas

    async def _process_batch_jpype(self, words: list[str]) -> list[dict[str, Any]]:
        """Process a batch of words using JPype."""
        return await self._lemmatize_sequential_jpype(words)

    async def _call_backend(
        self, text: str, batch: bool = False, **kwargs
    ) -> dict[str, Any]:
        """
        Extract lemmas from Turkish text

        Args:
            text: Turkish text to lemmatize
            batch: Enable batch mode for higher throughput

        Returns:
            BatchLemmaResult as dictionary
        """
        start_time = time.perf_counter()

        words = text.split()
        lemmas: list[dict[str, Any]] = []

        if batch:
            # Batch mode - parallel processing (not implemented in HTTP backend)
            # Fall back to sequential for now, but measure throughput
            lemmas = await self._lemmatize_sequential(words)
        else:
            lemmas = await self._lemmatize_sequential(words)

        elapsed_seconds = time.perf_counter() - start_time
        throughput = len(words) / elapsed_seconds if elapsed_seconds > 0 else 0

        return {
            "text": text,
            "lemmas": lemmas,
            "total_words": len(words),
            "throughput_wps": round(throughput, 2),
        }

    async def _lemmatize_sequential(
        self, words: list[str]
    ) -> list[dict[str, Any]]:
        """
        Lemmatize words sequentially

        Args:
            words: List of words to lemmatize

        Returns:
            List of LemmaResult dictionaries
        """
        lemmas = []

        for word in words:
            try:
                # Call morphology endpoint
                response = await self._post("/analyze", {"word": word})
                analyses = response.get("analyses", [])

                if analyses:
                    # Use first analysis (most likely)
                    analysis = analyses[0]
                    lemma = analysis.get("lemma", word)
                    pos = analysis.get("pos", "")

                    # Determine word type
                    is_verb = "Verb" in pos
                    is_noun = "Noun" in pos and not is_verb

                    # For verbs, ensure infinitive form (-mek/-mak)
                    if is_verb and not lemma.endswith(("mek", "mak")):
                        lemma = self._get_infinitive(lemma)

                    # Confidence based on analysis count
                    confidence = 1.0 if len(analyses) == 1 else 0.9

                    lemmas.append({
                        "word": word,
                        "lemma": lemma,
                        "pos": pos,
                        "is_verb": is_verb,
                        "is_noun": is_noun,
                        "confidence": confidence,
                    })
                else:
                    # No analysis - return word as-is
                    lemmas.append({
                        "word": word,
                        "lemma": word,
                        "pos": None,
                        "is_verb": False,
                        "is_noun": False,
                        "confidence": 0.5,
                    })

            except Exception as e:
                logger.warning(f"[Lemmatization] Error for '{word}': {e}")
                lemmas.append({
                    "word": word,
                    "lemma": word,
                    "pos": None,
                    "is_verb": False,
                    "is_noun": False,
                    "confidence": 0.0,
                    "error": str(e),
                })

        return lemmas

    def _get_infinitive(self, lemma: str) -> str:
        """
        Convert verb stem to infinitive form

        Turkish verbs: stem + mek/mak
        Vowel harmony: e, i, ö, ü -> mek; a, ı, o, u -> mak
        """
        # Check last vowel for vowel harmony (Turkish locale-safe)
        last_vowel = None
        for char in reversed(normalize_tr(lemma)):
            if char in "aeıioöuü":
                last_vowel = char
                break

        if last_vowel in "eiöü":
            return lemma + "mek"
        return lemma + "mak"

    def _get_cache_input(self, text: str, batch: bool = False, **kwargs) -> str:
        """Generate cache input including batch flag"""
        return f"{text}|batch={batch}"
