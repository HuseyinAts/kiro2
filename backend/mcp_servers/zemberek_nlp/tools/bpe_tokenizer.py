"""
BPE Subword Tokenizer (REQ-4.6)
Turkish BPE tokenization using HuggingFace tokenizers library

Uses dbmdz/bert-base-turkish-cased tokenizer (BERTurk)
- 32K vocabulary size
- Turkish text optimized
- Singleton pattern for efficiency
"""

import logging
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)

# Model identifier
BERTURK_MODEL_ID = "dbmdz/bert-base-turkish-cased"


class BPETokenizer:
    """
    Thread-safe singleton BPE tokenizer for Turkish text.

    Uses BERTurk's pre-trained tokenizer from HuggingFace.
    Lazy-loads the model on first use to avoid startup overhead.
    """

    _instance: Optional["BPETokenizer"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "BPETokenizer":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._tokenizer = None
        self._initialized = True
        logger.info("[BPETokenizer] Instance created (lazy-load)")

    def _ensure_loaded(self) -> None:
        """Load tokenizer on first use (lazy loading)."""
        if self._tokenizer is None:
            try:
                from tokenizers import Tokenizer

                logger.info(f"[BPETokenizer] Loading {BERTURK_MODEL_ID}...")
                self._tokenizer = Tokenizer.from_pretrained(BERTURK_MODEL_ID)
                logger.info("[BPETokenizer] Model loaded successfully")
            except ImportError:
                logger.error(
                    "[BPETokenizer] tokenizers library not installed. "
                    "Install with: pip install tokenizers>=0.15.0"
                )
                raise
            except Exception as e:
                logger.error(f"[BPETokenizer] Failed to load model: {e}")
                raise

    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text using BPE algorithm.

        Args:
            text: Turkish text to tokenize

        Returns:
            List of subword tokens (including ## prefix for continuations)

        Example:
            >>> bpe = BPETokenizer()
            >>> bpe.tokenize("Turkiye'nin baskenti Ankara")
            ['Turkiye', "'", 'nin', 'baskent', '##i', 'Ankara']
        """
        self._ensure_loaded()

        encoding = self._tokenizer.encode(text)
        tokens = encoding.tokens

        # Remove special tokens [CLS] and [SEP] if present
        return [t for t in tokens if t not in ("[CLS]", "[SEP]", "[PAD]")]

    def tokenize_with_offsets(self, text: str) -> List[dict]:
        """
        Tokenize text with character offsets.

        Args:
            text: Turkish text to tokenize

        Returns:
            List of dicts with token, start, end positions

        Example:
            >>> bpe = BPETokenizer()
            >>> bpe.tokenize_with_offsets("Merhaba")
            [{'token': 'Merhaba', 'start': 0, 'end': 7}]
        """
        self._ensure_loaded()

        encoding = self._tokenizer.encode(text)
        tokens = encoding.tokens
        offsets = encoding.offsets

        result = []
        for i, (token, (start, end)) in enumerate(zip(tokens, offsets)):
            if token not in ("[CLS]", "[SEP]", "[PAD]"):
                result.append({
                    "token": token,
                    "start": start,
                    "end": end,
                })

        return result

    def get_ids(self, text: str) -> List[int]:
        """
        Get token IDs for text.

        Args:
            text: Turkish text to tokenize

        Returns:
            List of token IDs from vocabulary
        """
        self._ensure_loaded()

        encoding = self._tokenizer.encode(text)
        return encoding.ids

    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs back to text.

        Args:
            token_ids: List of token IDs

        Returns:
            Reconstructed text
        """
        self._ensure_loaded()
        return self._tokenizer.decode(token_ids)

    @property
    def vocab_size(self) -> int:
        """Get vocabulary size."""
        self._ensure_loaded()
        return self._tokenizer.get_vocab_size()

    @property
    def is_loaded(self) -> bool:
        """Check if tokenizer is loaded."""
        return self._tokenizer is not None


def get_bpe_tokenizer() -> BPETokenizer:
    """
    Get singleton BPE tokenizer instance.

    Returns:
        BPETokenizer instance (singleton)
    """
    return BPETokenizer()
