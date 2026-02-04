"""
Comprehensive tests for core/encoding.py
Tests Turkish character encoding and UTF-8 support
"""
import pytest
import json
import locale
from unittest.mock import patch, MagicMock
import sys
import os


class TestValidateTurkishText:
    """Test validate_turkish_text function"""

    def test_valid_turkish_text(self):
        """Test validation of valid Turkish text"""
        from core.encoding import validate_turkish_text

        text = "Türkçe karakterler: ç, ğ, ı, ö, ş, ü"
        result = validate_turkish_text(text)

        assert result is True

    def test_valid_uppercase_turkish(self):
        """Test validation of uppercase Turkish characters"""
        from core.encoding import validate_turkish_text

        text = "ÖĞRETMEN VE ÖĞRENCİ"
        result = validate_turkish_text(text)

        assert result is True

    def test_ascii_text(self):
        """Test validation of ASCII text"""
        from core.encoding import validate_turkish_text

        text = "Hello World"
        result = validate_turkish_text(text)

        assert result is True

    def test_empty_string(self):
        """Test validation of empty string"""
        from core.encoding import validate_turkish_text

        result = validate_turkish_text("")

        assert result is True


class TestEnsureUtf8Encoding:
    """Test ensure_utf8_encoding function"""

    def test_none_input(self):
        """Test ensure_utf8_encoding with None"""
        from core.encoding import ensure_utf8_encoding

        result = ensure_utf8_encoding(None)

        assert result == ""

    def test_string_input(self):
        """Test ensure_utf8_encoding with string"""
        from core.encoding import ensure_utf8_encoding

        text = "Türkçe metin"
        result = ensure_utf8_encoding(text)

        assert result == text

    def test_bytes_utf8_input(self):
        """Test ensure_utf8_encoding with UTF-8 bytes"""
        from core.encoding import ensure_utf8_encoding

        text = "Öğrenci"
        bytes_data = text.encode("utf-8")
        result = ensure_utf8_encoding(bytes_data)

        assert result == text

    def test_integer_input(self):
        """Test ensure_utf8_encoding with integer"""
        from core.encoding import ensure_utf8_encoding

        result = ensure_utf8_encoding(12345)

        assert result == "12345"

    def test_list_input(self):
        """Test ensure_utf8_encoding with list"""
        from core.encoding import ensure_utf8_encoding

        data = [1, 2, 3]
        result = ensure_utf8_encoding(data)

        assert "[1, 2, 3]" in result


class TestTurkishSafeEncode:
    """Test turkish_safe_encode function"""

    def test_encode_turkish_text(self):
        """Test encoding Turkish text"""
        from core.encoding import turkish_safe_encode

        text = "Türkçe"
        result = turkish_safe_encode(text)

        assert isinstance(result, bytes)
        assert result.decode("utf-8") == text

    def test_encode_with_non_string(self):
        """Test encoding with non-string input"""
        from core.encoding import turkish_safe_encode

        result = turkish_safe_encode(12345)

        assert isinstance(result, bytes)
        assert result.decode("utf-8") == "12345"

    def test_encode_with_custom_encoding(self):
        """Test encoding with custom encoding parameter"""
        from core.encoding import turkish_safe_encode

        text = "Test"
        result = turkish_safe_encode(text, encoding="ascii")

        assert isinstance(result, bytes)

    def test_encode_empty_string(self):
        """Test encoding empty string"""
        from core.encoding import turkish_safe_encode

        result = turkish_safe_encode("")

        assert result == b""


