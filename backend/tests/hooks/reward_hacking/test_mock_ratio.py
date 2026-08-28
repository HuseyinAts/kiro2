"""Mock oranı invaryantı: bir oran 1.0'ı AŞAMAZ (#455).

30 Tem 2026 ÖLÇÜMÜ — bekçinin kendi çıktısı imkânsız bir sayı basıyordu:

    🔴 Line 1: High mock ratio (125%) - consider integration tests
       Code: Mock ratio: 125% (5/4)

KÖK NEDEN (probe ile ölçüldü, kod okunarak değil) — `ast_analyzer.py:336-339`:

    for node in self._walk():
        if isinstance(node, ast.Call):        # <- @patch(...) BURADA sayılıyor
            total_calls += 1
            ... mock_count += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                if self._is_patch_decorator(decorator):
                    mock_count += 1          # <- AYNI DÜĞÜM ikinci kez

`@patch("modul.a")` bir `ast.Call` düğümüdür ve `ast.walk` onu zaten ziyaret eder.
Probe çıktısı:

    satir 4: "patch('modul.a')"  _is_patch_decorator=True  (ayni dugum ast.Call mi? True)
    satir 5: "patch('modul.b')"  _is_patch_decorator=True  (ayni dugum ast.Call mi? True)
    -> mock_count=5  total_calls=3  oran=%167

Yani her `@patch(...)` payda'da bir, pay'da İKİ kez sayılıyor. Sonuç:
`MOCK_RATIO_THRESHOLD = 0.8` karşılaştırması anlamsız — %167 üreten bir sayaç
eşiği rastgele tetikler.

DEKORATÖR DÖNGÜSÜ TAMAMEN GEREKSİZ (ölçüldü, varsayılmadı):
- `@patch(...)` -> `ast.Call`, Call dalı zaten sayıyor
- bare `@patch` -> `ast.Name`, `_is_patch_decorator` ona `False` döner (Call değil)
- `@patch.object(...)` -> `func.attr == "object"`, İKİ dal da yakalamıyor
Yani döngünün yakaladığı, Call dalının kaçırdığı hiçbir vaka yok.
"""

from __future__ import annotations

import asyncio

import pytest

from hooks.reward_hacking.analyzers.ast_analyzer import ASTAnalyzer
from hooks.reward_hacking.detectors import MockAbuseDetector

pytestmark = [pytest.mark.unit]


# --- Fixture'lar: hepsi ayrı bir oran rejimini temsil eder --------------------

AZ_MOCK = """\
from unittest.mock import MagicMock, patch


@patch("modul.a")
@patch("modul.b")
def test_ornek(b, a):
    istemci = MagicMock()
    metin = "abc".upper()
    sayi = len(metin)
    baska = str(sayi)
    assert istemci is not None
    assert baska == "3"
"""
# mock: patch x2 + MagicMock = 3 · toplam çağrı: 3 + upper + len + str = 6 -> 0.50

COK_MOCK = """\
from unittest.mock import MagicMock, Mock


def test_hepsi_mock():
    a = MagicMock()
    b = Mock()
    c = MagicMock()
    assert a and b and c
"""
# mock: 3 · toplam çağrı: 3 -> 1.00 (eşik 0.8 üstü, GERÇEK bulgu)

MOCKSUZ = """\
def test_saf():
    metin = "abc".upper()
    assert len(metin) == 3
"""
# mock: 0 · toplam çağrı: 2 -> 0.00

SADECE_DEKORATOR = """\
from unittest.mock import patch


@patch("modul.a")
@patch("modul.b")
def test_iki_patch(b, a):
    assert b is not None
    assert a is not None
"""
# mock: 2 · toplam çağrı: 2 -> 1.00


def _say(kaynak: str) -> tuple[int, int]:
    cozumleyici = ASTAnalyzer(kaynak, "test_ornek.py")
    cozumleyici.parse()
    return cozumleyici.count_mock_usage()


# --- 1) INVARYANT ------------------------------------------------------------


