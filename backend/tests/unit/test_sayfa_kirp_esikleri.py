"""sayfa_kirp_zkitap.py'deki OLCULMUS esikleri civiler.

Neden test: bu esiklerin her biri gercek bir yanlis-sayim vakasindan dogdu ve
degerleri ORNEKLEMDEN olculdu, secilmedi. Bir refactor'da (veya sessiz bir
dosya kaybinda) eski degere donerlerse manifest sessizce yanlis uretir ve
hicbir sey kirilmaz -- cikti "calisiyor" gorunur, sadece yanlis olur.

Gercek vaka: IKON_SUTUN_ESIGI bir kez uygulandi, manifest'e yansidi, sonra
dosyadan KAYBOLDU; kayip ancak bagimsiz bir OCR cikarimi manifestle
celistiginde fark edildi. Bu test o sessiz kaybi gurultulu hale getirir.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PIPELINE = Path(__file__).resolve().parents[2] / "scripts" / "pipeline"
sys.path.insert(0, str(PIPELINE))

kirp = pytest.importorskip("sayfa_kirp_zkitap", reason="pipeline script'i bulunamadi")


def test_sutun_esigi_kume_arasinda() -> None:
    """Sutun esigi, olculen iki ikon kumesinin ARASINDA olmali.

    Olculen dagilim (1034 ikon, tum kitap): sol kume x=39..57, sag kume
    x=232..380. Esik bu bos bolgede degilse (orn. kirpma siniri OLUK_SAG=370)
    sag kumenin icinden geser ve sinirdaki ikonlari yanlis sutuna yazar.
    """
    SOL_KUME_MAX = 57
    SAG_KUME_MIN = 232

    assert SOL_KUME_MAX < kirp.IKON_SUTUN_ESIGI < SAG_KUME_MIN, (
        f"IKON_SUTUN_ESIGI={kirp.IKON_SUTUN_ESIGI} olculen bos bolgenin "
        f"({SOL_KUME_MAX}..{SAG_KUME_MIN}) disinda"
    )
    # Kontrol kolu: kirpma sinirini sutun esigi olarak kullanmak HATALI idi.
    assert kirp.IKON_SUTUN_ESIGI != kirp.OLUK_SAG, (
        "sutun esigi kirpma siniriyla ayni: 360..369 arasindaki ikonlar "
        "yanlis sutuna yazilir (olculdu: 14 ikon)"
    )


def test_manifest_sutun_hesabi_esigi_kullaniyor() -> None:
    """Sabit tanimli olmasi YETMEZ; manifest hesabi onu KULLANMALI.

    Sabitin tanimlanip kullanilmamasi tam da bir kez yasanan sessiz kayiptir.
    """
    kaynak = (PIPELINE / "sayfa_kirp_zkitap.py").read_text(encoding="utf-8")
    assert (
        "x < IKON_SUTUN_ESIGI" in kaynak
    ), "manifest sol/sag hesabi IKON_SUTUN_ESIGI kullanmiyor"
    assert (
        "x < OLUK_SAG" not in kaynak
    ), "manifest hesabi hala kirpma sinirini (OLUK_SAG) kullaniyor"


def test_ust_esik_ile_cevap_bandi_arasinda_gercek_sorular_kaliyor() -> None:
    """Soru ikonlari icin gecerli y araligi anlamli genislikte olmali.

    y<60 -> soru olmayan ikonlar (ust bant / 'Sinavda Bu Tarz Sorular' basligi).
    y>=880 -> cevap anahtari satirinin yanindaki ikon.
    Aradaki bolge gercek sorularin bolgesi; olculen en ustteki gercek soru
    ikonu y~100 idi, en asagidaki ~794.
    """
    assert kirp.IKON_MIN_Y < 100, "esik gercek sorulari (y~100) elerdi"
    assert kirp.CEVAP_ARAMA[0] > 794, "esik gercek sorulari (y~794) elerdi"
    assert kirp.CEVAP_ARAMA[0] - kirp.IKON_MIN_Y > 700


def test_soru_esigi_gozlemlenen_dagilimla_tutarli() -> None:
    """Gercek soru sayfalari 3-7 ikon tasiyor; hicbir sayfada 2 yok.

    Esik 2 -> bolum kapaklarindaki tek basibos ikon soru sayilmaz, ama
    gercek bir sayfa da elenmez.
    """
    assert kirp.SORU_ESIGI == 2
    assert kirp.SORU_ESIGI <= 3, "esik 3'un uzerine cikarsa gercek sayfalar elenir"


def test_limit_ile_manifest_yazilmaz() -> None:
    """--limit verildiginde manifest YAZILMAMALI.

    Gercek vaka: manifest 4 kez ilk 8 satira dustu. Bozulma "yarim yazma" gibi
    gorunmuyordu -- dosya iyi bicimli, guncel baslikli ve eksiksiz yaziliyordu;
    sadece GIRDI alt kumeydi. Bu yuzden once atomiklik suclandi (ki o da gercek
    bir kusurdu ama bu degildi). Ayirt edici kanit: kirpik dosyanin basligi
    GUNCEL surumun basligiydi ve tam olarak ilk N sayfayi iceriyordu.
    """
    kaynak = (PIPELINE / "sayfa_kirp_zkitap.py").read_text(encoding="utf-8")
    manifest_blok = kaynak[kaynak.index("def _manifest_asamasi(") :]
    manifest_blok = manifest_blok[: manifest_blok.index("def _ozet_yaz(")]

    assert (
        "args.limit" in manifest_blok
    ), "--limit korumasi yok: kirpik girdiyle tam manifest ezilir"
    yaz = manifest_blok.index("_manifest_yaz(")
    kontrol = manifest_blok.index("args.limit")
    assert kontrol < yaz, "--limit kontrolu _manifest_yaz cagrisindan SONRA geliyor"
