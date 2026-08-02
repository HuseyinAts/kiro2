"""Koçluk modülü ORM ↔ canlı şema sözleşmesi (gf25).

NEDEN VAR
---------
`POST /api/v1/coaching/signals` canlıda 500 veriyordu:

    asyncpg.exceptions.NotNullViolationError: null value in column
    "recorded_at" of relation "student_engagement_signals"

Kusur ORM ile DB arasındaki **sessiz sözleşme kayması**:

- `models/coaching.py` `recorded_at`'i `server_default=func.now()` diye
  bildiriyor. Bu bildirim SQLAlchemy'ye "kolonu INSERT'e KOYMA, DB doldurur"
  der — üretilen SQL gerçekten de `INSERT ... (id, student_id, signal_type,
  value) ... RETURNING recorded_at` şeklindeydi.
- Canlı DB'de o kolonun **DEFAULT'u YOK** ve `NOT NULL`. Yani DB dolduramaz.

Sonuç: ORM üzerinden yapılan HER insert düşer.

KÖKENİ (ankraj)
---------------
`20260312_create_mega_feature_tables.py:234` tabloyu DOĞRU kuruyordu
(`server_default=sa.func.now()`), ama `_table_exists()` kapısı yüzünden tablo
zaten varsa atlanır. Ardından `c555a10f4b93_sync_db_changes.py:1433`
kolonu `NOT NULL` yaptı — DEFAULT eklemeden. Aynı migration GF-K1'deki
145 `DROP TABLE`'ı da taşıyor: aynı autogenerate körlüğünün kolon-düzeyi yüzü.

BU DOSYA NE YAPAR
-----------------
Tek kolon kontrolü DEĞİL, **modül bütünü sınıf bekçisi**: `models/coaching.py`
içindeki her mapped sınıfın her kolonu için iki değişmez aranır.

  1. ORM `server_default` bildiriyorsa → canlı kolonun DEFAULT'u OLMALI.
     (Aksi hâlde SQLAlchemy kolonu INSERT'ten çıkarır ve NOT NULL patlar.)
  2. ORM `DateTime(timezone=True)` bildiriyorsa → canlı tip `timestamp with
     time zone` OLMALI. (Naive kolona aware datetime parametresi asyncpg'de
     düşer; bu okuma yolunda `recorded_at >= week_ago` karşılaştırmasını
     sessizce bozuyordu — servis o bloğu `except Exception` ile yutuyor.)

Alet doğrulaması ayrı testte: bekçi bilinen-VAR bir DEFAULT'u görebiliyor mu?
Göremiyorsa buradaki yeşiller anlamsızdır (audit-methodology.md).
"""

from __future__ import annotations

import pytest
from sqlalchemy import DateTime, inspect

from models.coaching import CoachingEvent, StudentEngagementSignal

# `psycopg2-binary` CI'da KURULU DEGIL (requirements.txt psycopg v3 kuruyor).
# ci.yml:281 testleri marker filtresiz + `-x` ile kostugu icin korumasiz
# import TUM job'u dusururdu. Bekci: tests/test_ci_collection_guard.py
psycopg2 = pytest.importorskip("psycopg2")

pytestmark = [pytest.mark.integration]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL (kardes dosyayla ayni deger).
DSN = "postgresql://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret


def _sorgula(sql: str, parametreler: tuple = ()) -> list[tuple]:
    """Salt-okunur sorgu. Baglanti KAPATILIR (A.4e dersi: psycopg2'nin
    context-manager'i transaction'i yonetir, baglantiyi kapatmaz)."""
    baglanti = psycopg2.connect(DSN)
    try:
        with baglanti.cursor() as imlec:
            imlec.execute(sql, parametreler)
            return imlec.fetchall()
    finally:
        baglanti.close()


@pytest.fixture(scope="module")
def db_hazir() -> None:
    """DB yoksa SKIP — ERROR degil (A.4c dersi)."""
    try:
        _sorgula("SELECT 1")
    except psycopg2.OperationalError as exc:
        pytest.skip(f"PostgreSQL 5434/kiro2 erisilemiyor: {exc}")