@pytest.mark.parametrize(
    "kaynak",
    [AZ_MOCK, COK_MOCK, MOCKSUZ, SADECE_DEKORATOR],
    ids=["az_mock", "cok_mock", "mocksuz", "sadece_dekorator"],
)
def test_mock_sayisi_toplam_cagriyi_asamaz(kaynak):
    """Bir alt küme, üst kümeden büyük olamaz — oran 1.0'ı aşamaz.

    Bu testin yakaladığı arıza: bekçi "%125 (5/4)" ve "%167 (5/3)" basıyordu.
    Oran metriği 1.0'ı aşabiliyorsa `MOCK_RATIO_THRESHOLD` karşılaştırması
    anlamsızdır — eşik artık "mock yoğunluğu"nu değil dekoratör sayısını ölçer.
    """
    mock_sayisi, toplam_cagri = _say(kaynak)
    # Mesaj ayri degiskende: uzun satirli `assert X, (f"...")` yazimini yerel
    # formatter ile pre-commit'in pinledigi ruff 0.7.1 ZIT bicimlendiriyor ve
    # commit sonsuz salinima giriyor (pyproject.toml'daki RUF100/S603 notuyla
    # ayni sinif). Kisa satir = iki formatter da ayni sonucu veriyor.
    yuzde = 100 * mock_sayisi / max(toplam_cagri, 1)
    mesaj = f"oran {mock_sayisi}/{toplam_cagri} = %{yuzde:.0f}"
    assert mock_sayisi <= toplam_cagri, mesaj


# --- 2) KESİN SAYILAR --------------------------------------------------------


@pytest.mark.parametrize(
    ("kaynak", "beklenen_mock", "beklenen_toplam"),
    [
        (AZ_MOCK, 3, 6),
        (COK_MOCK, 3, 3),
        (MOCKSUZ, 0, 2),
        (SADECE_DEKORATOR, 2, 2),
    ],
    ids=["az_mock", "cok_mock", "mocksuz", "sadece_dekorator"],
)
def test_sayaclar_kesin_degerleri_verir(kaynak, beklenen_mock, beklenen_toplam):
    """Sayaçlar elle sayılan değerlerle birebir tutmalı (çift sayım yok)."""
    assert _say(kaynak) == (beklenen_mock, beklenen_toplam)


def test_patch_dekoratoru_mock_olarak_sayilmaya_devam_eder():
    """MUTASYON GÜVENCESİ: çift sayımı Call dalını silerek 'düzeltmek' YASAK.

    Kolay ama yanlış fix: `node.func.id in ('Mock','MagicMock','patch','mock')`
    listesinden `patch`i çıkarmak. O zaman oran 1.0'ı aşmaz ama `@patch`
    tamamen görünmez olur ve dedektör mock ağırlıklı dosyaları kaçırır.
    """
    mock_sayisi, _ = _say(SADECE_DEKORATOR)
    assert mock_sayisi == 2, "iki @patch dekoratörü mock olarak sayılmalı"


# --- 3) DAVRANIŞ DÜZEYİ: dedektör ne raporluyor ------------------------------


def _oran_bulgulari(kaynak: str) -> list[str]:
    sonuclar = asyncio.run(MockAbuseDetector().detect("tests/test_ornek.py", kaynak))
    return [r.message for r in sonuclar if "mock ratio" in r.message.lower()]


def test_dusuk_oranli_dosya_yuksek_oran_bulgusu_uretmez():
    """%50 mock oranı eşiğin (0.8) altında — bulgu ÜRETİLMEMELİ.

    Ölçüm: fix öncesi bu dosya "High mock ratio (125%)" üretiyordu, çünkü
    2 dekoratör pay'da çift sayılıyordu.
    """
    assert _oran_bulgulari(AZ_MOCK) == []


def test_gercekten_yuksek_oran_hala_bulgu_uretir():
    """KÖRLEŞME GÜVENCESİ: %100 mock oranı hâlâ raporlanmalı.

    Çift sayımı düzeltirken oran kuralını tamamen etkisiz hale getirirsek
    (örn. sayacı hep 0 döndürmek) bu test kırmızıya döner.
    """
    bulgular = _oran_bulgulari(COK_MOCK)
    assert len(bulgular) == 1, f"beklenen 1 oran bulgusu, gelen: {bulgular}"
    assert "100%" in bulgular[0], bulgular[0]