class TestTurkishSafeDecode:
    """Test turkish_safe_decode function"""

    def test_decode_bytes(self):
        """Test decoding bytes"""
        from core.encoding import turkish_safe_decode

        text = "Türkçe"
        bytes_data = text.encode("utf-8")
        result = turkish_safe_decode(bytes_data)

        assert result == text

    def test_decode_string_input(self):
        """Test decoding string (should return as-is)"""
        from core.encoding import turkish_safe_decode

        text = "Already a string"
        result = turkish_safe_decode(text)

        assert result == text

    def test_decode_with_errors_replace(self):
        """Test decoding with errors='replace'"""
        from core.encoding import turkish_safe_decode

        # Valid bytes
        bytes_data = "Öğrenci".encode("utf-8")
        result = turkish_safe_decode(bytes_data, errors="replace")

        assert "Öğrenci" in result


class TestNormalizeTurkishText:
    """Test normalize_turkish_text function"""

    def test_lowercase_conversion(self):
        """Test text is converted to lowercase"""
        from core.encoding import normalize_turkish_text

        text = "TÜRKÇE METİN"
        result = normalize_turkish_text(text)

        assert result == "türkçe metin"

    def test_strip_whitespace(self):
        """Test whitespace is stripped"""
        from core.encoding import normalize_turkish_text

        text = "  Metin  "
        result = normalize_turkish_text(text)

        assert result == "metin"

    def test_multiple_spaces_replaced(self):
        """Test multiple spaces are replaced with single space"""
        from core.encoding import normalize_turkish_text

        text = "Bir    iki     üç"
        result = normalize_turkish_text(text)

        assert result == "bir iki üç"

    def test_non_string_input(self):
        """Test normalization with non-string input"""
        from core.encoding import normalize_turkish_text

        result = normalize_turkish_text(12345)

        assert result == "12345"

    def test_empty_string(self):
        """Test normalization of empty string"""
        from core.encoding import normalize_turkish_text

        result = normalize_turkish_text("")

        assert result == ""


class TestGetSystemEncoding:
    """Test get_system_encoding function"""

    def test_returns_string(self):
        """Test get_system_encoding returns a string"""
        from core.encoding import get_system_encoding

        result = get_system_encoding()

        assert isinstance(result, str)

    def test_returns_valid_encoding(self):
        """Test returned encoding is valid"""
        from core.encoding import get_system_encoding

        result = get_system_encoding()

        assert result in ["utf-8", "UTF-8", "cp1252", "cp1254"] or len(result) > 0

    @patch("locale.getpreferredencoding")
    def test_fallback_to_utf8(self, mock_locale):
        """Test fallback to UTF-8 on exception"""
        from core.encoding import get_system_encoding

        mock_locale.side_effect = Exception("Locale error")
        result = get_system_encoding()

        assert result == "utf-8"


class TestSafeJsonEncode:
    """Test safe_json_encode function"""

    def test_encode_dict(self):
        """Test encoding dictionary"""
        from core.encoding import safe_json_encode

        data = {"name": "Öğrenci", "age": 18}
        result = safe_json_encode(data)

        assert "Öğrenci" in result
        assert isinstance(result, str)

    def test_encode_turkish_characters(self):
        """Test encoding preserves Turkish characters"""
        from core.encoding import safe_json_encode

        data = {"text": "Türkçe karakterler: ğüşıöç"}
        result = safe_json_encode(data)

        assert "Türkçe" in result
        assert "ğüşıöç" in result

    def test_encode_with_indent(self):
        """Test encoding with indent parameter"""
        from core.encoding import safe_json_encode

        data = {"key": "value"}
        result = safe_json_encode(data, indent=2)

        assert "\n" in result  # Indented JSON has newlines

    def test_encode_non_serializable(self):
        """Test encoding non-serializable object"""
        from core.encoding import safe_json_encode

        class CustomClass:
            pass

        obj = CustomClass()
        result = safe_json_encode(obj)

        assert isinstance(result, str)

    def test_encode_list(self):
        """Test encoding list"""
        from core.encoding import safe_json_encode

        data = ["bir", "iki", "üç"]
        result = safe_json_encode(data)

        assert "üç" in result


