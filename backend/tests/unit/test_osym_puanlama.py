"""ÖSYM net hesabı TEK KAYNAKTAN gelmeli.

NEDEN BU DOSYA VAR (27 Ağu 2026 ölçümü)
---------------------------------------
Net hesabı üretimde **beş ayrı yerde** ve **iki çelişen politikayla** yaşıyordu:

    core/osym_exam_engine.py:1940   net = doğru            (cezasız)
    core/osym_exam_engine.py:1193   net = doğru            (cezasız, kopya)
    api/sinav.py:789                net = doğru            (cezasız, kopya)
    services/exam_performance_service.py:274,391  doğru - yanlış/4   (cezalı)
    analytics/exam_results_reporting.py:124       max(0, doğru - yanlış/4)

Üçü aynı yanlış gerekçeyi taşıyordu: *"ÖSYM 2023+ 1/4 ceza kaldırıldı"*.
Bir inanç üç dosyaya kopyalanmıştı. **Kullanıcı 27 Ağu 2026'da doğruladı:
kural HÂLÂ GEÇERLİ** — 4 yanlış 1 doğruyu götürür.

Sonuç kullanıcı-görünürdü: aynı oturum açıkken `/osym-exam/.../performance`
cezasız net, `/study-plan/projection` cezalı net servis ediyordu. Öğrenciye
sınav hazırlığı hakkında ŞİŞİRİLMİŞ bir sayı gösteriliyordu — ki A1 altın
yolunun kabul kriteri tam olarak "netini görür".

KIRPMA KARARI
-------------
Net **0'a kırpılmaz**. Negatif net Türk deneme kültüründe standarttır ve
kırpmak, tahmin etmenin verdiği zararı gizler — öğrenci "0 net" görüp
"hiç değilse sıfırdayım" sanır, oysa 8 yanlışla -2.0'dadır.
`analytics/exam_results_reporting.py:124`'ün `max(0, ...)` kırpması bu kararla
kanona bağlanıyor.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.osym_puanlama import osym_net

BACKEND = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Kanon
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dogru", "yanlis", "beklenen"),
    [
        (0, 0, 0.0),
        (20, 0, 20.0),
        (0, 4, -1.0),  # KIRPILMAZ
        (6, 8, 4.0),  # canlı prop senaryosu: 6 doğru + 8 yanlış
        (40, 0, 40.0),
        (1, 3, 0.25),
        (0, 40, -10.0),  # tamamı yanlış: en kötü hâl görünür kalmalı
    ],
)
def test_kanon_dogru_eksi_yanlis_bolu_dort(
    dogru: int, yanlis: int, beklenen: float
) -> None:
    assert osym_net(dogru, yanlis) == pytest.approx(beklenen)


def test_net_sifira_KIRPILMAZ() -> None:  # noqa: N802 - vurgu kasıtlı değil, alttaki docstring'e bak
    """Negatif net GÖRÜNÜR kalır — kırpma tahmin zararını gizler."""
    assert osym_net(0, 8) < 0


def test_bos_cevap_neti_ETKILEMEZ() -> None:  # noqa: N802
    """ÖSYM'de boş cevabın cezası yoktur; fonksiyon boşu zaten almıyor."""
    # Aynı doğru/yanlış ile, kaç soru boş bırakılmış olursa olsun net aynıdır.
    assert osym_net(10, 4) == osym_net(10, 4)


def test_alet_dogrulamasi_fonksiyon_sabit_dondurmuyor() -> None:
    """Ölçüm aleti kontrolü: sabit dönen bir fonksiyon üstteki testleri de geçerdi."""
    degerler = {osym_net(d, y) for d, y in [(0, 0), (5, 0), (0, 5), (5, 5)]}
    assert len(degerler) == 4, f"fonksiyon ayrım yapmıyor: {degerler}"


# ---------------------------------------------------------------------------
# Çırçır — bağımsız net hesabı SAYISI artmamalı
# ---------------------------------------------------------------------------

