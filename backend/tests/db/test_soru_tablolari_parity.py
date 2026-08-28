"""4-tablo parity bekçisi — kısmi INSERT sessizdir (A4, 19-20 Ağu 2026).

NEDEN VAR
---------
S210'un 69-alan split'i `question_bank`'ı dört tabloya ayırdı. Bir satırın
"tam" olması için dördünde de karşılığı olmalı. Bunu zorlayan **hiçbir yapı yok**:

  - `question_statistics`'e INSERT eden kod depoda **hiçbir yerde yok** (S222 ölçtü),
    backfill yok, split migration'ı da yok;
  - FK yönü **çocuk → ebeveyn** (`ON DELETE CASCADE`): yetim ÇOCUĞU yasaklar,
    her ebeveynin çocuğu olmasını **şart koşmaz**;
  - hedef tablolarda **0 trigger**, 1:1'i kısıt olarak zorlayan bir şey yok;
  - `rowcount` hiçbir yazım noktasında kontrol edilmiyor.

Yani `question_bank`'a yazıp yavruya yazmayan bir göç/script **sessizce** yarım
satır bırakır. O satır:

  - öğrenci kapısında **görünmez** (`v_safe_for_beta` LEFT JOIN'liyor →
    `quality_review_status` NULL → elenir),
  - `question_bank`'ta **durur** ve hacim sayımını şişirir,
  - ve **hiçbir test görmez** — 19 Ağu ölçümü: parity/yetim assert eden test
    sayısı depoda **0** (grep).

Bu bekçi tam da FAZ C/D'de 3.554 satır yazılırken devreye girecek.

⚠️ JOIN ANAHTARI `qc.id = qb.id` — yavru tabloların PK'si `id` ve AYNI ZAMANDA
parent'a FK; `question_id` adında kolon **hiçbirinde yok**
(`L-s230-yavru-tablonun-pk-si-id`). Ad tahmini bu şemada bir kez yanlış fix üretti.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from tests.e2e.pg_dsn import SKIP_REASON, resolve_pg_dsn

pytestmark = pytest.mark.db_invariant

YAVRULAR = ("question_content", "question_metadata", "question_statistics")
_IZINLI_TABLOLAR = frozenset({"question_bank", *YAVRULAR})


def _tablo(ad: str) -> str:
    """Tablo adini beyaz listeye karsi dogrula, sonra SQL'e interpolasyona izin ver.

    ruff S608 (SQL injection) bu dosyada 4 yerde ateslenir. Bastirmayi bir
    SOZE degil GERCEK bir kapiya dayandiriyoruz: adlar bugun sabit bir
    demetten geliyor, ama bir sonraki duzenleme onu degisken yapabilir.
    O gun bu fonksiyon `ValueError` atar; `# noqa` sessizce yalan soylemez.
    (Depo kurali: bastirma gercek bir kapiya dayanmali -- S232-H.)
    """
    if ad not in _IZINLI_TABLOLAR:
        raise ValueError(f"izinsiz tablo adi: {ad!r}")
    return ad


def _yetim_yavru_sql(yavru: str) -> str:
    """Ebeveyni olmayan yavru satırı (FK bunu zaten yasaklar; kontrol kolu)."""
    return (
        f"SELECT count(*) FROM {_tablo(yavru)} c "  # noqa: S608 - _tablo() beyaz listesi
        f"LEFT JOIN question_bank qb ON qb.id = c.id WHERE qb.id IS NULL"
    )


def _yavrusuz_ebeveyn_sql(yavru: str) -> str:
    """Yavrusu olmayan ebeveyn — ASIL RISK. Hicbir kisit bunu engellemiyor."""
    return (
        f"SELECT count(*) FROM question_bank qb "  # noqa: S608 - _tablo() beyaz listesi
        f"LEFT JOIN {_tablo(yavru)} c ON c.id = qb.id WHERE c.id IS NULL"
    )


def parity_ihlalleri(sonuclar: dict[str, int]) -> list[str]:
    """Sıfır olmayan her sayımı ihlal olarak döndür (saf; DB'siz çivilenebilir).

    Ayrı bir fonksiyon çünkü karar mantığı sorgudan bağımsız sınanabilmeli.
    """
    return sorted(f"{ad}={n}" for ad, n in sonuclar.items() if n != 0)


# ---------------------------------------------------------------------------
# SAF KATMAN
# ---------------------------------------------------------------------------


def test_ihlal_yoksa_bos_liste():
    assert parity_ihlalleri({"a": 0, "b": 0}) == []


def test_tek_ihlal_yakalanir():
    assert parity_ihlalleri({"a": 0, "b": 3}) == ["b=3"]


def test_tum_ihlaller_raporlanir_ilki_degil():
    """Ilk ihlalde durmak, kalan tablolari gizlerdi."""
    assert parity_ihlalleri({"a": 1, "b": 2, "c": 0}) == ["a=1", "b=2"]


def test_izinsiz_tablo_adi_reddedilir():
    """`# noqa: S608` bastirmasinin dayandigi kapi -- soz degil KOD.

    Bu test dusesse bastirma yalan soyluyor demektir.
    """
    with pytest.raises(ValueError):
        _tablo("users; DROP TABLE question_bank")
    assert _tablo("question_bank") == "question_bank"


def test_join_anahtari_id_uzerinden(yavru=YAVRULAR[0]):
    """`question_id` DEGIL `id` (L-s230). Ad tahmini bu semada yanlis fix uretti."""
    for sql in (_yetim_yavru_sql(yavru), _yavrusuz_ebeveyn_sql(yavru)):
        assert "c.id = qb.id" in sql or "qb.id = c.id" in sql
        assert "question_id" not in sql


# ---------------------------------------------------------------------------
# CANLI KATMAN
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
async def test_dort_tablo_parity_yetim_yok(db_session):
    """6 yön: her yavru için hem yetim-yavru hem yavrusuz-ebeveyn.

    Kırmızı olursa: bir yazım yolu `question_bank`'a yazıp yavruya yazmamış.
    Göç sırasında bu, satırların öğrenciye HİÇ ulaşmaması demektir.
    """
    sonuclar: dict[str, int] = {}
    for yavru in YAVRULAR:
        sonuclar[f"yetim_yavru:{yavru}"] = (
            await db_session.execute(text(_yetim_yavru_sql(yavru)))
        ).scalar_one()
        sonuclar[f"yavrusuz_ebeveyn:{yavru}"] = (
            await db_session.execute(text(_yavrusuz_ebeveyn_sql(yavru)))
        ).scalar_one()

    assert parity_ihlalleri(sonuclar) == [], (
        f"4-tablo parity BOZUK: {parity_ihlalleri(sonuclar)}. "
        "Yavrusuz ebeveyn satiri kapida GORUNMEZ ama question_bank'ta durur."
    )


@pytest.mark.asyncio
async def test_yetim_sorgusu_sentetik_yetimi_goruyor(db_session):
    """KONTROL KOLU — bekçinin bilinen-KÖTÜ'de kırmızı verdiğini kanıtlar.

    Üstteki test her zaman 0 döndürüyor. Bu tek başına iki şeyden biri olabilir:
    (a) parity gerçekten sağlam, (b) sorgu hiçbir şey görmüyor. Ayırt etmenin
    tek yolu, deseni GÖRMESİ GEREKEN bir girdiyle sınamak.

    Yazma YOK: sentetik id `VALUES` ile üretiliyor.
    `L-s232-kontrol-kolu-bekciyi-DUZELTIR` — bir bekçinin ayırt edici olduğu,
    bilinen-kötüde kırmızı vermesiyle değil bilinen-iyide yeşil vermesiyle
    kanıtlanır; burada ikisi birden ölçülüyor.
    """
    for yavru in YAVRULAR:
        n = (
            await db_session.execute(
                text(
                    f"SELECT count(*) FROM (VALUES ('yok-boyle-bir-id')) v(id) "  # noqa: S608
                    f"LEFT JOIN {_tablo(yavru)} c ON c.id = v.id WHERE c.id IS NULL"
                )
            )
        ).scalar_one()
        assert n == 1, (
            f"{yavru}: LEFT JOIN ... IS NULL deseni sentetik yetimi GORMEDI "
            "-> ustteki parity testinin 0'i ANLAMSIZ (yanlis-sifir)."
        )


@pytest.mark.asyncio
async def test_tablolar_bos_degil(db_session):
    """Yanlış-SIFIR kapısı (`L-s219-yanlis-sifir-tek-kabul-edilemez-hata`).

    `question_bank` boşsa 6 sayımın 6'sı da 0 olur ve parity testi VAKUM olarak
    yeşil kalır. 5 Ağu 2026'da tablo 187.835 → 2.304'e düştü; o gün bu bekçi
    olsaydı, hacim testi kırmızı verirken parity testi YEŞİL kalacaktı.
    """
    n = (
        await db_session.execute(text("SELECT count(*) FROM question_bank"))
    ).scalar_one()
    assert n > 0, "question_bank BOS — parity testi vakum olarak yesil kalir"


@pytest.mark.asyncio
async def test_dort_tablo_satir_sayisi_esit(db_session):
    """Parity'nin ikinci, bağımsız ifadesi: sayımlar eşit olmalı.

    6-yönlü yetim kontrolüyle mantıken eşdeğer ama ucuz ve başarısızlık
    çıktısı çok daha okunur (`36967 != 36960` gibi).
    """
    sayimlar = {}
    for tablo in ("question_bank", *YAVRULAR):
        sayimlar[tablo] = (
            await db_session.execute(text(f"SELECT count(*) FROM {_tablo(tablo)}"))  # noqa: S608
        ).scalar_one()
    assert len(set(sayimlar.values())) == 1, f"satir sayilari AYRISMIS: {sayimlar}"