class TestSafeJsonDecode:
    """Test safe_json_decode function"""

    def test_decode_valid_json(self):
        """Test decoding valid JSON"""
        from core.encoding import safe_json_decode

        json_str = '{"name": "Öğrenci"}'
        result = safe_json_decode(json_str)

        assert result == {"name": "Öğrenci"}

    def test_decode_invalid_json(self):
        """Test decoding invalid JSON"""
        from core.encoding import safe_json_decode

        result = safe_json_decode("not valid json")

        assert result is None

    def test_decode_empty_string(self):
        """Test decoding empty string"""
        from core.encoding import safe_json_decode

        result = safe_json_decode("")

        assert result is None

    def test_decode_none(self):
        """Test decoding None"""
        from core.encoding import safe_json_decode

        result = safe_json_decode(None)

        assert result is None

    def test_decode_list_json(self):
        """Test decoding JSON list"""
        from core.encoding import safe_json_decode

        json_str = '["bir", "iki", "üç"]'
        result = safe_json_decode(json_str)

        assert result == ["bir", "iki", "üç"]


class TestSafeTurkishPrint:
    """Test safe_turkish_print function"""

    @patch("builtins.print")
    def test_print_turkish_text(self, mock_print):
        """Test printing Turkish text"""
        from core.encoding import safe_turkish_print

        text = "Türkçe metin"
        safe_turkish_print(text)

        mock_print.assert_called_once_with(text)

    @patch("builtins.print")
    def test_print_handles_encoding_error(self, mock_print):
        """Test printing handles encoding errors"""
        from core.encoding import safe_turkish_print

        # Simulate encoding error
        mock_print.side_effect = [
            UnicodeEncodeError("utf-8", "test", 0, 1, "error"),
            None,
        ]

        text = "Türkçe"
        safe_turkish_print(text)

        # Should be called twice (first fails, second succeeds with fallback)
        assert mock_print.call_count == 2


class TestGetEncodingInfo:
    """Test get_encoding_info function"""

    def test_returns_dict(self):
        """Test get_encoding_info returns dictionary"""
        from core.encoding import get_encoding_info

        result = get_encoding_info()

        assert isinstance(result, dict)

    def test_has_required_keys(self):
        """Test encoding info has required keys"""
        from core.encoding import get_encoding_info

        result = get_encoding_info()

        assert "system_encoding" in result
        assert "stdout_encoding" in result
        assert "filesystem_encoding" in result
        assert "locale" in result

    def test_values_are_not_none(self):
        """Test encoding info values are not None"""
        from core.encoding import get_encoding_info

        result = get_encoding_info()

        for key, value in result.items():
            assert value is not None

    def test_includes_python_io_encoding(self):
        """Test includes PYTHONIOENCODING"""
        from core.encoding import get_encoding_info

        result = get_encoding_info()

        assert "python_io_encoding" in result

    def test_includes_lang_and_lc_all(self):
        """Test includes LANG and LC_ALL"""
        from core.encoding import get_encoding_info

        result = get_encoding_info()

        assert "lang" in result
        assert "lc_all" in result


class TestSetupTurkishEncoding:
    """Test setup_turkish_encoding function"""

    @patch.dict(os.environ, {}, clear=True)
    def test_sets_pythonioencoding(self):
        """Test sets PYTHONIOENCODING environment variable"""
        from core import encoding

        # Re-run setup
        encoding.setup_turkish_encoding()

        assert os.environ.get("PYTHONIOENCODING") == "utf-8"

    @patch.dict(os.environ, {}, clear=True)
    def test_sets_lang(self):
        """Test sets LANG environment variable"""
        from core import encoding

        encoding.setup_turkish_encoding()

        assert os.environ.get("LANG") == "tr_TR.UTF-8"

    @patch.dict(os.environ, {}, clear=True)
    def test_sets_lc_all(self):
        """Test sets LC_ALL environment variable"""
        from core import encoding

        encoding.setup_turkish_encoding()

        assert os.environ.get("LC_ALL") == "tr_TR.UTF-8"
