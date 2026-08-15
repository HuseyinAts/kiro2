"""question_bank_service'in split şema (#485) sonrası davranışını çivileyen testler.

Bu testler GERÇEK `models.question_bank` modelini kullanır — `tests/unit/
test_coverage_final_50.py` aynı servisi sahte (stub) bir model modülüyle
yüklüyor, o yüzden oradaki yeşil testler split davranışı hakkında hiçbir şey
ölçmez (`test_create_question` kırık kodda bile geçiyordu).

DB gerekmez: kurucu/delege davranışı saf Python, eager-load ise Select
nesnesinin `_with_options` alanından okunur.
"""

import re
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.question_bank import (
    QuestionContent,
    QuestionMetadata,
    QuestionStatistics,
)
from services.question_bank_service import QuestionBankService, split_question_fields


def _loaded_attrs(stmt) -> set[str]:
    """Select üzerindeki eager-load seçeneklerinin hedef ilişki adları."""
    names: set[str] = set()
    for opt in stmt._with_options:
        names.update(e.key for e in opt.path if hasattr(e, "key"))
    return names


def _make_service():
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return QuestionBankService(db), db


class TestSplitQuestionFields:
    """Delegeli alanlar doğru split tablosuna yönlendirilmeli."""

    def test_routes_each_field_to_owning_table(self):
        base, content, meta, stats = split_question_fields(
            {
                "soru_hash": "abc",  # question_bank (temel)
                "question_text": "Soru?",  # question_content
                "exam_type": "TYT",  # question_metadata
                "irt_difficulty": 0.75,  # question_statistics
            }
        )
        assert base == {"soru_hash": "abc"}
        assert content == {"question_text": "Soru?"}
        assert meta == {"exam_type": "TYT"}
        assert stats == {"irt_difficulty": 0.75}

    def test_unknown_key_stays_in_base(self):
        """Tanınmayan anahtar sessizce YUTULMAMALI — kurucuya gidip patlamalı."""
        base, _, _, _ = split_question_fields({"voliv_alan": 1})
        assert base == {"voliv_alan": 1}

    def test_id_is_not_treated_as_delegated(self):
        """'id' üç split tablosunun da PK'si; temelde kalmalı."""
        base, _, _, stats = split_question_fields({"id": "q-1"})
        assert base == {"id": "q-1"}
        assert "id" not in stats


class TestCreateQuestion:
    @pytest.mark.asyncio
    async def test_delegated_fields_land_on_related_rows(self):
        """Split öncesi bu çağrı TypeError/AttributeError ile ölüyordu."""
        svc, db = _make_service()
        q = await svc.create_question(
            {
                "soru_hash": "h1",
                "primary_topic_id": "t1",
                "question_text": "2+2 kaçtır?",
                "correct_answer": "B",
                "exam_type": "TYT",
                "grade_level": 12,
                "irt_difficulty": 1.25,
            },
            created_by="admin",
        )
        assert isinstance(q.content, QuestionContent)
        assert isinstance(q.metadata_info, QuestionMetadata)
        assert isinstance(q.statistics, QuestionStatistics)
        assert q.content.question_text == "2+2 kaçtır?"
        assert q.metadata_info.exam_type == "TYT"
        assert q.statistics.irt_difficulty == 1.25
        assert q.created_by == "admin"
        assert db.add.called

    @pytest.mark.asyncio
    async def test_irt_based_difficulty_is_computed(self):
        """statistics kaydı kurulmadan bu atama AttributeError atıyordu."""
        svc, _ = _make_service()
        q = await svc.create_question(
            {"soru_hash": "h2", "primary_topic_id": "t1", "irt_difficulty": 1.25}
        )
        assert q.statistics.irt_based_difficulty is not None

    @pytest.mark.asyncio
    async def test_works_without_any_delegated_field(self):
        """Yalnız temel alanlar verilse de statistics kurulmalı (irt hesabı için)."""
        svc, _ = _make_service()
        q = await svc.create_question({"soru_hash": "h3", "primary_topic_id": "t1"})
        assert isinstance(q.statistics, QuestionStatistics)


