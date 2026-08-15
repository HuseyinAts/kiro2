"""advanced_reports'un split şema (#485) sonrası IRT toplam sorgusunu çivileyen testler.

`_get_subject_irt_aggregate` içindeki 4 sınıf-düzeyi `QuestionBankItem.<alan>` erişimi
(irt_difficulty/irt_discrimination/irt_guessing QuestionStatistics'te, subject_area
QuestionMetadata'da) split sonrası devredicinin açık AttributeError'ını tetikliyordu —
sorgu KURULAMIYORDU. Ölçüldü (S214 kontrol kolu):

    AttributeError: QuestionBankItem.irt_difficulty sinif duzeyinde kullanilamaz

S212 A-sınıfı tuzağı: SELECT listesinde YALNIZ `QuestionStatistics` kolonları var, bu
yüzden SQLAlchemy sol tarafı o tablo sanar ve kendisine JOIN etmeye çalışır. Explicit
`.select_from(QuestionBankItem)` olmadan sorgu ÇALIŞMA anında değil KURULURKEN patlar
(`InvalidRequestError: Don't know how to join to ...`).

Bu bir kolon seçimi (entity DEĞİL) — `Row` döner, ORM nesnesi değil, yani lazy-load /
MissingGreenlet riski YOK. Ölçüldü:
`grep 'select(QuestionBankItem)' api/advanced_reports.py` → 0 sonuç.

Testler GERÇEK `models.question_bank` modeline karşı koşar (sahte `sys.modules` stub'ı
kırık kodda da yeşil kalıyordu — bkz. S212 D maddesi).
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _assert_single_from(stmt) -> None:
    """Kartezyen kontrolü — metin değil YAPI üzerinden (get_final_froms)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


class _CaptureSession:
    """`session.execute(stmt)` çağrısını yakalayan sahte AsyncSession."""

    def __init__(self, row):
        self.row = row
        self.stmt = None

    async def execute(self, stmt):
        self.stmt = stmt
        result = MagicMock()
        result.one.return_value = self.row
        return result


def _row(difficulty=0.5, discrimination=1.1, guessing=0.21, sample=42):
    return MagicMock(
        avg_difficulty=difficulty,
        avg_discrimination=discrimination,
        avg_guessing=guessing,
        sample_size=sample,
    )


@pytest.fixture
def wired(monkeypatch):
    """Cache'i boşa alır, DB oturumunu yakalayıcıyla değiştirir.

    `_get_subject_irt_aggregate` import'ları fonksiyon gövdesinde yaptığı için
    yamalar KAYNAK modüllerde (core.cache / core.database) yapılmalı.
    """
    import core.cache
    import core.database

    session = _CaptureSession(_row())

    @asynccontextmanager
    async def fake_ctx():
        yield session

    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    monkeypatch.setattr(core.database, "get_db_session_context", fake_ctx)
    monkeypatch.setattr(core.cache, "cache_manager", cache)
    return session, cache


class TestIRTAggregateCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, wired):
        """Kurulma + postgresql derlemesi — split öncesi burada AttributeError'dı."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        await _get_subject_irt_aggregate("matematik")

        assert session.stmt is not None, "session.execute hiç çağrılmadı"
        _compiled_sql(session.stmt)
        _assert_single_from(session.stmt)

    @pytest.mark.asyncio
    async def test_joins_both_split_tables(self, wired):
        """irt_* QuestionStatistics'ten, subject_area QuestionMetadata'dan okunmalı."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        await _get_subject_irt_aggregate("matematik")
        sql = _compiled_sql(session.stmt)

        assert "JOIN question_statistics" in sql, f"statistics JOIN yok:\n{sql}"
        assert "JOIN question_metadata" in sql, f"metadata JOIN yok:\n{sql}"
        assert "avg(question_statistics.irt_difficulty)" in sql, sql
        assert "avg(question_statistics.irt_discrimination)" in sql, sql
        assert "avg(question_statistics.irt_guessing)" in sql, sql

    @pytest.mark.asyncio
    async def test_left_side_is_question_bank(self, wired):
        """Explicit select_from — FROM question_bank olmalı, question_statistics DEĞİL."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        await _get_subject_irt_aggregate("matematik")
        sql = _compiled_sql(session.stmt)

        assert (
            "FROM question_bank JOIN" in sql
        ), f"sol taraf question_bank değil:\n{sql}"

    @pytest.mark.asyncio
    async def test_subject_filter_uppercased_on_metadata(self, wired):
        """subject_area filtresi QuestionMetadata'ya taşınmalı ve UPPERCASE kalmalı."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        await _get_subject_irt_aggregate("matematik")
        sql = _compiled_sql(session.stmt)

        assert "question_metadata.subject_area = 'MATEMATIK'" in sql, sql

    @pytest.mark.asyncio
    async def test_is_active_filter_preserved(self, wired):
        """is_active question_bank'te KALDI — JOIN çevirisinde düşürülmemeli."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        await _get_subject_irt_aggregate("matematik")
        sql = _compiled_sql(session.stmt)

        assert "question_bank.is_active" in sql, f"is_active kapısı düşmüş:\n{sql}"


class TestIRTAggregateResultShape:
    @pytest.mark.asyncio
    async def test_returns_expected_dict_shape(self, wired):
        """Dönen sözlüğün alan adları çağıranlarla (irt/ösym-ets) sözleşmeyi bozmasın."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, cache = wired
        session.row = _row(difficulty=0.25, discrimination=1.4, guessing=0.18, sample=7)

        result = await _get_subject_irt_aggregate("fizik")

        assert result == {
            "avg_difficulty": 0.25,
            "avg_discrimination": 1.4,
            "avg_guessing": 0.18,
            "sample_size": 7,
        }
        cache.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_null_aggregates_fall_back_to_defaults(self, wired):
        """Boş subject (JOIN sonrası 0 satır) → AVG NULL; varsayılanlar korunmalı."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, _ = wired
        session.row = _row(
            difficulty=None, discrimination=None, guessing=None, sample=None
        )

        result = await _get_subject_irt_aggregate("kimya")

        assert result == {
            "avg_difficulty": 0.0,
            "avg_discrimination": 1.0,
            "avg_guessing": 0.2,
            "sample_size": 0,
        }

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self, wired):
        """Cache dolu ise sorgu hiç kurulmamalı (DB'ye gidilmemeli)."""
        from api.advanced_reports import _get_subject_irt_aggregate

        session, cache = wired
        cached = {
            "avg_difficulty": 1.0,
            "avg_discrimination": 2.0,
            "avg_guessing": 0.3,
            "sample_size": 99,
        }
        cache.get = AsyncMock(return_value=cached)

        result = await _get_subject_irt_aggregate("biyoloji")

        assert result == cached
        assert session.stmt is None, "cache hit'te DB sorgusu kuruldu"
