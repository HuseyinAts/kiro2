"""CI toplama bekcisi — korumasiz opsiyonel-bagimlilik import'u yasak (A.4).

NEDEN VAR
---------
1 Agu 2026 olcumu (`.github/workflows/ci.yml`):

    :281  pytest tests/ --tb=short --cov=. ... -x       <- MARKER FILTRESI YOK
    :249  uv pip install -r requirements.txt
          uv pip install pytest pytest-cov pytest-asyncio pytest-xdist httpx
          uv pip install pyyaml pillow tqdm numpy

Marker filtresi olmadigi icin `-m integration` isaretli dosyalar da TOPLANIR.
Ama kurulum kumesinde `psycopg2-binary` YOK:

    requirements.txt:10  psycopg[binary]>=3.1.0        <- psycopg **v3**
    requirements.txt:11  sqlalchemy[asyncio]>=2.0.36   <- psycopg2 yalniz
                                                          [postgresql*] extra'sinda

Sonuc: modul duzeyinde `import psycopg2` yapan bir test dosyasi CI'da
**collection ERROR** verir; `-x` bunu tek dosyadan TUM test job'una yayar.
Hata RLS/FSRS ile ilgisizdir — suit ilgisiz bir sebeple kirmizi olur.
Bu dosya o sinifi kapatir.

Duzeltme kalibi:

    psycopg2 = pytest.importorskip("psycopg2")   # DB yoksa SKIP, ERROR degil

KAPSAM SINIRI (bilincli, gizli varsayim degil)
----------------------------------------------
Yalnizca **dogrudan** import'lar taranir. Toplanan bir test, korumasiz import
iceren bir yardimci modulu (or. `tests/fixtures/factories.py` -> `faker`)
import ederse bu bekci onu GORMEZ. Import grafigini yurumek icin ayri bir
kalem gerekir.
"""

from __future__ import annotations

import ast
from pathlib import Path

TESTLER_KOKU = Path(__file__).resolve().parent

# pytest.ini:6 -> `python_files = test_*.py *_test.py`; conftest.py daima yuklenir.
TOPLANAN_TABAN = 500  # 1 Agu 2026 olcumu: 633 dosya. Tarayici bosa donerse yakala.

# CI ortaminda (requirements.txt kapanisi + ci.yml ekstralari) import EDILEMEYEN
# paketler — 1 Agu 2026'da `importlib.metadata` ile olculdu:
#   psycopg2       -> psycopg2-binary; sqlalchemy'de yalniz [postgresql*] extra'sinda
#   locust         -> hicbir dagitim gerektirmiyor, requirements.txt'te yok
#   testcontainers -> yerel ortamda bile kurulu degil
#   faker          -> yerel ortamda bile kurulu degil
#
# `websocket` BILEREK listede DEGIL: `backend/websocket.py` yerel modulu ayni adi
# golgeliyor (olculdu), listeye eklenirse yanlis-pozitif uretir.
CI_DISI_PAKETLER = frozenset({"psycopg2", "locust", "testcontainers", "faker"})


def _korumali_mi(metin: str, paket: str) -> bool:
    """Dosya bu paketi importorskip/modul-skip ardina almis mi."""
    return (
        f'importorskip("{paket}"' in metin
        or f"importorskip('{paket}'" in metin
        or "allow_module_level=True" in metin
    )


def _korumasiz_importlar(metin: str) -> list[tuple[int, str]]:
    """Modul GOVDESINDE (fonksiyon/try disi) korumasiz CI-disi import'lar.

    Fonksiyon ici veya `try/except ImportError` icindeki import'lar toplama
    hatasi URETMEZ, bu yuzden bulgu sayilmaz.
    """
    try:
        agac = ast.parse(metin)
    except SyntaxError:
        return []

    bulgular: list[tuple[int, str]] = []
    for dugum in agac.body:
        if isinstance(dugum, ast.Import):
            adlar = [takma.name.split(".")[0] for takma in dugum.names]
        elif isinstance(dugum, ast.ImportFrom) and dugum.level == 0 and dugum.module:
            adlar = [dugum.module.split(".")[0]]
        else:
            continue
        for ad in adlar:
            if ad in CI_DISI_PAKETLER and not _korumali_mi(metin, ad):
                bulgular.append((dugum.lineno, ad))
    return bulgular


def _toplanan_dosyalar() -> list[Path]:
    return sorted(
        {
            yol
            for yol in TESTLER_KOKU.rglob("*.py")
            if yol.name.startswith("test_")
            or yol.name.endswith("_test.py")
            or yol.name == "conftest.py"
        }
    )


def test_alet_dogrulamasi_ekilmis_ihlal_yakalaniyor() -> None:
    """KONTROL KOLU: tarayici bilinen-KOTU girdiyi gormezse bekci vakumdur."""
    kotu = "import os\nimport psycopg2\nimport pytest\n"
    assert _korumasiz_importlar(kotu) == [(2, "psycopg2")], (
        "Tarayici ekilmis modul-duzeyi ihlali yakalayamadi -> "
        "asagidaki 'ihlal yok' sonucu ANLAMSIZ"
    )


def test_alet_dogrulamasi_korumali_import_temiz_sayiliyor() -> None:
    """KONTROL KOLU: bilinen-IYI girdi bulgu URETMEMELI (yanlis-pozitif yok)."""
    iyi = 'import pytest\n\npsycopg2 = pytest.importorskip("psycopg2")\n'
    assert (
        _korumasiz_importlar(iyi) == []
    ), "Korumali import ihlal sayildi -> bekci duzeltilmis dosyalari da bloklar"


def test_alet_dogrulamasi_fonksiyon_ici_import_sayilmiyor() -> None:
    """Fonksiyon ici import toplama hatasi uretmez — bulgu sayilmamali."""
    fonksiyon_ici = "def f():\n    import psycopg2\n    return psycopg2\n"
    assert (
        _korumasiz_importlar(fonksiyon_ici) == []
    ), "Fonksiyon ici import ihlal sayildi -> dedektor asiri genis"


def test_toplanan_test_modulleri_ci_disi_paketi_korumasiz_import_etmiyor() -> None:
    """A.4: CI'da toplanan hicbir test modulu ERROR'a yol acmamali."""
    dosyalar = _toplanan_dosyalar()
    assert len(dosyalar) >= TOPLANAN_TABAN, (
        f"Yalnizca {len(dosyalar)} dosya tarandi (taban {TOPLANAN_TABAN}) -> "
        "tarayici yanlis koke bakiyor, sonuc gecersiz"
    )

    ihlaller: list[str] = []
    for yol in dosyalar:
        metin = yol.read_text(encoding="utf-8", errors="replace")
        for satir, paket in _korumasiz_importlar(metin):
            goreli = yol.relative_to(TESTLER_KOKU).as_posix()
            ihlaller.append(f"tests/{goreli}:{satir} -> {paket}")

    assert not ihlaller, (
        "CI'da kurulu OLMAYAN paketi modul duzeyinde korumasiz import eden "
        f"{len(ihlaller)} test modulu var. ci.yml `-x` ile kostugu icin bunlarin "
        "her biri TUM test job'unu dusurur.\n"
        + "\n".join(f"  {i}" for i in ihlaller)
        + '\n\nDuzeltme: `paket = pytest.importorskip("paket")`'
    )
