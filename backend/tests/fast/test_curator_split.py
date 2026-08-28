"""curator.py'nin split şema (#485) sonrası sorgularını çivileyen testler.

get_queue/get_flagged_queue/post_verdict içindeki 10 sınıf-düzeyi
`QuestionBankItem.<alan>` erişimi (quality_review_status ×2 + difficulty_level ×2
QuestionStatistics'te, subject_area ×2 QuestionMetadata'da, question_image_url ×4
QuestionContent'te) split sonrası devredicinin açık AttributeError'ını
tetikliyordu — sorgu KURULAMIYORDU.

Üç endpoint de `select(QuestionBankItem)` (entity seçimi) kullanıyor ve
`_row_to_queue_item` / post_verdict gövdesi row.content/.metadata_info/.statistics
okuyor+yazıyor — eager-load olmadan async'te MissingGreenlet atar (S212 dersi).
Mock oturumla MissingGreenlet reprodüke EDİLEMEZ, bu yüzden eager-load YAPISAL
olarak doğrulanır (üretilen Select'te ilgili loader var mı) + delege
getter/setter'ı GERÇEK model üzerinde ayrıca test edilir.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.dialects import postgresql

from models.question_bank import QuestionBankItem, QuestionMetadata, QuestionStatistics

SPLIT_RELATIONS = {"content", "metadata_info", "statistics"}


def _loaded_attrs(stmt) -> set[str]:
    """Select üzerindeki eager-load seçeneklerinin hedef ilişki adları."""
    names: set[str] = set()
    for opt in stmt._with_options:
        names.update(e.key for e in opt.path if hasattr(e, "key"))
    return names


def _assert_single_from(stmt):
    """Kartezyen çarpım kontrolü — METİN DEĞİL yapı üzerinden (get_final_froms)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


def _compile(stmt):
    stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})


def _admin():
    return SimpleNamespace(id="admin-test-1")


def _count_result(n: int):
    r = MagicMock()
    r.scalar.return_value = n
    return r


def _scalars_result(rows: list):
    r = MagicMock()
    r.scalars.return_value.all.return_value = rows
    return r


def _recording_db(results: list):
    """Her execute() çağrısını sırayla `results`'tan döndürür, stmt'i kaydeder."""
    db = AsyncMock()
    calls: list = []

    async def fake_execute(stmt, *a, **kw):
        calls.append(stmt)
        idx = len(calls) - 1
        if idx < len(results):
            return results[idx]
        empty = MagicMock()
        empty.scalar.return_value = 0
        empty.all.return_value = []
        return empty

    db.execute = fake_execute
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db, calls


