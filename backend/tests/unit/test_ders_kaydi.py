"""Ders kaydinin KENDISINI denetleyen bekci.

NEDEN VAR
---------
Bu depoda dersler 13 ayri `.claude/rules/*.md` dosyasinda, 2203 satir prose
icinde dagilmis durumdaydi: kimligi, durumu, kaniti ve zorlayicisi yoktu.
`testing.md` #15 zaten sunu yaziyor — "ders cikarilmasi YETMEZ: (1) yaz,
(2) hook/lint ekle, (3) CI'da kontrol et" — ve 2. ile 3. adimin YAPILMADIGINI
itiraf ediyor.

Prose dosyalari YERINDE KALIYOR (uzun anlatim orada). `.claude/lessons/
ders_kaydi.yaml` onlarin ustunde bir YASAM DONGUSU katmani: her ders bir
kimlik, kaynak ankraji, durum ve (varsa) zorlayici tasir.

BU DOSYA NE YAPAR
-----------------
Defterin CURUMESINI gorunur kilar:
  - `kaynak` dosyasi silinmis mi? (ders artik hicbir yere isaret etmiyor)
  - `zorlayici` testi silinmis mi? (ders "otomatiklesti" diyor ama bekci yok)
  - `aktif` ders KANITSIZ mi? (olculmemis iddia "aktif" sayilamaz)
  - `curutuldu` ders kanitsiz mi? (bir ders SESSIZCE silinemez/curutulemez)

DENETLE / DEGISTIR / SIL
------------------------
  denetle : bu test + `durum: dogrulanmadi` olanlari azalt
  degistir: `durum` alanini oynat (dogrulanmadi -> aktif, kanit ekleyerek)
  sil     : SESSIZ SILME YOK. `durum: curutuldu` + `kanit` (neyin curuttugu).
            Fiziksel silme git diff'inde gorunur; bu test sayiyi da tabanla
            koruyor, yani toplu silme sessizce gecemez.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

DEPO_KOKU = Path(__file__).resolve().parents[3]
KAYIT_YOLU = DEPO_KOKU / ".claude" / "lessons" / "ders_kaydi.yaml"

ZORUNLU_ALANLAR = {"id", "baslik", "kaynak", "sinif", "durum", "zorlayici", "kanit"}
GECERLI_DURUMLAR = {"aktif", "dogrulanmadi", "curutuldu", "devredildi"}
# 1 Agu 2026 olcumu: 66 ders (47 gocurulen + 19 S202). Taban, toplu silmenin
# sessizce gecmesini engeller — sayi DUSERSE bilincli karar gerekir.
DERS_TABANI = 60


def _kayit() -> list[dict[str, Any]]:
    if not KAYIT_YOLU.exists():
        pytest.fail(f"Ders kaydi YOK: {KAYIT_YOLU}")
    return yaml.safe_load(KAYIT_YOLU.read_text(encoding="utf-8"))


def _dosya_yolu(kaynak: str) -> Path:
    """`.claude/rules/testing.md#12` -> depo kokune gore Path."""
    return DEPO_KOKU / kaynak.split("#", 1)[0]


# --------------------------------------------------------------------------
# ALET DOGRULAMASI
# --------------------------------------------------------------------------


def test_alet_dogrulamasi_kayit_okunabiliyor_ve_dolu() -> None:
    """KONTROL KOLU: defter okunamiyorsa asagidaki 'ihlal yok' sonuclari SAHTE."""
    kayit = _kayit()
    assert isinstance(kayit, list), f"Defter liste degil: {type(kayit)}"
    assert len(kayit) >= DERS_TABANI, (
        f"Yalniz {len(kayit)} ders var (taban {DERS_TABANI}). Toplu silme mi "
        "oldu, yoksa dosya mi bozuldu? Sessizce gecemez."
    )


def test_alet_dogrulamasi_bozuk_girdi_yakalaniyor() -> None:
    """Denetleyici bilinen-KOTU girdiyi gormezse bu dosya vakumdur."""
    bozuk = {"id": "L-test", "baslik": "x"}  # zorunlu alanlarin cogu yok
    assert ZORUNLU_ALANLAR - set(
        bozuk
    ), "Eksik-alan denetimi bozuk girdiyi yakalayamadi -> bekci anlamsiz"
    assert "uydurma_durum" not in GECERLI_DURUMLAR, "Durum beyaz listesi ise yaramiyor"


# --------------------------------------------------------------------------
# SEMA
# --------------------------------------------------------------------------


def test_her_dersin_zorunlu_alanlari_var() -> None:
    eksikler = [
        f"{g.get('id', '(id YOK)')}: {sorted(ZORUNLU_ALANLAR - set(g))}"
        for g in _kayit()
        if ZORUNLU_ALANLAR - set(g)
    ]
    assert not eksikler, "Zorunlu alani eksik dersler:\n  " + "\n  ".join(eksikler)


def test_durum_degerleri_beyaz_listede() -> None:
    hatali = [
        f"{g['id']}: {g['durum']}"
        for g in _kayit()
        if g["durum"] not in GECERLI_DURUMLAR
    ]
    assert (
        not hatali
    ), f"Gecersiz durum: {hatali}. Izin verilenler: {sorted(GECERLI_DURUMLAR)}"


def test_kimlikler_benzersiz() -> None:
    kimlikler = [g["id"] for g in _kayit()]
    tekrar = sorted({k for k in kimlikler if kimlikler.count(k) > 1})
    assert not tekrar, f"Tekrarlayan ders kimligi: {tekrar} -> ankraj belirsizlesir"


# --------------------------------------------------------------------------
# CURUME TESPITI — defterin asil isi
# --------------------------------------------------------------------------


def test_kaynak_dosyalari_hala_var() -> None:
    """Ders bir yere isaret etmeli; kaynak silinmisse ders yetimdir."""
    yetim = [
        f"{g['id']} -> {g['kaynak']}"
        for g in _kayit()
        if not _dosya_yolu(g["kaynak"]).exists()
    ]
    assert not yetim, (
        "Kaynak dosyasi SILINMIS dersler (yetim ankraj):\n  " + "\n  ".join(yetim)
    )


def test_zorlayici_testleri_hala_var() -> None:
    """`zorlayici` dolu ama dosya yoksa ders 'otomatiklesti' diye YALAN soyluyor."""
    kayip = [
        f"{g['id']} -> {g['zorlayici']}"
        for g in _kayit()
        if g["zorlayici"] and not (DEPO_KOKU / g["zorlayici"]).exists()
    ]
    assert not kayip, (
        "Zorlayicisi SILINMIS dersler — ders korundugunu saniyor ama bekci yok:\n  "
        + "\n  ".join(kayip)
    )


def test_aktif_dersler_kanit_tasiyor() -> None:
    """`aktif` = OLCULDU demek. Kanitsiz 'aktif' bu deponun kacindigi sey."""
    kanitsiz = [g["id"] for g in _kayit() if g["durum"] == "aktif" and not g["kanit"]]
    assert not kanitsiz, (
        f"Kanitsiz 'aktif' ders: {kanitsiz}. Ya kanit (commit/olcum) ekle ya da "
        "durumu 'dogrulanmadi' yap — olculmemis iddia aktif sayilamaz."
    )


# S232'de olculdu: 143 dersin 41'inde `zorlayici` var ve o 41'i pre-push
# kapisinda (`ders-zorlayici` hook'u) FIILEN kosuyor. Bundan ONCE oran %29 idi
# ama KOSAN %0'di — yani "zorlayici alani dolu" tek basina hicbir sey
# kanitlamiyordu (S231 olcumu).
#
# CIRCIR (ratchet) MANTIGI: bu sayi DUSMEMELI. Enforcement sessizce erimenin
# tam olarak nasil gerceklestigini bu depo yasadi: 28 Tem'de pre-commit test
# hook'u kaldirildi, kimse fark etmedi, aylar sonra %0 olarak olculdu.
#
# NEDEN ORAN DEGIL MUTLAK SAYI: `L-s231-sabit-esik-suite-buyudukce-gevser`
# mutlak esiklerin evren buyudukce gevsedigini soyler ve bu genelde dogru.
# BURADA TERSI: yeni ders eklemek orani DUSURUR (payda buyur), yani oran
# tabani mesru ders eklemeyi BLOKLARDI. Korunmasi gereken sey "kac dersin
# bekcisi var" — o yuzden taban SAYIYA baglandi.
ZORLAYICI_TABANI = 43


def test_zorlayici_sayisi_gerilemiyor() -> None:
    """Enforcement geriye gitmemeli — bu depoda %0'a dusen bir kapi var.

    Bu test DUSERSE iki mesru sebep olabilir:
      1. Bir bekci dosyasi silindi/tasindi  -> dersi guncelle
      2. Bir ders curutuldu ve bekcisi de gitti -> TABANI dusur ve
         commit mesajinda NEDEN dustugunu yaz (sessiz gerileme yasak)
    """
    sayi = sum(1 for g in _kayit() if g["zorlayici"])
    assert sayi >= ZORLAYICI_TABANI, (
        f"Zorlayicisi olan ders sayisi {sayi} — taban {ZORLAYICI_TABANI}. "
        "Enforcement GERILEDI. Bir bekci dosyasi mi silindi, yoksa taban mi "
        "bilincli dusuruluyor? Ikincisiyse tabani guncelle ve gerekcesini yaz."
    )


def test_curutulen_dersler_gerekce_tasiyor() -> None:
    """Bir ders SESSIZCE curutulemez: neyin curuttugu yazili olmali."""
    gerekcesiz = [
        g["id"]
        for g in _kayit()
        if g["durum"] in {"curutuldu", "devredildi"} and not g["kanit"]
    ]
    assert not gerekcesiz, (
        f"Gerekcesiz curutulen/devredilen ders: {gerekcesiz}. "
        "Curutme de bir OLCUMDUR — neyin curuttugunu yaz."
    )
