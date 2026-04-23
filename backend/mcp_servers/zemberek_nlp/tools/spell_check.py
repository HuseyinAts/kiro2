"""
Spell Check Tool (REQ-3)
Turkce yazim denetimi ve duzeltme onerileri

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import logging
from typing import Any

from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Turkish diacritic mappings for error detection
DIACRITIC_MAP = {
    "i": "ı",
    "ı": "i",
    "s": "ş",
    "ş": "s",
    "g": "ğ",
    "ğ": "g",
    "c": "ç",
    "ç": "c",
    "u": "ü",
    "ü": "u",
    "o": "ö",
    "ö": "o",
}


class SpellCheckHandler(BaseToolHandler):
    """Spell check tool handler"""

    tool_name = "spell_check"

    async def _call_jpype(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Check spelling using JPype bridge.

        Args:
            text: Turkish text to check

        Returns:
            SpellCheckResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        words = self._tokenize_for_spell_check(text)
        word_results: list[dict[str, Any]] = []
        error_count = 0

        for word in words:
            if not word.isalpha():
                continue

            try:
                result = await self.bridge.check_spelling_async(word)
                is_correct = result.get("is_correct", False)
                suggestions = result.get("suggestions", [])

                has_diacritic_error = False
                edit_distance = None

                if not is_correct:
                    error_count += 1
                    has_diacritic_error = self._check_diacritic_error(word, suggestions)
                    if suggestions:
                        edit_distance = self._levenshtein(word, suggestions[0])

                word_results.append({
                    "word": word,
                    "is_correct": is_correct,
                    "suggestions": suggestions[:5],
                    "has_diacritic_error": has_diacritic_error,
                    "edit_distance": edit_distance,
                })

            except Exception as e:
                logger.warning(f"[SpellCheck] JPype error for '{word}': {e}")
                word_results.append({
                    "word": word,
                    "is_correct": False,
                    "suggestions": [],
                    "has_diacritic_error": False,
                    "edit_distance": None,
                    "error": str(e),
                })
                error_count += 1

        total_words = len(word_results)
        accuracy = (total_words - error_count) / total_words if total_words > 0 else 1.0

        return {
            "text": text,
            "words": word_results,
            "total_words": total_words,
            "error_count": error_count,
            "accuracy": round(accuracy, 4),
        }

    async def _call_backend(self, text: str, **kwargs) -> dict[str, Any]:
        """
        Check spelling of Turkish text

        Args:
            text: Turkish text to check

        Returns:
            SpellCheckResult as dictionary
        """
        words = self._tokenize_for_spell_check(text)
        word_results: list[dict[str, Any]] = []
        error_count = 0

        for word in words:
            # Skip punctuation and numbers
            if not word.isalpha():
                continue

            try:
                # Check word via morphology (if it has valid analysis, it's correct)
                response = await self._post("/analyze", {"word": word})
                analyses = response.get("analyses", [])

                is_correct = len(analyses) > 0
                suggestions = []
                has_diacritic_error = False
                edit_distance = None

                if not is_correct:
                    error_count += 1
                    # Generate suggestions
                    suggestions = await self._generate_suggestions(word)
                    # Check for diacritic errors
                    has_diacritic_error = self._check_diacritic_error(word, suggestions)
                    # Calculate edit distance to best suggestion
                    if suggestions:
                        edit_distance = self._levenshtein(word, suggestions[0])

                word_results.append({
                    "word": word,
                    "is_correct": is_correct,
                    "suggestions": suggestions[:5],  # Max 5 suggestions
                    "has_diacritic_error": has_diacritic_error,
                    "edit_distance": edit_distance,
                })

            except Exception as e:
                logger.warning(f"[SpellCheck] Error for '{word}': {e}")
                word_results.append({
                    "word": word,
                    "is_correct": False,
                    "suggestions": [],
                    "has_diacritic_error": False,
                    "edit_distance": None,
                    "error": str(e),
                })
                error_count += 1

        total_words = len(word_results)
        accuracy = (total_words - error_count) / total_words if total_words > 0 else 1.0

        return {
            "text": text,
            "words": word_results,
            "total_words": total_words,
            "error_count": error_count,
            "accuracy": round(accuracy, 4),
        }

    def _tokenize_for_spell_check(self, text: str) -> list[str]:
        """Tokenize text for spell checking"""
        # Simple whitespace tokenization
        # Remove punctuation attached to words
        import re
        words = re.findall(r"\b[\w']+\b", text, re.UNICODE)
        return words

    async def _generate_suggestions(
        self, word: str, max_suggestions: int = 5
    ) -> list[str]:
        """
        Generate spelling suggestions for a misspelled word

        Uses edit distance and diacritic variants
        """
        suggestions = set()

        # 1. Try diacritic variants
        diacritic_variants = self._generate_diacritic_variants(word)
        for variant in diacritic_variants:
            try:
                response = await self._post("/analyze", {"word": variant})
                if response.get("analyses"):
                    suggestions.add(variant)
            except Exception:
                pass

        # 2. Try common Turkish corrections
        common_corrections = self._get_common_corrections(word)
        for correction in common_corrections:
            try:
                response = await self._post("/analyze", {"word": correction})
                if response.get("analyses"):
                    suggestions.add(correction)
            except Exception:
                pass

        # Sort by edit distance
        sorted_suggestions = sorted(
            suggestions, key=lambda s: self._levenshtein(word, s)
        )

        return sorted_suggestions[:max_suggestions]

    def _generate_diacritic_variants(self, word: str) -> list[str]:
        """Generate variants with Turkish diacritics"""
        variants = []
        word_lower = word.lower()

        for i, char in enumerate(word_lower):
            if char in DIACRITIC_MAP:
                # Create variant with swapped diacritic
                variant = word_lower[:i] + DIACRITIC_MAP[char] + word_lower[i + 1 :]
                variants.append(variant)

        return variants[:10]  # Limit variants

    def _get_common_corrections(self, word: str) -> list[str]:
        """Get common Turkish spelling corrections"""
        corrections = []
        word_lower = word.lower()

        # Common typos and fixes
        common_typos = {
            "yalniz": "yalnız",
            "sekerli": "şekerli",
            "gormek": "görmek",
            "olmak": "olmak",
            "yapmak": "yapmak",
        }

        if word_lower in common_typos:
            corrections.append(common_typos[word_lower])

        return corrections

    def _check_diacritic_error(
        self, word: str, suggestions: list[str]
    ) -> bool:
        """Check if error is likely a diacritic mistake"""
        if not suggestions:
            return False

        for suggestion in suggestions:
            if self._is_diacritic_variant(word, suggestion):
                return True
        return False

    def _is_diacritic_variant(self, word1: str, word2: str) -> bool:
        """Check if two words differ only in Turkish diacritics"""
        if len(word1) != len(word2):
            return False

        diff_count = 0
        for c1, c2 in zip(word1.lower(), word2.lower()):
            if c1 != c2:
                if c1 in DIACRITIC_MAP and DIACRITIC_MAP[c1] == c2:
                    diff_count += 1
                else:
                    return False

        return diff_count > 0

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance"""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
