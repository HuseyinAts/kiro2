"""Autogenerate emniyetinin SOZLESMESI (GF-K1'in kok nedeni).

1 AGU 2026 CANLI OLCUMU — VE BIR OLCUM DUZELTMESI
--------------------------------------------------
Ilk olcum `compare_metadata`'yi **hicbir filtre olmadan** kosturdu ve
"86 tablo dusecek" dedi. Bu yanlisti: alembic o konfigurasyonu HIC kullanmiyor.
`alembic/env.py` 27 Tem 2026'dan beri tablolari zaten koruyordu. Gercek yol
olculunce tablo tarafinin kapali, **index tarafinin acik** oldugu goruldu:

    filtre YOK                  -> remove_table=86  remove_index=134
    onceki kural (yalniz tablo) -> remove_table= 0  remove_index= 65   <- ACIK
    bu modulun kurali           -> remove_table= 0  remove_index=  0

Ders (audit-methodology "Olcum aletini dogrula"): bir kontrol kolu secmeden
once **sistemin fiilen kullandigi** konfigurasyonun hangisi oldugunu kanitla.

Arka plan: `alembic/versions/c555a10f4b93_sync_db_changes.py` `upgrade()`
icinde 145 adet `op.execute('DROP TABLE IF EXISTS ... CASCADE')` var; GF-K1'in
6 tablosu ve `user_item_fsrs` orada dustu. Ayrica `Base.metadata` 123 tablo
tanirken canli sema 210 tablo tasiyor (87 tablo yonetilmiyor) — asil duzeltme
o modulleri metadata'ya kaydetmek, bu filtre o gune kadar emniyet kilidi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.alembic_autogen_guard import yonetilmeyeni_disla
from models.database import Base

pytestmark = [pytest.mark.integration]

# Yerel gelistirme DSN'i — uretim kimligi DEGIL (bkz. test_fsrs_schema_contract.py).
# psycopg **v3** dialect'i: requirements.txt'teki surum bu (psycopg2 CI'da yok).
DSN = "postgresql+psycopg://postgres:postgres@localhost:5434/kiro2"  # pragma: allowlist secret


def _onceki_kural(nesne, ad, tur, yansitilmis, karsilastirilan):
    """env.py'nin 27 Tem - 1 Agu arasi tasidigi kural: YALNIZ tablo."""
    return not (tur == "table" and yansitilmis and karsilastirilan is None)


def _farklar(opts: dict) -> list:
    motor = create_engine(DSN)
    try:
        with motor.connect() as baglanti:
            baglam = MigrationContext.configure(baglanti, opts=opts)
            return compare_metadata(baglam, Base.metadata)  # type: ignore[no-any-return]  # pre-existing, out of scope for SS10.42
    finally:
        motor.dispose()


def _say(farklar: list, tur: str) -> int:
    return sum(1 for f in farklar if isinstance(f, tuple) and f[0] == tur)


@pytest.fixture(scope="module")
def filtresiz() -> list:
    try:
        return _farklar({})
    except Exception as hata:
        pytest.skip(
            f"PostgreSQL :5434 karsilastirmasi yapilamadi ({hata.__class__.__name__})"
        )


@pytest.fixture(scope="module")
def onceki_kuralla(filtresiz: list) -> list:
    return _farklar({"include_object": _onceki_kural})


@pytest.fixture(scope="module")
def korumali(filtresiz: list) -> list:
    return _farklar({"include_object": yonetilmeyeni_disla})


# --------------------------------------------------------------------------
# ALET DOGRULAMASI
# --------------------------------------------------------------------------


def test_alet_dogrulamasi_filtresiz_kol_tehlikeyi_goruyor(filtresiz: list) -> None:
    """KONTROL KOLU: filtresiz karsilastirma DROP gormezse olcum gecersizdir.

    Kirmiziya donerse iki ihtimal: (a) 87 tablo metadata'ya kaydedildi (harika,
    bu dosya guncellenmeli), (b) karsilastirma hic kosmuyor ve asagidaki
    "0 DROP" sonuclari SAHTE. Ikisi de bakilmali.
    """
    assert _say(filtresiz, "remove_table") > 0, (
        "Filtresiz karsilastirma hic DROP gormedi -> ya drift kapandi ya da "
        "olcum aleti arizali; 'emniyet calisiyor' sonucu ANLAMSIZ olur"
    )


