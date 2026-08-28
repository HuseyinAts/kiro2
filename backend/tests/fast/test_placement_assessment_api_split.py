"""placement_assessment_api.py'nin `_check_correctness` yardımcısını (#485)
çivileyen testler.

`QuestionBankItem.correct_answer` sınıf-düzeyi erişimi (alan artık
`QuestionContent`'te) sorgu KURULURKEN AttributeError atıyordu. Bu dosyada
`QuestionBankItem`'ın başka hiçbir kolonu (is_active dahil) kullanılmıyordu,
bu yüzden JOIN gerekmiyor — `QuestionContent.id` `question_bank.id` ile aynı
paylaşılan PK olduğundan doğrudan `QuestionContent`'e filtrelemek yeterli.

Testler GERÇEK `models.question_bank` modeline karşı koşar (S212 D maddesi).
"""

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


def _capture_session(row):
    """`db.execute(stmt)` çağrısını yakalayan sahte AsyncSession."""
    session = MagicMock()
    session.statements = []

    async def _execute(stmt, params=None):
        session.statements.append(stmt)
        result = MagicMock()
        result.first.return_value = row
        return result

    session.execute = _execute
    return session


class TestCheckCorrectnessCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, monkeypatch):
        """Kurulma + postgresql derlemesi — split öncesi burada AttributeError'dı."""
        from api import placement_assessment_api as mod

        session = _capture_session(("A",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        await mod._check_correctness("q-1", "A")

        stmt = session.statements[0]
        _compiled_sql(stmt)
        froms = stmt.get_final_froms()
        assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"

    @pytest.mark.asyncio
    async def test_correct_answer_selected_from_question_content(self, monkeypatch):
        from api import placement_assessment_api as mod

        session = _capture_session(("A",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        await mod._check_correctness("q-1", "A")

        stmt = session.statements[0]
        assert stmt.selected_columns[0].table.name == "question_content"

    @pytest.mark.asyncio
    async def test_where_clause_filters_on_question_id(self, monkeypatch):
        """WHERE iddiası whereclause üzerinden derlenir (S214 dersi)."""
        from api import placement_assessment_api as mod

        session = _capture_session(("A",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        await mod._check_correctness("q-42", "A")

        where_sql = _compiled_where(session.statements[0])
        assert "question_content.id = 'q-42'" in where_sql, where_sql


class TestCheckCorrectnessBusinessLogic:
    @pytest.mark.asyncio
    async def test_matching_answer_returns_true(self, monkeypatch):
        from api import placement_assessment_api as mod

        session = _capture_session(("A",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        assert await mod._check_correctness("q-1", "a") is True

    @pytest.mark.asyncio
    async def test_non_matching_answer_returns_false(self, monkeypatch):
        from api import placement_assessment_api as mod

        session = _capture_session(("B",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        assert await mod._check_correctness("q-1", "A") is False

    @pytest.mark.asyncio
    async def test_multi_char_correct_answer_truncated_to_first(self, monkeypatch):
        """Mevcut davranış: `correct_answer` 1 karakterden uzunsa ilk karakter alınır."""
        from api import placement_assessment_api as mod

        session = _capture_session(("A) Seçenek metni",))
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        assert await mod._check_correctness("q-1", "A") is True

    @pytest.mark.asyncio
    async def test_missing_row_returns_false(self, monkeypatch):
        from api import placement_assessment_api as mod

        session = _capture_session(None)
        monkeypatch.setattr(
            mod, "get_db_session_context", lambda: _Ctx(session), raising=True
        )

        assert await mod._check_correctness("q-missing", "A") is False


class _Ctx:
    """`get_db_session_context()` async context manager sahtesi."""

    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc_info):
        return False