class TestEagerLoading:
    """Async oturumda yüklenmemiş ilişkiye erişmek MissingGreenlet atar;
    delege okuyan her metot split ilişkilerini eager-load etmeli."""

    @pytest.mark.asyncio
    async def test_get_question_eager_loads_split_relations(self):
        svc, db = _make_service()
        db.execute = AsyncMock(return_value=MagicMock())
        await svc.get_question("q-1")
        loaded = _loaded_attrs(db.execute.call_args[0][0])
        assert {"content", "metadata_info", "statistics"} <= loaded

    @pytest.mark.asyncio
    async def test_batch_update_difficulties_eager_loads_statistics(self):
        svc, db = _make_service()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)
        await svc.batch_update_difficulties()
        loaded = _loaded_attrs(db.execute.call_args[0][0])
        assert "statistics" in loaded

    @pytest.mark.asyncio
    async def test_search_questions_eager_loads_split_relations(self):
        svc, db = _make_service()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)
        await svc.search_questions()
        loaded = _loaded_attrs(db.execute.call_args[0][0])
        assert {"metadata_info", "statistics"} <= loaded

    @pytest.mark.asyncio
    async def test_questions_needing_calibration_eager_loads_statistics(self):
        svc, db = _make_service()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=result)
        await svc.get_questions_needing_calibration()
        loaded = _loaded_attrs(db.execute.call_args[0][0])
        assert "statistics" in loaded


class TestCompiledQueryShapes:
    """S212'de bir JOIN çevirisi DERLEME anında patlıyordu (eksik select_from);
    gözle inceleme bunu kaçırdı, derleme yakaladı."""

    @staticmethod
    def _from_clause(sql: str) -> str:
        """Derlenmiş SQL'in FROM yan tümcesi.

        NOT: `sql.split(" from ")` KULLANMA — SQLAlchemy 'FROM'u yeni satıra
        koyar (`... \\nFROM question_bank`), o yüzden boşluklu arama HİÇ
        eşleşmez ve kontrol sessizce boşa düşer (bu testin ilk sürümünde
        tam olarak bu oldu). Sınır olarak \\b kullanılır.
        """
        m = re.search(
            r"\bfrom\b(.*?)(?:\bwhere\b|\border by\b|\blimit\b|$)",
            sql,
            re.IGNORECASE | re.DOTALL,
        )
        assert m, f"FROM yan tümcesi bulunamadı:\n{sql}"
        return m.group(1)

    def test_from_clause_helper_detects_a_comma(self):
        """Kontrol kolu: alet gerçekten virgül yakalıyor mu? (vakum test önleme)"""
        assert "," in self._from_clause("SELECT 1 \nFROM a, b \nWHERE x")
        assert "," not in self._from_clause("SELECT 1 \nFROM a JOIN b ON 1 \nWHERE x")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "call",
        [
            lambda s: s.batch_update_difficulties(),
            lambda s: s.get_questions_needing_calibration(),
            lambda s: s.search_questions(exam_type="TYT", min_quality_score=0.5),
            lambda s: s.get_topic_statistics("t1"),
        ],
    )
    async def test_statement_compiles_against_postgres(self, call):
        from sqlalchemy.dialects import postgresql

        svc, db = _make_service()
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        result.scalar.return_value = 0
        db.execute = AsyncMock(return_value=result)
        # get_topic_statistics önce topic'i çeker; None dönerse erken çıkar
        # ve ölçmek istediğimiz sorgu HİÇ kurulmaz.
        db.get = AsyncMock(return_value=MagicMock())

        await call(svc)

        assert db.execute.called, "sorgu hiç çalıştırılmadı"
        for c in db.execute.call_args_list:
            stmt = c[0][0]
            # Derlemenin kendisi asıl kontrol: S212'de eksik select_from
            # yüzünden bu adım InvalidRequestError ile patlıyordu.
            sql = str(
                stmt.compile(
                    dialect=postgresql.dialect(),
                    compile_kwargs={"literal_binds": True},
                )
            )
            assert "," not in self._from_clause(sql), f"kartezyen çarpım riski:\n{sql}"
