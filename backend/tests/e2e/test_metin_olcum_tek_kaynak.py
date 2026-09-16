"""metin_olcum.py TEK KAYNAK kalsin diye nobetci testler.

Alti ithal script'i uzun sure kendi satir ici olcum kopyasini tasidi.
Kopyalar zamanla AYRISTI: neofizik_tyt_ithal.py, PR #266/#269 ile
onarilan katastrofik geri izleme desenini hala tasiyordu. Tasima
yapildi; bu dosya kopyanin GERI GELMESINI engeller.

Testler AST uzerinden calisir -- modulleri ice aktarmaz, psycopg ya da
DB istemez, yani CI'da da koser.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

KITAP = KOK / "scripts" / "kitap"

# metin_olcum.py'nin sahibi oldugu adlar. Bir ithal script'i bunlardan
# birini YENIDEN tanimlarsa kopya geri gelmis demektir.
PAYLASILAN_ADLAR = frozenset(
    {
        "EKLER",
        "SAYISAL_SIK",
        "NICELIK",
        "nfc",
        "_nfc",
        "soru_hash",
        "kelime_istatistik",
        "_kelime_istatistik",
        "ek_ayikla",
        "_ek_ayikla",
        "morfoloji_karmasikligi",
        "okunabilirlik",
        "bloom_belirle",
        "sik_bayraklari",
    }
)

ITHAL_SCRIPTLERI = (
    "biyo345_ithal.py",
    "biyo345tyt_ithal.py",
    "dilbilgisi_ithal.py",
    "geo345_ithal.py",
    "mikro_geo_ithal.py",
    "neofizik_ithal.py",
    "neofizik_tyt_ithal.py",
)


def _ust_duzey_adlar(yol: Path) -> set[str]:
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    adlar: set[str] = set()
    for n in agac.body:
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            adlar.add(n.name)
        elif isinstance(n, ast.Assign):
            for h in n.targets:
                if isinstance(h, ast.Name):
                    adlar.add(h.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            adlar.add(n.target.id)
    return adlar


def _ice_aktarilanlar(yol: Path) -> set[str]:
    agac = ast.parse(yol.read_text(encoding="utf-8"))
    adlar: set[str] = set()
    for n in ast.walk(agac):
        if isinstance(n, ast.ImportFrom) and (n.module or "").endswith("metin_olcum"):
            for a in n.names:
                adlar.add(a.asname or a.name)
    return adlar


@pytest.mark.parametrize("dosya", ITHAL_SCRIPTLERI)
def test_script_paylasilan_tanimi_yeniden_uretmiyor(dosya: str) -> None:
    yol = KITAP / dosya
    assert yol.exists(), yol
    tekrar = _ust_duzey_adlar(yol) & PAYLASILAN_ADLAR
    assert not tekrar, (
        f"{dosya} su adlari YENIDEN tanimliyor: {sorted(tekrar)}. "
        "Bu adlarin evi scripts/kitap/metin_olcum.py; kopya ayrisir "
        "(bkz. neofizik_tyt'nin eski SAYISAL_SIK deseni)."
    )


@pytest.mark.parametrize("dosya", ITHAL_SCRIPTLERI)
def test_script_olcumu_moduldan_aliyor(dosya: str) -> None:
    alinan = _ice_aktarilanlar(KITAP / dosya)
    assert alinan, f"{dosya} metin_olcum'dan hicbir sey ice aktarmiyor"
    assert (
        "soru_hash" in alinan
    ), f"{dosya}: soru_hash metin_olcum'dan gelmeli -- id'ler ona bagli"


def test_metin_olcum_adlari_hala_sahipleniyor() -> None:
    """Modul, nobetcinin korudugu adlari gercekten tanimliyor mu?

    Bu test olmasa, modulden bir ad silindiginde nobetci sessizce
    anlamsizlasirdi.
    """
    sahip = _ust_duzey_adlar(KITAP / "metin_olcum.py")
    beklenen = {
        "EKLER",
        "SAYISAL_SIK",
        "NICELIK",
        "nfc",
        "soru_hash",
        "kelime_istatistik",
        "ek_ayikla",
        "morfoloji_karmasikligi",
        "okunabilirlik",
        "bloom_belirle",
        "sik_bayraklari",
    }
    eksik = beklenen - sahip
    assert not eksik, f"metin_olcum.py su adlari kaybetmis: {sorted(eksik)}"


def test_onarilmis_sayisal_sik_deseni_geri_gelmedi() -> None:
    """Katastrofik geri izleme deseni HICBIR yerde olmamali.

    Eski desen ic ice niceliyordu: `(?:[...]{0,6}\\s*)*`. Onarilmis
    surum ic ice nicelemez.
    """
    kotu = "}\\s*)*"
    for dosya in (*ITHAL_SCRIPTLERI, "metin_olcum.py"):
        metin = (KITAP / dosya).read_text(encoding="utf-8")
        assert (
            kotu not in metin
        ), f"{dosya}: ic ice niceleyen desen geri gelmis (ReDoS riski)"
