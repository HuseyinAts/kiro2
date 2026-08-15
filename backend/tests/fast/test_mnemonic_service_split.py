"""mnemonic_service'in split şema (#485) sonrası sorgularını çivileyen testler.

Bu dosya seride **iki kusur sınıfını birlikte** taşıyan ilk dosyaydı:

1. **Sınıf düzeyi** (3 erişim, sorgu KURULURKEN patlıyordu — ölçüldü):
   `get_mnemonic` → `QuestionBankItem.question_text` (QuestionContent),
   `QuestionBankItem.subject_area` (QuestionMetadata);
   `batch_generate_mnemonics` → `QuestionBankItem.subject_area`.

       AttributeError: QuestionBankItem.question_text sinif duzeyinde kullanilamaz

2. **Örnek düzeyi** — `generate_mnemonic` `select(QuestionBankItem)` ile ENTITY
   seçiyor, sonra `question.question_text` / `.correct_answer` / `.subject_area`
   okuyor. Üç ilişki de `lazy='select'` (ölçüldü) → async oturumda eager-load'suz
   erişim `MissingGreenlet` atar. Bu yüzden `selectinload` ZORUNLU; önceki beş
   dosyada N/A'ydı, burada değil.

Testler GERÇEK `models.question_bank` modeline karşı koşar.
"""

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


def _eager_loaded(stmt) -> dict[str, str | None]:
    """Yüklenen ilişki -> yükleme stratejisi. Metin değil YAPI üzerinden.

    `lazyload` da bir `_with_options` girdisi üretir; bu yüzden yalnız
    "seçenek var mı" bakmak yetmez, stratejinin `selectin` olduğu da ölçülür.
    """
    loaded: dict[str, str | None] = {}
    for opt in stmt._with_options:
        relationship_name = opt.path[1].key
        strategy = dict(opt.context[0].strategy) if opt.context else {}
        loaded[relationship_name] = strategy.get("lazy")
    return loaded


class _CaptureDB:
    """`db.execute(stmt)` çağrılarını yakalayan sahte AsyncSession."""

    def __init__(self, *, first=None, scalar=None, all_rows=None):
        self.statements: list = []
        self._first = first
        self._scalar = scalar
        self._all = all_rows or []

    async def execute(self, stmt):
        self.statements.append(stmt)
        result = MagicMock()
        result.first.return_value = self._first
        result.scalar_one_or_none.return_value = self._scalar
        result.all.return_value = self._all
        return result

    @property
    def stmt(self):
        return self.statements[-1]


def _real_question(*, qid="q-1", text="Soru metni?", answer="A", subject="MATEMATIK"):
    """GERÇEK ORM nesneleri — sahte sys.modules stub'ı YOK.

    İlişkiler elle bağlanır: eager-load edilmiş bir satırın örnek düzeyi
    devredicilerinin çalıştığını kanıtlar (S212 D maddesi).
    """
    from models.question_bank import (
        QuestionBankItem,
        QuestionContent,
        QuestionMetadata,
    )

    question = QuestionBankItem(id=qid)
    question.content = QuestionContent(
        id=qid, question_text=text, correct_answer=answer
    )
    question.metadata_info = QuestionMetadata(id=qid, subject_area=subject)
    return question


class TestGetMnemonicCompiledShape:
    @pytest.mark.asyncio
    async def test_query_builds_and_compiles(self):
        """Kurulma + derleme — split öncesi burada AttributeError'dı."""
        from services.mnemonic_service import get_mnemonic

        db = _CaptureDB(first=None)
        await get_mnemonic(db=db, question_id="q-1")

        _compiled_sql(db.stmt)
        _assert_single_from(db.stmt)

    @pytest.mark.asyncio
    async def test_joins_both_split_tables(self):
        from services.mnemonic_service import get_mnemonic

        db = _CaptureDB(first=None)
        await get_mnemonic(db=db, question_id="q-1")
        sql = _compiled_sql(db.stmt)

        assert "FROM question_bank JOIN" in sql, f"sol taraf yanlış:\n{sql}"
        assert "JOIN question_content" in sql, f"content JOIN yok:\n{sql}"
        assert "JOIN question_metadata" in sql, f"metadata JOIN yok:\n{sql}"
        assert "question_content.question_text" in sql, sql
        assert "question_metadata.subject_area" in sql, sql

    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self):
        from services.mnemonic_service import get_mnemonic

        db = _CaptureDB(first=None)
        assert await get_mnemonic(db=db, question_id="yok") is None

    @pytest.mark.asyncio
    async def test_result_shape_uses_joined_columns(self):
        """Dönen sözlük `row.subject_area`'yı okuyor — JOIN etiketi değişmemeli."""
        from services.mnemonic_service import get_mnemonic

        row = MagicMock(id="q-1", question_text="Soru?", subject_area="FIZIK")
        db = _CaptureDB(first=row)

        assert await get_mnemonic(db=db, question_id="q-1") == {
            "question_id": "q-1",
            "mnemonic_hint": None,
            "has_mnemonic": False,
            "subject": "FIZIK",
        }


