"""345 2025 TYT-AYT Geometri Soru Bankasi ithal hatti -- koruma testleri.

Bu dosya DORT sinif seyi dogrular:

1. SOZLESME: kaynak adi ASCII ve KAYNAK_KAYITLARI'nda kayitli.
2. HESAP: soru_hash formulu pilot_500p ile birebir; id = uuid5(hash).
3. KONU BLOKLARI: bloklar ayni cilt icinde ORTUSMEZ ve ARTAN sirada
   durur; her blogun adi KONU_HARITASI'nda karsiligi olan bir banddir;
   harita yalnizca var olan agac kodlarini (GEO-U<n> ya da GEO-U<n>-...)
   gosterir. Bu, "sayfa hangi konuya ait" sorusunun tek dogruluk kaynagi
   oldugu icin en kritik denetim.
4. KILITLENME KORUMASI: SAYISAL_SIK deseni geri izlemeye girmiyor.
   MUTASYON KARSILIGI var -- eski (ic ice nicelenmis) desen ayni girdide
   sureyi patlatir; test bunu ayrica olcer.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import unicodedata
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from scripts.kitap import geo345_ithal as geo  # noqa: E402
from scripts.kitap import metin_olcum as olcum  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    kaynak_adi_dogrula,
)

# Eski (bozuk) desen -- YALNIZCA mutasyon olcumu icin burada duruyor.
_ESKI_SAYISAL = re.compile("^[\\s\\d.,/+\\-x*^()−√·]+(?:[a-zA-Z°%/²³]{0,6}\\s*)*$")
# PR #266'da olculen kilitleyici girdi; desen iki dosyada da ayni.
_PATLATAN = "2, karbondioksit olabilir."

_KOD_DESENI = re.compile(r"^GEO-U[1-9]\d*(-[A-Z0-9-]+)?$")

_TEMEL = {
    "question_text": "ABC ucgeninde x kac derecedir?",
    "a": "1",
    "b": "2",
    "c": "3",
    "d": "4",
    "e": "5",
    "correct_answer": "A",
    "id": "x",
    "cilt": "c1",
    "sayfa": 100,
    "sutun": "sol",
    "soru_no": 1,
    "kutu": [10, 20, 300, 400],
    "sekil_var": True,
    "sekil_aciklama": "ABC ucgeni",
}


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(geo.KAYNAK_ADI, kayitli_olmali=True)
    assert KAYNAK_KAYITLARI[geo.KAYNAK_ADI]["onek"] == "GEO345"
    assert (
        KAYNAK_KAYITLARI[geo.KAYNAK_ADI]["ithal_araci"]
        == "scripts/kitap/geo345_ithal.py"
    )


def test_kaynak_dosyalari_ascii() -> None:
    """Ev kurali: ithal/kirp kaynaklari ASCII kalir (Turkce \\u kacisiyla)."""
    for ad in ("geo345_ithal.py", "geo345_kirp.py"):
        ham = (KOK / "scripts" / "kitap" / ad).read_bytes()
        disi = sorted({b for b in ham if b > 126})
        assert not disi, f"{ad} ASCII disi bayt tasiyor: {disi[:8]}"


def test_soru_hash_pilot_formuluyle_ayni() -> None:
    metin = "Açıortayın uzunluğu kaç cm'dir?"
    sec = {"A": "3", "B": "4", "C": "5", "D": "6", "E": "7"}
    beklenen = hashlib.md5(  # nosec B324
        "|".join(
            [unicodedata.normalize("NFC", metin).strip().lower()]
            + [unicodedata.normalize("NFC", sec[h]).strip() for h in "ABCDE"]
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    assert geo.soru_hash(metin, sec) == beklenen


def test_id_hashten_tureiyor() -> None:
    k = geo.kayit_uret(dict(_TEMEL))
    assert k["id"] == str(uuid.uuid5(uuid.NAMESPACE_OID, k["soru_hash"]))
    assert k["soru_hash"] == geo.soru_hash(
        _TEMEL["question_text"], {h: _TEMEL[h.lower()] for h in "ABCDE"}
    )


def test_sikkin_turkce_karakteri_duzlestirilmiyor() -> None:
    """Hash girdi metnini ASCII'ye indirmez -- 'n\\u0131n' ile 'nin' ayri."""
    a = geo.soru_hash("kenarın uzunluğu", dict.fromkeys("ABCDE", "x"))
    b = geo.soru_hash("kenarin uzunlugu", dict.fromkeys("ABCDE", "x"))
    assert a != b


