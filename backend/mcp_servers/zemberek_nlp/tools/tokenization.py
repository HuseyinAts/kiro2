"""
Tokenization Tool (REQ-4)
Turkce metin tokenizasyonu - sozcuk ayirma

Supports both JPype (direct Zemberek access) and HTTP backend.
Includes BPE subword tokenization support (REQ-4.6).
"""

import re
import logging
from typing import Any, Dict, List, Optional

from .base import BaseToolHandler

logger = logging.getLogger(__name__)

# Lazy import for BPE tokenizer
_bpe_tokenizer = None


def _get_bpe_tokenizer():
    """Get singleton BPE tokenizer (lazy load)."""
    global _bpe_tokenizer
    if _bpe_tokenizer is None:
        from .bpe_tokenizer import get_bpe_tokenizer
        _bpe_tokenizer = get_bpe_tokenizer()
    return _bpe_tokenizer

# Patterns for special tokens
URL_PATTERN = re.compile(
    r"https?://[^\s]+|www\.[^\s]+", re.IGNORECASE
)
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE
)
NUMBER_PATTERN = re.compile(
    r"\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:,\d+)?"
)
ABBREVIATION_PATTERN = re.compile(
    r"\b(?:Dr|Prof|Doç|Yrd|vb|vs|bkz|a\.ş|ltd|şti)\.", re.IGNORECASE
)


class TokenizationHandler(BaseToolHandler):
    """Tokenization tool handler"""

    tool_name = "tokenization"

    async def _call_jpype(
        self, text: str, use_subword: bool = False, **kwargs
    ) -> Dict[str, Any]:
        """
        Tokenize text using JPype bridge.

        Args:
            text: Turkish text to tokenize
            use_subword: If True, also perform BPE subword tokenization (REQ-4.6)

        Returns:
            TokenizationResult as dictionary
        """
        if not self.bridge:
            raise RuntimeError("JPype bridge not initialized")

        try:
            tokens_data = await self.bridge.tokenize_async(text)
            tokens = [t.get("text", "") for t in tokens_data]
        except Exception as e:
            logger.warning(f"[Tokenization] JPype error: {e}, using fallback")
            tokens = self._simple_tokenize(text)

        has_url = bool(URL_PATTERN.search(text))
        has_email = bool(EMAIL_PATTERN.search(text))
        has_number = bool(NUMBER_PATTERN.search(text))
        has_abbreviation = bool(ABBREVIATION_PATTERN.search(text))

        # BPE subword tokenization (REQ-4.6)
        subword_tokens: Optional[List[str]] = None
        subword_token_count: Optional[int] = None
        if use_subword:
            subword_tokens = self._bpe_tokenize(text)
            subword_token_count = len(subword_tokens) if subword_tokens else None

        return {
            "text": text,
            "tokens": tokens,
            "token_count": len(tokens),
            "subword_tokens": subword_tokens,
            "subword_token_count": subword_token_count,
            "has_url": has_url,
            "has_email": has_email,
            "has_number": has_number,
            "has_abbreviation": has_abbreviation,
        }

    async def _call_backend(
        self, text: str, use_subword: bool = False, **kwargs
    ) -> Dict[str, Any]:
        """
        Tokenize Turkish text

        Args:
            text: Turkish text to tokenize
            use_subword: If True, also perform BPE subword tokenization (REQ-4.6)

        Returns:
            TokenizationResult as dictionary
        """
        try:
            # Call backend tokenizer
            response = await self._post("/tokenize", {"text": text})
            tokens = response.get("tokens", [])
        except Exception as e:
            logger.warning(f"[Tokenization] Backend error: {e}, using fallback")
            # Fallback to simple tokenization
            tokens = self._simple_tokenize(text)

        # Analyze token types
        has_url = bool(URL_PATTERN.search(text))
        has_email = bool(EMAIL_PATTERN.search(text))
        has_number = bool(NUMBER_PATTERN.search(text))
        has_abbreviation = bool(ABBREVIATION_PATTERN.search(text))

        # BPE subword tokenization (REQ-4.6)
        subword_tokens: Optional[List[str]] = None
        subword_token_count: Optional[int] = None
        if use_subword:
            subword_tokens = self._bpe_tokenize(text)
            subword_token_count = len(subword_tokens) if subword_tokens else None

        return {
            "text": text,
            "tokens": tokens,
            "token_count": len(tokens),
            "subword_tokens": subword_tokens,
            "subword_token_count": subword_token_count,
            "has_url": has_url,
            "has_email": has_email,
            "has_number": has_number,
            "has_abbreviation": has_abbreviation,
        }

    def _simple_tokenize(self, text: str) -> List[str]:
        """
        Simple fallback tokenizer

        Preserves:
        - URLs
        - Emails
        - Numbers with Turkish format (1.000.000)
        - Abbreviations (Dr., vb.)
        """
        tokens = []

        # Protect special patterns
        protected = {}
        counter = 0

        # Protect URLs
        for match in URL_PATTERN.finditer(text):
            placeholder = f"__URL_{counter}__"
            protected[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
            counter += 1

        # Protect emails
        for match in EMAIL_PATTERN.finditer(text):
            placeholder = f"__EMAIL_{counter}__"
            protected[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
            counter += 1

        # Protect abbreviations
        for match in ABBREVIATION_PATTERN.finditer(text):
            placeholder = f"__ABBR_{counter}__"
            protected[placeholder] = match.group()
            text = text.replace(match.group(), placeholder, 1)
            counter += 1

        # Protect Turkish numbers (1.000.000)
        for match in NUMBER_PATTERN.finditer(text):
            if "." in match.group() and len(match.group()) > 3:
                placeholder = f"__NUM_{counter}__"
                protected[placeholder] = match.group()
                text = text.replace(match.group(), placeholder, 1)
                counter += 1

        # Tokenize remaining text
        # Split on whitespace and punctuation (except apostrophe in words)
        pattern = r"(\s+|[.,!?;:()\"'\[\]{}])"
        parts = re.split(pattern, text)

        for part in parts:
            if not part or part.isspace():
                continue

            # Restore protected tokens
            if part.startswith("__") and part.endswith("__"):
                tokens.append(protected.get(part, part))
            else:
                tokens.append(part)

        return tokens

    def _bpe_tokenize(self, text: str) -> Optional[List[str]]:
        """
        Perform BPE subword tokenization using HuggingFace tokenizers.

        Uses BERTurk (dbmdz/bert-base-turkish-cased) pre-trained tokenizer.

        Args:
            text: Turkish text to tokenize

        Returns:
            List of subword tokens or None if BPE tokenization fails
        """
        try:
            bpe = _get_bpe_tokenizer()
            return bpe.tokenize(text)
        except Exception as e:
            logger.warning(f"[Tokenization] BPE tokenization failed: {e}")
            return None

    def _get_cache_input(self, text: str, use_subword: bool = False, **kwargs) -> str:
        """
        Generate cache input including subword flag.

        Args:
            text: Input text
            use_subword: Whether BPE subword tokenization is requested

        Returns:
            Cache key input string
        """
        if use_subword:
            return f"{text}::subword=true"
        return text
