"""Golden Flow merge kapisinin SOZLESMESI (A.2).

1 AGU 2026 CANLI OLCUMU — kapinin esigi ilk kez olculdu
--------------------------------------------------------
    cd backend && pytest tests/e2e/test_golden_flows.py -m golden_flow \
        --junitxml=gf-olcum.xml

    178 test  ->  164 GECTI · 12 DUSTU · 2 ATLANDI   (94 saniye)

Atlanan ikisi de belgeli: `gf4w2` (seed'e bagli due-card yok) ve `gf1wb`
(deploy Bearer-only, refresh cookie set etmiyor). Yani `ESIK = 150` bugun
ULASILABILIR — "esik yanlissa kapi kalici kirmizi olur" endisesi olcumle
CURUDU. Kusur baska yerdeydi:

  1. **Sabit esik suite buyudukce gevser.** golden-flows.md "yeni ust-duzey
     ozellik -> yeni GF testi" diyor. 250 teste cikildiginda `gecen >= 150`
     kurali **100 skip'i** yesil gecirir; yani esigin engellemek icin konuldugu
     "skip yalani" zamanla geri gelir.
  2. **`hata` hesaplaniyor ama assert EDILMIYORDU** (golden-flows.yml:247-260).
     Bugun yalniz pytest'in kendi cikis kodu yakaliyor; kapinin kendisi kirik
     akisi olcmuyordu.
  3. Mantik YAML ici heredoc'tu -> **test edilemezdi**.

Bu dosya sozlesmeyi civiler. Kural: hata SIFIR · atlanan <= AZAMI_ATLANAN ·
toplam >= TOPLAM_TABANI. Ucu birlikte hem "hepsi atlandi" yalanini hem
"suite kuculdu" yalanini hem de kirik akisi yakalar; hicbiri sabit bir
gecen-sayisina bagli degildir.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.gf_esik_kapisi import (
    AZAMI_ATLANAN,
    TOPLAM_TABANI,
    kapi_karari,
    sayimlari_cikar,
)


def _rapor(tests: int, failures: int = 0, errors: int = 0, skipped: int = 0) -> str:
    return (
        f'<testsuite name="pytest" tests="{tests}" failures="{failures}" '
        f'errors="{errors}" skipped="{skipped}"></testsuite>'
    )


# --------------------------------------------------------------------------
# ALET DOGRULAMASI — ayristirici gercekten sayiyor mu
# --------------------------------------------------------------------------


def test_alet_dogrulamasi_canli_olcum_sayimlari_yeniden_uretiliyor() -> None:
    """KONTROL KOLU: 1 Agu canli kosumunun sayimlari ayristiricidan cikmali."""
    sayimlar = sayimlari_cikar(_rapor(tests=178, failures=12, skipped=2))
    assert sayimlar == {"toplam": 178, "gecen": 164, "atlanan": 2, "hata": 12}, (
        f"Ayristirici canli olcumu yeniden uretemedi: {sayimlar} "
        "-> bu dosyadaki hicbir karar gecerli degil"
    )


def test_alet_dogrulamasi_testsuites_kok_etiketi_de_okunuyor() -> None:
    """pytest bazen <testsuites> sarmalayicisi uretir — ikisi de desteklenmeli."""
    sarmali = f"<testsuites>{_rapor(tests=10, failures=1, skipped=2)}</testsuites>"
    assert sayimlari_cikar(sarmali)["toplam"] == 10, (
        "<testsuites> koku okunamadi -> gercek raporda 0 test gorunur ve kapi "
        "yanlislikla 'bos rapor' der"
    )


def test_alet_dogrulamasi_hata_errors_alanini_da_topluyor() -> None:
    """`errors` (collection/fixture hatasi) da `hata` sayilmali."""
    assert (
        sayimlari_cikar(_rapor(tests=10, errors=3))["hata"] == 3
    ), "errors goz ardi edildi -> collection hatasi kapidan sizardi"


# --------------------------------------------------------------------------
# KAPI SOZLESMESI
# --------------------------------------------------------------------------


def test_saglikli_kosum_geciyor() -> None:
    """Bilinen-IYI: 178 test, 176 gecti, 2 belgeli atlama, 0 hata."""
    assert (
        kapi_karari(sayimlari_cikar(_rapor(178, skipped=2))) is None
    ), "Saglikli kosum reddedildi -> kapi yanlis-pozitif, merge kalici bloke"


def test_dusen_akis_kapiyi_kirmiziya_cevirir() -> None:
    """A.2 KUSUR-2: `hata` hesaplanip assert EDILMIYORDU.

    170 gecen + 8 dusen: eski `gecen >= 150` kurali bunu YESIL geciriyordu.
    golden-flows.md: kirik Golden Flow ile merge YASAK.
    """
    karar = kapi_karari(sayimlari_cikar(_rapor(178, failures=8)))
    assert (
        karar is not None
    ), "8 dusen Golden Flow'a ragmen kapi YESIL -> `hata` assert'i yuk tasimiyor"
    assert "8" in karar, f"Karar mesaji dusen sayisini soylemiyor: {karar!r}"


def test_esik_suite_buyudukce_gevsemiyor() -> None:
    """A.2 KUSUR-1: sabit esik, test sayisi artinca skip'e kapi acar.

    250 test / 160 gecen / 90 atlanan: eski `gecen >= 150` kurali YESIL derdi.
    Oysa bu tam olarak esigin engellemek icin konuldugu "skip yalani".
    """
    assert kapi_karari(sayimlari_cikar(_rapor(250, skipped=90))) is not None, (
        "250 testin 90'i atlandigi halde kapi YESIL -> sabit esik geri gelmis; "
        "suite buyudukce kapi sessizce gevsiyor"
    )


def test_hepsi_atlanmis_yalani_reddediliyor() -> None:
    """30 Tem 2026 vakasi: 178 testin 148'i skip, is yesil bitiyordu (#462/B4-x)."""
    assert (
        kapi_karari(sayimlari_cikar(_rapor(178, skipped=148))) is not None
    ), "148 atlama kapidan gecti -> #462'nin duzelttigi yalan geri gelmis"


def test_suite_kuculurse_yakalaniyor() -> None:
    """Testler silinse/toplanamasa 'hepsi gecti' yalani uretilebilir."""
    karar = kapi_karari(sayimlari_cikar(_rapor(20)))
    assert karar is not None, (
        f"Yalniz 20 test kosuldugu halde kapi YESIL (taban {TOPLAM_TABANI}) -> "
        "collection cokusu 'tertemiz gecti' gibi gorunur"
    )


def test_bos_rapor_reddediliyor() -> None:
    """0 test = kapi bos; bu depoda '0 satir tarandi, sorun yok' yalani yasandi."""
    assert (
        kapi_karari(sayimlari_cikar(_rapor(0))) is not None
    ), "0 testlik rapor kapidan gecti -> bos kosum yesil sayiliyor"


@pytest.mark.parametrize("atlanan", [AZAMI_ATLANAN, AZAMI_ATLANAN + 1])
def test_atlama_siniri_tam_sinirda_dogru_davraniyor(atlanan: int) -> None:
    """Sinir degeri: AZAMI_ATLANAN kabul, bir fazlasi RED (off-by-one civisi)."""
    karar = kapi_karari(sayimlari_cikar(_rapor(178, skipped=atlanan)))
    if atlanan <= AZAMI_ATLANAN:
        assert karar is None, f"{atlanan} atlama sinirin altinda ama reddedildi"
    else:
        assert karar is not None, f"{atlanan} atlama sinirin ustunde ama kabul edildi"
