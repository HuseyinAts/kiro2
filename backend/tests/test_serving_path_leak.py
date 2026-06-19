"""Serving-path leak guard — placement + offline_sync ONLY v_safe_for_beta servis etmeli.

Regression: 94K active-ama-yargılanmamış (unverified/pending) soru sızıntısı.
load_assessment_items (placement) ve build_sync_package (offline) question_bank'ı
yalnız is_active ile sorguluyordu; soru_bankasi_service._safe_for_beta_gate()'in
zorladığı v_safe_for_beta kapısını BYPASS ediyordu (placement havuzunun %94,1'i
yargılanmamış soruydu).

Test stratejisi: test harness DB'yi mock'lar (TESTING env), bu yüzden canlı-DB
entegrasyonu yerine KAYNAK-introspeksiyon guard kullanılır (lint-tarzı, DB'siz,
flaky değil). Her student-facing soru-seçim fonksiyonu v_safe_for_beta'ya
REFERANS vermeli. Fix öncesi FAIL, sonrası PASS.

Bkz: .claude/rules/testing.md #15 (dersi enforce et), #31 (is_active sızıntısı),
     docs/quality_review_status_convention.md
"""

from __future__ import annotations

import inspect

from services import offline_sync_service, placement_assessment_service

_GATE = "v_safe_for_beta"


def test_placement_pool_uses_v_safe_gate():
    """Seviye-tespit soru havuzu v_safe_for_beta kapısını kullanmalı."""
    src = inspect.getsource(placement_assessment_service.load_assessment_items)
    assert _GATE in src, (
        "placement load_assessment_items v_safe_for_beta kapısını kullanmıyor; "
        "is_active-only sorgu 94K unverified/pending soruyu öğrenciye sızdırır"
    )


def test_offline_package_uses_v_safe_gate():
    """Offline paket soru seçimi v_safe_for_beta kapısını kullanmalı."""
    src = inspect.getsource(offline_sync_service.build_sync_package)
    assert _GATE in src, (
        "offline build_sync_package v_safe_for_beta kapısını kullanmıyor; "
        "is_active-only sorgu yargılanmamış soruyu offline'a indirir"
    )
