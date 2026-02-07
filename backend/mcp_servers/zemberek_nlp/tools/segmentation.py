"""
Sentence Segmentation Tool (REQ-6)
Turkce cumle segmentasyonu

Supports both JPype (direct Zemberek access) and HTTP backend.
"""

import re
import logging
from typing import Any, Dict, List

from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Abbreviations that don't end sentences
ABBREVIATIONS = {
    "dr", "prof", "doç", "yrd", "av", "mr", "mrs", "ms",
    "st", "jr", "sr", "inc", "ltd", "corp",
    "vb", "vs", "bkz", "örn", "yy", "aş", "şti",
    "no", "tel", "fax", "pk", "apt",
}

# Dialog markers
DIALOG_MARKERS = ["-", "–", "—", '"', "'", "«", "»"]


class SegmentationHandler(BaseToolHandler):
    """Sentence segmentation tool handler"""

    tool_name = "segmentation"

    async def _call_jpype(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Segment text into sentences using JPype bridge.

        Args:
            text: Turkish text to segment

        Returns:
            SegmentationResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        try:
            sentences = await self.bridge.segment_sentences_async(text)
        except Exception as e:
            logger.warning(f"[Segmentation] JPype error: {e}, using fallback")
            sentences = self._segment_sentences(text)

        has_dialog = self._has_dialog(text)
        has_quotation = self._has_quotation(text)

        return {
            "text": text,
            "sentences": sentences,
            "sentence_count": len(sentences),
            "has_dialog": has_dialog,
            "has_quotation": has_quotation,
        }

    async def _call_backend(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Segment Turkish text into sentences

        Args:
            text: Turkish text to segment

        Returns:
            SegmentationResult as dictionary
        """
        try:
            # Call backend sentence extractor
            response = await self._post("/sentences", {"text": text})
            sentences = response.get("sentences", [])
        except Exception as e:
            logger.warning(f"[Segmentation] Backend error: {e}, using fallback")
            # Fallback to rule-based segmentation
            sentences = self._segment_sentences(text)

        # Detect dialog and quotations
        has_dialog = self._has_dialog(text)
        has_quotation = self._has_quotation(text)

        return {
            "text": text,
            "sentences": sentences,
            "sentence_count": len(sentences),
            "has_dialog": has_dialog,
            "has_quotation": has_quotation,
        }

    def _segment_sentences(self, text: str) -> List[str]:
        """
        Rule-based Turkish sentence segmentation

        Handles:
        - Standard sentence endings (. ! ?)
        - Abbreviations (Dr., vb.)
        - Quotations
        - Ellipsis (...)
        - Dialog
        """
        sentences = []
        current_sentence = []
        words = text.split()

        i = 0
        while i < len(words):
            word = words[i]
            current_sentence.append(word)

            # Check if this word ends a sentence
            if self._is_sentence_end(word, i, words):
                sentence = " ".join(current_sentence).strip()
                if sentence:
                    sentences.append(sentence)
                current_sentence = []

            i += 1

        # Add remaining text as final sentence
        if current_sentence:
            sentence = " ".join(current_sentence).strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _is_sentence_end(
        self, word: str, index: int, words: List[str]
    ) -> bool:
        """Determine if word ends a sentence"""
        # Check for sentence-ending punctuation
        if not word:
            return False

        last_char = word[-1]

        # Definite sentence endings
        if last_char in "!?":
            return True

        # Ellipsis
        if word.endswith("..."):
            return True

        # Period - need to check for abbreviations
        if last_char == ".":
            # Check if it's an abbreviation
            word_lower = word.lower().rstrip(".")
            if word_lower in ABBREVIATIONS:
                return False

            # Check if followed by lowercase (likely not end of sentence)
            if index + 1 < len(words):
                next_word = words[index + 1]
                if next_word and next_word[0].islower():
                    return False

            return True

        return False

    def _has_dialog(self, text: str) -> bool:
        """Check if text contains dialog"""
        # Check for dialog markers at line starts
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            for marker in DIALOG_MARKERS:
                if stripped.startswith(marker):
                    return True

        # Check for quoted speech patterns
        if re.search(r'"[^"]+"\s*dedi', text, re.IGNORECASE):
            return True

        return False

    def _has_quotation(self, text: str) -> bool:
        """Check if text contains quotations"""
        quote_patterns = [
            r'"[^"]+"',  # Double quotes
            r"'[^']+'",  # Single quotes
            r"«[^»]+»",  # French quotes
            '[\u201c][^\u201d]+[\u201d]',  # Smart quotes (Unicode)
        ]

        for pattern in quote_patterns:
            if re.search(pattern, text):
                return True

        return False