# --- konu bloklari -------------------------------------------------------


def test_bloklar_ortusmuyor_ve_artan() -> None:
    for cilt, bloklar in geo.KONU_BLOKLARI.items():
        onceki_son = 0
        for bas, son, ad in bloklar:
            assert bas <= son, f"{cilt}/{ad}: bas > son"
            assert bas > onceki_son, f"{cilt}/{ad}: onceki blokla ortusuyor"
            onceki_son = son


def test_her_blok_adi_haritada_var() -> None:
    adlar = {ad for bloklar in geo.KONU_BLOKLARI.values() for _, _, ad in bloklar}
    assert adlar == set(geo.KONU_HARITASI), (
        "blok adlari ile KONU_HARITASI anahtarlari birebir ayni olmali; "
        f"fark: {adlar ^ set(geo.KONU_HARITASI)}"
    )


def test_harita_kodlari_gecerli_desende() -> None:
    for ad, (kod, duzey) in geo.KONU_HARITASI.items():
        assert _KOD_DESENI.match(kod), f"{ad}: kod desene uymuyor ({kod})"
        assert duzey in ("yaprak", "unite"), f"{ad}: bilinmeyen duzey {duzey}"
        # unite kodunda tire sonrasi ek parca YOK; yaprakta VAR.
        ek_var = kod.count("-") > 1
        assert ek_var == (
            duzey == "yaprak"
        ), f"{ad}: duzey {duzey} ile kod bicimi {kod} celisiyor"


def test_konu_bandi_sinirlarda_dogru() -> None:
    bas, son, ad = geo.KONU_BLOKLARI["c1"][0]
    assert geo.konu_bandi("c1", bas) == ad
    assert geo.konu_bandi("c1", son) == ad
    assert geo.konu_bandi("c1", bas - 1) != ad
    assert geo.konu_bandi("c1", son + 1) != ad
    assert geo.konu_bandi("c3", bas) is None


def test_kayit_konuyu_bloktan_aliyor() -> None:
    # c1/100 -> BENZERLIK blogu (94-141), bir YAPRAGA baglanir.
    k = geo.kayit_uret({**_TEMEL, "sayfa": 100})
    pm = k["pipeline_metadata"]
    assert pm["konu_bandi"] == "BENZERLİK"
    assert k["konu_kodu"] == "GEO-U1-BENZERLIK"
    assert pm["konu_eslesme_duzeyi"] == "yaprak"
    assert pm["konu_kaynagi"] == "sayfa_baslik_bandi"
    assert k["question_image_url"] == "/static/crops/GEO345/x.png"
    assert k["source_page"] == 100
    assert pm["gorsel_kaynagi"] == "tam_soru_kirpimi"
    assert pm["kirpim_kutusu"] == _TEMEL["kutu"]


def test_birlesim_konusu_uniteye_baglanir() -> None:
    """Var olan yapraklarla ortusen sahte yaprak uydurulmaz."""
    # c1/360 -> DIKDORTGEN - KARE (353-414): GEO-U2-DIKDORTGEN +
    # GEO-U2-KARE birlesimi oldugu icin UNITE'ye baglanir.
    k = geo.kayit_uret({**_TEMEL, "sayfa": 360})
    assert k["konu_kodu"] == "GEO-U2"
    assert k["pipeline_metadata"]["konu_eslesme_duzeyi"] == "unite"


def test_osym_damgasi_bu_kitapta_hic_vurulmuyor() -> None:
    """Kitabin OSYM sorulari Mikro ithalinde duruyor; burada damga yok."""
    k = geo.kayit_uret(dict(_TEMEL))
    assert k["osym_year"] is None
    assert k["osym_format_compliant"] is False


def test_sinav_turu_olculmedigi_isaretli() -> None:
    k = geo.kayit_uret(dict(_TEMEL))
    assert (
        k["pipeline_metadata"]["sinav_turu_kaynagi"]
        == "olculmedi_kitap_TYT-AYT_karisik"
    )


# --- bayraklar ve on kontrol --------------------------------------------


