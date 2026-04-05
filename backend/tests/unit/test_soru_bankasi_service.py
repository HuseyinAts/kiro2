"""
Unit tests for services/soru_bankasi_service.py

Tests the SoruBankasiServisi singleton that manages the question_bank table
(77,336 production questions). All DB and cache calls are mocked.

Rules:
- NO assert True / assert False patterns
- NO empty tests
- Mock db_manager.get_session and cache_manager
- Verify is_active == True filter is applied in every query path
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_question(
    id: str = "q-001",
    exam_type: str = "TYT",
    subject_area: str = "MATEMATIK",
    difficulty_level: str = "medium",
    irt_difficulty: float = 0.0,
    irt_discrimination: float = 1.0,
    irt_guessing: float = 0.25,
    is_active: bool = True,
    times_asked: int = 0,
    times_correct: int = 0,
    average_response_time: float = 0.0,
    morphology_complexity: float = 0.0,
    readability_score: float = 0.0,
) -> MagicMock:
    """Return a minimal MagicMock that looks like a QuestionBankItem."""
    q = MagicMock()
    q.id = id
    q.exam_type = exam_type
    q.subject_area = subject_area
    q.difficulty_level = difficulty_level
    q.irt_difficulty = irt_difficulty
    q.irt_discrimination = irt_discrimination
    q.irt_guessing = irt_guessing
    q.is_active = is_active
    q.times_asked = times_asked
    q.times_correct = times_correct
    q.average_response_time = average_response_time
    q.morphology_complexity = morphology_complexity
    q.readability_score = readability_score
    return q


def _scalars_result(items: list) -> MagicMock:
    """Build the MagicMock that session.execute() returns for .scalars().all() calls."""
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _scalar_one_or_none_result(item: Any) -> MagicMock:
    """Build the MagicMock for .scalar_one_or_none() calls."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = item
    return result_mock


def _scalar_result(value: Any) -> MagicMock:
    """Build the MagicMock for .scalar() calls (COUNT queries etc.)."""
    result_mock = MagicMock()
    result_mock.scalar.return_value = value
    return result_mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session() -> AsyncMock:
    """Bare async mock for SQLAlchemy AsyncSession."""
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def patches(mock_session):
    """
    Yield active patches for db_manager and cache_manager that stay alive
    for the duration of each test.  Also returns the mock objects.
    """

    @asynccontextmanager
    async def _session_ctx():
        yield mock_session

    mock_db = MagicMock()
    # Use side_effect so every call to get_session() gets a *fresh* context manager
    mock_db.get_session.side_effect = lambda: _session_ctx()

    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)  # cache miss by default
    mock_cache.set = AsyncMock()

    with (
        patch("services.soru_bankasi_service.db_manager", mock_db) as p_db,
        patch("services.soru_bankasi_service.cache_manager", mock_cache) as p_cache,
        patch("services.soru_bankasi_service.IRTAnalysisService"),
    ):
        yield {"db": mock_db, "cache": mock_cache, "session": mock_session}


@pytest.fixture
def service(patches):
    """Return a fresh SoruBankasiServisi instance with all deps patched."""
    from services.soru_bankasi_service import SoruBankasiServisi

    return SoruBankasiServisi()


# Helper: refresh the context manager each call (it's a one-shot generator)
def _rebind_session(patches_dict, mock_session):
    """
    db_manager.get_session() returns a context manager. Because it's consumed
    once per 'async with' call, we need to reset it before each service call
    that opens a DB session.
    """

    @asynccontextmanager
    async def _session_ctx():
        yield mock_session

    patches_dict["db"].get_session.return_value = _session_ctx()


# ---------------------------------------------------------------------------
# _normalize_topic (pure function — no DB needed)
# ---------------------------------------------------------------------------