class TestGenerateMnemonicEagerLoad:
    @pytest.mark.asyncio
    async def test_entity_query_eager_loads_read_relationships(self):
        """ENTITY seçimi — okunan iki ilişki de `selectin` ile yüklenmeli.

        `lazyload` da bir seçenek girdisi üretir, bu yüzden strateji ölçülüyor.
        """
        from services.mnemonic_service import generate_mnemonic

        db = _CaptureDB(scalar=_real_question())
        await generate_mnemonic(db=db, question_id="q-1")

        assert _eager_loaded(db.stmt) == {
            "content": "selectin",
            "metadata_info": "selectin",
        }

    @pytest.mark.asyncio
    async def test_is_active_filter_preserved(self):
        from services.mnemonic_service import generate_mnemonic

        db = _CaptureDB(scalar=_real_question())
        await generate_mnemonic(db=db, question_id="q-1")

        assert "question_bank.is_active" in _compiled_sql(db.stmt)

    @pytest.mark.asyncio
    async def test_returns_error_when_missing(self):
        from services.mnemonic_service import generate_mnemonic

        db = _CaptureDB(scalar=None)
        assert await generate_mnemonic(db=db, question_id="yok") == {
            "error": "Soru bulunamadı"
        }

    @pytest.mark.asyncio
    async def test_force_path_reads_delegated_fields(self, monkeypatch):
        """force=True yolu üç devrediciyi de OKUR — split sonrası asıl risk burası.

        Gerçek ORM nesnesi + gerçek devrediciler kullanılıyor; prompt'ta hem
        content (soru metni, cevap) hem metadata_info (konu) görünmeli.
        """
        import core.llm_service
        from services.mnemonic_service import generate_mnemonic

        llm = MagicMock()
        llm.generate = AsyncMock(return_value="Hafıza ipucu metni")
        monkeypatch.setattr(core.llm_service, "LLMService", MagicMock(return_value=llm))

        db = _CaptureDB(
            scalar=_real_question(
                text="Bir üçgenin iç açıları toplamı kaçtır?",
                answer="C",
                subject="GEOMETRI",
            )
        )
        result = await generate_mnemonic(db=db, question_id="q-1", force=True)

        assert result == {
            "question_id": "q-1",
            "mnemonic_hint": "Hafıza ipucu metni",
            "generated": True,
        }
        prompt = llm.generate.await_args[0][0]
        assert "Bir üçgenin iç açıları toplamı kaçtır?" in prompt
        assert "GEOMETRI" in prompt
        assert "C" in prompt


class TestBatchGenerateMnemonics:
    @pytest.mark.asyncio
    async def test_query_builds_and_joins_metadata(self):
        from services.mnemonic_service import batch_generate_mnemonics

        db = _CaptureDB(all_rows=[])
        await batch_generate_mnemonics(db=db, subject="matematik")
        sql = _compiled_sql(db.stmt)

        _assert_single_from(db.stmt)
        assert "FROM question_bank JOIN question_metadata" in sql, sql
        assert (
            "question_metadata.subject_area = 'MATEMATIK'" in sql
        ), f"subject UPPERCASE'e çevrilmiyor veya metadata'ya taşınmadı:\n{sql}"

    @pytest.mark.asyncio
    async def test_random_order_and_limit_preserved(self):
        from services.mnemonic_service import batch_generate_mnemonics

        db = _CaptureDB(all_rows=[])
        await batch_generate_mnemonics(db=db, subject="fizik", limit=7)
        sql = _compiled_sql(db.stmt)

        assert "ORDER BY random()" in sql, sql
        assert "LIMIT 7" in sql, sql
