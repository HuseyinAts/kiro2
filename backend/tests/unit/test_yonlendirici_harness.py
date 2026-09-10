"""Yonlendirici benchmark harness'inin bekcileri (sentetik veri, veri seti gerekmez).

Harness'in uc iddiasi test edilir:
  1. Ozellik cikarici okuma-1 metninden dogru sayar (ondalik, alt simge, rakam,
     sayisal sik, bayrak).
  2. 18/18 kapisi YALNIZCA tam recall'da ve %100'den kucuk yonlendirmede gecer;
     bir eksik = kaldi, herkesi gondermek = kaldi.
  3. LOO, esigi 18'den ogrenen adayin sinir vakasini duSURUR (17/18) -- yani
     orneklem-ici 18/18'i iyimser gosteren mekanizma gercekten calisiyor; bir
     adim pay bunu kurtarir.
"""

from __future__ import annotations

from scripts.kitap.neofizik_yonlendirici_harness import (
    Kayit,
    _degerlendir,
    _payli,
    _secim,
    ozellik_cikar,
    tek_aday_puanla,
    varlik_kurali_puanla,
)


def _kayit(kid: str, hakem: bool = False, **ozellik: float) -> Kayit:
    k = Kayit(
        id=kid,
        sayfa=1,
        sira=int(kid[1:]),
        metin="",
        secenekler={},
        bayraklar=[],
        kutu=None,
    )
    k.ozellik = dict(ozellik)
    k.etiket = {
        "hakem": hakem,
        "okuma1_yanlis": hakem,
        "dusuk_uyum": hakem,
        "cozum_uyusmaz": False,
    }
    return k


# --- 1. ozellik cikarici -------------------------------------------------------


def test_ozellik_cikar_ondalik_ve_alt_simge_sayar():
    o = ozellik_cikar(
        "Hiz 0,5 m/s ve sure 2.5 s; kuvvet F\u2081 ile F\u2082 dengede.",
        {"A": "10 N", "B": "20 N", "C": "Yalniz I", "D": "0,25", "E": "I ve II"},
        ["gorsel", "tablo_sik"],
        [0, 0, 100, 50],
    )
    assert o["ondalik_sayisi"] == 3  # 0,5  2.5  0,25
    assert o["alt_ust_simge_sayisi"] == 2  # F1 F2 alt simgeleri
    assert o["rakam_sayisi"] == 13
    assert o["sayisal_sik_sayisi"] == 3  # 10 N, 20 N, 0,25
    assert o["bayrak_gorsel"] == 1.0 and o["bayrak_tablo_sik"] == 1.0
    assert o["bayrak_formul"] == 0.0
    assert o["kutu_alani"] == 5000.0


def test_ozellik_cikar_bos_metin_bolme_hatasi_vermez():
    o = ozellik_cikar("", {}, [], None)
    assert o["rakam_yogunlugu"] == 0.0
    assert "kutu_alani" not in o


# --- 2. 18/18 kapisi -----------------------------------------------------------


def test_kapi_yalnizca_tam_recallda_ve_yuzde_yuzden_kucukte_gecer():
    kayitlar = [_kayit(f"q{i}", hakem=(i < 3), x=float(i)) for i in range(10)]
    hepsi = {k.id for k in kayitlar}
    tam, _, gecti = _degerlendir({"q0", "q1", "q2", "q5"}, kayitlar)
    assert tam["hakem"] == "3/3" and gecti
    eksik, _, gecti2 = _degerlendir({"q0", "q1", "q5"}, kayitlar)
    assert eksik["hakem"] == "2/3" and not gecti2
    _, oran, gecti3 = _degerlendir(hepsi, kayitlar)
    assert oran == 1.0 and not gecti3  # herkesi gondermek yonlendirme degil