def test_bayraklar_veri_setinin_isaretlerini_tasiyor() -> None:
    temiz = geo.kayit_uret(dict(_TEMEL))
    assert temiz["pipeline_metadata"]["bayraklar"] == []

    bos = geo.kayit_uret({**_TEMEL, "b": "", "sik_bos": True})
    assert "sik_bos" in bos["pipeline_metadata"]["bayraklar"]

    tekrar = geo.kayit_uret({**_TEMEL, "b": "1", "sik_tekrar": True})
    assert "sik_tekrar" in tekrar["pipeline_metadata"]["bayraklar"]

    supheli = geo.kayit_uret({**_TEMEL, "okuma_supheli": True})
    assert "okuma_supheli" in supheli["pipeline_metadata"]["bayraklar"]

    okunamaz = geo.kayit_uret({**_TEMEL, "c": "3 [okunamadi]"})
    assert "okunamadi" in okunamaz["pipeline_metadata"]["bayraklar"]


def test_on_kontrol_bos_anahtar_sikkini_yakaliyor() -> None:
    k = geo.kayit_uret({**_TEMEL, "b": "  ", "correct_answer": "B"})
    hata = geo._on_kontrol([k])
    assert any("sikki bos" in h for h in hata)


def test_on_kontrol_bloksuz_sayfayi_yakaliyor() -> None:
    """Konu blogu disinda kalan sayfa sessizce koke dusmez, ITHALI DURDURUR."""
    k = geo.kayit_uret({**_TEMEL, "sayfa": 1})
    assert k["pipeline_metadata"]["konu_bandi"] is None
    hata = geo._on_kontrol([k])
    assert any("konu blogunda degil" in h for h in hata)


# --- veri seti varsa: tam kapsama ---------------------------------------


def test_veri_setindeki_her_soru_bir_blokta() -> None:
    """Veri seti git disinda (.gitignore veriseti/); yoksa test atlanir."""
    yol = KOK.parent / geo.VARSAYILAN_VERI
    if not yol.is_file():
        pytest.skip(f"veri seti yok: {yol}")
    veri = json.loads(yol.read_text(encoding="utf-8"))
    disarida = [
        (r["cilt"], r["sayfa"])
        for r in veri
        if geo.konu_bandi(r["cilt"], int(r["sayfa"])) is None
    ]
    assert not disarida, f"{len(disarida)} soru blok disinda: {disarida[:5]}"


# --- kilitlenme korumasi -------------------------------------------------


@pytest.mark.parametrize("sik", ["12", "3,5 cm", "45°", "2√3", "1/2", "100 m²"])
def test_sayisal_sik_kabul(sik: str) -> None:
    assert olcum.SAYISAL_SIK.match(sik)


@pytest.mark.parametrize(
    "sik",
    [_PATLATAN, "Yalnız I", "I ve II", "[şekil seçeneği]", "[okunamadi]"],
)
def test_sayisal_sik_reddediyor(sik: str) -> None:
    assert not olcum.SAYISAL_SIK.match(sik)


def test_sayisal_sik_geri_izlemeye_girmiyor() -> None:
    t = time.perf_counter()
    olcum.SAYISAL_SIK.match(_PATLATAN)
    sure = time.perf_counter() - t
    assert sure < 0.05, f"desen {sure:.3f}s surdu -- geri izleme geri geldi"


def test_mutasyon_eski_desen_gercekten_patliyor() -> None:
    """Koruma bos degil: eski desen AYNI girdide kat kat yavas.

    Olcut mutlak sure degil ORAN -- makineden bagimsiz olsun diye.
    DIKKAT: dizginin SONUNDAKI NOKTA sart (PR #266'da olculdu).
    """
    t = time.perf_counter()
    olcum.SAYISAL_SIK.match(_PATLATAN)
    yeni_sure = max(time.perf_counter() - t, 1e-7)

    t = time.perf_counter()
    _ESKI_SAYISAL.match(_PATLATAN)
    eski_sure = time.perf_counter() - t

    assert eski_sure > yeni_sure * 50, (
        "eski desen bu girdide yavaslamadi -- mutasyon testi bir sey "
        f"kollamiyor olabilir (eski {eski_sure:.6f}s, yeni {yeni_sure:.6f}s)"
    )


def test_bloom_dar_kural() -> None:
    sayisal = {h: str(i) for i, h in enumerate("ABCDE", 1)}
    metin_sayi = "Bu uzunluğun değeri ne kadardır?"
    seviye, ad, kaynak = geo.bloom_belirle(metin_sayi, sayisal)
    assert (seviye, ad) == (3, "application")
    assert kaynak.startswith("kural")

    metinsel = dict.fromkeys("ABCDE", "Yalnız I")
    seviye, ad, kaynak = geo.bloom_belirle(metin_sayi, metinsel)
    assert (seviye, ad) == (2, "comprehension")
    assert kaynak.startswith("varsayilan")
