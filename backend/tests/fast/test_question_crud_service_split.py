"""question_crud_service'in split şema (#485) sonrası davranışını çivileyen testler.

S211'de bu dosyanın sınıf-düzeyi sorguları JOIN'e çevrildi, ancak iki şey
ölçülmedi: (a) sorguların gerçekten DERLENDİĞİ, (b) delegeli alan okuyan
metotların ilişkileri EAGER-LOAD ettiği. S212'de kardeş dosyada aynı iki
sınıftan da kusur çıkınca bu testler geriye dönük eklendi.

Mock oturumla MissingGreenlet reprodüke EDİLEMEZ (lazy-load hiç tetiklenmez),
bu yüzden eager-load YAPISAL olarak doğrulanır: üretilen Select üzerinde
ilgili loader seçeneği var mı?
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from models.question_bank import QuestionBankItem
from services.question_crud_service import QuestionCRUDService

SPLIT_RELATIONS = {"content", "metadata_info", "statistics"}


def _loaded_attrs(stmt) -> set[str]:
    """Select üzerindeki eager-load seçeneklerinin hedef ilişki adları."""
    names: set[str] = set()
    for opt in stmt._with_options:
        names.update(e.key for e in opt.path if hasattr(e, "key"))
    return names


def _make_service():
    db = AsyncMock()
    db.add = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    result.scalar.return_value = 0
    result.scalar_one_or_none.return_value = None
    result.fetchall.return_value = []
    result.all.return_value = []
    db.execute = AsyncMock(return_value=result)
    db.get = AsyncMock(return_value=MagicMock())
    return QuestionCRUDService(db), db, result


class TestEagerLoading:
    """Split ilişkileri lazy='select'; async oturumda yüklenmemiş erişim
    MissingGreenlet atar. Delegeli alan okuyan her yol eager-load etmeli."""

    @pytest.mark.asyncio
    async def test_update_question_eager_loads_split_relations(self):
        """_create_question_version 10 delegeli alan okuyor (question_text,
        option_a-e, correct_answer, explanation, difficulty_level.value,
        irt_*). Eager-load yoksa MissingGreenlet, üstelik satır 428'deki
        çıplak `except Exception` onu yutup versiyon geçmişini SESSİZCE
        kaybeder."""
        svc, db, result = _make_service()
        result.scalar_one_or_none.return_value = QuestionBankItem(
            id="q-1", soru_hash="h", primary_topic_id="t"
        )
        await svc.update_question("q-1", {}, "user-1", create_version=True)

        fetch_stmt = db.execute.call_args_list[0][0][0]
        assert _loaded_attrs(fetch_stmt) >= SPLIT_RELATIONS

    @pytest.mark.asyncio
    async def test_get_question_by_id_eager_loads_split_relations(self):
        """Çağıran taraf soru metnini/seçenekleri okuyor. Ayrıca bu metot
        istisnaları yutup None döndürüyor — eksik eager-load 'soru
        bulunamadı' gibi görünür."""
        svc, db, _ = _make_service()
        await svc.get_question_by_id("q-1")
        assert _loaded_attrs(db.execute.call_args_list[0][0][0]) >= SPLIT_RELATIONS

    @pytest.mark.asyncio
    async def test_get_question_by_id_split_relations_also_without_include(self):
        """include_relations=False yalnız AĞIR koleksiyonları kapatmalı;
        split ilişkileri kavramsal olarak sorunun kendi kolonları."""
        svc, db, _ = _make_service()
        await svc.get_question_by_id("q-1", include_relations=False)
        assert _loaded_attrs(db.execute.call_args_list[0][0][0]) >= SPLIT_RELATIONS


class TestCompiledQueryShapes:
    """S212'de kardeş dosyada bir JOIN çevirisi DERLEME anında patlıyordu
    (eksik select_from). Bu dosyanın 6 yeniden yazılmış metodu için regresyon
    bekçisi."""

    @staticmethod
    def _assert_single_from(stmt):
        """Kartezyen çarpım kontrolü — METİN DEĞİL yapı üzerinden.

        Metinsel 'FROM'da virgül var mı' kontrolü YANLIŞ-POZİTİF verir:
        `SELECT count(*) FROM (SELECT a, b ...)` şeklinde virgül alt-sorgunun
        SELECT listesindedir. get_final_froms() semantik cevabı verir.
        """
        froms = stmt.get_final_froms()
        assert len(froms) == 1, f"kartezyen çarpım: {len(froms)} ayrı FROM"

    def test_single_from_detector_control_arm(self):
        """Alet doğrulaması: gerçek kartezyeni yakalıyor, alt-sorguyu değil."""
        from sqlalchemy import func, select

        from models.question_bank import QuestionContent

        joined = select(QuestionBankItem).join(
            QuestionContent, QuestionContent.id == QuestionBankItem.id
        )
        self._assert_single_from(joined)
        self._assert_single_from(select(func.count()).select_from(joined.subquery()))
        with pytest.raises(AssertionError):
            self._assert_single_from(select(QuestionBankItem, QuestionContent))

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "call",
        [
            lambda s: s.get_archived_questions(),
            lambda s: s.search_questions(
                "test",
                {
                    "exam_type": "TYT",
                    "subject_area": "MATEMATIK",
                    "difficulty": "medium",
                    "grade_level": 12,
                    "min_quality": 0.5,
                    "irt_difficulty_range": (-1, 1),
                    "osym_compliant": True,
                    "source_book": "X",
                },
            ),
            lambda s: s._calculate_facets(
                ["exam_type", "subject_area", "difficulty", "source_book"]
            ),
            lambda s: s.get_question_statistics(),
            lambda s: s.get_random_questions(5),
            lambda s: s.list_source_books(),
        ],
    )
    async def test_statements_compile_against_postgres(self, call):
        svc, db, _ = _make_service()
        await call(svc)

        assert db.execute.called, "sorgu hiç çalıştırılmadı (sessiz except?)"
        for c in db.execute.call_args_list:
            stmt = c[0][0]
            stmt.compile(
                dialect=postgresql.dialect(),
                compile_kwargs={"literal_binds": True},
            )
            self._assert_single_from(stmt)


