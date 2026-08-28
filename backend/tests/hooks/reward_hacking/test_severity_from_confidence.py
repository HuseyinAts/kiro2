"""Bekçi sözleşmesi: tavsiye bloklamaz, gerçek tespit bloklar.

29 Tem 2026 ÖLÇÜMÜ — `git push` bloke oldu. Gerekçe:

    hardcoded_test_data_detector.py:224-232
        if 'hypothesis' not in content.lower() and test_count > 10:
            ... message="Consider Hypothesis for property-based testing", confidence=0.5

Bu bir TAVSİYE (confidence=0.5, tüm dedektörlerdeki en düşük değer) ama CRITICAL sayılıp
exit 2 üretti. Hook'un kendi çıktısı da çelişkiliydi:

    ✅ No reward hacking patterns detected
    ❌ REWARD HACKING DETECTED - 1 critical issue(s)

KÖK NEDEN: `base_detector.py:145`
    severity = self.config.severity if self.config else self.default_severity
`confidence` sonuca yazılıyor ama severity'ye HİÇ etki etmiyor. Dedektör varsayılanı
CRITICAL olduğu için 0.5'lik tavsiye ile 0.95'lik `assert True` aynı sınıfa düşüyor.

EŞİK NEDEN 0.7 — ölçüldü, seçilmedi. Tüm dedektörlerdeki confidence dağılımı:
    0.95 x3 · 0.90 · 0.85 · 0.80 x2 · 0.75 · 0.70 x2   <- gerçek tespitler
    0.60 · 0.50                                         <- iki "Consider..." tavsiyesi
0.7 tam ayrım noktası. Eşik yukarı kaydırılırsa gerçek tespitler kör olur; aşağı
kaydırılırsa tavsiye yine bloklar.

BU DOSYANIN ASIL İŞİ: bekçiyi gevşetirken KÖR ETMEDİĞİMİZİ kanıtlamak. Aşağıdaki
`test_gercek_tespit_hala_bloklar` mutasyon güvencesidir — eşik değişikliği gerçek bir
reward-hacking desenini geçirmeye başlarsa KIRMIZIYA döner. O test olmadan bu
değişiklik "bekçiyi kendi push'unu geçirmek için gevşetme" olurdu.
"""

from __future__ import annotations

import pytest

from hooks.reward_hacking.base_detector import BaseDetector
from hooks.reward_hacking.models.enums import ExitCode, PatternType, SeverityLevel

pytestmark = [pytest.mark.unit, pytest.mark.security]


class _SahteDedektor(BaseDetector):
    """Sadece `_create_result`ı çağırmak için asgari somut dedektör."""

    name = "sahte"
    pattern_type = PatternType.HARDCODED_TEST_DATA

    def detect(self, file_path: str, content: str):  # pragma: no cover - kullanılmıyor
        return []

    def get_patterns(self):  # pragma: no cover - kullanılmıyor
        return []


def _sonuc(confidence: float):
    return _SahteDedektor()._create_result(
        file_path="x.py",
        line_number=1,
        code_snippet="kod",
        message="mesaj",
        confidence=confidence,
    )


@pytest.mark.parametrize("confidence", [0.5, 0.6, 0.69])
def test_dusuk_guvenli_bulgu_bloklamaz(confidence):
    """confidence < 0.7 tavsiyedir — CRITICAL olamaz, yani push'u bloklayamaz.

    Bu testin yakaladığı arıza: "Consider Hypothesis" gibi bir stil önerisi commit ve
    push'u durduruyordu. Blokladığı için de kimse mesajı okuyup düzeltmiyor, sadece
    bekçiyi atlatmanın yolunu arıyordu.
    """
    assert _sonuc(confidence).severity != SeverityLevel.CRITICAL


@pytest.mark.parametrize("confidence", [0.70, 0.75, 0.80, 0.85, 0.90, 0.95])
def test_gercek_tespit_hala_bloklar(confidence):
    """MUTASYON GÜVENCESİ: >=0.7 olan HER tespit CRITICAL kalmalı.

    Değerler uydurma değil — depodaki tüm dedektörlerin fiilen kullandığı confidence
    değerleri (assert_true, placeholder, echo_success, empty_exception, mock_abuse,
    coverage_manipulation, cicd_bypass). Biri bile CRITICAL olmaktan çıkarsa bekçi o
    desene karşı körelmiş demektir ve bu test kırmızıya döner.
    """
    assert _sonuc(confidence).severity == SeverityLevel.CRITICAL


