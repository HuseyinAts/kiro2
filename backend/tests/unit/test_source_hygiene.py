"""Kaynak dosya hijyeni: hiçbir `.py` UTF-8 BOM ile başlamamalı (#456).

30 TEM 2026 ÖLÇÜMÜ — bekçi koşumunda şu uyarı çıktı:

    Warning: EmptyExceptionDetector AST parse edemedi
    tests/integration/test_end_to_end_platform.py: invalid non-printable
    character U+FEFF (line 1)

`pytest` BOM'u sorunsuz okur (`utf-8-sig`); o dosyadan **10 test toplanıyor**.
Ama `ast.parse()` decode edilmiş metnin başındaki U+FEFF'i basılamaz karakter
sayıp `SyntaxError` atıyor. Sonuç: AST tabanlı dedektörler (EmptyException,
MockAbuse mock-oranı) o dosyayı **SESSİZCE atlıyordu** — regex yolu çalışmaya
devam ettiği için kusur görünmüyordu. Yani bir dosya, kendisini denetleyen
kontrolün yarısından 3 bayt yüzünden muaf kalıyordu.

NEDEN BOM KONTROLÜ, `ast.parse` DEĞİL — ölçüldü:

    tüm backend/*.py    2453 dosya   ast.parse hatası 2   süre 5.48s
    tests+hooks          733 dosya   ast.parse hatası 1   süre 1.51s
    BOM'lu dosya sayısı: 2  (ve ast.parse hatası veren TAM O 2 dosya)

Paket şu an ~4s koşuyor; 5.5s'lik bir `ast.parse` süpürmesi onu ikiye
katlardı. BOM zaten kök nedenin kendisi ve 3 bayt okumak bedava. Gerçek
sözdizimi hataları ise pytest'in toplama/import aşamasında yakalanıyor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

BACKEND = Path(__file__).resolve().parents[2]
BOM = b"\xef\xbb\xbf"

# Kendi sanal ortamları / önbellekleri bizim kaynağımız değil.
HARIC_PARCALAR = frozenset(
    {
        "venv",
        ".venv",
        "site-packages",
        "__pycache__",
        ".mypy_cache",
        ".hypothesis",
        "node_modules",
        "backend",  # backend/backend/ — depoya kaçmış artık dizini (#456)
    }
)


def _kaynak_dosyalari() -> list[Path]:
    return [
        p
        for p in BACKEND.rglob("*.py")
        if not (set(p.relative_to(BACKEND).parts[:-1]) & HARIC_PARCALAR)
    ]


def test_hicbir_py_dosyasi_bom_ile_baslamiyor():
    """BOM = AST tabanlı denetimden sessiz muafiyet. Yeni BOM'lu dosya girmesin.

    Bu test 30 Tem 2026'da 2 dosyada KIRMIZI idi; ikisi de düzeltildi.
    Kırmızıya dönerse çözüm 3 baytı silmek: `p.write_bytes(p.read_bytes()[3:])`.
    """
    bomlular = [
        str(p.relative_to(BACKEND))
        for p in _kaynak_dosyalari()
        if p.read_bytes()[:3] == BOM
    ]
    mesaj = (
        "BOM ile baslayan dosyalar (ast.parse bunlari SyntaxError yapar):\n  "
        + "\n  ".join(bomlular)
    )
    assert bomlular == [], mesaj


def test_tarama_gercekten_dosya_goruyor():
    """KÖRLEŞME GÜVENCESİ: hariç tutma listesi her şeyi süzerse test vakumlaşır.

    `HARIC_PARCALAR`a yanlışlıkla `tests` veya `hooks` eklenirse yukarıdaki
    test 0 dosya tarayıp yine yeşil kalır. Bu test bunu engeller.
    """
    dosyalar = _kaynak_dosyalari()
    assert (
        len(dosyalar) > 2000
    ), f"yalnizca {len(dosyalar)} dosya tarandi — filtre fazla geniş"