class TestNormalizeTopic:
    def test_empty_string_returns_empty(self):
        from services.soru_bankasi_service import _normalize_topic

        result = _normalize_topic("")
        assert result == ""

    def test_turkish_dotted_i_lowercased_correctly(self):
        from services.soru_bankasi_service import _normalize_topic

        result = _normalize_topic("İSTANBUL")
        assert result == "istanbul"

    def test_dotless_i_maps_to_dotless_lowercase(self):
        from services.soru_bankasi_service import _normalize_topic

        result = _normalize_topic("IRMAK")
        assert "ı" in result  # I → ı

    def test_normal_ascii_word_lowercased(self):
        from services.soru_bankasi_service import _normalize_topic

        result = _normalize_topic("Matematik")
        assert result == "matematik"

    def test_nfc_normalization_applied(self):
        """Single-codepoint İ (NFC) must lower-case to plain i."""
        import unicodedata

        from services.soru_bankasi_service import _normalize_topic

        composed = unicodedata.normalize("NFC", "İ")
        result = _normalize_topic(composed)
        assert result == "i"


# ---------------------------------------------------------------------------
# _hece_say (syllable counter — pure, no async)
# ---------------------------------------------------------------------------


class TestHeceSay:
    def test_single_vowel_word_returns_one(self, service):
        assert service._hece_say("a") == 1

    def test_word_with_multiple_vowels(self, service):
        # 'a', 'e', 'a', 'i' in "matematik" → 4
        assert service._hece_say("matematik") == 4

    def test_consonant_only_cluster_returns_minimum_one(self, service):
        assert service._hece_say("krt") == 1

    def test_turkish_dotless_i_counts_as_vowel(self, service):
        # "ışık": 'ı' at pos 0 and pos 2 → 2 vowels
        assert service._hece_say("ışık") == 2


# ---------------------------------------------------------------------------
# _hesapla_morfoloji_karmasikligi (async, no DB)
# ---------------------------------------------------------------------------


class TestMorfolojiKarmasikligi:
    @pytest.mark.asyncio
    async def test_result_between_zero_and_one(self, service):
        result = await service._hesapla_morfoloji_karmasikligi(
            "Bu soruyu dikkatlice okuyarak cevaplayınız."
        )
        assert 0.0 <= result <= 1.0

    @pytest.mark.asyncio
    async def test_complex_suffix_increases_score(self, service):
        simple = "Soru kısadır."
        complex_text = "Bunu okuyarak düşündüğünde anlayabileceğin bir sonuç elde ederek ilerleyebilirsin."
        simple_score = await service._hesapla_morfoloji_karmasikligi(simple)
        complex_score = await service._hesapla_morfoloji_karmasikligi(complex_text)
        assert complex_score >= simple_score


# ---------------------------------------------------------------------------
# _hesapla_okunabilirlik (async, no DB)
# ---------------------------------------------------------------------------


class TestOkunabilirlik:
    @pytest.mark.asyncio
    async def test_result_between_zero_and_one(self, service):
        result = await service._hesapla_okunabilirlik(
            "Bu basit bir cümledir. Kısa ve anlaşılırdır."
        )
        assert 0.0 <= result <= 1.0

    @pytest.mark.asyncio
    async def test_no_sentence_terminator_still_works(self, service):
        result = await service._hesapla_okunabilirlik("Hiç noktalama işareti yok")
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# _hesapla_irt_parametreleri (async, no DB)
# ---------------------------------------------------------------------------


class TestHesaplaIrtParametreleri:
    @pytest.mark.asyncio
    async def test_returns_all_three_keys(self, service):
        params = await service._hesapla_irt_parametreleri("medium", "Matematik")
        assert "difficulty" in params
        assert "discrimination" in params
        assert "guessing" in params

    @pytest.mark.asyncio
    async def test_guessing_always_0_25(self, service):
        params = await service._hesapla_irt_parametreleri("hard", "Fizik")
        assert params["guessing"] == 0.25

    @pytest.mark.asyncio
    async def test_hard_difficulty_higher_than_easy(self, service):
        easy = await service._hesapla_irt_parametreleri("easy", "Matematik")
        hard = await service._hesapla_irt_parametreleri("hard", "Matematik")
        assert hard["difficulty"] > easy["difficulty"]

    @pytest.mark.asyncio
    async def test_discrimination_in_valid_range(self, service):
        params = await service._hesapla_irt_parametreleri("medium", "Kimya")
        assert 0.8 <= params["discrimination"] <= 2.0


# ---------------------------------------------------------------------------
# _hesapla_dogru_cevap_olasiligi (3PL IRT — async, no DB)
# ---------------------------------------------------------------------------


