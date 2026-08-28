"""Serving-path leak guard — öğrenci-yüzü seçim yolları kalite kapısını kullanmalı.

Regression: 94K active-ama-yargılanmamış (unverified/pending) soru sızıntısı.
`load_assessment_items` (placement) ve `build_sync_package` (offline)
question_bank'ı yalnız `is_active` ile sorguluyordu.

Test stratejisi: test harness DB'yi sqlite'a çeviriyor (bkz. conftest.py:21), bu
yüzden canlı-DB entegrasyonu yerine KAYNAK-introspeksiyon guard'ı kullanılır
(lint-tarzı, DB'siz, flaky değil). Davranışsal karşılığı
`tests/e2e/test_quality_gate_leak.py` — o gerçek PostgreSQL ister ve DB yoksa
SKIP olur. Yani bu dosya CI'da tek çalışan kapı bekçisidir; kapsamı gerçekten
korunan yüzeyle eşleşmek ZORUNDA.

27 TEM 2026 — İKİ KUSUR DÜZELTİLDİ
----------------------------------
1. KAPSAM YALANI: docstring "her student-facing soru-seçim fonksiyonu" diyordu
   ama test 3 kapılı yerden yalnız 2'sini kontrol ediyordu.
   `soru_bankasi_service._safe_for_beta_gate()` — yani kapının TA KENDİSİ —
   guard'sızdı; silinse bu dosya yeşil kalırdı.
2. SUBSTRING KAZASI: `_GATE = "v_safe_for_beta"` idi. Kapı `mv_safe_for_beta`'ya
   taşındığında test KAZA ESERİ geçecekti (biri diğerinin alt dizesi). Artık
   iddia `core.quality_gate` sabitlerine bağlı: ad değişirse test de birlikte
   taşınır, sessizce geçmez.

Bkz: .claude/rules/testing.md #15 (dersi enforce et), #31 (is_active sızıntısı),
     core/quality_gate.py, docs/quality_review_status_convention.md
"""

from __future__ import annotations

import inspect

from core.quality_gate import SAFE_POOL_RELATION
from services import (
    offline_sync_service,
    placement_assessment_service,
    soru_bankasi_service,
)

# Kaynakta kapıyı temsil eden kabul edilebilir imzalar. Ya ortak yardımcı
# çağrılır ya da (kapı tanımının kendisinde) ilişki adı doğrudan geçer.
_GATE_MARKERS = ("safe_for_beta_gate", "safe_for_beta_sql", SAFE_POOL_RELATION)


def _assert_gated(fn, label: str) -> None:
    src = inspect.getsource(fn)
    assert any(marker in src for marker in _GATE_MARKERS), (
        f"{label} kalite kapısını kullanmıyor. Beklenen imzalardan biri "
        f"geçmeli: {_GATE_MARKERS}. Kapısız sorgu 85K yargılanmamış/reddedilmiş "
        f"soruyu öğrenciye servis eder (bkz. testing.md #31)."
    )


def test_gate_relation_is_a_filtered_pool_not_the_base_table():
    """Kapı ilişkisi filtrelenmiş havuz olmalı — ham tablo DEĞİL.

    Diğer testler `SAFE_POOL_RELATION` sabitine bağlı; sabit `question_bank`
    yapılırsa kapı sessizce no-op'a döner ve o testler yeşil kalır (27 Tem
    2026 mutasyon testinde bu delik ölçüldü). Bu canary sabiti sözleşmeye
    bağlar: adı değiştirmek bilinçli bir karar hâline gelir.
    """
    assert SAFE_POOL_RELATION not in {"question_bank", "questions"}, (
        f"Kapı ham soru tablosunu gösteriyor ({SAFE_POOL_RELATION}) — "
        f"bu kapıyı no-op yapar, hiçbir şey filtrelenmez."
    )
    assert SAFE_POOL_RELATION.endswith("safe_for_beta"), (
        f"Beklenmeyen kapı ilişkisi: {SAFE_POOL_RELATION}. Havuz adı "
        f"'safe_for_beta' ile bitmeli (v_ canlı view / mv_ matview)."
    )


def test_gate_helper_compiles_to_pool_lookup():
    """Kapı DAVRANIŞSAL olarak havuz ilişkisini sorgulamalı.

    Neden kaynak-taraması DEĞİL: `_safe_for_beta_gate` fonksiyonunun ADI
    "safe_for_beta_gate" dizesini zaten içeriyor. `inspect.getsource` ile
    marker aramak bu fonksiyon için HER ZAMAN geçerdi — gövdesi tamamen
    boşaltılsa bile. (27 Tem 2026: mutasyon testiyle yakalandı; guard'ın
    ilk hâli `return Question.id.isnot(None)` mutasyonunu SESSİZCE geçirdi.)

    Derlenmiş SQL'e bakmak bu deliği kapatır ve DB gerektirmez.
    """
    clause = str(soru_bankasi_service._safe_for_beta_gate())
    assert SAFE_POOL_RELATION in clause, (
        f"_safe_for_beta_gate() havuz ilişkisini sorgulamıyor. "
        f"Derlenen koşul: {clause!r}"
    )


def test_placement_pool_uses_gate():
    """Seviye-tespit soru havuzu kalite kapısını kullanmalı."""
    _assert_gated(
        placement_assessment_service.load_assessment_items,
        "placement load_assessment_items",
    )


def test_offline_package_uses_gate():
    """Offline paket soru seçimi kalite kapısını kullanmalı."""
    _assert_gated(
        offline_sync_service.build_sync_package,
        "offline build_sync_package",
    )
