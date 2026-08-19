"""Yedek ÖNKOŞUL kapsamı bekçisi — 19 Ağu 2026 (A2b).

NEDEN VAR
---------
`pg_dump -t <tablo>` ile alınan bir yedek **kendi kendine yeterli DEĞİLDİR**:
enum ve uzantı tiplerini TAŞIMAZ. 19 Ağu'da ölçüldü — S232-G'nin "147.880 satır
doğrulandı" dediği yedek boş bir hedefe geri yüklenmeye çalışıldığında:

    pg_restore: hata: ERROR: type "public.questiondifficultylevel" does not exist
    -> question_statistics TABLOSU HIC OLUSMADI
    -> 36.967 satir HIC YUKLENMEDI   (5 tablodan 4'u yuklendi)

Yani dump'ın **içeriği** doğrulanmıştı, **geri yüklenebilirliği** değil. İkinci
katman tip eklenince çıktı: `public.vector` (pgvector uzantısı).

Bu, bu deponun kayıtlı dersinin yedek ayağı:
`L-s202-drop-table-enum-birakir` — "DROP TABLE PG enum TİPİNİ düşürmez;
restore'da düz `sa.Enum` 'type already exists' ile patlar."

NEDEN DOSYAYA DEĞİL ÜRETECE BAĞLI
---------------------------------
`backups/*.prereq.sql` `.gitignore:106` ile takip DIŞI. Ona bağlanan bir test
taze bir klonda anlamsız olurdu. Yük taşıyan şey dosya değil **onu üreten
yordam**: şema değişince (yeni enum kolonu, yeni uzantı) üretecin çıktısı da
değişmeli. Bu yüzden bekçi `yedek_onkosul_uret.py`'yi sınar.

KAPSAM SINIRI (dürüst)
----------------------
Bu bekçi "önkoşul TAM MI" sorusunu yanıtlar. "Yedek gerçekten geri yüklenebilir
mi" sorusunu YANITLAMAZ — o, gerçek bir `pg_restore` provası ister (19 Ağu'da
elle yapıldı, 147.894/147.894). Boşluk bilinçli ve görünür bırakıldı.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

DEPO_KOKU = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPO_KOKU / "backend" / "scripts" / "quality"))

from yedek_onkosul_uret import (  # noqa: E402
    YEDEK_TABLOLARI,
    eksik_tipler,
    gerekli_tipler,
    onkosul_sql,
)

pytestmark = pytest.mark.db_invariant


# ---------------------------------------------------------------------------
# SAF KATMAN — DB'siz. Bekcinin cekirdegi burada; mutasyonla civilenebilir.
# ---------------------------------------------------------------------------


def test_eksik_uzanti_yakalanir():
    """Uzanti satiri dusen bir onkosul, `type "public.vector" does not exist` verir."""
    gerekli = {"uzantilar": {"vector"}, "enumlar": {"questiondifficultylevel": ["A"]}}
    sql = "CREATE TYPE public.questiondifficultylevel AS ENUM ('A');"
    assert eksik_tipler(sql, gerekli) == {"uzanti:vector"}


def test_eksik_enum_yakalanir():
    """19 Agu'da question_statistics'i tamamen dusuren tam olarak buydu."""
    gerekli = {"uzantilar": {"vector"}, "enumlar": {"questiondifficultylevel": ["A"]}}
    sql = "CREATE EXTENSION IF NOT EXISTS vector;"
    assert eksik_tipler(sql, gerekli) == {"enum:questiondifficultylevel"}


def test_tam_onkosul_bos_doner():
    """Kontrol kolu: bekci cok siki olursa gecerli bir onkosulu de reddeder."""
    gerekli = {"uzantilar": {"vector"}, "enumlar": {"questiondifficultylevel": ["A"]}}
    sql = (
        "CREATE EXTENSION IF NOT EXISTS vector;\n"
        "CREATE TYPE public.questiondifficultylevel AS ENUM ('A');"
    )
    assert eksik_tipler(sql, gerekli) == set()


def test_uretilen_sql_kendi_kapsamini_saglar():
    """Uretec kendi kontrolunden gecmeli — aksi halde bekci vakumdur."""
    gerekli = {
        "uzantilar": {"vector", "pg_trgm"},
        "enumlar": {"bir_enum": ["X", "Y"], "iki_enum": ["Z"]},
    }
    assert eksik_tipler(onkosul_sql(gerekli), gerekli) == set()


def test_enum_etiketleri_sirayi_korur():
    """PG'de enum SIRASI anlamlidir (ORDER BY, karsilastirma).

    Alfabetik siralamak sessizce yanlis bir tip uretirdi.
    """
    sql = onkosul_sql({"uzantilar": set(), "enumlar": {"e": ["VERY_EASY", "EASY"]}})
    assert sql.index("'VERY_EASY'") < sql.index("'EASY'")


def test_yedek_tablolari_dumpla_ayni_kume():
    """Uretec, yedegin aldigi tablolarla ayni kumeye bakmali.

    Ayrisirsa uretec eksik tip uretir ve bekci bunu goremez (yanlis-sifir).
    """
    assert YEDEK_TABLOLARI == (
        "question_bank",
        "question_content",
        "question_metadata",
        "question_statistics",
        "topic_hierarchy",
    )


# ---------------------------------------------------------------------------
# CANLI KATMAN — gercek semaya karsi. A3'ten beri kapi bu DSN'i enjekte ediyor.
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session():
    dsn = resolve_pg_dsn()
    if not dsn:
        pytest.skip(SKIP_REASON)

    engine = create_async_engine(dsn, poolclass=NullPool)
    try:
        conn = await engine.connect()
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"DB erisilemiyor: {type(exc).__name__}")

    maker = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    session = maker()
    try:
        yield session
    finally:
        await session.close()
        await conn.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_canli_semada_uretilen_onkosul_tam(db_session):
    """Sema degisirse (yeni enum kolonu / yeni uzanti) bu test KIRMIZI olur.

    O an `backups/*.prereq.sql` yeniden uretilmeli; aksi halde bir sonraki
    felakette yedek geri YUKLENEMEZ ve bunu ancak o an ogreniriz.
    """
    gerekli = await gerekli_tipler(db_session)
    eksik = eksik_tipler(onkosul_sql(gerekli), gerekli)
    assert eksik == set(), (
        f"Uretec canli semayi karsilamiyor, eksik: {sorted(eksik)}. "
        "Yedek boyle alinirsa pg_restore ilgili TABLOYU HIC OLUSTURMAZ."
    )


@pytest.mark.asyncio
async def test_canli_bagimlilik_kumesi_bos_degil(db_session):
    """Yanlis-SIFIR kontrolu (`L-s219-yanlis-sifir-tek-kabul-edilemez-hata`).

    Sorgu bozulursa `gerekli` bos doner, `eksik` de bos olur ve ustteki test
    HER ZAMAN yesil kalir — bekci sessizce olur. 19 Ağu ölçümü: uzanti 1
    (vector), enum 1 (questiondifficultylevel).
    """
    gerekli = await gerekli_tipler(db_session)
    assert gerekli["uzantilar"], "hic uzanti bulunamadi — sorgu bozuk olabilir"
    assert gerekli["enumlar"], "hic enum bulunamadi — sorgu bozuk olabilir"
    assert "vector" in gerekli["uzantilar"]
    assert "questiondifficultylevel" in gerekli["enumlar"]
