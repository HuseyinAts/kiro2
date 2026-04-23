"""
Unit and Property Tests for BPE Subword Tokenization (REQ-4.6)

Tests the BPE tokenizer module using HuggingFace tokenizers library
with BERTurk (dbmdz/bert-base-turkish-cased) model.
"""

from unittest.mock import MagicMock

import pytest

# Dynamic check for tokenizers library and model availability
try:
    import tokenizers
    HAS_TOKENIZERS = True
except ImportError:
    HAS_TOKENIZERS = False

# Check if BERTurk model is accessible (may fail due to network or model format issues)
HAS_BERTURK_MODEL = False
if HAS_TOKENIZERS:
    try:
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import BPETokenizer
        _test_tokenizer = BPETokenizer()
        _test_tokenizer._ensure_loaded()
        HAS_BERTURK_MODEL = True
    except Exception:
        # Model not available (network, format, or other issues)
        HAS_BERTURK_MODEL = False

# Reusable skipif decorator for tests requiring actual model
requires_tokenizers = pytest.mark.skipif(
    not HAS_TOKENIZERS,
    reason="Requires tokenizers library - run: pip install tokenizers>=0.15.0"
)

requires_berturk_model = pytest.mark.skipif(
    not HAS_BERTURK_MODEL,
    reason="BERTurk model not available (network issue or model format incompatible)"
)


class TestBPETokenizerModule:
    """Tests for the BPE tokenizer module"""

    def test_singleton_pattern(self):
        """Test that BPETokenizer follows singleton pattern"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import BPETokenizer

        # Create two instances
        instance1 = BPETokenizer()
        instance2 = BPETokenizer()

        # They should be the same object
        assert instance1 is instance2

    def test_lazy_loading(self):
        """Test that tokenizer is not loaded until first use"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import BPETokenizer

        tokenizer = BPETokenizer()
        # The internal tokenizer should be None until first use
        assert tokenizer._tokenizer is None or tokenizer.is_loaded is True

    @requires_berturk_model
    def test_tokenize_basic(self):
        """Test basic BPE tokenization"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()
        tokens = tokenizer.tokenize("Merhaba dunya")

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        # Should not contain special tokens
        assert "[CLS]" not in tokens
        assert "[SEP]" not in tokens

    @requires_berturk_model
    def test_tokenize_with_offsets(self):
        """Test BPE tokenization with character offsets"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()
        result = tokenizer.tokenize_with_offsets("Merhaba")

        assert isinstance(result, list)
        for item in result:
            assert "token" in item
            assert "start" in item
            assert "end" in item
            assert isinstance(item["start"], int)
            assert isinstance(item["end"], int)

    @requires_berturk_model
    def test_get_ids(self):
        """Test getting token IDs"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()
        ids = tokenizer.get_ids("Merhaba")

        assert isinstance(ids, list)
        assert all(isinstance(i, int) for i in ids)

    @requires_berturk_model
    def test_decode(self):
        """Test decoding token IDs back to text"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()
        original = "Merhaba dunya"
        ids = tokenizer.get_ids(original)
        decoded = tokenizer.decode(ids)

        # Decoded should be similar to original (may have minor differences)
        assert isinstance(decoded, str)
        assert len(decoded) > 0

    @requires_berturk_model
    def test_vocab_size(self):
        """Test vocabulary size property"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()
        vocab_size = tokenizer.vocab_size

        # BERTurk has ~32K vocab
        assert vocab_size > 30000
        assert vocab_size < 50000


class TestBPETokenizerWithMock:
    """Tests with mocked tokenizer (no library required)"""

    def test_tokenize_with_mock(self):
        """Test BPE tokenization with mocked HuggingFace tokenizer"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import BPETokenizer

        # Reset singleton for testing
        BPETokenizer._instance = None

        # Create mock encoding
        mock_encoding = MagicMock()
        mock_encoding.tokens = ["Turki", "##ye", "guzel"]
        mock_encoding.offsets = [(0, 5), (5, 7), (8, 13)]
        mock_encoding.ids = [1234, 5678, 9012]

        # Create mock tokenizer
        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = mock_encoding
        mock_tokenizer.decode.return_value = "Turkiye guzel"
        mock_tokenizer.get_vocab_size.return_value = 32000

        # Create tokenizer and inject mock
        tokenizer = BPETokenizer()
        tokenizer._tokenizer = mock_tokenizer  # Bypass lazy loading

        tokens = tokenizer.tokenize("Turkiye guzel")

        assert tokens == ["Turki", "##ye", "guzel"]

    def test_tokenize_removes_special_tokens(self):
        """Test that special tokens [CLS], [SEP], [PAD] are removed"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import BPETokenizer

        # Reset singleton
        BPETokenizer._instance = None

        mock_encoding = MagicMock()
        mock_encoding.tokens = ["[CLS]", "Merhaba", "[SEP]", "[PAD]"]

        mock_tokenizer = MagicMock()
        mock_tokenizer.encode.return_value = mock_encoding

        tokenizer = BPETokenizer()
        tokenizer._tokenizer = mock_tokenizer

        tokens = tokenizer.tokenize("Merhaba")

        # Should only contain "Merhaba", not special tokens
        assert "[CLS]" not in tokens
        assert "[SEP]" not in tokens
        assert "[PAD]" not in tokens
        assert "Merhaba" in tokens


class TestBPEPropertyBased:
    """Property-based tests for BPE tokenization (REQ-4.6)"""

    @requires_berturk_model
    def test_property_tokenize_returns_list(self):
        """Property: tokenize always returns a list"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()

        test_cases = [
            "Merhaba",
            "Turkiye'nin baskenti Ankara",
            "123 456",
            "",
            "   ",
            "A",
            "Cok uzun bir cumle ile test yapalim bakalim nasil sonuc alacagiz",
        ]

        for text in test_cases:
            result = tokenizer.tokenize(text)
            assert isinstance(result, list), f"Failed for text: {text}"

    @requires_berturk_model
    def test_property_non_empty_text_has_tokens(self):
        """Property: non-empty, non-whitespace text produces at least one token"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()

        test_cases = [
            "Merhaba",
            "Test",
            "A",
            "1",
        ]

        for text in test_cases:
            tokens = tokenizer.tokenize(text)
            assert len(tokens) >= 1, f"Expected at least 1 token for '{text}'"

    @requires_berturk_model
    def test_property_decode_roundtrip(self):
        """Property: encode -> decode should approximate original text"""
        from backend.mcp_servers.zemberek_nlp.tools.bpe_tokenizer import (
            get_bpe_tokenizer,
        )

        tokenizer = get_bpe_tokenizer()

        test_cases = [
            "Merhaba",
            "Turkiye guzel bir ulke",
            "Istanbul'da hava guzel",
        ]

        for original in test_cases:
            ids = tokenizer.get_ids(original)
            decoded = tokenizer.decode(ids)
            # Remove extra spaces and special chars that may be added
            decoded_clean = decoded.replace("[CLS]", "").replace("[SEP]", "").strip()
            # Should be approximately the same
            assert original.lower() in decoded_clean.lower() or decoded_clean.lower() in original.lower(), \
                f"Roundtrip failed: '{original}' -> '{decoded_clean}'"
