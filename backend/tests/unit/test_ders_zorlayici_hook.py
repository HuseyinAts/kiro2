"""`ders_zorlayici_kos.py` bekcisinin kendi bekcisi — S232.

NEDEN VAR
---------
Bu hook artik enforcement'in belkemigi: pre-push'ta kosacak test listesini
`.claude/lessons/ders_kaydi.yaml` icindeki `zorlayici:` alanlarindan TURETIR.
Yani "bir derse zorlayici yazmak" = "onu otomatik kapiya baglamak".

Belkemigi olmasi onu kirilgan da yapiyor: iki sessiz bozulma yolu var ve
ikisi de kapiyi ETKISIZ birakir, kirmizi vermeden:

  1. Ayristirici bozulur  -> liste BOS -> hicbir bekci kosmaz
  2. Bicim kapisi bozulur -> defterdeki bir satir pytest BAYRAGINA donusur
     (`-p no:cacheprovider`, `--co`) -> pytest hicbir sey kosmadan cikar

Deponun kendi dersi (`L-s219-yorum-cida-dusmez`): mesajdaki bilgi kaybolur,
yorumdaki bilgi silinebilir, yalnizca TEST kapida duser.

OZYINELEME YOK
--------------
`main()` sonunda pytest cagiriyor. Bu dosya defterde `zorlayici` olarak
kayitli, yani hook onu KOSUYOR. O yuzden burada `main()` DEGIL yalnizca saf
fonksiyonlar (`zorlayicilari_topla`, `bicim_gecersizleri`) sinaniyor.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

DEPO_KOKU = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(DEPO_KOKU / "backend" / "hooks"))

from ders_zorlayici_kos import (  # noqa: E402
    DEFTER,
    bicim_gecersizleri,
    zorlayicilari_topla,
)

# ---------------------------------------------------------------------------
# BICIM KAPISI — pytest ARGV'sine gitmesi guvenli olmayan degerler
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kotu",
    [
        pytest.param("-p no:cacheprovider", id="pytest-bayragi"),
        pytest.param("--co", id="pytest-uzun-bayragi"),
        pytest.param("backend/../../etc/passwd.py", id="ust-dizine-kacis"),
        pytest.param("backend/tests/../../../x.py", id="gomulu-ust-dizin"),
        pytest.param("frontend/src/x.py", id="backend-disi"),
        pytest.param("backend/tests/unit", id="dosya-degil-dizin"),
        pytest.param("backend/tests/unit/x.txt", id="py-degil"),
    ],
)
def test_bicim_kapisi_guvensiz_degeri_reddeder(kotu: str):
    """Bu degerlerden biri gecerse pytest hicbir bekci kosmadan yesil donebilir."""
    assert bicim_gecersizleri([kotu]) == [kotu], (
        f"{kotu!r} bicim kapisindan GECTI — pytest ARGV'sine boyle bir deger "
        "girerse kapi sessizce etkisizlesir (bayrak olarak yorumlanir veya "
        "depo disina isaret eder)."
    )


@pytest.mark.parametrize(
    "iyi",
    [
        "backend/tests/unit/test_ders_kaydi.py",
        "backend/tests/db/test_question_bank_invariants.py",
        "backend/tests/integration/test_icerik_gecerliligi.py",
    ],
)
def test_bicim_kapisi_mesru_yolu_kabul_eder(iyi: str):
    """Kontrol kolu: kapi cok siki olursa gercek bekcileri kilitler."""
    assert bicim_gecersizleri([iyi]) == []


def test_bicim_kapisi_yalniz_kotu_olani_ayiklar():
    """Karisik listede iyi/kotu ayrimi — hepsini reddetmek de bir kusurdur."""
    iyi = "backend/tests/unit/test_ders_kaydi.py"
    assert bicim_gecersizleri([iyi, "-p x", "backend/a/../b.py"]) == [
        "-p x",
        "backend/a/../b.py",
    ]


# ---------------------------------------------------------------------------
# AYRISTIRICI — defterden liste turetme
# ---------------------------------------------------------------------------


def test_defter_ayristirici_bos_donmemeli():
    """Bos liste bir BULGU degil, ALET ARIZASI adayidir.

    S219 dersi: bir olcum aletinde YANLIS-SIFIR tek kabul edilemez hata
    turudur — isi sessizce 'bitmis' gosterir. Burada da bos liste
    'enforcement yok' demektir ama kirmizi vermez.
    """
    yollar = zorlayicilari_topla()
    assert yollar, (
        "Defterden hic `zorlayici` turetilemedi. Ya ayristirici regex'i bozuldu "
        "ya defterin girinti bicimi degisti. Her iki halde de pre-push kapisi "
        "HICBIR bekci kosmuyor demektir."
    )


def test_defterdeki_her_zorlayici_diskte_var():
    """Defter YALAN SOYLEYEMEZ: isaret ettigi dosya var olmali.

    Silinen/tasinan bir bekci dosyasi defterde kalirsa hook her push'ta
    patlar; bu test o durumu push'tan ONCE gosterir.
    """
    eksik = [y for y in zorlayicilari_topla() if not (DEPO_KOKU / y).exists()]
    assert not eksik, (
        f"Defterde var, diskte YOK: {eksik}. Ders ya duzeltilmeli ya "
        "`zorlayici: null` yapilmali (bosluk gorunur kalsin)."
    )


def test_defterden_turetilen_liste_tekil_ve_sirali():
    """Ayni dosyayi iki kez kosmak bosa zaman; sira determinizm icin."""
    yollar = zorlayicilari_topla()
    assert len(yollar) == len(set(yollar)), "liste tekil degil"
    assert yollar == sorted(yollar), "liste sirali degil"


def test_ayristirici_null_ve_bos_degerleri_atlar(tmp_path, monkeypatch):
    """`zorlayici: null` bir bosluk isaretidir — yol olarak ISLENMEMELI.

    141 dersin 101'i null; biri bile yol sanilirsa hook her push'ta duser.
    """
    sahte = tmp_path / "ders_kaydi.yaml"
    sahte.write_text(
        "- id: A\n"
        "  zorlayici: null\n"
        "- id: B\n"
        "  zorlayici: ~\n"
        "- id: C\n"
        "  zorlayici: backend/tests/unit/test_ders_kaydi.py\n"
        "- id: D\n"
        "  zorlayici: backend/tests/unit/test_ders_kaydi.py\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("ders_zorlayici_kos.DEFTER", sahte)

    assert zorlayicilari_topla() == ["backend/tests/unit/test_ders_kaydi.py"]


def test_defter_gercek_dosya_ve_okunabilir():
    """Hook'un okudugu defter, bu depodaki gercek defter olmali."""
    assert DEFTER.exists(), f"ders defteri yok: {DEFTER}"
    assert DEFTER.name == "ders_kaydi.yaml"
