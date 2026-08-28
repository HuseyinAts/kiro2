"""osym_routes.py'un split şema (#485) sonrası anchor atama sorgusunu çivileyen testler.

`auto_assign_anchors` içindeki 2 sınıf-düzeyi `QuestionBankItem.subject_area`
erişimi (alan artık `QuestionMetadata`'da) split sonrası devredicinin açık
AttributeError'ını tetikliyordu — sorgu KURULAMIYORDU:

    AttributeError: QuestionBankItem.subject_area sinif duzeyinde kullanilamaz

`id`/`is_anchor` QuestionBankItem üzerinde KALDI (split edilmedi), bu yüzden
`.order_by(QuestionBankItem.id)` ve döngüde `q.is_anchor = ...` dokunulmadı.

SELECT listesinde yalnız `QuestionBankItem` var (tam entity, split kolon
DEĞİL) — S214 dersi: `.select_from()` bu durumda SÜS, eklenmedi. Kartezyen
kontrolü METİNLE değil `get_final_froms()` ile yapılır (S212 B maddesi).
WHERE iddiası `stmt.whereclause` üzerinden derlenir, tam SQL'de aranmaz
(S214 dersi: `select(Entity)` tüm kolonları SELECT'e koyduğu için tam SQL'de
alt-metin eşleşmesi filtre silinse bile oluşabilir).

`is_anchor` split-olmayan bir alan olduğu için eager-load N/A — ölçüldü:
`grep 'select(QuestionBankItem)' api/osym_routes.py` → 2 sonuç, ikisi de
yalnız `is_anchor` yazıyor (instance-level, split tabloya dokunmuyor).

Testler GERÇEK `models.question_bank` modeline karşı koşar (S212 D maddesi
— sahte `sys.modules` stub'ı kırık kodda da yeşil kalıyordu).
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


def _assert_single_from(stmt) -> None:
    """Kartezyen kontrolü — metin değil YAPI üzerinden (get_final_froms)."""
    froms = stmt.get_final_froms()
    assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"


class _FakeQuestion:
    def __init__(self, id_: str, is_anchor: bool = False):
        self.id = id_
        self.is_anchor = is_anchor


class _CaptureSession:
    """`session.execute(stmt)` çağrılarını sırayla yakalayan sahte AsyncSession."""

    def __init__(self, rows_per_call: list[list]):
        self._rows_per_call = rows_per_call
        self.statements: list = []
        self.committed = False

    async def execute(self, stmt):
        rows = self._rows_per_call[len(self.statements)]
        self.statements.append(stmt)
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    async def commit(self):
        self.committed = True


@pytest.fixture
def wired(monkeypatch):
    """DB oturumunu yakalayıcıyla değiştirir.

    `auto_assign_anchors` importları fonksiyon gövdesinde yaptığı için yama
    KAYNAK modülde (`core.database`) yapılmalı.
    """
    import core.database

    def make(rows_per_call):
        session = _CaptureSession(rows_per_call)

        class _Ctx:
            async def __aenter__(self):
                return session

            async def __aexit__(self, *exc):
                return False

        monkeypatch.setattr(core.database, "get_db_session_context", lambda: _Ctx())
        return session

    return make


class TestAutoAssignAnchorsCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self, wired):
        """Kurulma + postgresql derlemesi — split öncesi burada AttributeError'dı."""
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        session = wired([[], []])
        await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="MATEMATIK", count=10)
        )

        assert len(session.statements) == 2, "iki sorgu da çalıştırılmalı (reset + seç)"
        for stmt in session.statements:
            _compiled_sql(stmt)
            _assert_single_from(stmt)

    @pytest.mark.asyncio
    async def test_both_queries_join_question_metadata(self, wired):
        """subject_area artık QuestionMetadata'da — her iki sorgu da JOIN etmeli."""
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        session = wired([[], []])
        await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="MATEMATIK", count=10)
        )

        for stmt in session.statements:
            sql = _compiled_sql(stmt)
            assert "JOIN question_metadata" in sql, f"metadata JOIN yok:\n{sql}"
            assert (
                "FROM question_bank JOIN" in sql
            ), f"sol taraf question_bank değil:\n{sql}"

    @pytest.mark.asyncio
    async def test_where_clause_filters_on_metadata_subject_area(self, wired):
        """WHERE iddiası SADECE whereclause'da aranır (tam SQL'de değil — S214 dersi).

        `select(QuestionBankItem)` tüm kolonları SELECT'e koyar; ama subject_area
        QuestionMetadata'da olduğu için SELECT listesinde YOK — tam SQL kontrolü
        de burada geçerli olurdu, whereclause daha sıkı ve tekrarlanabilir.
        """
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        session = wired([[], []])
        await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="MATEMATIK", count=10)
        )

        for stmt in session.statements:
            where_sql = _compiled_where(stmt)
            assert (
                "question_metadata.subject_area = 'MATEMATIK'" in where_sql
            ), where_sql

    @pytest.mark.asyncio
    async def test_select_query_orders_by_question_bank_id(self, wired):
        """id split edilmedi — order_by hâlâ question_bank.id olmalı."""
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        session = wired([[], []])
        await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="MATEMATIK", count=10)
        )

        sql = _compiled_sql(session.statements[1])
        assert "ORDER BY question_bank.id" in sql, sql
        assert "LIMIT 10" in sql, sql


class TestAutoAssignAnchorsBusinessLogic:
    @pytest.mark.asyncio
    async def test_resets_old_anchors_and_assigns_new(self, wired):
        """Eski anchor'lar False'a düşmeli, yeni seçilenler True olmalı."""
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        old_anchor = _FakeQuestion("q-old", is_anchor=True)
        new_anchor = _FakeQuestion("q-new", is_anchor=False)
        session = wired([[old_anchor], [new_anchor]])

        result = await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="FIZIK", count=5)
        )

        assert old_anchor.is_anchor is False
        assert new_anchor.is_anchor is True
        assert session.committed is True
        assert result == {
            "status": "success",
            "message": "1 soru anchor olarak atandı.",
            "subject": "FIZIK",
        }

    @pytest.mark.asyncio
    async def test_empty_subject_returns_zero_count(self, wired):
        """Eşleşen soru yoksa 0 sayısı dönmeli, hata fırlatmamalı."""
        from api.osym_routes import AutoAssignAnchorsRequest, auto_assign_anchors

        session = wired([[], []])

        result = await auto_assign_anchors(
            AutoAssignAnchorsRequest(subject="BILINMEYEN", count=100)
        )

        assert result["message"] == "0 soru anchor olarak atandı."
        assert session.committed is True
