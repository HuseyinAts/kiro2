"""IRTService'i GERCEK modele karsi sinar (stub'a karsi DEGIL).

NEDEN VAR
---------
`services/irt_service.py` uzun sure `models.irt_morfoloji`nin SUNMADIGI bir
API'ye gore yazilmisti: `IRTParametreleri.hesapla_probability` (gercek ad
`olasilik_hesapla`), `.discrimination` / `.difficulty` (gercek ad
`a_parametresi` / `b_parametresi`), ve profilde var olmayan 11 alan.
Olculdu: 19 kirik erisim, sifir ortusme.

Sonuc uretimde GORUNMUYORDU, cunku `hesapla_cevap_olasiligi` govdesi genis
bir `except Exception` ile sarili ve hata yolunda `return 0.5` var. Yani her
theta icin sabit 0.5 donuyordu -- IRT egrisi tamamen cokmustu ve yalnizca
log okunursa fark ediliyordu.

Mevcut test paketi bunu yakalayamadi: `test_coverage_final_50.py` gercek
modeli, o yanlis adlari TASIYAN sahte bir sinifla degistiriyor. Yesil, ama
var olmayan bir modele karsi yesil.

Bu dosya stub KURMAZ. Gercek Pydantic modellerini import eder ve servisin
ciktisinin theta ile gercekten degistigini olcer. Sabit 0.5'e dusen her
regresyon burada duser.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from models.irt_morfoloji import (  # noqa: E402
    IRTParametreleri,
    IRTParametreTipi,
    OgrenciMorfolojiProfili,
)
from services.irt_service import IRTService  # noqa: E402

THETALAR = (-2.0, -1.0, 0.0, 1.0, 2.0)


def _parametreler() -> IRTParametreleri:
    return IRTParametreleri(
        a_parametresi=1.8,
        b_parametresi=0.5,
        c_parametresi=0.2,
        d_parametresi=1.0,
        parametre_tipi=IRTParametreTipi.UC_PARAMETRE,
    )


# --- Modelin kendi API'si (servis dogru adi cagirmali) -----------------


def test_model_olasilik_hesapla_metodunu_sunuyor() -> None:
    p = _parametreler()
    assert hasattr(p, "olasilik_hesapla")
    # Servisin eskiden cagirdigi ad modelde YOK; bu testin amaci o adin
    # geri gelmedigini kilitlemek.
    assert not hasattr(p, "hesapla_probability")


def test_model_alan_adlari_a_b_c_parametresi() -> None:
    p = _parametreler()
    for ad in ("a_parametresi", "b_parametresi", "c_parametresi"):
        assert hasattr(p, ad)
    for eski in ("discrimination", "difficulty", "guessing"):
        assert not hasattr(p, eski)


# --- Asil koruma: olasilik theta ile DEGISMELI ------------------------


@pytest.mark.asyncio
async def test_olasilik_theta_ile_degisiyor_profilsiz() -> None:
    svc = IRTService()
    par = _parametreler()
    sonuc = [await svc.hesapla_cevap_olasiligi(t, par, None) for t in THETALAR]
    assert len(set(sonuc)) > 1, (
        f"olasilik her theta icin ayni ({sonuc[0]}) -- IRT egrisi cokmus "
        "olabilir (hata yutulup varsayilan donuyor)"
    )
    assert sonuc == sorted(sonuc), "olasilik theta ile artmali"


@pytest.mark.asyncio
async def test_olasilik_theta_ile_degisiyor_profille() -> None:
    """Uretim yolu: API her zaman bir profil GECIRIR.

    Eski kodda profil gecilince `_hesapla_ogrenci_morfoloji_ayarlamasi`
    modelde olmayan bir metoda gidiyor, hata yutuluyor ve sonuc yine sabit
    0.5 oluyordu. Bu yuzden profilli yol AYRICA sinaniyor.
    """
    svc = IRTService()
    par = _parametreler()
    profil = OgrenciMorfolojiProfili(ogrenci_id="koruma-testi")
    sonuc = [await svc.hesapla_cevap_olasiligi(t, par, profil) for t in THETALAR]
    assert len(set(sonuc)) > 1, (
        f"profil gecilince olasilik sabitlendi ({sonuc[0]}) -- morfoloji "
        "ayarlamasi hatayi yutuyor olabilir"
    )
    assert sonuc == sorted(sonuc)


@pytest.mark.asyncio
async def test_servis_modelle_ayni_sonucu_veriyor() -> None:
    """Ayarlama devre disiyken servis, modelin kendi hesabini AYNEN vermeli."""
    svc = IRTService()
    par = _parametreler()
    for t in THETALAR:
        beklenen = par.olasilik_hesapla(t)
        alinan = await svc.hesapla_cevap_olasiligi(t, par, None)
        assert alinan == pytest.approx(beklenen, abs=1e-9)


@pytest.mark.asyncio
async def test_sabit_varsayilan_donmuyor() -> None:
    """MUTASYON KARSILIGI: hata yolunun donduru 0.5'tir.

    Eger biri metot adini yeniden bozarsa TUM degerler 0.5 olur. Burada
    hicbir theta'nin 0.5'e esit CIKMAMASI gerekmiyor -- ama hepsinin birden
    0.5 olmasi kesin regresyondur.
    """
    svc = IRTService()
    par = _parametreler()
    sonuc = [await svc.hesapla_cevap_olasiligi(t, par, None) for t in THETALAR]
    assert sonuc != [0.5] * len(THETALAR)


# --- Morfoloji ayarlamasi: durustce devre disi -------------------------


@pytest.mark.asyncio
async def test_morfoloji_ayarlamasi_devre_disi_ve_isaretli() -> None:
    """Eksik model alanlari icin formul UYDURULMADI.

    Ayarlama 0.0 doner (taban olasilik degismeden gecer) ve durum
    `morfoloji_ayarlamasi_aktif = False` ile gozlenebilir olur.
    """
    svc = IRTService()
    par = _parametreler()
    profil = OgrenciMorfolojiProfili(ogrenci_id="koruma-testi")

    assert svc.morfoloji_ayarlamasi_aktif is None  # henuz denenmedi
    ayarlama = await svc._hesapla_ogrenci_morfoloji_ayarlamasi(profil, par)
    assert ayarlama == 0.0
    assert svc.morfoloji_ayarlamasi_aktif is False


@pytest.mark.asyncio
async def test_ayarlama_atilmiyor_yutulmuyor() -> None:
    """Yardimci AttributeError ATMAMALI (eskiden atiyordu ve yutuluyordu)."""
    svc = IRTService()
    par = _parametreler()
    profil = OgrenciMorfolojiProfili(ogrenci_id="koruma-testi")
    # Atarsa test hata ile duser; yakalamiyoruz ki fark edilsin.
    assert await svc._hesapla_ogrenci_morfoloji_ayarlamasi(profil, par) == 0.0
