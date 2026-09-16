"""345 2025 TYT Biyoloji ithal hatti -- koruma testleri.

Bu dosya BES sinif seyi dogrular:

1. SOZLESME: kaynak adi ASCII ve KAYNAK_KAYITLARI'nda kayitli; kaynak
   dosyalari ASCII kaliyor.
2. HESAP: soru_hash formulu pilot_500p ile birebir; id = uuid5(hash).
3. KONU BLOKLARI: bloklar ortusmez ve artan; her blok 0022'nin kurdugu bir
   BIO-T koduna karsilik gelir; blok kodlari BIO-U* (AYT) ile CAKISMAZ.
4. ALEL DUYARLILIGI: siklar harf buyukluguyle ayrilan genetik sorulari
   "sik tekrar" sayilmaz. MUTASYON KARSILIGI var: .lower() ile kiyaslayan
   eski kural ayni girdide yanlis pozitif uretir, test bunu ayrica olcer.
5. KILITLENME KORUMASI: SAYISAL_SIK deseni geri izlemeye girmiyor.
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

from scripts.kitap import biyo345tyt_derle as derle  # noqa: E402
from scripts.kitap import biyo345tyt_ithal as btyt  # noqa: E402
from scripts.kitap import metin_olcum as olcum  # noqa: E402
from scripts.kitap.kaynak_sozlesmesi import (  # noqa: E402
    KAYNAK_KAYITLARI,
    kaynak_adi_dogrula,
)

_ESKI_SAYISAL = re.compile("^[\\s\\d.,/+\\-x*^()−√·]+(?:[a-zA-Z°%/²³]{0,6}\\s*)*$")
_PATLATAN = "2, karbondioksit olabilir."

# Kitaptan gelen GERCEK sik kumesi: yalnizca harf buyukluguyle ayrisiyor
# (s0174 sag #5, Mendel genetigi). Alel gosteriminde 'A' baskin, 'a' cekinik.
_ALEL_SIKLARI = {"A": "aBCD", "B": "ABDd", "C": "ABCD", "D": "aBcd", "E": "ABcd"}

_TEMEL = {
    "question_text": "Hucre zarindan madde gecisi ile ilgili ne soylenebilir?",
    "a": "Difuzyon",
    "b": "Osmoz",
    "c": "Aktif tasima",
    "d": "Endositoz",
    "e": "Ekzositoz",
    "correct_answer": "A",
    "sayfa": 90,
    "basili_sayfa": 90,
    "sutun": "sol",
    "pozisyon": 1,
    "soru_no": 1,
    "konu_kodu": "BIO-T7",
    "konu_bandi": "HUCRE ZARINDAN MADDE GECISLERI",
    "sayfada_bant_var": True,
    "test_turu": "Karma Sorular",
    "test_no": 1,
    "sekil_var": False,
    "cikmis": False,
    "sinav_yili": None,
    "zorluk_tahmini": "MEDIUM",
    "cevap_kaynagi": "cevap_seridi",
    "sutun_gorseli": "sayfa_0090_sol.png",
    "cikarim_guveni": 0.94,
}


def test_kaynak_adi_sozlesmeye_uyuyor() -> None:
    kaynak_adi_dogrula(btyt.KAYNAK_ADI, kayitli_olmali=True)
    assert KAYNAK_KAYITLARI[btyt.KAYNAK_ADI]["onek"] == "BIYO345TYT"
    assert (
        KAYNAK_KAYITLARI[btyt.KAYNAK_ADI]["ithal_araci"]
        == "scripts/kitap/biyo345tyt_ithal.py"
    )


def test_ayt_kitabiyla_ayni_kaynak_adi_degil() -> None:
    """TYT ve AYT biyoloji kitaplari AYRI kaynaklardir; ad cakismasi olmamali."""
    assert btyt.KAYNAK_ADI != "345 2025 AYT Biyoloji Soru Bankasi"
    assert btyt.KAYNAK_ADI in KAYNAK_KAYITLARI


def test_kaynak_dosyalari_ascii() -> None:
    """Ev kurali: ithal/derle kaynaklari ASCII kalir (Turkce \\u kacisiyla)."""
    for ad in ("biyo345tyt_ithal.py", "biyo345tyt_derle.py"):
        ham = (KOK / "scripts" / "kitap" / ad).read_bytes()
        disi = sorted({b for b in ham if b > 126})
        assert not disi, f"{ad} ASCII disi bayt tasiyor: {disi[:8]}"


def test_soru_hash_pilot_formuluyle_ayni() -> None:
    metin = "Enzimlerin çalışmasını ne etkiler?"
    sec = {"A": "pH", "B": "Sıcaklık", "C": "Substrat", "D": "Su", "E": "Tuz"}
    beklenen = hashlib.md5(  # nosec B324
        "|".join(
            [unicodedata.normalize("NFC", metin).strip().lower()]
            + [unicodedata.normalize("NFC", sec[h]).strip() for h in "ABCDE"]
        ).encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()
    assert btyt.soru_hash(metin, sec) == beklenen
    # derle betigi AYNI formulu kullanmali; yoksa veri seti ile ithal ayrisir
    assert derle.soru_hash(metin, sec) == beklenen


def test_id_hashten_tureiyor() -> None:
    k = btyt.kayit_uret(dict(_TEMEL))
    assert k["id"] == str(uuid.uuid5(uuid.NAMESPACE_OID, k["soru_hash"]))


# --- konu bloklari ------------------------------------------------------


def test_bloklar_ortusmuyor_ve_artan() -> None:
    onceki_son = 0
    for bas, son, kod in derle.BLOKLAR:
        assert bas <= son, f"{kod}: bas > son"
        assert bas > onceki_son, f"{kod}: onceki blokla ortusuyor"
        onceki_son = son


def test_blok_kodlari_0022_desenine_uyuyor() -> None:
    kodlar = [k for _b, _s, k in derle.BLOKLAR]
    assert len(kodlar) == len(set(kodlar)) == 14
    for kod in kodlar:
        assert re.fullmatch(r"BIO-T([1-9]|1[0-4])", kod), kod
        assert kod.startswith(btyt.KOD_ONEKI)


def test_blok_kodlari_ayt_uniteleriyle_cakismiyor() -> None:
    """BIO-U* (0021, AYT) ile BIO-T* (0022, TYT) ayri olmali.

    Bu, agaci bozmamanin tek satirlik guvencesi: LIKE 'BIO-T%' deseni
    BIO-U* unitelerini KAPSAMAMALI.
    """
    for _b, _s, kod in derle.BLOKLAR:
        assert not kod.startswith("BIO-U")
    assert not "BIO-U1".startswith(btyt.KOD_ONEKI)
    assert not "BIO-OSYM-GENEL".startswith(btyt.KOD_ONEKI)
    assert not btyt.BIO_KOK_KODU.startswith(btyt.KOD_ONEKI)


def test_blok_kodu_sinirlarda_dogru() -> None:
    bas, son, kod = derle.BLOKLAR[0]
    assert derle.blok_kodu(bas) == kod
    assert derle.blok_kodu(son) == kod
    assert derle.blok_kodu(bas - 1) != kod
    assert derle.blok_kodu(son + 1) != kod


def test_kanon_bant_buyuk_kucuk_harfi_katliyor() -> None:
    """'ESEYLI ve ESEYSIZ UREME' ile 'ESEYLI VE ESEYSIZ UREME' ayni bant."""
    a = derle.kanon_bant("EŞEYLİ VE EŞEYSİZ ÜREME")
    b = derle.kanon_bant("EŞEYLİ ve EŞEYSİZ ÜREME")
    assert a == b
    assert derle.kanon_bant(None) is None
    assert derle.kanon_bant("   ") is None


# --- bayraklar ----------------------------------------------------------


def test_alel_siklari_tekrar_sayilmiyor() -> None:
    """Genetik sikleri yalnizca harf buyukluguyle ayrilir -- tekrar DEGIL."""
    r = {**_TEMEL, **{h.lower(): v for h, v in _ALEL_SIKLARI.items()}}
    bayrak = btyt.kayit_uret(r)["pipeline_metadata"]["bayraklar"]
    assert "sik_tekrar" not in bayrak


def test_mutasyon_lower_ile_kiyas_yanlis_pozitif_uretirdi() -> None:
    """Koruma bos degil: eski (.lower()'li) kural AYNI girdide patlar.

    Olculdu: veri setinin tamaminda lower() 9 soruyu "sik tekrar" sayiyor,
    harf buyukluguna duyarli kiyas 0 sayiyor.
    """
    sik = dict(_ALEL_SIKLARI)
    duyarli = len({v.strip() for v in sik.values()})
    duyarsiz = len({v.strip().lower() for v in sik.values()})
    assert duyarli == 5, "duyarli kiyasta bes sik da farkli olmali"
    assert duyarsiz < 5, (
        "eski kural bu girdide yanlis pozitif uretmiyor -- mutasyon testi "
        "bir sey kollamiyor olabilir"
    )


def test_gorsel_olmayan_sekilli_soru_isaretleniyor() -> None:
    """Bu kitapta soru kirpimi yok; sekilli sorular acikca bayraklanir."""
    k = btyt.kayit_uret({**_TEMEL, "sekil_var": True})
    pm = k["pipeline_metadata"]
    assert "gorsel_yok_sekilli" in pm["bayraklar"]
    assert k["question_image_url"] is None
    assert pm["gorsel_kaynagi"] == "yok_soru_kirpimi_uretilmedi"
    assert pm["sutun_gorseli"] == "sayfa_0090_sol.png"


def test_bantsiz_sayfa_konusu_komsudan_isaretleniyor() -> None:
    bantli = btyt.kayit_uret(dict(_TEMEL))["pipeline_metadata"]
    assert bantli["konu_kaynagi"] == "sayfa_baslik_bandi"
    assert "konu_komsudan" not in bantli["bayraklar"]

    bantsiz = btyt.kayit_uret({**_TEMEL, "sayfada_bant_var": False})
    pm = bantsiz["pipeline_metadata"]
    assert pm["konu_kaynagi"] == "blok_icinde_komsu_sayfadan"
    assert "konu_komsudan" in pm["bayraklar"]


def test_osym_damgasi_yalniz_cikmis_soruda() -> None:
    yayinevi = btyt.kayit_uret(dict(_TEMEL))
    assert yayinevi["osym_year"] is None
    assert yayinevi["osym_format_compliant"] is False

    cikmis = btyt.kayit_uret({**_TEMEL, "cikmis": True, "sinav_yili": 2023})
    assert cikmis["osym_year"] == 2023
    assert cikmis["osym_format_compliant"] is True

    # cikmis isaretli ama yili yoksa DAMGA VURULMAZ
    yilsiz = btyt.kayit_uret({**_TEMEL, "cikmis": True, "sinav_yili": None})
    assert yilsiz["osym_year"] is None
    assert yilsiz["osym_format_compliant"] is False
    assert yilsiz["pipeline_metadata"]["cikmis_soru"] is True


def test_unite_duzeyi_isaretli() -> None:
    pm = btyt.kayit_uret(dict(_TEMEL))["pipeline_metadata"]
    assert pm["konu_eslesme_duzeyi"] == "unite"
    assert pm["ithal_araci"] == "scripts/kitap/biyo345tyt_ithal.py"


# --- on kontrol ---------------------------------------------------------


def test_on_kontrol_bos_anahtar_sikkini_yakaliyor() -> None:
    k = btyt.kayit_uret({**_TEMEL, "b": "  ", "correct_answer": "B"})
    hata = btyt._on_kontrol([k])
    assert any("sikki bos" in h for h in hata)


def test_on_kontrol_yanlis_konu_kodunu_yakaliyor() -> None:
    """AYT unitesine (BIO-U*) baglamak sessizce gecmemeli."""
    k = btyt.kayit_uret({**_TEMEL, "konu_kodu": "BIO-U1"})
    hata = btyt._on_kontrol([k])
    assert any("BIO-T" in h for h in hata)


def test_on_kontrol_temiz_kayitta_susuyor() -> None:
    assert btyt._on_kontrol([btyt.kayit_uret(dict(_TEMEL))]) == []


# --- veri seti varsa: tam kapsama ---------------------------------------


def test_veri_setindeki_her_soru_bir_blokta() -> None:
    """Veri seti git disinda (.gitignore veriseti/); yoksa test atlanir."""
    yol = KOK.parent / btyt.VARSAYILAN_VERI
    if not yol.is_file():
        pytest.skip(f"veri seti yok: {yol}")
    veri = json.loads(yol.read_text(encoding="utf-8"))
    assert len(veri) == 1024
    disarida = [r["sayfa"] for r in veri if not derle.blok_kodu(int(r["sayfa"]))]
    assert not disarida, f"{len(disarida)} soru blok disinda: {disarida[:5]}"
    kodlar = {r["konu_kodu"] for r in veri}
    assert kodlar == {k for _b, _s, k in derle.BLOKLAR}


def test_veri_setinde_harf_duyarli_sik_tekrari_yok() -> None:
    yol = KOK.parent / btyt.VARSAYILAN_VERI
    if not yol.is_file():
        pytest.skip(f"veri seti yok: {yol}")
    veri = json.loads(yol.read_text(encoding="utf-8"))
    tekrar = [
        r["sayfa"]
        for r in veri
        if len({(r[h.lower()] or "").strip() for h in "ABCDE"}) < 5
    ]
    assert not tekrar, f"harf duyarli sik tekrari: {tekrar[:5]}"


# --- kilitlenme korumasi ------------------------------------------------


@pytest.mark.parametrize("sik", ["12", "3,5 cm", "45°", "2√3", "1/2", "100 m²"])
def test_sayisal_sik_kabul(sik: str) -> None:
    assert olcum.SAYISAL_SIK.match(sik)


@pytest.mark.parametrize("sik", [_PATLATAN, "Yalnız I", "I ve II", "Difüzyon", "aBCD"])
def test_sayisal_sik_reddediyor(sik: str) -> None:
    assert not olcum.SAYISAL_SIK.match(sik)


def test_sayisal_sik_geri_izlemeye_girmiyor() -> None:
    t = time.perf_counter()
    olcum.SAYISAL_SIK.match(_PATLATAN)
    sure = time.perf_counter() - t
    assert sure < 0.05, f"desen {sure:.3f}s surdu -- geri izleme geri geldi"


def test_mutasyon_eski_desen_gercekten_patliyor() -> None:
    """Olcut mutlak sure degil ORAN -- makineden bagimsiz olsun diye."""
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
