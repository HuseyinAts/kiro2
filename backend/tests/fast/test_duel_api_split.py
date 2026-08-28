"""duel_api'nin split şema (#485) sonrası sorgularını çivileyen testler.

Bu dosyadaki 12 sınıf-düzeyi `QuestionBankItem.<alan>` erişimi kolon seçimi
(entity DEĞİL) içinde: `select(QuestionBankItem.question_text, ...)`. Split
sonrası bu erişimler devredicinin açık AttributeError'ını tetikler, yani
sorgu KURULAMAZ — düello akışı çalışma anında değil, sorgu kurulurken patlar.

Entity seçimi olmadığı için (Row döner, ORM nesnesi değil) bu dosyada
lazy-load / MissingGreenlet riski YOK — eager-load kontrolü N/A. Ölçüldü:
`grep 'select(QuestionBankItem)' api/duel_api.py` → 0 sonuç.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.dialects import postgresql


def _fake_ctx(db):
    @asynccontextmanager
    async def _ctx():
        yield db

    return _ctx


def _fake_db():
    db = AsyncMock()
    result = MagicMock()
    result.first.return_value = None
    result.all.return_value = []
    result.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=result)
    return db


def _assert_single_from(stmt):
    """Kartezyen kontrolü — metin değil YAPI üzerinden (get_final_froms).

    Metinsel "FROM'da virgül" kontrolü `SELECT count(*) FROM (SELECT a, b ...)`
    şeklinde yanlış-pozitif verir; S212'de bir kez verdi.
    """
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


def _compile_all(db):
    """db üzerinde kurulan HER sorguyu postgres'e karşı derle + FROM kontrolü."""
    assert db.execute.called, "hiç sorgu kurulmadı"
    for call in db.execute.call_args_list:
        stmt = call[0][0]
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
        _assert_single_from(stmt)


class TestSelectDuelQuestions:
    """IRT bandı + top-up fallback: subject_area -> QuestionMetadata,
    irt_difficulty -> QuestionStatistics."""

    @pytest.mark.asyncio
    async def test_irt_band_query_builds_and_compiles(self):
        from api import duel_api

        db = _fake_db()
        with patch.object(duel_api, "get_db_session_context", _fake_ctx(db)):
            await duel_api._select_duel_questions("MATEMATIK", count=5)
        _compile_all(db)

    @pytest.mark.asyncio
    async def test_topup_fallback_query_builds_and_compiles(self):
        """IRT bandı boş dönünce top-up sorgusu kurulur — o da split alan kullanıyor."""
        from api import duel_api

        db = _fake_db()
        with patch.object(duel_api, "get_db_session_context", _fake_ctx(db)):
            await duel_api._select_duel_questions("MATEMATIK", count=5)
        assert len(db.execute.call_args_list) >= 2, "top-up sorgusu kurulmadı"
        _compile_all(db)

    @pytest.mark.asyncio
    async def test_quality_gate_still_applied_to_both_queries(self):
        """Kalite kapısı korunmalı: kapısız sorgu yargılanmamış/reddedilmiş
        soruyu öğrenciye servis eder (kapı S212 öncesi eklendi, JOIN
        çevirisinde düşürülmemeli)."""
        from api import duel_api

        db = _fake_db()
        with patch.object(duel_api, "get_db_session_context", _fake_ctx(db)):
            await duel_api._select_duel_questions("MATEMATIK", count=5)
        for call in db.execute.call_args_list:
            sql = str(
                call[0][0].compile(
                    dialect=postgresql.dialect(),
                    compile_kwargs={"literal_binds": True},
                )
            )
            assert "mv_safe_for_beta" in sql, f"kalite kapısı düşmüş:\n{sql}"


class TestCheckAnswerCorrectness:
    """correct_answer -> QuestionContent."""

    @pytest.mark.asyncio
    async def test_answer_lookup_query_builds_and_compiles(self):
        from api import duel_api

        db = _fake_db()
        match_row = MagicMock()
        match_row.__getitem__ = lambda self, i: "q-1"
        first_result = MagicMock()
        first_result.first.return_value = match_row
        db.execute = AsyncMock(return_value=first_result)

        with patch.object(duel_api, "get_db_session_context", _fake_ctx(db)):
            await duel_api._check_answer_correctness("s-1", 1, "A")
        _compile_all(db)


class TestGetCurrentQuestion:
    """question_text + option_a-e -> QuestionContent."""

    @pytest.mark.asyncio
    async def test_question_fetch_query_builds_and_compiles(self):
        from api import duel_api

        db = _fake_db()
        session = MagicMock(
            status="active",
            time_per_question_sec=30,
            player1_score=0,
            player2_score=0,
            player1_id="u-1",
            player2_id="u-2",
        )
        match = MagicMock(question_order=1, question_id="q-1")
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=session)),
            MagicMock(scalar=MagicMock(return_value=3)),
            MagicMock(scalar_one_or_none=MagicMock(return_value=match)),
            MagicMock(first=MagicMock(return_value=None)),
        ]
        db.execute = AsyncMock(side_effect=results * 4)
        user = MagicMock(id="u-1", user_id="u-1")

        with patch.object(duel_api, "get_db_session_context", _fake_ctx(db)):
            try:
                await duel_api.get_current_question("s-1", current_user=user)
            except Exception as exc:  # 404 vb. iş kuralı hatası sorun değil
                assert "AttributeError" not in type(exc).__name__, exc
        _compile_all(db)