def test_onceki_kural_index_acigi_artik_kapali(onceki_kuralla: list) -> None:
    """TARIHSEL KAYIT: eski `type_ == "table"` kurali index'leri kapsamiyordu.

    1 Agu 2026 olcumu: onceki kuralla remove_table=0, remove_index=65 --
    `yonetilmeyeni_disla` fix'inin +0 kazancli olmadiginin kaniti buydu
    (asagidaki assert o zaman `> 0` idi).

    5 Eyl 2026 (SS10.42, docs/guvenlik-borcu.md): son kalan tek ornek de
    kapandi. `models/system_models.py`'deki `Session.token` ORM kolonu
    "token" adini beklerken canli DB'deki gercek kolon "hashed_token" idi
    (bkz. alembic/versions_archive/040b91d243a0_secure_plaintext_sessions.py).
    Bu yuzden DB'nin `ix_sessions_hashed_token` index'i metadata'da hicbir
    karsilik bulamiyor ve onceki kuralla "remove_index" olarak cikiyordu --
    tam da bu testin orijinal iddiasinin kanitiydi. SS10.42, `token`'i
    `mapped_column("hashed_token", ...)` ile gercek kolona esledi; artik
    ORM'un urettigi index adi da DB'ninkiyle birebir ortusuyor, yani bu
    ornek de yonetilmeyeni_disla'ya ihtiyac duymadan kendiliginden kapaniyor.

    Bu fonksiyon SILINMEDI (dosyanin ust kismindaki "1 Agu 2026 CANLI
    OLCUMU" notu ve `onceki_kuralla` fixture'i hala gecmisi belgeliyor);
    artik "acik kaldi" degil "artik kapali" durumunu dogruluyor. Assert
    bir gun tekrar kirilirsa (yeni bir kolon/index adi uyumsuzlugu), dogru
    yaklasim bu testi gevsetmek degil, SS10.42'dekiyle ayni yontemle
    (onceki/sonraki index listesini karsilastirip) kok nedeni bulup asil
    ORM/DB uyumsuzlugunu duzeltmektir.
    """
    assert (
        _say(onceki_kuralla, "remove_table") == 0
    ), "Onceki kural tablolari korumuyordu -> tarihsel varsayim yanlis"
    assert _say(onceki_kuralla, "remove_index") == 0, (
        "Onceki kuralla yeniden bir index DROP'u goruldu -> SS10.42'de "
        "kapatilan sessions.hashed_token gibi yeni bir ORM/DB kolon-adi "
        "uyumsuzlugu olusmus olabilir; kok nedeni bul ve duzelt"
    )


# --------------------------------------------------------------------------
# CANLI SOZLESME
# --------------------------------------------------------------------------


def test_autogenerate_hicbir_tabloyu_dusurmeyi_onermiyor(korumali: list) -> None:
    dusenler = [
        f[1].name for f in korumali if isinstance(f, tuple) and f[0] == "remove_table"
    ]
    assert not dusenler, (
        f"autogenerate {len(dusenler)} tabloyu DUSURMEYI oneriyor: "
        f"{sorted(dusenler)[:10]} — c555a10f4b93 vakasi (145 DROP) tekrarlanir"
    )


def test_autogenerate_hicbir_index_dusurmeyi_onermiyor(korumali: list) -> None:
    """Yonetilmeyen tablolarin index'leri de korunmali (65 adet olculdu)."""
    kalan = _say(korumali, "remove_index")
    assert kalan == 0, (
        f"autogenerate {kalan} index'i dusurmeyi oneriyor — A1.1 gocuyle eklenen "
        "hot-path index'leri bu yolla sessizce kaybedilebilir"
    )


# --------------------------------------------------------------------------
# SAF KATMAN — yuklem dogru YONDE eliyor mu (DB gerekmez)
# --------------------------------------------------------------------------


def test_yonetilen_nesne_elenmiyor() -> None:
    """Metadata'da karsiligi OLAN yansitilmis nesne gocte kalmali.

    Elenirse filtre autogenerate'i tamamen korlestirir: gercek model
    degisiklikleri de goc uretmez, arac sessizce ise yaramaz hale gelir.
    """
    assert (
        yonetilmeyeni_disla(object(), "users", "table", True, object()) is True
    ), "Yonetilen (karsiligi olan) tablo elendi -> autogenerate tamamen kor"


def test_metadata_kaynakli_nesne_elenmiyor() -> None:
    """Yansitilmamis (metadata'dan gelen) nesne her zaman gocte kalmali."""
    assert (
        yonetilmeyeni_disla(object(), "yeni_tablo", "table", False, None) is True
    ), "Metadata'dan gelen yeni tablo elendi -> CREATE TABLE uretilemez"


@pytest.mark.parametrize("tur", ["table", "index", "column"])
def test_yansitilmis_ve_karsiliksiz_nesne_eleniyor(tur: str) -> None:
    """Asil kural TUR AYRIMI YAPMADAN gecerli olmali (index acigi buradan cikti)."""
    assert (
        yonetilmeyeni_disla(object(), "billing_subscriptions", tur, True, None) is False
    ), f"DB'de olup metadata'da olmayan {tur} gocte KALDI -> DROP uretilir"