def test_secim_ozelligi_olmayan_kaydi_yonlendirmez():
    kayitlar = [_kayit("q0", x=1.0), _kayit("q1")]  # q1'de x yok (kismi kapsam)
    assert _secim(kayitlar, "x", ">=", 1.0) == {"q0"}


# --- 3. LOO ve pay ---------------------------------------------------------------


def test_payli_bir_populasyon_adimi_gevsetir():
    pop = [1.0, 2.0, 3.0, 5.0]
    assert _payli(pop, 3.0, ">=") == 2.0
    assert _payli(pop, 3.0, "<=") == 5.0
    assert _payli(pop, 1.0, ">=") == 1.0  # altinda deger yok -> degismez


def test_loo_sinir_vakasini_dusurur_pay_kurtarir():
    # hakemli x degerleri {2, 5, 7}; populasyonda 1 ve 3 de var.
    # siki esik = 2 -> 3/3 orneklem-ici; LOO'da 2 dusunce esik 5 olur, 2 kacar -> 2/3.
    # payli esik = 1 -> LOO'da esik 5'in bir adim alti 3'e gevser, 2 yine kacar -> 2/3;
    # ama populasyonda 4 olsaydi kurtarirdi -- pay bir ADIM, garanti degil. Bu test
    # tam olarak bu davranisi sabitler.
    kayitlar = [
        _kayit("q0", hakem=True, x=2.0),
        _kayit("q1", hakem=True, x=5.0),
        _kayit("q2", hakem=True, x=7.0),
        _kayit("q3", x=1.0),
        _kayit("q4", x=3.0),
        _kayit("q5", x=0.0),
    ]
    sonuclar = {(s.aday, s.yon): s for s in tek_aday_puanla(kayitlar, "x")}
    siki = sonuclar[("x", ">=")]
    assert siki.recall["hakem"] == "3/3" and siki.gecti
    assert siki.loo == (2, 3)
    payli = sonuclar[("x (payli)", ">=")]
    assert payli.esik == 1.0 and payli.gecti
    assert payli.loo == (2, 3)


def test_loo_bagli_deger_varsa_tam_kalir():
    # iki hakemli ayni minimumda (2, 2, 7): birini dusurunce esik hala 2 -> 3/3
    kayitlar = [
        _kayit("q0", hakem=True, x=2.0),
        _kayit("q1", hakem=True, x=2.0),
        _kayit("q2", hakem=True, x=7.0),
        _kayit("q3", x=1.0),
    ]
    siki = next(
        s for s in tek_aday_puanla(kayitlar, "x") if s.aday == "x" and s.yon == ">="
    )
    assert siki.loo == (3, 3)


def test_ikili_ozellik_yalnizca_varlik_satiri_uretir():
    kayitlar = [
        _kayit("q0", hakem=True, b=1.0),
        _kayit("q1", b=0.0),
        _kayit("q2", b=1.0),
    ]
    sonuclar = tek_aday_puanla(kayitlar, "b")
    assert (
        len(sonuclar) == 1
        and sonuclar[0].esik == 1.0
        and sonuclar[0].recall["hakem"] == "1/1"
    )


def test_varlik_kurali_birlesimi_iki_mekanizmayi_kapsar():
    # hakem vakalarinin biri yalniz 'a', digeri yalniz 'b' tasiyor: tekli kalir, birlesim gecer
    kayitlar = [
        _kayit("q0", hakem=True, a=1.0, b=0.0),
        _kayit("q1", hakem=True, a=0.0, b=1.0),
        _kayit("q2", a=0.0, b=0.0),
        _kayit("q3", a=0.0, b=0.0),
    ]
    sonuclar = {s.aday: s for s in varlik_kurali_puanla(kayitlar, ["a", "b"], 2)}
    assert not sonuclar["a>=1"].gecti and not sonuclar["b>=1"].gecti
    assert sonuclar["a>=1 U b>=1"].gecti
    assert sonuclar["a>=1 U b>=1"].yonlendirme_orani == 0.5