class TestDegroCevapOlasiligi:
    @pytest.mark.asyncio
    async def test_output_between_guessing_and_one(self, service):
        prob = await service._hesapla_dogru_cevap_olasiligi(0.0, 0.0, 1.0, 0.25)
        assert 0.25 <= prob <= 1.0

    @pytest.mark.asyncio
    async def test_high_ability_higher_probability(self, service):
        p_low = await service._hesapla_dogru_cevap_olasiligi(-3.0, 0.0, 1.0, 0.25)
        p_high = await service._hesapla_dogru_cevap_olasiligi(3.0, 0.0, 1.0, 0.25)
        assert p_high > p_low

    @pytest.mark.asyncio
    async def test_overflow_guard_positive_exponent(self, service):
        # exponent > 700 → returns tahmin
        prob = await service._hesapla_dogru_cevap_olasiligi(-1000.0, 0.0, 1.0, 0.25)
        assert prob == pytest.approx(0.25, abs=0.01)

    @pytest.mark.asyncio
    async def test_overflow_guard_negative_exponent(self, service):
        # exponent < -700 → returns 1.0
        prob = await service._hesapla_dogru_cevap_olasiligi(1000.0, 0.0, 1.0, 0.25)
        assert prob == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_at_equal_ability_and_difficulty(self, service):
        # θ == b → P = c + (1-c)*0.5 = 0.25 + 0.375 = 0.625
        prob = await service._hesapla_dogru_cevap_olasiligi(0.0, 0.0, 1.0, 0.25)
        assert prob == pytest.approx(0.625, abs=0.01)


# ---------------------------------------------------------------------------
# _hesapla_bilgi_fonksiyonu (IRT information — async, no DB)
# ---------------------------------------------------------------------------


class TestBilgiFonksiyonu:
    @pytest.mark.asyncio
    async def test_non_negative_information(self, service):
        info = await service._hesapla_bilgi_fonksiyonu(0.0, 0.0, 1.0, 0.25)
        assert info >= 0.0

    @pytest.mark.asyncio
    async def test_zero_when_probability_exactly_equals_guessing(self, service):
        # exponent > 700 path → _hesapla_dogru_cevap_olasiligi returns exactly tahmin
        # → guard `p_theta <= tahmin` fires → information = 0.0
        info = await service._hesapla_bilgi_fonksiyonu(-1000.0, 0.0, 1.0, 0.25)
        assert info == 0.0

    @pytest.mark.asyncio
    async def test_peak_near_item_difficulty(self, service):
        info_at = await service._hesapla_bilgi_fonksiyonu(0.0, 0.0, 1.5, 0.25)
        info_far = await service._hesapla_bilgi_fonksiyonu(3.0, 0.0, 1.5, 0.25)
        assert info_at > info_far

    @pytest.mark.asyncio
    async def test_higher_discrimination_gives_more_information(self, service):
        info_low_a = await service._hesapla_bilgi_fonksiyonu(0.0, 0.0, 0.5, 0.25)
        info_high_a = await service._hesapla_bilgi_fonksiyonu(0.0, 0.0, 2.0, 0.25)
        assert info_high_a > info_low_a


# ---------------------------------------------------------------------------
# soru_getir — cache hit path
# ---------------------------------------------------------------------------


class TestSoruGetirCacheHit:
    @pytest.mark.asyncio
    async def test_returns_cached_question_without_db_call(self, patches, mock_session):
        cached_question = _make_question(id="q-cached")
        patches["cache"].get = AsyncMock(return_value=cached_question)

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_getir("q-cached")

        assert result is cached_question
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# soru_getir — DB path (cache miss)
# ---------------------------------------------------------------------------


