"""productive_failure_service'in split şema (#485) sonrası sorgusunu çivileyen testler.

`get_pretest_questions` içindeki 9 sınıf-düzeyi `QuestionBankItem.<alan>` erişimi
(question_text/option_a-e/correct_answer ×7 QuestionContent'te, difficulty_level
QuestionStatistics'te, subject_area QuestionMetadata'da) split sonrası devredicinin
açık AttributeError'ını tetikliyordu — sorgu KURULAMIYORDU.

Bu bir `select(QuestionBankItem.id, ...)` KOLON seçimi (entity DEĞİL) — `Row` döner,
ORM nesnesi değil, yani lazy-load / MissingGreenlet riski YOK. Ölçüldü:
`grep 'select(QuestionBankItem)' services/productive_failure_service.py` → 0 sonuç
(bkz. test_duel_api_split.py'deki aynı desen).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql


def _fake_db(rows=None):
    db = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows or []
    db.execute = AsyncMock(return_value=result)
    return db


def _assert_single_from(stmt):
    """Kartezyen kontrolü — metin değil YAPI üzerinden (get_final_froms)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


def _compiled_sql(stmt) -> str:
    return str(
        stmt.compile(
            dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
        )
    )


class TestGetPretestQuestionsCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self):
        from services.productive_failure_service import get_pretest_questions

        db = _fake_db()
        await get_pretest_questions(db=db, topic_id="t-1", subject="MATEMATIK", count=5)

        assert db.execute.called
        stmt = db.execute.call_args[0][0]
        _compiled_sql(stmt)
        _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_query_builds_without_explicit_subject(self):
        """subject=None -> topic_id prefixinden türetilir, aynı sorgu şekli."""
        from services.productive_failure_service import get_pretest_questions

        db = _fake_db()
        await get_pretest_questions(db=db, topic_id="MAT.GEO.1", count=3)

        stmt = db.execute.call_args[0][0]
        _compiled_sql(stmt)
        _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_quality_gate_preserved(self):
        """Kalite kapısı (mv_safe_for_beta) JOIN çevirisinde düşürülmemeli."""
        from services.productive_failure_service import get_pretest_questions

        db = _fake_db()
        await get_pretest_questions(db=db, topic_id="t-1", subject="MATEMATIK", count=5)
        stmt = db.execute.call_args[0][0]
        sql = _compiled_sql(stmt)
        assert "mv_safe_for_beta" in sql, f"kalite kapısı düşmüş:\n{sql}"


class TestGetPretestQuestionsResultShape:
    @pytest.mark.asyncio
    async def test_returns_expected_dict_shape_from_row(self):
        """Row nesnesindeki kolon adları (question_text, option_a-e,
        correct_answer, difficulty_level) split JOIN sonrası da değişmemeli —
        döndürülen dict'in alan adları çağıran tarafla (productive_failure_api)
        sözleşmeyi bozmasın."""
        from services.productive_failure_service import get_pretest_questions

        row = MagicMock(
            id="q-1",
            question_text="Soru metni?",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            option_e=None,
            correct_answer="A",
            difficulty_level="medium",
        )
        db = _fake_db(rows=[row])

        result = await get_pretest_questions(
            db=db, topic_id="t-1", subject="MATEMATIK", count=5
        )

        assert result == [
            {
                "question_id": "q-1",
                "question_text": "Soru metni?",
                "options": {"A": "A", "B": "B", "C": "C", "D": "D", "E": None},
                "correct_answer": "A",
                "difficulty": "medium",
            }
        ]