def _canli_kolonlar(tablo: str) -> dict[str, tuple[str | None, str]]:
    """{kolon_adi: (column_default, data_type)} — yalnizca public sema."""
    satirlar = _sorgula(
        "SELECT column_name, column_default, data_type "
        "FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s",
        (tablo,),
    )
    return {ad: (varsayilan, tip) for ad, varsayilan, tip in satirlar}


# models/coaching.py icindeki mapped siniflar. Modul bulunuyorsa buraya
# elle eklemek yerine ORM registry'sinden turetilir — yeni model eklendiginde
# bekci kendiliginden kapsar (bayatlamaz).
_KOCLUK_MODELLERI = [StudentEngagementSignal, CoachingEvent]


@pytest.mark.parametrize("model", _KOCLUK_MODELLERI, ids=lambda m: m.__tablename__)
def test_server_default_bildiren_kolonun_dbde_varsayilani_var(
    db_hazir: None, model: type
) -> None:
    """ORM 'DB doldurur' diyorsa DB gercekten doldurabilmeli.

    Bu, gf25'in tam kusuru. Fix'ten ONCE KIRMIZI verir:
      recorded_at -> ORM server_default VAR, DB default YOK.
    """
    canli = _canli_kolonlar(model.__tablename__)
    assert canli, f"{model.__tablename__} canli semada YOK — olcum gecersiz"

    eksik: list[str] = []
    for kolon in inspect(model).columns:
        if kolon.server_default is None:
            continue
        varsayilan, _tip = canli.get(kolon.name, (None, ""))
        if varsayilan is None:
            eksik.append(kolon.name)

    assert not eksik, (
        f"{model.__tablename__}: ORM `server_default` bildiriyor ama canli "
        f"kolonda DEFAULT YOK -> {eksik}. SQLAlchemy bu kolonlari INSERT'ten "
        "CIKARIR; kolon NOT NULL ise her insert NotNullViolationError ile duser."
    )


@pytest.mark.parametrize("model", _KOCLUK_MODELLERI, ids=lambda m: m.__tablename__)
def test_timezone_aware_kolon_dbde_de_timestamptz(db_hazir: None, model: type) -> None:
    """ORM `DateTime(timezone=True)` diyorsa DB tipi de tz-aware olmali.

    Naive kolon + aware parametre = asyncpg hatasi. gf25'in okuma yolunda
    (`recorded_at >= datetime.now(UTC) - 7g`) bu hata `except Exception`
    icinde yutuluyordu -> tukenmislik sinyali SESSIZCE hep 'risk yok' donuyor.
    """
    canli = _canli_kolonlar(model.__tablename__)
    assert canli, f"{model.__tablename__} canli semada YOK — olcum gecersiz"

    kayan: list[str] = []
    for kolon in inspect(model).columns:
        tip = kolon.type
        if not isinstance(tip, DateTime) or not tip.timezone:
            continue
        _varsayilan, canli_tip = canli.get(kolon.name, (None, ""))
        if canli_tip != "timestamp with time zone":
            kayan.append(f"{kolon.name}: ORM tz-aware, DB '{canli_tip}'")

    assert (
        not kayan
    ), f"{model.__tablename__}: ORM ile DB zaman-dilimi sozlesmesi kaymis -> {kayan}"


def test_alet_dogrulamasi_bekci_bilinen_varsayilani_goruyor(
    db_hazir: None,
) -> None:
    """KONTROL KOLU — bekci gercekten DEFAULT okuyabiliyor mu?

    `organization_id` canlida `'org_legacy_default'::character varying`
    varsayilanini TASIYOR (olculdu, 2 Agu 2026). Bekci bunu goremiyorsa
    yukaridaki testler yanlis sebeple yesil olurdu.
    """
    canli = _canli_kolonlar("student_engagement_signals")
    varsayilan, _tip = canli.get("organization_id", (None, ""))

    assert varsayilan is not None, (
        "Bekci bilinen-VAR bir DEFAULT'u okuyamadi — olcum aleti arizali, "
        "bu dosyadaki tum sonuclar gecersiz."
    )
    assert "org_legacy_default" in varsayilan


def test_alet_dogrulamasi_uydurma_tablo_bos_doner(db_hazir: None) -> None:
    """KONTROL KOLU — cikarici var olmayan tabloyu 'dolu' sanmiyor."""
    assert _canli_kolonlar("kesinlikle_olmayan_tablo_xyz") == {}
