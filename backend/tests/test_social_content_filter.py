"""Tests for Social Content Filter — 7-layer moderation pipeline."""

import importlib
import os
import sys

import pytest

# backend/services/ and backend/app/services/ both exist.
# conftest adds app/ first, so "services" resolves to app/services/.
# Fix: register backend/services as a separate package path.
_backend = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_scf_path = os.path.join(_backend, "services", "social_content_filter.py")
_spec = importlib.util.spec_from_file_location(
    "services.social_content_filter",
    _scf_path,
    submodule_search_locations=[],
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["services.social_content_filter"] = _mod
_spec.loader.exec_module(_mod)

SocialContentFilter = _mod.SocialContentFilter
_normalize_tr = _mod._normalize_tr
_strip_evasion = _mod._strip_evasion


@pytest.fixture
def content_filter():
    return SocialContentFilter()


# ---------------------------------------------------------------------------
# Turkish NLP helpers
# ---------------------------------------------------------------------------


class TestNormalizeTr:
    def test_basic_lowercase(self):
        assert _normalize_tr("HELLO") == "hello"

    def test_turkish_i_mapping(self):
        # İ -> i (Turkish dotted capital I)
        assert _normalize_tr("İSTANBUL") == "istanbul"

    def test_turkish_undotted_i(self):
        # I -> ı (Turkish undotted capital I)
        result = _normalize_tr("ISIK")
        assert "ı" in result

    def test_empty_string(self):
        assert _normalize_tr("") == ""

    def test_nfc_normalization(self):
        # Composed vs decomposed İ
        composed = "\u0130"  # İ
        decomposed = "I\u0307"  # I + combining dot above
        assert _normalize_tr(composed) == "i"


class TestStripEvasion:
    def test_leetspeak(self):
        assert _strip_evasion("h3ll0") == "hello"

    def test_at_sign(self):
        assert _strip_evasion("s@l@k") == "salak"

    def test_dollar_sign(self):
        assert _strip_evasion("$alak") == "salak"

    def test_dots_removed(self):
        assert _strip_evasion("s.a.l.a.k") == "salak"


# ---------------------------------------------------------------------------
# Layer tests
# ---------------------------------------------------------------------------


class TestLengthLayer:
    @pytest.mark.asyncio
    async def test_empty_message_blocked(self, content_filter):
        result = await content_filter.filter_content("", "user1")
        assert not result.passed
        assert result.blocked_layer == "length"

    @pytest.mark.asyncio
    async def test_whitespace_only_blocked(self, content_filter):
        result = await content_filter.filter_content("   ", "user1")
        assert not result.passed
        assert result.blocked_layer == "length"

    @pytest.mark.asyncio
    async def test_too_long_blocked(self, content_filter):
        result = await content_filter.filter_content("a" * 2001, "user1")
        assert not result.passed
        assert result.blocked_layer == "length"

    @pytest.mark.asyncio
    async def test_normal_length_passes(self, content_filter):
        result = await content_filter.filter_content("merhaba", "user1")
        assert result.passed


class TestBlacklistLayer:
    @pytest.mark.asyncio
    async def test_heavy_word_blocked(self, content_filter):
        result = await content_filter.filter_content("amk ya", "user1")
        assert not result.passed
        assert result.blocked_layer == "blacklist"

    @pytest.mark.asyncio
    async def test_insult_blocked(self, content_filter):
        result = await content_filter.filter_content("salak misin", "user1")
        assert not result.passed
        assert result.blocked_layer == "blacklist"

    @pytest.mark.asyncio
    async def test_leetspeak_evasion_caught(self, content_filter):
        result = await content_filter.filter_content("s@l@k misin", "user1")
        assert not result.passed
        assert result.blocked_layer == "blacklist"

    @pytest.mark.asyncio
    async def test_clean_text_passes(self, content_filter):
        result = await content_filter.filter_content("Bu soruyu nasil cozerim", "user1")
        assert result.passed


class TestFlirtLayer:
    @pytest.mark.asyncio
    async def test_endearment_blocked(self, content_filter):
        result = await content_filter.filter_content("sevgilim nasilsin", "user1")
        assert not result.passed
        assert result.blocked_layer == "flirt"

    @pytest.mark.asyncio
    async def test_social_media_solicitation_blocked(self, content_filter):
        result = await content_filter.filter_content("instagramin ne", "user1")
        assert not result.passed
        assert result.blocked_layer == "flirt"

    @pytest.mark.asyncio
    async def test_meeting_request_blocked(self, content_filter):
        result = await content_filter.filter_content("bulusalim mi", "user1")
        assert not result.passed
        assert result.blocked_layer == "flirt"


class TestPersonalInfoLayer:
    @pytest.mark.asyncio
    async def test_phone_number_blocked(self, content_filter):
        result = await content_filter.filter_content("numaram 05321234567", "user1")
        assert not result.passed
        assert result.blocked_layer == "personal_info"

    @pytest.mark.asyncio
    async def test_email_blocked(self, content_filter):
        result = await content_filter.filter_content("mailem test@gmail.com", "user1")
        assert not result.passed
        assert result.blocked_layer == "personal_info"


class TestSpamLayer:
    @pytest.mark.asyncio
    async def test_repeated_chars_blocked(self, content_filter):
        result = await content_filter.filter_content("aaaaaaaaaa", "user1")
        assert not result.passed
        assert result.blocked_layer == "spam"

    @pytest.mark.asyncio
    async def test_all_caps_blocked(self, content_filter):
        result = await content_filter.filter_content(
            "BU SORUYU NASIL COZERIM YARDIM EDIN", "user1"
        )
        assert not result.passed
        assert result.blocked_layer == "spam"

    @pytest.mark.asyncio
    async def test_excessive_punctuation_blocked(self, content_filter):
        result = await content_filter.filter_content("ne??????!!!!!!!", "user1")
        assert not result.passed
        assert result.blocked_layer == "spam"


class TestFilterResult:
    @pytest.mark.asyncio
    async def test_clean_message_full_pipeline(self, content_filter):
        result = await content_filter.filter_content(
            "Bu integral sorusunda yardim eder misiniz", "user1"
        )
        assert result.passed
        assert result.blocked_layer is None
        assert result.flag_reason == "clean"
        assert result.processing_ms >= 0
        assert result.content_hash  # SHA-256 hash should exist

    @pytest.mark.asyncio
    async def test_details_contain_all_layers(self, content_filter):
        result = await content_filter.filter_content("merhaba", "user1")
        assert "length" in result.details
        assert "blacklist" in result.details

    @pytest.mark.asyncio
    async def test_pii_sanitized(self, content_filter):
        result = await content_filter.filter_content("numaram 05321234567 yaz", "user1")
        assert result.sanitized_content
        assert "[***]" in result.sanitized_content