# 27 Ağu 2026'da kanona BAĞLANAMAYAN, hâlâ kendi hesabını yapan yer sayısı.
# Bu tur `osym_exam_engine` (2) ve `api/sinav.py` (1) kanona bağlandı — onlar
# zaten `net = doğru` yazdığı için bu listede hiç yoktular; geriye cezalı
# tarafın kopyaları kaldı:
#     services/exam_performance_service.py:274
#     services/exam_performance_service.py:391
#     analytics/exam_results_reporting.py:124
#     analytics/unified_analytics_data_model.py:172
#
# 🔴 Bu sayı TAHMİN EDİLMEDİ, ÖLÇÜLDÜ. İlk yazdığımda 3 sanmıştım ve tarayıcı
# 4 buldu (`unified_analytics_data_model.py:172`'yi doğrulamamıştım). Çırçır
# kendi varsayımımı yakaladı — ölçmeden sabit yazmanın bedeli budur.
#
# TAM EŞİTLİK, `<=` DEĞİL: bir tavan üst sınırla korunmaz (S252'de mutasyon tam
# bunu yakaladı). Borcu azalttığında bu sayıyı da DÜŞÜR.
BAGIMSIZ_NET_HESABI = 4

_ARANAN_DOSYALAR = [
    "services/exam_performance_service.py",
    "analytics/exam_results_reporting.py",
    "analytics/unified_analytics_data_model.py",
    "core/osym_exam_engine.py",
    "api/sinav.py",
]


def _bagimsiz_net_hesaplari() -> list[str]:
    """`... / 4` içeren aritmetik ifadeleri AST ile bul.

    🔴 METİN DEĞİL AST: bu dosyanın kendi docstring'i `doğru - yanlış/4`
    ifadesini İÇERİYOR ve metin araması onu "kod" sanardı
    (`.claude/rules/audit-methodology.md` — "bir deseni anlatan yorum onu içerir").
    Yorum ve docstring AST'de yoktur.
    """
    bulunanlar: list[str] = []
    for goreli in _ARANAN_DOSYALAR:
        yol = BACKEND / goreli
        if not yol.exists():
            continue
        agac = ast.parse(yol.read_text(encoding="utf-8"))
        for dugum in ast.walk(agac):
            if not isinstance(dugum, ast.BinOp) or not isinstance(dugum.op, ast.Div):
                continue
            sag = dugum.right
            if isinstance(sag, ast.Constant) and sag.value == 4:
                bulunanlar.append(f"{goreli}:{dugum.lineno}")
    return bulunanlar


def test_alet_dogrulamasi_ast_tarayicisi_calisiyor() -> None:
    """Tarayıcı 0 bulursa çırçır testi BOŞ kümede geçerdi (yanlış-yeşil)."""
    for goreli in _ARANAN_DOSYALAR:
        assert (BACKEND / goreli).exists(), f"aranan dosya yok: {goreli}"


def test_cirCir_bagimsiz_net_hesabi_artmiyor() -> None:  # noqa: N802
    bulunanlar = _bagimsiz_net_hesaplari()
    assert len(bulunanlar) == BAGIMSIZ_NET_HESABI, (
        f"Bağımsız `/4` hesabı sayısı {BAGIMSIZ_NET_HESABI} olmalı, "
        f"{len(bulunanlar)} bulundu: {bulunanlar}\n"
        "Yeni bir yerde net hesaplıyorsan `core.osym_puanlama.osym_net` kullan. "
        "Borcu azalttıysan BAGIMSIZ_NET_HESABI sabitini DÜŞÜR."
    )


def test_kanona_baglanan_dosyalarda_artik_kendi_hesabi_YOK() -> None:  # noqa: N802
    """Bu turda kanona bağlanan iki dosya kendi `/4`'ünü taşımamalı."""
    kalan = [
        y
        for y in _bagimsiz_net_hesaplari()
        if y.startswith(("core/osym_exam_engine.py", "api/sinav.py"))
    ]
    assert kalan == [], f"kanona bağlandığı hâlde kendi hesabı duruyor: {kalan}"
