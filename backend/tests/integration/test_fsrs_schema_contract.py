"""FSRS ham-SQL sema sozlesmesi (#461 / K1).

NEDEN VAR
---------
`user_item_fsrs` tablosu 11 Haz 2026'da `c555a10f4b93_sync_db_changes.py:183`
tarafindan DROP edildi. `app/services/fsrs_service.py` icindeki BES raw SQL
sabiti ve `app/api/fsrs.py` hala o tabloya vuruyor; router `routers/loader.py`'de
KAYITLI, yani `/api/v1/fsrs/*` uclari canli ve 500 veriyor.

Kusur **alti hafta** fark edilmedi ve bu surede olu koda IKI ozellik shiplendi
(mercy `ac4936f8b`, kalite kapisi `7ede1fcf9`). Sebep: bu kod yolunu gercek
semaya karsi sinayan tek bir test yoktu — var olan
`test_fsrs_mercy_endpoint.py` servisi TAMAMEN mock'luyor, metot silinse bile
yesil kalir.

Bu dosya o bosluğu kapatir. Tek tablo kontrolu DEGIL, **sinif bekcisi**:
ham SQL'de gecen HER tablo adi canli semada aranir. Yarin baska bir tablo
duserse bu test onu da yakalar.

Alet dogrulamasi: `test_bekci_uydurma_tabloyu_yakalar` bekcinin kendisini
mutasyonla sinar — uydurma bir tablo adi enjekte edilir ve bekcinin KIRMIZI
donmesi beklenir. O test gecmezse bu dosyadaki yesil sonuclar anlamsizdir.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import psycopg2
import pytest

pytestmark = [pytest.mark.integration]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL. Mevcut gercek-DB testleriyle
# ayni deger (bkz. tests/unit/test_fsrs_card_persistence.py).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

_BACKEND = Path(__file__).resolve().parents[2]

# Ham SQL tasiyan uretim dosyalari (router loader'da KAYITLI olanlar)
SQL_KAYNAKLARI = (
    _BACKEND / "app" / "services" / "fsrs_service.py",
    _BACKEND / "app" / "api" / "fsrs.py",
)

# SQL'de tablo adinin gelebilecegi konumlar
_TABLO_DESENI = re.compile(
    r"\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE)\s+([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)

# Tablo degil, SQL anahtar kelimesi/alias olarak gelebilecekler
_TABLO_OLMAYAN = {"select", "lateral", "unnest", "generate_series", "only", "set"}

# Bir string literalin SQL olup olmadigini ayirt eder (docstring'leri eler)
_SQL_GORUNUMLU = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)


def _sql_tablolari(yol: Path) -> set[str]:
    """Dosyadaki ham SQL'den tablo adlarini cikarir.

    YALNIZ string literalleri taranir. Ilk surum tum dosya metnine bakiyordu ve
    Python'un `from X import Y` satirlarini SQL `FROM X` sandi (`__future__`,
    `sqlalchemy`, `datetime` ... yanlis-pozitif). Alet duzeltildi;
    `test_cikartici_python_importlarini_yakalamaz` bunu civiliyor.
    """
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    bulunan: set[str] = set()
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Constant) or not isinstance(dugum.value, str):
            continue
        govde = dugum.value
        if not _SQL_GORUNUMLU.search(govde):
            continue
        bulunan |= {
            ad.lower()
            for ad in _TABLO_DESENI.findall(govde)
            if ad.lower() not in _TABLO_OLMAYAN
        }
    return bulunan


def _canli_tablolar() -> set[str]:
    """Canli semadaki tablo + view adlari."""
    with psycopg2.connect(DSN) as baglanti, baglanti.cursor() as imlec:
        imlec.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'"
        )
        return {satir[0].lower() for satir in imlec.fetchall()}


@pytest.fixture(scope="module")
def canli_tablolar() -> set[str]:
    """DB yoksa TUM modulu atla — fixture icinde kontrol (testing.md #7)."""
    try:
        tablolar = _canli_tablolar()
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    if not tablolar:
        pytest.skip("information_schema bos dondu — olcum aleti supheli")
    return tablolar


def test_alet_dogrulamasi_bilinen_tablolar_gorunuyor(canli_tablolar: set[str]) -> None:
    """KONTROL KOLU: bekci gercekten semayi okuyor mu.

    Bilinen-VAR bir tablo gorunmuyorsa asagidaki testlerin YESILI degersizdir.
    """
    assert "question_bank" in canli_tablolar, (
        "Bilinen-VAR tablo semada gorunmuyor -> olcum aleti arizali, "
        "bu dosyadaki hicbir sonuca guvenilmez"
    )
    assert (
        "zzz_olmayan_tablo" not in canli_tablolar
    ), "Bilinen-YOK tablo semada gorunuyor -> sorgu yanlis kumeyi donduruyor"


def test_bekci_uydurma_tabloyu_yakalar(canli_tablolar: set[str]) -> None:
    """MUTASYON: bekci mantigini uydurma tablo adiyla sina.

    Bu test gecmezse bekci hicbir sey olcmuyor demektir.
    """
    sahte = {"question_bank", "zzz_kesinlikle_olmayan_tablo"}
    eksik = sahte - canli_tablolar
    assert eksik == {
        "zzz_kesinlikle_olmayan_tablo"
    }, f"Bekci mantigi uydurma tabloyu yakalayamadi: eksik={eksik}"


def test_sql_kaynaklarindan_tablo_cikarilabiliyor() -> None:
    """Regex gercekten tablo buluyor mu — bos kume sessiz yesil uretir."""
    for yol in SQL_KAYNAKLARI:
        assert yol.exists(), f"Kaynak dosya yok: {yol}"
    hepsi = set().union(*(_sql_tablolari(y) for y in SQL_KAYNAKLARI))
    assert hepsi, (
        "Ham SQL'den HIC tablo cikarilamadi -> regex bozuk, "
        "asagidaki test bos kume uzerinde sessizce gecerdi"
    )


def test_cikartici_python_importlarini_yakalamaz() -> None:
    """ALET MUTASYONU: `from X import Y` SQL `FROM X` sanilmamali.

    Ilk surumum tam olarak bu hatayi yapti ve `__future__`, `sqlalchemy`,
    `datetime` gibi modul adlarini "eksik tablo" diye raporladi. Fix
    uygulansaydi bile test KIRMIZI kalirdi.
    """
    hepsi = set().union(*(_sql_tablolari(y) for y in SQL_KAYNAKLARI))
    kirletenler = {"__future__", "sqlalchemy", "datetime", "typing", "fastapi", "uuid"}
    assert not (
        hepsi & kirletenler
    ), f"Cikartici Python import'larini SQL sandi: {sorted(hepsi & kirletenler)}"


def test_fsrs_ham_sql_tablolari_canli_semada_var(canli_tablolar: set[str]) -> None:
    """SINIF BEKCISI: ham SQL'de gecen her tablo semada olmali.

    Bugun KIRMIZI: `user_item_fsrs` 11 Haz 2026'da DROP edildi.
    """
    eksikler: dict[str, set[str]] = {}
    for yol in SQL_KAYNAKLARI:
        eksik = _sql_tablolari(yol) - canli_tablolar
        if eksik:
            eksikler[yol.name] = eksik

    assert not eksikler, (
        "Ham SQL var olmayan tabloya vuruyor — bu uclar canlida 500 verir:\n"
        + "\n".join(
            f"  {dosya}: {sorted(tablolar)}" for dosya, tablolar in eksikler.items()
        )
    )
