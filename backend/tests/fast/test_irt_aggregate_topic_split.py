"""`_get_irt_aggregate` icin #485 split + sozlesme bekcisi.

TEK BEKCI (#515, 22 Agu 2026): onceki ikiz `_get_subject_irt_aggregate` ve
onu civileyen `tests/fast/test_advanced_reports_split.py` SILINDI -- fonksiyon
uretimde oluydu (`3c44910ff` iki cagri yerini de buraya tasidi). Silmeden ONCE
eski bekcinin HER invaryanti mutasyonla olculdu; ucu bu dosyada KAPSANMIYORDU
ve buraya tasindi:
    M-C  ders dalinda QuestionMetadata JOIN'i dus -> KARTEZYEN (2 FROM),
         sessizce yanlis ortalama; eski hali 5/5 YESIL kaliyordu
    M-D  NULL-toplam varsayilani boz -> donen sozluk hic okunmuyordu
    M-E  cache-hit erken donusu kaldir -> hic olculmuyordu
Karsilik gelen testler: `test_ders_dalinda_kartezyen_yok`,
`test_null_toplamlar_varsayilana_duser`, `test_cache_dolu_ise_db_ye_gidilmez`.

NEDEN CIVILI: ayni sinifta bir split kacagi tekrar edebilir (bkz.
`L-s230-ast-sayaci-ham-sql-goremez` ve ES sema kacagi vakasi: sorgu S210
split'inden once yazilmisti, senkron AYLARDIR UndefinedColumnError ile
sessizce dusuyordu).

DIKKAT: WHERE iddiasi derlenmis SQL dizesinde JOIN dusse bile DURUR
(audit-methodology.md). Kartezyen yalniz `get_final_froms()` ile olculur --
her iki dal icin de.

Testler GERCEK `models.question_bank` modeline karsi kosar; sahte
`sys.modules` stub'i kirik kodda da yesil kalirdi.
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


class _CaptureSession:
    def __init__(self, row):
        self.row = row
        self.stmt = None

    async def execute(self, stmt):
        self.stmt = stmt
        result = MagicMock()
        result.one.return_value = self.row
        return result


@pytest.fixture
def wired(monkeypatch):
    """Cache bosa alinir, DB oturumu yakalayiciya yonlendirilir."""
    import core.cache
    import core.database

    session = _CaptureSession(
        MagicMock(
            avg_difficulty=0.4, avg_discrimination=1.2, avg_guessing=0.2, sample_size=7
        )
    )

    @asynccontextmanager
    async def fake_ctx():
        yield session

    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()

    monkeypatch.setattr(core.database, "get_db_session_context", fake_ctx)
    monkeypatch.setattr(core.cache, "cache_manager", cache)
    return session, cache


class TestKonuBazliSorgu:
    @pytest.mark.asyncio
    async def test_konu_kodu_varsa_topic_hierarchy_join_edilir(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")

        assert session.stmt is not None, "session.execute hic cagrilmadi"
        sql = _compiled_sql(session.stmt)
        assert "JOIN topic_hierarchy" in sql, f"topic_hierarchy JOIN yok:\n{sql}"
        assert "topic_hierarchy.code = 'MAT.FON'" in sql, sql
        # Split (#485): irt_* QuestionStatistics'te
        assert "avg(question_statistics.irt_difficulty)" in sql, sql
        assert "avg(question_statistics.irt_discrimination)" in sql, sql
        assert "avg(question_statistics.irt_guessing)" in sql, sql

    @pytest.mark.asyncio
    async def test_tek_from_kartezyen_yok(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")
        froms = session.stmt.get_final_froms()
        assert len(froms) == 1, f"kartezyen carpim: {len(froms)} ayri FROM"

    @pytest.mark.asyncio
    async def test_konu_kodu_yoksa_derse_duser(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code=None, ders="matematik")
        sql = _compiled_sql(session.stmt)
        assert "question_metadata.subject_area = 'MATEMATIK'" in sql, sql
        assert "topic_hierarchy" not in sql, f"gereksiz JOIN:\n{sql}"

    @pytest.mark.asyncio
    async def test_ders_dalinda_kartezyen_yok(self, wired):
        """#515 M-C: ders dalinda da tek FROM + gercek JOIN olmali.

        WHERE dizesi JOIN dusse bile derlenmis SQL'de DURUR -- ustteki
        `subject_area = 'MATEMATIK'` assert'i JOIN'siz halde de gecer ve
        `FROM question_bank JOIN question_statistics ..., question_metadata`
        (KARTEZYEN) uretir: her aktif soru x her ayni-ders metadata satiri,
        yani sessizce sisirilmis sample_size ve yanlis ortalama. Kartezyen
        yalniz YAPI uzerinden olculur.
        """
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code=None, ders="matematik")

        froms = session.stmt.get_final_froms()
        assert len(froms) == 1, f"ders dalinda kartezyen: {len(froms)} ayri FROM"
        assert "JOIN question_metadata" in _compiled_sql(session.stmt), _compiled_sql(
            session.stmt
        )

    @pytest.mark.asyncio
    async def test_is_active_filtresi_zorunlu(self, wired):
        """Soru sorgusunda `is_active` atlanamaz (.claude/rules/database.md)."""
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")
        sql = _compiled_sql(session.stmt)
        assert "is_active" in sql, sql


class TestCakismaVeCache:
    @pytest.mark.asyncio
    async def test_cache_anahtarlari_cakismaz(self, wired):
        """Ayni anahtar altinda iki farkli semantik veri tutulamaz.

        Olculdu: 'Kimya' hem level-1 KONU adi hem DERS adi. Tek anahtar
        semasi ikisini birbirine karistirirdi.
        """
        from api.advanced_reports import _get_irt_aggregate

        _, cache = wired
        await _get_irt_aggregate(topic_code="KIM", ders="kimya")
        await _get_irt_aggregate(topic_code=None, ders="kimya")

        anahtarlar = [c.args[0] for c in cache.set.call_args_list]
        assert len(set(anahtarlar)) == 2, f"cache anahtarlari cakisti: {anahtarlar}"
        assert any(a.startswith("irt_aggregate:topic:") for a in anahtarlar), anahtarlar
        assert any(
            a.startswith("irt_aggregate:subject:") for a in anahtarlar
        ), anahtarlar

    @pytest.mark.asyncio
    async def test_cache_dolu_ise_db_ye_gidilmez(self, wired):
        """#515 M-E: cache-hit erken donusu -- sorgu HIC kurulmamali."""
        from api.advanced_reports import _get_irt_aggregate

        session, cache = wired
        onbellekli = {
            "avg_difficulty": 1.0,
            "avg_discrimination": 2.0,
            "avg_guessing": 0.3,
            "sample_size": 99,
        }
        cache.get = AsyncMock(return_value=onbellekli)

        sonuc = await _get_irt_aggregate(topic_code="KIM", ders="kimya")

        assert sonuc == onbellekli
        assert session.stmt is None, "cache hit'te DB sorgusu kuruldu"


