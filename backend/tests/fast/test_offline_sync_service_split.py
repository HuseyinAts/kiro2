"""offline_sync_service.py'in split şema (#485) sonrası sorgusunu çivileyen testler.

`build_sync_package` iki kusur sınıfını birlikte taşıyordu:

1. **Sınıf düzeyi** (1 erişim — sorgu KURULURKEN patlıyordu, ölçüldü):
   `.where(QuestionBankItem.subject_area == subject.upper())` — alan artık
   `QuestionMetadata`'da:

       AttributeError: QuestionBankItem.subject_area sinif duzeyinde kullanilamaz

2. **Örnek düzeyi** (sayaç GÖRMEDİ — mnemonic_service ile aynı desen, S214
   dersi): `select(QuestionBankItem)` ile ENTITY seçiliyor, sonra döngüde
   `q.question_text` / `.option_a..e` / `.correct_answer` (content),
   `q.subject_area` (metadata_info), `q.difficulty_level` (statistics) OKUNUYOR.
   Üç ilişki de `lazy='select'` (ölçüldü) → async oturumda eager-load'suz
   erişim `MissingGreenlet` atardı. `selectinload` ZORUNLU.

Testler GERÇEK `models.question_bank` modeline karşı koşar (S212 D maddesi).

`select_from` yok: SELECT listesinde `QuestionBankItem` (tam entity) var,
sol taraf ondan çıkarılıyor — S214 dersi ile aynı desen.
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


def _eager_loaded(stmt) -> dict[str, str | None]:
    """Yüklenen ilişki -> yükleme stratejisi. Metin değil YAPI üzerinden."""
    loaded: dict[str, str | None] = {}
    for opt in stmt._with_options:
        relationship_name = opt.path[1].key
        strategy = dict(opt.context[0].strategy) if opt.context else {}
        loaded[relationship_name] = strategy.get("lazy")
    return loaded


class _CaptureSession:
    """`db.execute(stmt)` çağrılarını sırayla yakalayan sahte AsyncSession.

    Çağrı sırası: [0] FSRS due-cards sorgusu, [1] question_bank sorgusu,
    [2] offline_sync_packages INSERT (raw SQL, rows_per_call'da tanımlanmaz).
    """

    def __init__(self, rows_per_call: list[list]):
        self._rows_per_call = rows_per_call
        self.statements: list = []
        self.committed = False

    async def execute(self, stmt, params=None):
        idx = len(self.statements)
        self.statements.append(stmt)
        rows = self._rows_per_call[idx] if idx < len(self._rows_per_call) else []
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        return result

    async def commit(self):
        self.committed = True


def _real_question(
    *,
    qid="q-1",
    text="Soru metni?",
    answer="A",
    subject="MATEMATIK",
    topic_id="topic-1",
):
    """GERÇEK ORM nesneleri — sahte sys.modules stub'ı YOK (S212 D maddesi)."""
    from models.question_bank import (
        QuestionBankItem,
        QuestionContent,
        QuestionDifficultyLevel,
        QuestionMetadata,
        QuestionStatistics,
    )

    question = QuestionBankItem(id=qid, primary_topic_id=topic_id)
    question.content = QuestionContent(
        id=qid,
        question_text=text,
        option_a="A şıkkı",
        option_b="B şıkkı",
        option_c="C şıkkı",
        option_d="D şıkkı",
        option_e=None,
        correct_answer=answer,
    )
    question.metadata_info = QuestionMetadata(id=qid, subject_area=subject)
    question.statistics = QuestionStatistics(
        id=qid, difficulty_level=QuestionDifficultyLevel.MEDIUM
    )
    return question


class TestBuildSyncPackageCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self):
        """Kurulma + derleme — split öncesi subject verilince AttributeError'dı."""
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        await build_sync_package(db=session, student_id="stu-1", subject=None, limit=10)

        q_query = session.statements[1]
        _compiled_sql(q_query)
        _assert_single_from(q_query)

    @pytest.mark.asyncio
    async def test_entity_query_eager_loads_split_relationships(self):
        """ENTITY seçimi — okunan üç ilişki de `selectin` ile yüklenmeli."""
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        await build_sync_package(db=session, student_id="stu-1", subject=None, limit=10)

        assert _eager_loaded(session.statements[1]) == {
            "content": "selectin",
            "metadata_info": "selectin",
            "statistics": "selectin",
        }

    @pytest.mark.asyncio
    async def test_is_active_and_quality_gate_preserved(self):
        """is_active + safe_for_beta_gate WHERE'den düşmemeli.

        Tam SQL'de aranmaz (S214 dersi): `select(QuestionBankItem)` tüm
        question_bank kolonlarını SELECT listesine koyar, filtre silinse bile
        alt-metin eşleşir. Yalnız whereclause derlenir.
        """
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        await build_sync_package(db=session, student_id="stu-1", subject=None, limit=10)

        where_sql = _compiled_where(session.statements[1])
        assert "question_bank.is_active" in where_sql, where_sql

    @pytest.mark.asyncio
    async def test_subject_filter_joins_metadata_without_cartesian(self):
        """subject verilince question_metadata JOIN edilmeli, kartezyen olmamalı."""
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        await build_sync_package(
            db=session, student_id="stu-1", subject="matematik", limit=10
        )

        q_query = session.statements[1]
        sql = _compiled_sql(q_query)
        assert "FROM question_bank JOIN question_metadata" in sql, sql
        _assert_single_from(q_query)

    @pytest.mark.asyncio
    async def test_subject_where_clause_filters_on_metadata_uppercase(self):
        """WHERE iddiası sadece whereclause'da aranır (S214 dersi)."""
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        await build_sync_package(
            db=session, student_id="stu-1", subject="matematik", limit=10
        )

        where_sql = _compiled_where(session.statements[1])
        assert "question_metadata.subject_area = 'MATEMATIK'" in where_sql, where_sql


class TestBuildSyncPackageBusinessLogic:
    @pytest.mark.asyncio
    async def test_reads_delegated_fields_from_eager_loaded_relations(self):
        """Örnek düzeyi devrediciler — split sonrası asıl risk burasıydı.

        Gerçek ORM nesnesi + gerçek devrediciler; sonuç sözlüğü content
        (metin, seçenekler, doğru cevap), metadata_info (konu) ve statistics
        (zorluk) alanlarının hepsini içermeli.
        """
        from services.offline_sync_service import build_sync_package

        question = _real_question(
            qid="q-1",
            text="Bir üçgenin iç açıları toplamı kaçtır?",
            answer="C",
            subject="GEOMETRI",
        )
        session = _CaptureSession([[], [question]])

        result = await build_sync_package(
            db=session, student_id="stu-1", subject=None, limit=5
        )

        assert result["total_questions"] == 1
        entry = result["questions"][0]
        assert entry["id"] == "q-1"
        assert entry["text"] == "Bir üçgenin iç açıları toplamı kaçtır?"
        assert entry["correct_answer"] == "C"
        assert entry["subject"] == "GEOMETRI"
        assert entry["topic"] == "topic-1"
        assert entry["difficulty"] == "medium"
        assert entry["options"]["A"] == "A şıkkı"

    @pytest.mark.asyncio
    async def test_no_questions_returns_empty_list(self):
        from services.offline_sync_service import build_sync_package

        session = _CaptureSession([[], []])
        result = await build_sync_package(
            db=session, student_id="stu-1", subject=None, limit=5
        )

        assert result["questions"] == []
        assert result["total_questions"] == 0
        assert session.committed is True
