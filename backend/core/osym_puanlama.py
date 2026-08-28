"""ÖSYM net hesabı — TEK KAYNAK.

NEDEN AYRI BİR MODÜL (27 Ağu 2026)
----------------------------------
Net hesabı üretimde **beş ayrı yerde** ve **iki çelişen politikayla** yaşıyordu:

    core/osym_exam_engine.py:1940   net = doğru                     (cezasız)
    core/osym_exam_engine.py:1193   net = doğru                     (cezasız, kopya)
    api/sinav.py:789                net = doğru                     (cezasız, kopya)
    services/exam_performance_service.py:274,391   doğru - yanlış/4 (cezalı)
    analytics/exam_results_reporting.py:124        max(0, ...)      (cezalı + kırpma)

Üçü aynı gerekçeyi taşıyordu: *"ÖSYM 2023+ 1/4 ceza kaldırıldı"*. Bir inanç üç
dosyaya kopyalanmıştı ve **yanlıştı** — kural hâlâ geçerli (27 Ağu 2026'da
operatör doğruladı).

Bu KULLANICI-GÖRÜNÜR bir çelişkiydi: aynı oturum açıkken
`/api/v1/osym-exam/{sid}/performance` cezasız, `/api/v1/study-plan/projection`
cezalı net servis ediyordu. Öğrenciye sınav hazırlığı hakkında **şişirilmiş**
bir sayı gösteriliyordu — ki A1 altın yolunun kabul kriteri tam olarak
"netini görür".

KURAL
-----
    net = doğru - (yanlış / 4)

Boş cevabın cezası YOKTUR; bu yüzden fonksiyon boş sayısını hiç almaz — alsaydı
çağıran onu hesaba katması gerektiğini sanabilirdi.

KIRPMA YOK — KASITLI
--------------------
Net 0'a **kırpılmaz**. Negatif net Türk deneme kültüründe standarttır ve
kırpmak tahmin etmenin verdiği zararı gizler: öğrenci "0 net" görüp "hiç
değilse sıfırdayım" sanır, oysa 8 yanlışla -2.0'dadır. Bu karar
`tests/unit/test_osym_puanlama.py` içinde çivilenmiştir.
"""

from __future__ import annotations

# ÖSYM: 4 yanlış 1 doğruyu götürür. Sabit BURADA, çağrı yerlerinde DEĞİL —
# kural değişirse tek satır değişsin diye.
YANLIS_BOLEN = 4


def osym_net(dogru_sayisi: int, yanlis_sayisi: int) -> float:
    """ÖSYM netini döndür: ``doğru - yanlış/4``.

    Args:
        dogru_sayisi: Doğru cevap sayısı.
        yanlis_sayisi: Yanlış cevap sayısı. **Boş cevaplar dahil DEĞİL** —
            ÖSYM'de boşun cezası yoktur.

    Returns:
        Net. Negatif olabilir ve **kırpılmaz** (modül docstring'indeki gerekçe).

    Raises:
        ValueError: Sayılardan biri negatifse. Sessizce 0 saymak, veri
            kusurunu öğrenciye doğru bir netmiş gibi gösterirdi.
    """
    if dogru_sayisi < 0 or yanlis_sayisi < 0:
        raise ValueError(
            f"net hesabı negatif sayı alamaz (doğru={dogru_sayisi}, "
            f"yanlış={yanlis_sayisi})"
        )
    return float(dogru_sayisi) - (float(yanlis_sayisi) / YANLIS_BOLEN)