def test_varsayilan_guven_kritik_kalir():
    """`_create_result` varsayılanı (0.95) CRITICAL olmalı — regex tespitlerinin yolu bu."""
    assert (
        _SahteDedektor()
        ._create_result(file_path="x.py", line_number=1, code_snippet="k", message="m")
        .severity
        == SeverityLevel.CRITICAL
    )


def test_esik_dedektorlerdeki_gercek_degerlerle_tutarli():
    """Eşik, depodaki confidence dağılımından KOPMAMALI.

    Yeni bir dedektör kuralı 0.7'nin altına bir değer koyarsa o kural sessizce
    bloklamaz hale gelir — bu kabul edilebilir. Ama 0.7 ile 0.95 arasındaki bir kural
    yanlışlıkla tavsiyeye düşerse bekçi körelir. Bu test sınırı belgeler ve sabitler.
    """
    from hooks.reward_hacking.base_detector import ADVISORY_CONFIDENCE_THRESHOLD

    assert pytest.approx(0.7) == ADVISORY_CONFIDENCE_THRESHOLD, (
        "Eşik değişiyorsa dedektörlerdeki confidence dağılımı YENİDEN ÖLÇÜLMELİ: "
        "grep -rn 'confidence=' backend/hooks/reward_hacking/detectors/"
    )


# ---------------------------------------------------------------------------
# Çıkış kodu sözleşmesi — severity düzeltmesi tek başına yetmedi
#
# 29 Tem: severity WARNING'e indi ama pre-commit çerçevesi SIFIR OLMAYAN her kodu
# başarısızlık sayar, dolayısıyla exit 1 de push'u bloklamaya devam etti.
#
# hook_manager.py:260-265
#     if critical > 0 or (warning > 0 and fail_on_warning): exit = 2
#     elif warning > 0:                                     exit = 1
#
# CLI'nin kendi yardım metni "Exit codes: 0=clean, 1=warning, 2=critical (blocks commit)"
# diyor ve ayrıca `--fail-on-warning` diye OPT-IN bir bayrak sunuyor. Eğer exit 1 zaten
# blokluyorsa o bayrak anlamsızdır. Bayrağın varlığı niyetin kanıtı: uyarı varsayılanda
# bloklamaz, isteyen CI --fail-on-warning ile sıkılaştırır.
# ---------------------------------------------------------------------------


def _cli(tmp_path, icerik: str, *ek_arg: str) -> int:
    from hooks.reward_hacking.cli import main

    dosya = tmp_path / "test_ornek.py"
    dosya.write_text(icerik, encoding="utf-8")
    return main([str(dosya), *ek_arg])


# 12'den fazla test + 'hypothesis' geçmeyen içerik -> yalnızca advisory bulgu üretir
_SADECE_UYARI = "\n".join(
    f"def test_{i}():\n    x = {i}\n    assert x == {i}\n" for i in range(13)
)
_GERCEK_IHLAL = "def test_sahte():\n    assert True\n"


def test_sadece_uyari_varsa_cikis_kodu_bloklamaz(tmp_path):
    """Yalnız advisory bulgu -> exit 0. pre-commit sıfır olmayan HER kodu bloklar."""
    assert _cli(tmp_path, _SADECE_UYARI) == ExitCode.SUCCESS


def test_fail_on_warning_ile_uyari_bloklar(tmp_path):
    """`--fail-on-warning` bayrağı anlamını korumalı: sıkı modda uyarı bloklar."""
    assert _cli(tmp_path, _SADECE_UYARI, "--fail-on-warning") == ExitCode.BLOCKING_ERROR


def test_gercek_ihlal_varsayilanda_da_bloklar(tmp_path):
    """MUTASYON GÜVENCESİ: `assert True` bayraksız da exit 2 vermeli."""
    assert _cli(tmp_path, _GERCEK_IHLAL) == ExitCode.BLOCKING_ERROR
