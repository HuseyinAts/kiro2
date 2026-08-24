"""B2B billing ham-SQL sema sozlesmesi (K3 / S252).

NEDEN VAR
---------
`services/billing_service.py` `data_processing_agreements` tablosuna vuruyor.
O tablo CANLIDA VAR -- ama YANLIS OLANI: FERPA/COPPA ucuncu-taraf sozlesme
tablosu (`models/ferpa_coppa_models.py:197`, goc `20260406_ferpa_coppa.py`).
B2B/KVKK tablosu cakisma yuzunden `billing_data_processing_agreements` adiyla
yaratildi, ama servis ve `models/billing.py:111` eski adda kaldi.

Sonuc (24 Agu 2026 canli olcum, 5 rolun 5'i):
    GET /api/v1/org/billing/dpa        -> 500  (asyncpg UndefinedColumnError)
    GET /api/v1/org/billing/activation -> 500
`require_dpa_signed` uzerinden 2 uc daha oluyor (dpa/sign, license/start-trial).

BU KUSUR SINIFI NEDEN ONCE YAKALANMADI
--------------------------------------
`tests/integration/test_fsrs_schema_contract.py` bir TABLO-VARLIGI bekcisidir.
Bu kusuru YAPISAL OLARAK goremez: aranan tablo adi semada MEVCUT. Yanlis olan
tablonun KIMLIGI, varligi degil. Bu yuzden buradaki bekci **kolon duzeyinde**
olcer ve olcumu PostgreSQL'in kendi ayristiricisina yaptirir -- servisin
uretimde calistirdigi SQL'in aynisini `EXPLAIN` ile plana sokar.

Ayrica `models/billing.py:111` ile `models/ferpa_coppa_models.py:200` AYNI
`__tablename__`'i beyan ediyordu. OLCULDU (ilk RED kosusu): `extend_existing`
yalnizca billing tarafinda vardi, ferpa tarafinda YOK. Sonuc IMPORT SIRASINA
bagli ve iki turlu de kotu:
  ferpa once -> billing'in extend_existing'i FERPA tanimini sessizce EZER
  billing once -> `InvalidRequestError: Table ... is already defined`
Yani cakisma ya susuyor ya patliyor, ama hicbir zaman DOGRU tabloyu vermiyordu.
Son test bunu civiliyor.

ALET DOGRULAMASI
----------------
`test_alet_bilinen_kotu_sqli_yakalar` bekcinin kendisini sinar: uydurma kolonlu
bir SELECT enjekte edilir ve bekcinin KIRMIZI donmesi beklenir. O test gecmezse
bu dosyadaki hicbir yesil anlamli degildir.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration]

# Yerel gelistirme DSN'i -- uretim kimligi DEGIL. Mevcut gercek-DB testleriyle
# ayni deger (bkz. tests/integration/test_fsrs_schema_contract.py).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret

_BACKEND = Path(__file__).resolve().parents[2]
BILLING_SERVICE = _BACKEND / "services" / "billing_service.py"

# Bir string literalin SQL olup olmadigini ayirt eder.
_SQL_GORUNUMLU = re.compile(r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM)\b", re.I)

# SQLAlchemy `:ad` baglama parametresi. EXPLAIN icin NULL'a cevrilir:
# plan asamasi NOT NULL kisitini uygulamaz, ama KOLON ADINI cozer.
_BAGLAMA = re.compile(r":\w+")


def _sql_literalleri(yol: Path) -> list[str]:
    """Kaynak dosyadaki SQL gorunumlu string literalleri toplar.

    DOCSTRING'LER AYIKLANIR. Depo dersi: *bir deseni ANLATAN yorum o deseni
    ICERIR* -- `billing_service.py:17` docstring'i tam olarak `status='signed'`
    yaziyor. Ayiklanmazsa bekci kendi anlatimini olcer.

    Bitisik literaller (implicit concatenation) Python tarafindan zaten tek
    Constant'a katlanir, bu yuzden cok satirli SQL tek parca gelir.
    """
    agac = ast.parse(yol.read_text(encoding="utf-8"))

    docstring_dugumleri: set[int] = set()
    for dugum in ast.walk(agac):
        if isinstance(
            dugum, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            govde = getattr(dugum, "body", None)
            if not govde:
                continue
            ilk = govde[0]
            if (
                isinstance(ilk, ast.Expr)
                and isinstance(ilk.value, ast.Constant)
                and isinstance(ilk.value.value, str)
            ):
                docstring_dugumleri.add(id(ilk.value))

    bulunan: list[str] = []
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Constant):
            continue
        if not isinstance(dugum.value, str):
            continue
        if id(dugum) in docstring_dugumleri:
            continue
        if _SQL_GORUNUMLU.search(dugum.value):
            bulunan.append(dugum.value)
    return bulunan


def _plana_sok(imlec, sql: str) -> None:
    """SQL'i PostgreSQL'e ayristirtir. Tablo/kolon yanlissa PG istisna atar.

    `EXPLAIN` yalnizca PLAN uretir -- veri okumaz, yazmaz. Cagiran islemi
    yine de geri alir (cift emniyet).
    """
    imlec.execute("EXPLAIN " + _BAGLAMA.sub("NULL", sql))


@pytest.fixture(scope="module")
def baglanti():
    """DB yoksa TUM modulu atla -- fixture icinde kontrol (testing.md #7)."""
    try:
        conn = psycopg2.connect(DSN)
    except psycopg2.OperationalError as hata:
        pytest.skip(f"PostgreSQL :5434 erisilemez ({hata.__class__.__name__})")
    try:
        yield conn
    finally:
        conn.close()


def test_alet_dogrulamasi_bilinen_iyi_sql_gecer(baglanti) -> None:
    """KONTROL KOLU: bekci saglam SQL'i REDDETMIYOR.

    Bu kirmizi olursa asagidaki basarisizliklar sema kusuru degil ALET arizasidir.
    """
    with baglanti, baglanti.cursor() as imlec:
        _plana_sok(imlec, "SELECT id FROM question_bank WHERE id = :x LIMIT 1")
    baglanti.rollback()


def test_alet_bilinen_kotu_sqli_yakalar(baglanti) -> None:
    """MUTASYON: uydurma kolon enjekte edilir, bekci KIRMIZI donmeli.

    Bu test gecmezse bekci hicbir sey olcmuyor demektir.
    """
    with (
        pytest.raises(psycopg2.errors.UndefinedColumn),
        baglanti,
        baglanti.cursor() as imlec,
    ):
        _plana_sok(
            imlec,
            "SELECT zzz_kesinlikle_olmayan_kolon FROM question_bank LIMIT 1",
        )
    baglanti.rollback()


def test_alet_sql_literallerini_buluyor() -> None:
    """KONTROL KOLU: cikartici bos donerse yukaridaki bekci BOSA gecer.

    Yanlis-SIFIR bir ilerleme sayacinda tek kabul edilemez hata turudur:
    cikartici 0 dondurse `test_billing_service_sql_canli_semayla_uyumlu`
    hicbir sey olcmeden YESIL olurdu.
    """
    literaller = _sql_literalleri(BILLING_SERVICE)
    assert len(literaller) >= 4, (
        f"billing_service.py'den yalniz {len(literaller)} SQL literali cikti; "
        "cikartici bozulmus olabilir (>=4 beklenir)"
    )
    # Docstring ayiklamasi GERCEKTEN calisiyor mu: :17 docstring'i "status='signed'"
    # iceriyor ama SELECT/INSERT tasimadigi icin zaten elenmeli. Yine de
    # docstring'e ozgu bir cumlenin listeye SIZMADIGINI civile.
    assert not any(
        "DPA'sı var mı" in s for s in literaller
    ), "docstring SQL sanildi -- cikartici yorum/anlatim ayikliyor olmali"


def test_billing_service_sql_canli_semayla_uyumlu(baglanti) -> None:
    """ASIL BEKCI: servisin her ham SQL'i canli semada ayristirilabilmeli.

    Bu test K3 duzeltilmeden ONCE KIRMIZI olmalidir (UndefinedColumn:
    `data_processing_agreements` FERPA sekilli, `status` kolonu yok).
    """
    hatalar: list[str] = []
    for sql in _sql_literalleri(BILLING_SERVICE):
        try:
            with baglanti, baglanti.cursor() as imlec:
                _plana_sok(imlec, sql)
        except psycopg2.Error as hata:
            ozet = " ".join(sql.split())[:90]
            hatalar.append(f"{type(hata).__name__}: {str(hata).strip()} <- {ozet}")
        finally:
            baglanti.rollback()

    assert not hatalar, (
        "billing_service.py SQL'i canli semayla UYUSMUYOR:\n" + "\n".join(hatalar)
    )


def test_iki_dpa_modeli_ayni_tablo_adini_paylasmiyor() -> None:
    """Cakisma bekcisi: iki farkli DPA kavrami TEK tablo adina yazilamaz.

    `extend_existing=True` SQLAlchemy'nin `InvalidRequestError`'ini susturuyor,
    bu yuzden cakisma calisma aninda GORUNMEZ. Kusur ancak SQL uretimde
    patladiginda ortaya cikti (6 hafta sonra). Burada statik olarak civilenir.
    """
    from models.billing import DataProcessingAgreement as BillingDPA
    from models.ferpa_coppa_models import DataProcessingAgreement as FerpaDPA

    assert BillingDPA.__tablename__ != FerpaDPA.__tablename__, (
        "models/billing.py ve models/ferpa_coppa_models.py AYNI __tablename__'i "
        f"({BillingDPA.__tablename__!r}) beyan ediyor. Iki tablo AYRI: B2B olan "
        "'billing_data_processing_agreements', FERPA olan "
        "'data_processing_agreements'."
    )
