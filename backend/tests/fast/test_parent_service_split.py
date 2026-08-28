"""parent_service.py'in split şema (#485) sonrası ders-bazlı doğruluk sorgusunu
çivileyen testler.

`get_child_performance` içindeki `answers_stmt` sınıf-düzeyi
`QuestionBankItem.subject_area` erişimi (alan artık `QuestionMetadata`'da)
sorgu KURULURKEN patlıyordu:

    AttributeError: QuestionBankItem.subject_area sinif duzeyinde kullanilamaz

Bu bir ENTITY-select değil, KOLON-select sorgusu (`select(QuestionMetadata.subject_area,
StudentAnswer.*, ...)`), bu yüzden S214'ün "select_from süs" ve "WHERE'i whereclause'da
ara" dersleri farklı şekilde uygulanır:

- `select_from` gerekmiyor — SELECT listesinde `StudentAnswer` kolonları da var,
  sol taraf zaten oradan çıkarılıyor (mevcut/eski kod da aynı şekilde çalışıyordu).
- SELECT listesindeki kolonun hangi tabloya ait olduğu YAPISAL olarak
  `stmt.selected_columns[0].table.name` ile doğrulanır — metin eşleşmesi değil.

Testler GERÇEK `models.question_bank` modeline karşı koşar (S212 D maddesi).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.dialects import postgresql


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _compiled_where(stmt) -> str:
    return str(
        stmt.whereclause.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


def _assert_single_from(stmt) -> None:
    """Kartezyen kontrolü — metin değil YAPI üzerinden (get_final_froms)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


def _relation_ok():
    result = MagicMock()
    result.fetchone.return_value = ("rel-1",)
    return result


def _user_result(user):
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    return result


def _exam_list_result(exams):
    result = MagicMock()
    result.scalars.return_value.all.return_value = exams
    return result


def _answer_rows_result(rows):
    result = MagicMock()
    result.all.return_value = rows
    return result


def _plan_result(plan):
    result = MagicMock()
    result.scalars.return_value.first.return_value = plan
    return result


class _CaptureSession:
    """`self.db.execute(stmt)` çağrılarını sırayla yakalayan sahte AsyncSession.

    Çağrı sırası (`get_child_performance`): [0] ilişki kontrolü (raw text),
    [1] child user, [2] ExamSession listesi, [3] answers_stmt (hedef sorgu),
    [4] aktif StudyPlan.
    """

    def __init__(self, results: list):
        self._results = results
        self.statements: list = []

    async def execute(self, stmt, params=None):
        idx = len(self.statements)
        self.statements.append(stmt)
        return self._results[idx]


def _child(first_name="Ali", last_name="Veli"):
    return SimpleNamespace(first_name=first_name, last_name=last_name)


def _session(*, exams=None, answer_rows=None, plan=None, child=None):
    return _CaptureSession(
        [
            _relation_ok(),
            _user_result(child or _child()),
            _exam_list_result(exams or []),
            _answer_rows_result(answer_rows or []),
            _plan_result(plan),
        ]
    )


class TestGetChildPerformanceCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self):
        """Kurulma + postgresql derlemesi — split öncesi burada AttributeError'dı."""
        from services.parent_service import ParentService

        session = _session()
        await ParentService(session).get_child_performance("p-1", "c-1")

        answers_stmt = session.statements[3]
        _compiled_sql(answers_stmt)
        _assert_single_from(answers_stmt)

    @pytest.mark.asyncio
    async def test_subject_area_selected_from_metadata_not_question_bank(self):
        """SELECT listesindeki subject_area artık question_metadata'ya ait olmalı."""
        from services.parent_service import ParentService

        session = _session()
        await ParentService(session).get_child_performance("p-1", "c-1")

        answers_stmt = session.statements[3]
        assert answers_stmt.selected_columns[0].table.name == "question_metadata"

    @pytest.mark.asyncio
    async def test_joins_question_metadata_without_cartesian(self):
        from services.parent_service import ParentService

        session = _session()
        await ParentService(session).get_child_performance("p-1", "c-1")

        sql = _compiled_sql(session.statements[3])
        assert (
            "JOIN question_metadata ON question_metadata.id = question_bank.id" in sql
        ), sql
        _assert_single_from(session.statements[3])

    @pytest.mark.asyncio
    async def test_where_clause_filters_on_student_id(self):
        """WHERE iddiası whereclause üzerinden derlenir (S214 dersi)."""
        from services.parent_service import ParentService

        session = _session()
        await ParentService(session).get_child_performance("p-1", "c-42")

        where_sql = _compiled_where(session.statements[3])
        assert "exam_sessions.student_id = 'c-42'" in where_sql, where_sql


class TestGetChildPerformanceBusinessLogic:
    @pytest.mark.asyncio
    async def test_subject_stats_flow_from_metadata_join_result(self):
        """answers_stmt'ten dönen (subject_area, ...) satırları doğru sırayla
        unpack edilip ders bazlı doğruluğa yansımalı — JOIN sonrası sütun sırası
        bozulmamış olmalı.
        """
        from services.parent_service import ParentService

        # classify_subjects min_questions=3 eşiği altındaki dersleri eler
        # (bkz. tests/unit/test_parent_kpi_aggregation.py), bu yüzden her
        # ders için en az 3 satır kullanılır.
        rows = [
            ("MATEMATIK", "A", True, None),
            ("MATEMATIK", "B", False, None),
            ("MATEMATIK", "C", True, None),
            ("TURKCE", "A", True, None),
            ("TURKCE", "B", True, None),
            ("TURKCE", "C", True, None),
        ]
        session = _session(answer_rows=rows)

        result = await ParentService(session).get_child_performance("p-1", "c-1")

        progress_by_subject = {p["subject"]: p for p in result.subject_progress}
        assert progress_by_subject["MATEMATIK"]["answered"] == 3
        assert round(progress_by_subject["MATEMATIK"]["mastery"], 2) == 66.7
        assert progress_by_subject["TURKCE"]["mastery"] == 100.0

    @pytest.mark.asyncio
    async def test_no_answers_returns_empty_subject_progress(self):
        from services.parent_service import ParentService

        session = _session()
        result = await ParentService(session).get_child_performance("p-1", "c-1")

        assert result.subject_progress == []
        assert result.solved_questions == 0