class TestGetQueueCompiledShapes:
    """quality_review_status/difficulty_level -> QuestionStatistics,
    subject_area -> QuestionMetadata, question_image_url -> QuestionContent."""

    @pytest.mark.asyncio
    async def test_default_filters_query_compiles(self):
        from api.curator import get_queue

        db, calls = _recording_db([_count_result(0), _scalars_result([])])
        resp = await get_queue(
            status_filter="bronze_clean",
            subject=None,
            difficulty=None,
            has_diagram=None,
            page=1,
            per_page=25,
            admin=_admin(),
            db=db,
        )
        assert resp.total == 0
        assert len(calls) == 2
        for stmt in calls:
            _compile(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_all_filters_query_builds_and_compiles(self):
        """subject + difficulty + has_diagram=True hepsi bir arada -> 3 ek JOIN."""
        from api.curator import get_queue

        db, calls = _recording_db([_count_result(0), _scalars_result([])])
        await get_queue(
            status_filter="pending",
            subject="matematik",
            difficulty="easy",
            has_diagram=True,
            page=2,
            per_page=10,
            admin=_admin(),
            db=db,
        )
        assert len(calls) == 2
        for stmt in calls:
            _compile(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_has_diagram_false_query_compiles(self):
        from api.curator import get_queue

        db, calls = _recording_db([_count_result(0), _scalars_result([])])
        await get_queue(
            status_filter="bronze_clean",
            subject=None,
            difficulty=None,
            has_diagram=False,
            page=1,
            per_page=25,
            admin=_admin(),
            db=db,
        )
        for stmt in calls:
            _compile(stmt)
            _assert_single_from(stmt)


class TestGetQueueEagerLoading:
    @pytest.mark.asyncio
    async def test_paged_query_eager_loads_split_relations(self):
        """_row_to_queue_item row.content/.metadata_info/.statistics okuyor."""
        from api.curator import get_queue

        db, calls = _recording_db([_count_result(0), _scalars_result([])])
        await get_queue(
            status_filter="bronze_clean",
            subject=None,
            difficulty=None,
            has_diagram=None,
            page=1,
            per_page=25,
            admin=_admin(),
            db=db,
        )
        paged_stmt = calls[1]
        assert _loaded_attrs(paged_stmt) >= SPLIT_RELATIONS


class TestGetFlaggedQueueEagerLoading:
    @pytest.mark.asyncio
    async def test_q_rows_query_compiles_and_eager_loads(self):
        from api.curator import get_flagged_queue

        count_r = _count_result(2)
        qids_r = MagicMock()
        qids_r.all.return_value = [("q-1",), ("q-2",)]
        q_rows_r = _scalars_result([])
        detail_r = MagicMock()
        detail_r.all.return_value = []

        db, calls = _recording_db([count_r, qids_r, q_rows_r, detail_r])
        resp = await get_flagged_queue(page=1, per_page=25, admin=_admin(), db=db)

        assert resp.total == 2
        assert len(calls) == 4

        q_rows_stmt = calls[2]
        _compile(q_rows_stmt)
        _assert_single_from(q_rows_stmt)
        assert _loaded_attrs(q_rows_stmt) >= SPLIT_RELATIONS


class TestPostVerdictEagerLoading:
    @pytest.mark.asyncio
    async def test_fetch_stmt_compiles_and_eager_loads_metadata_and_statistics(self):
        from api.curator import VerdictRequest, post_verdict

        question = QuestionBankItem(id="q-1", soru_hash="h", primary_topic_id="t")
        question.metadata_info = QuestionMetadata(pipeline_metadata={})
        question.statistics = QuestionStatistics(quality_review_status="bronze_clean")

        fetch_r = MagicMock()
        fetch_r.scalar_one_or_none.return_value = question
        db, calls = _recording_db([fetch_r])

        body = VerdictRequest(question_id="q-1", verdict="verify")
        with patch("api.curator.asyncio.to_thread", new=AsyncMock()):
            await post_verdict(body, request=None, admin=_admin(), db=db)

        fetch_stmt = calls[0]
        _compile(fetch_stmt)
        _assert_single_from(fetch_stmt)
        assert _loaded_attrs(fetch_stmt) >= {"metadata_info", "statistics"}


class TestPostVerdictRealModelDelegates:
    """GERÇEK modele karşı: split ilişkiler zaten yüklüyken (manuel atanmış)
    delege getter/setter'ın (quality_review_status, pipeline_metadata,
    reviewed_at) doğru ada/yöne yazdığını doğrular. MissingGreenlet riski
    mock oturumla reprodüke edilemez (bkz. modül docstring) — bu test onu
    değil, delege AD/YÖN doğruluğunu kapsar; sahte stub (SimpleNamespace)
    kullanmadığı için `test_curator_api.py`'nin kaçırdığı sınıfı yakalar."""

    @pytest.mark.asyncio
    async def test_verify_verdict_mutates_real_delegates(self):
        from api.curator import VerdictRequest, post_verdict

        question = QuestionBankItem(
            id="q-1", soru_hash="h", primary_topic_id="t", is_active=True
        )
        question.metadata_info = QuestionMetadata(pipeline_metadata={"ai_count": 3})
        question.statistics = QuestionStatistics(quality_review_status="bronze_clean")

        fetch_r = MagicMock()
        fetch_r.scalar_one_or_none.return_value = question
        db = AsyncMock()
        db.execute = AsyncMock(return_value=fetch_r)
        db.commit = AsyncMock()

        body = VerdictRequest(
            question_id="q-1",
            verdict="verify",
            notes="ok",
            reviewer_velocity_seconds=42,
        )
        with patch("api.curator.asyncio.to_thread", new=AsyncMock()):
            resp = await post_verdict(body, request=None, admin=_admin(), db=db)

        assert question.quality_review_status == "auto_judged_high"
        assert question.reviewed_by == "admin-test-1"
        assert question.pipeline_metadata["ai_count"] == 3
        assert question.pipeline_metadata["curator_verdict"]["verdict"] == "verify"
        assert resp.new_status == "auto_judged_high"
        assert resp.previous_status == "bronze_clean"
