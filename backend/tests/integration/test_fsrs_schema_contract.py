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
import importlib
import re
from pathlib import Path

import pytest
from sqlalchemy.sql.elements import TextClause

from core.quality_gate import SAFE_POOL_RELATION

# `psycopg2-binary` CI'da KURULU DEGIL (requirements.txt psycopg v3 kuruyor;
# sqlalchemy'de psycopg2 yalniz [postgresql*] extra'sinda). ci.yml:281 testleri
# marker filtresiz + `-x` ile kostugu icin korumasiz import TUM job'u dusururdu.
# Bekci: tests/test_ci_collection_guard.py
psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL. Mevcut gercek-DB testleriyle
# ayni deger (bkz. tests/unit/test_fsrs_card_persistence.py).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

_BACKEND = Path(__file__).resolve().parents[2]

# Ham SQL tasiyan uretim dosyalari (router loader'da KAYITLI olanlar)
FSRS_SERVICE = _BACKEND / "app" / "services" / "fsrs_service.py"
FSRS_API = _BACKEND / "app" / "api" / "fsrs.py"

SQL_KAYNAKLARI = (FSRS_SERVICE, FSRS_API)

# SQL'de tablo adinin gelebilecegi konumlar
_TABLO_DESENI = re.compile(
    r"\b(?:FROM|JOIN|INSERT\s+INTO|UPDATE)\s+([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)

# Tablo degil, SQL anahtar kelimesi/alias olarak gelebilecekler
_TABLO_OLMAYAN = {"select", "lateral", "unnest", "generate_series", "only", "set"}

# Bir string literalin SQL olup olmadigini ayirt eder (docstring'leri eler)
_SQL_GORUNUMLU = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)


def _govdeden_tablolar(govde: str) -> set[str]:
    """Tek bir SQL govdesinden tablo adlarini cikarir."""
    if not _SQL_GORUNUMLU.search(govde):
        return set()
    return {
        ad.lower()
        for ad in _TABLO_DESENI.findall(govde)
        if ad.lower() not in _TABLO_OLMAYAN
    }


def _ast_sql_tablolari(yol: Path) -> set[str]:
    """KAYNAK METINDEKI string literallerden tablo adlarini cikarir.

    YALNIZ string literalleri taranir. Ilk surum tum dosya metnine bakiyordu ve
    Python'un `from X import Y` satirlarini SQL `FROM X` sandi (`__future__`,
    `sqlalchemy`, `datetime` ... yanlis-pozitif). Alet duzeltildi;
    `test_cikartici_python_importlarini_yakalamaz` bunu civiliyor.

    Bu yarim FONKSIYON ICI `text("...")` cagrilarini yakalar (modul duzeyinde
    sabit degiller, calisma-zamani yarimi onlari GOREMEZ). Ornek:
    app/api/fsrs.py:237 `get_stats` icindeki inline SELECT.
    `test_cikartici_fonksiyon_ici_sqli_kacirmiyor` bu yarimi civiliyor.
    """
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    bulunan: set[str] = set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.Constant) and isinstance(dugum.value, str):
            bulunan |= _govdeden_tablolar(dugum.value)
    return bulunan


def _modul_adi(yol: Path) -> str:
    """backend/app/services/fsrs_service.py -> app.services.fsrs_service"""
    return ".".join(yol.relative_to(_BACKEND).with_suffix("").parts)


def _calisma_zamani_sql_tablolari(yol: Path) -> set[str]:
    """MODUL DUZEYI SQL sabitlerini CALISMA ZAMANINDA okur (A.1).

    Neden gerekli: `_FETCH_DUE_SQL` (app/services/fsrs_service.py:42-79) duz
    literal + `f"AND {safe_for_beta_sql('q.id')}"` birlesimiyle kuruluyor.
    Tablo adi `core/quality_gate.py:69` sabitinden gelir ve fsrs_service.py'nin
    KAYNAK METNINDE hic gecmez — AST yarimi yapisal olarak kordur
    (f-string `ast.JoinedStr`'dir, cagriyi statik cozmek imkansiz).

    Bu yarim modulu import edip `text()` nesnelerinin DERLENMIS metnini tarar,
    yani ucun uretimde calistirdigi SQL'i. `test_cikartici_calisma_zamani_
    sqlini_okuyor` bu yarimi civiliyor.
    """
    modul = importlib.import_module(_modul_adi(yol))
    bulunan: set[str] = set()
    for deger in vars(modul).values():
        if isinstance(deger, TextClause):
            bulunan |= _govdeden_tablolar(str(deger))
        elif isinstance(deger, str):
            bulunan |= _govdeden_tablolar(deger)
    return bulunan


def _sql_tablolari(yol: Path) -> set[str]:
    """Ham SQL'de gecen tablo adlari — IKI yarimin BIRLESIMI.

    Ikisi de yuk tasiyor, hicbiri tek basina yetmiyor (1 Agu 2026 olcumu):
      - salt-AST      -> f-string ile birlestirilen `mv_safe_for_beta`'yi kacirir
      - salt-calisma  -> fonksiyon ici `text(...)` sabitlerini kacirir
    """
    return _ast_sql_tablolari(yol) | _calisma_zamani_sql_tablolari(yol)