# ---------------------------------------------------------------------------
# create_question — NOT NULL / kanon alanlari (S226)
# ---------------------------------------------------------------------------


def _soru_verisi(metin: str = "Iki kere iki kactir?") -> dict:
    return {
        "soru_metni": metin,
        "secenekler": ["A) 3", "B) 4", "C) 5", "D) 6", "E) 7"],
        "dogru_cevap": "b",
        "konu": "Matematik",
        "sinav_tipi": "tyt",
        "zorluk_seviyesi": "orta",
    }


class TestCreateQuestionZorunluAlanlar:
    """`create_question` DB'ye giden nesneyi eksiksiz kurmali.

    NEDEN MOCK OTURUMLA OLCULUYOR: bu servis uretimden ULASILAMAZ (olculdu
    17 Agu — `QuestionCRUDService` yalnizca 3 TEST dosyasinda geciyor, ne
    `routers/loader.py`de ne `main.py`de ne de baska bir serviste). Yani
    canli DB'ye yazan bir uctan uca test yazmak orantisiz olurdu; bunun
    yerine `db.add(...)`e VERILEN nesne dogrudan denetleniyor. Bu, NOT NULL
    kusurunu flush'a hic gitmeden deterministik yakalar.

    Kusur GERCEK ama LATENT: biri bu servisi kablolarsa ilk cagride
    `NotNullViolationError: null value in column "soru_hash"` alir
    (`question_bank.soru_hash` NOT NULL, DB-default YOK — olculdu).
    """

    async def _eklenen(self, svc, db, veri):
        await svc.create_question(veri, created_by="test-user")
        assert db.add.called, "db.add hic cagrilmadi (sessiz except?)"
        return db.add.call_args[0][0]

    async def test_soru_hash_dolduruluyor(self):
        """`soru_hash` NOT NULL — bugun HIC set edilmiyor."""
        svc, db, _ = _make_service()

        eklenen = await self._eklenen(svc, db, _soru_verisi())

        assert eklenen.soru_hash, "soru_hash bos/None -> NOT NULL ihlali"
        assert (
            len(eklenen.soru_hash) == 32
        ), f"soru_hash uzunlugu {len(eklenen.soru_hash)}; kolon String(32)"

    async def test_soru_hash_icerige_bagli(self):
        """Farkli sorular FARKLI hash almali.

        AYIRT EDICI: sabit bir dize dondurmek yukaridaki testi yesil yapar ama
        `uq_qb_soru_hash_active` kismi benzersizlik indeksini ise yaramaz kilar
        (ikinci soru catisir). Bu test o naif fix'i reddeder.
        """
        svc1, db1, _ = _make_service()
        svc2, db2, _ = _make_service()

        bir = await self._eklenen(svc1, db1, _soru_verisi("Birinci soru?"))
        iki = await self._eklenen(svc2, db2, _soru_verisi("Ikinci soru?"))

        assert (
            bir.soru_hash != iki.soru_hash
        ), f"iki farkli soru ayni hash aldi: {bir.soru_hash}"

    async def test_subject_area_kanonik_buyuk_harf(self):
        """`subject_area` canli kanona uymali (BUYUK harf).

        Olculdu: `question_metadata.subject_area` canli degerleri MATEMATIK /
        GEOMETRI / FIZIK ... Bugun bu servis girdiyi (veya 'Matematik'
        varsayilanini) DUZ geciriyor -> satir `subject_area='Matematik'` olur
        ve `subject_area='MATEMATIK'` filtreleyen sorgulardan DUSER.
        """
        svc, db, _ = _make_service()

        eklenen = await self._eklenen(svc, db, _soru_verisi())

        assert (
            eklenen.metadata_info.subject_area == "MATEMATIK"
        ), f"kanonik degil: {eklenen.metadata_info.subject_area!r}"
        assert (
            eklenen.metadata_info.exam_type == "TYT"
        ), f"kanonik degil: {eklenen.metadata_info.exam_type!r}"