class TestDonenSozlesme:
    """Cagiranlarla (irt / osym-ets) alan sozlesmesi + NULL varsayilanlari."""

    @pytest.mark.asyncio
    async def test_donen_sozluk_sekli(self, wired):
        from api.advanced_reports import _get_irt_aggregate

        session, cache = wired
        session.row = MagicMock(
            avg_difficulty=0.25,
            avg_discrimination=1.4,
            avg_guessing=0.18,
            sample_size=7,
        )

        sonuc = await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")

        assert sonuc == {
            "avg_difficulty": 0.25,
            "avg_discrimination": 1.4,
            "avg_guessing": 0.18,
            "sample_size": 7,
        }
        cache.set.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_null_toplamlar_varsayilana_duser(self, wired):
        """#515 M-D: bos konu (JOIN sonrasi 0 satir) -> AVG NULL.

        Varsayilanlar IRT semantigi tasir: guclugu 0.0, ayirt ediciligi 1.0,
        sansi 0.2. Biri kayarsa cagiran sessizce yanlis yetenek kestirir.
        """
        from api.advanced_reports import _get_irt_aggregate

        session, _ = wired
        session.row = MagicMock(
            avg_difficulty=None,
            avg_discrimination=None,
            avg_guessing=None,
            sample_size=None,
        )

        sonuc = await _get_irt_aggregate(topic_code="MAT.FON", ders="matematik")

        assert sonuc == {
            "avg_difficulty": 0.0,
            "avg_discrimination": 1.0,
            "avg_guessing": 0.2,
            "sample_size": 0,
        }