def _canli_tablolar() -> set[str]:
    """Canli semadaki tablo + view + MATVIEW adlari.

    `information_schema.tables` MATVIEW LISTELEMEZ (A.1b). Canli olcum
    (1 Agu 2026): `to_regclass('mv_safe_for_beta')` VAR ama information_schema
    icinde YOK. Bu yuzden kapi iliskisi "eksik tablo" gibi raporlanirdi —
    sema arizasi degil, ALET arizasi.

    relkind: r=tablo · p=bolumlenmis tablo · v=view · m=matview · f=yabanci tablo
    """
    baglanti = psycopg2.connect(DSN)
    try:
        with baglanti, baglanti.cursor() as imlec:
            imlec.execute(
                "SELECT c.relname FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace "
                "WHERE n.nspname = 'public' "
                "AND c.relkind IN ('r', 'p', 'v', 'm', 'f')"
            )
            return {satir[0].lower() for satir in imlec.fetchall()}
    finally:
        baglanti.close()


@pytest.fixture(scope="module")
def canli_tablolar() -> set[str]:
    """DB yoksa TUM modulu atla — fixture icinde kontrol (testing.md #7)."""
    try:
        tablolar = _canli_tablolar()
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    if not tablolar:
        pytest.skip("pg_class bos dondu — olcum aleti supheli")
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


def test_cikartici_calisma_zamani_sqlini_okuyor() -> None:
    """CIVI (A.1): calisma-zamani yarimi YUK TASIYOR.

    `mv_safe_for_beta` fsrs_service.py'nin kaynak metninde HIC gecmez ama
    modul yuklendiginde `_FETCH_DUE_SQL`'in derlenmis metninde VARDIR.
    Iki iddiayi ayni anda civiler:
      1. ad gercekten kaynakta yok  -> AST yarimi onu bulamaz (kor oldugu ispat)
      2. ad calisma-zamaninda var   -> yeni yarim gercekten SQL okuyor

    MUTASYON: `_sql_tablolari` salt-AST'ye dondurulurse bu test DUSER.
    """
    kaynak = FSRS_SERVICE.read_text(encoding="utf-8")
    assert SAFE_POOL_RELATION not in kaynak, (
        "Onkosul degisti: ad artik kaynak metinde geciyor. Bu test'in "
        "civiledigi kor nokta kalkmis olabilir — testi yeniden tasarla."
    )
    assert SAFE_POOL_RELATION in _calisma_zamani_sql_tablolari(
        FSRS_SERVICE
    ), "Calisma-zamani yarimi kapi iliskisini gormuyor -> A.1 geri geldi"


def test_cikartici_fonksiyon_ici_sqli_kacirmiyor() -> None:
    """CIVI: AST yarimi da YUK TASIYOR — salt-calisma yeterli DEGIL.

    app/api/fsrs.py:237 `get_stats` icindeki `text("... FROM user_item_fsrs")`
    modul duzeyi bir sabit degil; `vars(modul)` uzerinden ASLA gorunmez.

    MUTASYON: `_sql_tablolari` salt-calisma-zamanina cevrilirse bu test DUSER.
    """
    assert "user_item_fsrs" in _sql_tablolari(FSRS_API), (
        "Fonksiyon ici ham SQL kacti -> AST yarimi kaldirilmis olabilir; "
        "birlesimin iki yarimi da gereklidir"
    )


def test_alet_dogrulamasi_matview_gorunuyor(canli_tablolar: set[str]) -> None:
    """KONTROL KOLU (A.1b): olcum aleti MATVIEW'leri de goruyor mu.

    `information_schema.tables` matview LISTELEMEZ (yalniz relkind 'r' ve 'v').
    Kalite kapisi `mv_safe_for_beta` bir matview oldugu icin, bu ad canli
    kumede yoksa asagidaki sinif bekcisi onu "eksik tablo" diye raporlar —
    yani ALET arizasi, sema arizasi degil.

    Canli olcum (1 Agu 2026): to_regclass -> 'mv_safe_for_beta' VAR;
    information_schema.tables icinde -> YOK.
    """
    assert SAFE_POOL_RELATION in canli_tablolar, (
        f"Bilinen-VAR matview '{SAFE_POOL_RELATION}' canli kumede gorunmuyor -> "
        "olcum aleti matview kor. information_schema.tables yerine "
        "pg_class(relkind IN 'r','p','v','m','f') kullanilmali."
    )


def test_kalite_kapisi_iliskisi_ham_sqlden_cikariliyor() -> None:
    """A.1: /due'nun GERCEK SQL'indeki kalite kapisi iliskisi gorulmeli.

    `_FETCH_DUE_SQL` duz literal + f-string birlesimi ile kuruluyor
    (app/services/fsrs_service.py:75). Tablo adi `core/quality_gate.py:69`
    sabitinden geliyor; fsrs_service.py'nin KAYNAK METNINDE string olarak
    HIC gecmiyor. Salt-AST cikarici bu yuzden kordur.

    Kontrol kolu: calisma-zamani `str(_FETCH_DUE_SQL)` icinde ad VAR
    (1 Agu 2026 olcumu) — yani eksik olan SQL degil, cikarici.
    """
    bulunan = _sql_tablolari(FSRS_SERVICE)
    assert SAFE_POOL_RELATION in bulunan, (
        f"Kapi iliskisi '{SAFE_POOL_RELATION}' ham SQL'den cikarilamadi "
        f"(cikarilan: {sorted(bulunan)}). Bekci /due'nun gercek SQL'ini "
        "gormuyor -> 'ham SQL'de gecen HER tablo' iddiasi overclaim."
    )


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