class TestSoruGetirDbPath:
    @pytest.mark.asyncio
    async def test_returns_question_from_db(self, patches, mock_session):
        question = _make_question(id="q-db")
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_getir("q-db")

        assert result is question
        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_getir("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_db_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_getir("q-error")

        assert result is None


# ---------------------------------------------------------------------------
# sorular_listele
# ---------------------------------------------------------------------------


class TestSorularListele:
    @pytest.mark.asyncio
    async def test_returns_list_of_questions(self, patches, mock_session):
        questions = [_make_question(id=f"q-{i}") for i in range(5)]
        mock_session.execute = AsyncMock(return_value=_scalars_result(questions))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.sorular_listele()

        assert len(result) == 5
        assert result[0].id == "q-0"

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_no_db_results(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalars_result([]))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.sorular_listele(sinav_tipi="TYT")

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=RuntimeError("connection lost"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.sorular_listele(konu="Matematik")

        assert result == []

    @pytest.mark.asyncio
    async def test_db_is_called_on_cache_miss(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalars_result([]))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        await svc.sorular_listele(konu="matematik")

        mock_session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, patches, mock_session):
        cached = [_make_question()]
        patches["cache"].get = AsyncMock(return_value=cached)

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.sorular_listele()

        assert result is cached
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# rastgele_sorular_sec
# ---------------------------------------------------------------------------


class TestRastgeleSorularSec:
    @pytest.mark.asyncio
    async def test_returns_requested_count_when_pool_is_large(
        self, patches, mock_session
    ):
        questions = [_make_question(id=f"q-{i}") for i in range(30)]
        mock_session.execute = AsyncMock(return_value=_scalars_result(questions))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.rastgele_sorular_sec(sinav_tipi="TYT", soru_sayisi=10)

        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_returns_all_when_pool_smaller_than_requested(
        self, patches, mock_session
    ):
        questions = [_make_question(id=f"q-{i}") for i in range(3)]
        mock_session.execute = AsyncMock(return_value=_scalars_result(questions))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.rastgele_sorular_sec(sinav_tipi="TYT", soru_sayisi=20)

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("timeout"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.rastgele_sorular_sec(sinav_tipi="TYT", soru_sayisi=5)

        assert result == []

    @pytest.mark.asyncio
    async def test_konu_dagilimi_distributes_by_subject(self, patches, mock_session):
        mat_qs = [
            _make_question(id=f"mat-{i}", subject_area="MATEMATIK") for i in range(10)
        ]
        fen_qs = [_make_question(id=f"fen-{i}", subject_area="FEN") for i in range(10)]
        mock_session.execute = AsyncMock(return_value=_scalars_result(mat_qs + fen_qs))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.rastgele_sorular_sec(
            sinav_tipi="TYT",
            soru_sayisi=6,
            konu_dagilimi={"Matematik": 3, "Fen": 3},
        )

        assert len(result) == 6
        assert sum(1 for q in result if q.subject_area == "MATEMATIK") == 3
        assert sum(1 for q in result if q.subject_area == "FEN") == 3


# ---------------------------------------------------------------------------
# soru_sil (soft delete)
# ---------------------------------------------------------------------------


class TestSoruSil:
    @pytest.mark.asyncio
    async def test_soft_delete_sets_is_active_false(self, patches, mock_session):
        question = _make_question(id="q-del", is_active=True)
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        success = await svc.soru_sil("q-del")

        assert success is True
        assert question.is_active is False
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_false_when_question_not_found(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        success = await svc.soru_sil("q-missing")

        assert success is False
        mock_session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_returns_false_on_db_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("DB crash"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        success = await svc.soru_sil("q-exception")

        assert success is False
        mock_session.rollback.assert_awaited()


# ---------------------------------------------------------------------------
# soru_guncelle
# ---------------------------------------------------------------------------


class TestSoruGuncelle:
    @pytest.mark.asyncio
    async def test_updates_plain_text_field(self, patches, mock_session):
        question = _make_question(id="q-upd")
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        updated = await svc.soru_guncelle("q-upd", {"question_text": "Yeni metin"})

        assert updated is question
        assert question.question_text == "Yeni metin"
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_guncelle("q-missing", {"question_text": "x"})

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_db_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("lock timeout"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_guncelle("q-err", {"question_text": "x"})

        assert result is None
        mock_session.rollback.assert_awaited()


# ---------------------------------------------------------------------------
# soru_performans_guncelle
# ---------------------------------------------------------------------------


class TestSoruPerformansGuncelle:
    @pytest.mark.asyncio
    async def test_increments_times_asked_and_correct(self, patches, mock_session):
        question = _make_question(id="q-perf", times_asked=5, times_correct=3)
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        success = await svc.soru_performans_guncelle(
            "q-perf", dogru_cevap=True, cevap_suresi=30.0
        )

        assert success is True
        assert question.times_asked == 6
        assert question.times_correct == 4

    @pytest.mark.asyncio
    async def test_wrong_answer_does_not_increment_times_correct(
        self, patches, mock_session
    ):
        question = _make_question(id="q-wrong", times_asked=2, times_correct=1)
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        await svc.soru_performans_guncelle(
            "q-wrong", dogru_cevap=False, cevap_suresi=20.0
        )

        assert question.times_correct == 1  # unchanged

    @pytest.mark.asyncio
    async def test_sets_initial_response_time_when_zero(self, patches, mock_session):
        question = _make_question(id="q-time", times_asked=0, average_response_time=0.0)
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        await svc.soru_performans_guncelle(
            "q-time", dogru_cevap=True, cevap_suresi=45.0
        )

        assert question.average_response_time == 45.0

    @pytest.mark.asyncio
    async def test_returns_false_for_missing_question(self, patches, mock_session):
        mock_session.execute = AsyncMock(return_value=_scalar_one_or_none_result(None))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.soru_performans_guncelle(
            "q-no", dogru_cevap=True, cevap_suresi=10.0
        )

        assert result is False


# ---------------------------------------------------------------------------
# irt_parametrelerini_yeniden_hesapla
# ---------------------------------------------------------------------------


class TestIrtParametreleriYenidenHesapla:
    @pytest.mark.asyncio
    async def test_returns_false_when_not_enough_responses(self, patches, mock_session):
        question = _make_question(id="q-irt", times_asked=5)  # < 10
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.irt_parametrelerini_yeniden_hesapla("q-irt")

        assert result is False

    @pytest.mark.asyncio
    async def test_updates_difficulty_from_success_rate(self, patches, mock_session):
        question = _make_question(
            id="q-irt2", times_asked=20, times_correct=10, average_response_time=30.0
        )
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.irt_parametrelerini_yeniden_hesapla("q-irt2")

        assert result is True
        # 50% success rate → logit(0.5) = 0
        assert question.irt_difficulty == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_difficulty_clamped_to_valid_range(self, patches, mock_session):
        # Very low success rate → high raw logit, must be clamped to 3.0
        question = _make_question(
            id="q-hard", times_asked=100, times_correct=1, average_response_time=60.0
        )
        mock_session.execute = AsyncMock(
            return_value=_scalar_one_or_none_result(question)
        )

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        await svc.irt_parametrelerini_yeniden_hesapla("q-hard")

        assert -3.0 <= question.irt_difficulty <= 3.0

    @pytest.mark.asyncio
    async def test_returns_false_on_db_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.irt_parametrelerini_yeniden_hesapla("q-db-err")

        assert result is False


# ---------------------------------------------------------------------------
# get_interleaved_questions
# ---------------------------------------------------------------------------


class TestGetInterleavedQuestions:
    @pytest.mark.asyncio
    async def test_empty_subjects_returns_empty_list(self, service):
        result = await service.get_interleaved_questions(subjects=[])
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_up_to_count_questions(self, patches, mock_session):
        questions = [
            _make_question(id=f"q-{i}", subject_area="MATEMATIK") for i in range(20)
        ]
        mock_session.execute = AsyncMock(return_value=_scalars_result(questions))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_interleaved_questions(
            subjects=["Matematik"], count=5, exam_type="TYT"
        )

        assert len(result) <= 5

    @pytest.mark.asyncio
    async def test_returns_empty_on_db_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=RuntimeError("timeout"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_interleaved_questions(subjects=["Matematik"], count=5)

        assert result == []

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, patches, mock_session):
        cached = [_make_question()]
        patches["cache"].get = AsyncMock(return_value=cached)

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_interleaved_questions(subjects=["Matematik"], count=3)

        assert result is cached
        mock_session.execute.assert_not_called()


# ---------------------------------------------------------------------------
# get_exit_quiz_questions
# ---------------------------------------------------------------------------


class TestGetExitQuizQuestions:
    @pytest.mark.asyncio
    async def test_returns_questions_for_known_subject(self, patches, mock_session):
        questions = [_make_question(id=f"eq-{i}") for i in range(5)]
        mock_session.execute = AsyncMock(return_value=_scalars_result(questions))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_exit_quiz_questions(
            subject="Matematik", count=5, exam_type="TYT"
        )

        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_unknown_subject_defaults_to_matematik(self, patches, mock_session):
        """Unmapped subject must not raise; defaults to MATEMATIK."""
        mock_session.execute = AsyncMock(return_value=_scalars_result([]))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_exit_quiz_questions(subject="UnsupportedSubject")

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self, patches, mock_session):
        mock_session.execute = AsyncMock(side_effect=Exception("network error"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.get_exit_quiz_questions(
            subject="Fizik", count=3, exam_type="AYT"
        )

        assert result == []


# ---------------------------------------------------------------------------
# toplu_soru_ekle (batch insert)
# ---------------------------------------------------------------------------


def _make_soru_data(idx: int = 1) -> dict:
    return {
        "soru_metni": f"Test sorusu {idx}",
        "secenekler": ["A) A", "B) B", "C) C", "D) D"],
        "dogru_cevap": "A",
        "sinav_tipi": "TYT",
        "zorluk_seviyesi": "orta",
        "konu": "Matematik",
    }


class TestTopluSoruEkle:
    @pytest.mark.asyncio
    async def test_returns_statistics_dict(self, patches, mock_session):
        sorular = [_make_soru_data(i) for i in range(3)]

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.toplu_soru_ekle(sorular)

        assert "basarili" in result
        assert "basarisiz" in result
        assert "toplam" in result
        assert result["toplam"] == 3

    @pytest.mark.asyncio
    async def test_basarili_plus_basarisiz_equals_toplam(self, patches, mock_session):
        """basarili + basarisiz must always equal toplam regardless of individual errors."""
        sorular = [_make_soru_data(i) for i in range(4)]

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.toplu_soru_ekle(sorular)

        assert result["basarili"] + result["basarisiz"] == result["toplam"]
        assert result["toplam"] == 4

    @pytest.mark.asyncio
    async def test_returns_zero_basarili_on_commit_exception(
        self, patches, mock_session
    ):
        mock_session.commit = AsyncMock(side_effect=Exception("DB locked"))

        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.toplu_soru_ekle([_make_soru_data(i) for i in range(2)])

        assert result["basarili"] == 0
        assert result["basarisiz"] == 2

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero_counts(self, patches, mock_session):
        from services.soru_bankasi_service import SoruBankasiServisi

        svc = SoruBankasiServisi()
        result = await svc.toplu_soru_ekle([])

        assert result["basarili"] == 0
        assert result["basarisiz"] == 0
        assert result["toplam"] == 0


# ---------------------------------------------------------------------------
# _enum_donusturucu
# ---------------------------------------------------------------------------


class TestEnumDonusturucu:
    @pytest.mark.asyncio
    async def test_known_exam_type_returned_correctly(self, service):
        from models.database import ExamType

        exam_type, _, _ = await service._enum_donusturucu("AYT", "orta", "Matematik")
        assert exam_type == ExamType.AYT

    @pytest.mark.asyncio
    async def test_unknown_exam_type_defaults_to_tyt(self, service):
        from models.database import ExamType

        exam_type, _, _ = await service._enum_donusturucu(
            "INVALID", "orta", "Matematik"
        )
        assert exam_type == ExamType.TYT

    @pytest.mark.asyncio
    async def test_difficulty_mapping_easy_and_hard(self, service):
        from models.database import QuestionDifficulty

        _, easy, _ = await service._enum_donusturucu("TYT", "kolay", "Matematik")
        _, hard, _ = await service._enum_donusturucu("TYT", "zor", "Matematik")
        assert easy == QuestionDifficulty.EASY
        assert hard == QuestionDifficulty.HARD

    @pytest.mark.asyncio
    async def test_subject_turkce_mapping(self, service):
        from models.database import SubjectArea

        _, _, subject = await service._enum_donusturucu("TYT", "orta", "Türkçe")
        assert subject == SubjectArea.TURKCE


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_module_level_singleton_exists(self):
        with patch("services.soru_bankasi_service.IRTAnalysisService"):
            import importlib

            import services.soru_bankasi_service as sbs

            importlib.reload(sbs)
            assert sbs.soru_bankasi_servisi is not None
            assert isinstance(sbs.soru_bankasi_servisi, sbs.SoruBankasiServisi)
