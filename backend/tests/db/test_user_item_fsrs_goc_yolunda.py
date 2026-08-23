"""`user_item_fsrs` AKTIF goc yolunda tanimli olmali -- arsivde degil.

NEDEN BU BEKCI VAR (23 Agu 2026'da olculdu, S249/I2)
---------------------------------------------------
Tablo canli DB'de YOKTU (`to_regclass` -> None) ve bu **ikinci** kayboluşuydu
(#461'de bir kez restore edilmisti). Depo kurali (verification.md): 2. kez
gorulen sorun PATCH'lenmez, KOK NEDEN cozulur + enforcement eklenir.

Kok neden UC katmanli olculdu:
  1. `alembic/env.py:84` koruma satiri yoruma alinmis + tablonun ORM modeli yok.
  2. DROP: `versions_archive/c555a10f4b93_sync_db_changes.py:419`
     (Uc ayri dokuman bu ankraji `:183` diye veriyor -- FANTOM ankraj.)
  3. **ASIL kalicilik sebebi: squash `e002f550b` (14 Agu 2026).**
     - `versions/0001_baseline_squash.py` govdesini
       `alembic/baseline/0001_baseline_schema.sql`'den okur; o dosya CANLI DB'nin
       `pg_dump --schema-only` ciktisi ve `user_item_fsrs` orada **0 kez** geciyor
       (243 CREATE TABLE var). Yani YOKLUK kanonik semaya donduruldu.
     - Ayni commit restore migration'ini R100 ile `versions/` -> `versions_archive/`
       tasidi. Tabloya dokunan 6 alembic dosyasinin 6'si da arsivde ve
       `down_revision` zincirleri aktif yola baglanmiyor.
     - Sonuc: `alembic upgrade head` bu tabloyu **bir daha asla** yaratmaz.

NEDEN AUTOGENERATE KORUMASI EKLENMEDI (+0 deger kurali)
------------------------------------------------------
`env.py:84`'u yorumdan cikarmak cazipti ama OLCULDU: `core/alembic_autogen_guard.py:82`
`return not (yansitilmis and karsilastirilan is None)` -- yansitilmis + metadata'siz
her nesneyi zaten disliyor. Yani o satir bugun +0 davranis degistirir. Tekrar-DROP
riski autogenerate'ten DEGIL squash'tan geldi; bekci de onu hedefliyor.

NEDEN CANLI DB'YE BAKMIYOR
--------------------------
`tests/integration/test_fsrs_schema_contract.py` zaten canli DB'ye bakiyor ve
tablo yokken KIRMIZI oluyordu -- ama `integration` marker'i yuzunden kimse
kosmuyordu. Detektorun yoklugu degil, KOSULMAMASI sorundu. Bu bekci STATIK:
DB istemez, her yerde kosar ve tam da squash sinifini yakalar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

BACKEND = Path(__file__).resolve().parents[2]
VERSIONS = BACKEND / "alembic" / "versions"
BASELINE = BACKEND / "alembic" / "baseline"
ARSIV = BACKEND / "alembic" / "versions_archive"

TABLO = "user_item_fsrs"


def _aktif_goc_metinleri() -> dict[str, str]:
    """AKTIF goc yolundaki her kaynak: versions/*.py + baseline/*.sql.

    `versions_archive/` KASITLI DISARIDA -- bekcinin tum varlik sebebi tablonun
    arsivde olup aktif yolda OLMAMASINI yakalamak.
    """
    metinler: dict[str, str] = {}
    for p in sorted(VERSIONS.glob("*.py")):
        metinler[f"versions/{p.name}"] = p.read_text(encoding="utf-8", errors="replace")
    for p in sorted(BASELINE.glob("*.sql")):
        metinler[f"baseline/{p.name}"] = p.read_text(encoding="utf-8", errors="replace")
    return metinler


# ---------------------------------------------------------------------------
# Korlesme guvencesi -- bunlar dusesse asagidaki denetim BOS KUME uzerinde gecer
# ve hicbir sey korumaz. Bu depoda tam bu sinif hata yasandi (S238 XPASS,
# S246 parents[2], S248 yanlis bundle yolu, S249 yanlis grep hedefi).
# ---------------------------------------------------------------------------


def test_korlesme_dizinler_var():
    assert VERSIONS.is_dir(), f"goc dizini yok: {VERSIONS}"
    assert BASELINE.is_dir(), f"baseline dizini yok: {BASELINE}"


def test_korlesme_aktif_goc_yolu_bos_degil():
    metinler = _aktif_goc_metinleri()
    assert metinler, "aktif goc yolunda hic kaynak bulunamadi -- ALET ARIZASI"
    toplam = sum(len(v) for v in metinler.values())
    assert toplam > 100_000, (
        f"aktif goc kaynaklarinin toplam boyutu {toplam} -- baseline SQL okunamamis "
        "olabilir (23 Agu olcumu: baseline tek basina ~563 KB). ALET ARIZASI."
    )


def test_korlesme_kontrol_kolu_bilinen_tablolar_bulunuyor():
    """Arama BILINEN-VAR tablolari bulmuyorsa bulgu degil ALET ARIZASI vardir."""
    metinler = _aktif_goc_metinleri()
    hepsi = "\n".join(metinler.values())
    for bilinen in ("question_bank", "users", "exam_sessions"):
        assert bilinen in hepsi, (
            f"kontrol kolu DUSTU: '{bilinen}' aktif goc yolunda bulunamadi. "
            "Bu bir ALET ARIZASIDIR -- asagidaki denetim guvenilmez."
        )


# ---------------------------------------------------------------------------
# Asil iddia
# ---------------------------------------------------------------------------


def test_user_item_fsrs_aktif_goc_yolunda_tanimli():
    """Tablo bos DB'den `alembic upgrade head` ile KURULABILIR olmali.

    23 Agu 2026'da bu test KIRMIZIYDI: tabloya dokunan 6 dosyanin 6'si da
    `versions_archive/` altindaydi ve aktif yolda 0 gecis vardi.
    """
    metinler = _aktif_goc_metinleri()
    bulunanlar = [ad for ad, metin in metinler.items() if TABLO in metin]

    assert bulunanlar, (
        f"'{TABLO}' AKTIF goc yolunda hic gecmiyor -- bos bir DB'de "
        "`alembic upgrade head` bu tabloyu YARATMAZ ve /api/v1/fsrs uclari "
        "500 verir.\n"
        f"Arandi: versions/*.py ({len(list(VERSIONS.glob('*.py')))} dosya) + "
        f"baseline/*.sql ({len(list(BASELINE.glob('*.sql')))} dosya).\n"
        "Tablo yalnizca versions_archive/ altindaysa bir squash veya arsiv "
        "tasimasi onu goc yolundan dusurmus demektir (S249 kok neden analizi)."
    )


def test_arsivde_olmasi_tek_basina_yeterli_degil():
    """Ayirt edici assert: arsivde bulmak testi tatmin ETMEMELI.

    Bu test olmadan yukaridaki assert, arama kumesine yanlislikla
    `versions_archive/` eklenirse sessizce gecmeye baslar ve bekci olur.
    """
    arsiv_gecis = any(
        TABLO in p.read_text(encoding="utf-8", errors="replace")
        for p in ARSIV.glob("*.py")
    )
    assert arsiv_gecis, (
        "kontrol kolu DUSTU: tablo arsivde de bulunamadi. Arsiv tasinmis veya "
        "silinmis olabilir -- ALET ARIZASI, bu bekcinin ayrimi anlamsizlasir."
    )
    # Ve aktif yol arsivi ICERMEMELI:
    assert not any(
        ad.startswith("versions_archive") for ad in _aktif_goc_metinleri()
    ), "arama kumesi arsivi iceriyor -- bekci kendi ayrimini kaybetmis"
