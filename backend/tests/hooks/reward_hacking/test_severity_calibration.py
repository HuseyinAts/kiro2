"""Bekçi kalibrasyonu: BEYAN EDİLEN severity fiilen uygulanmalı (#453).

30 Tem 2026 ÖLÇÜMÜ — `python scripts/quality/guard_severity_census.py`, 250 gerçek
test dosyası (`backend/tests`, sıralı ilk 250):

    pattern_type              CRITICAL  WARNING
    assert_true                      6        0
    empty_exception                 54        0
    hardcoded_test_data             74      253
    mock_abuse                     336        0
    placeholder                      4        0
    ------------------------------------------
    TOPLAM                         474      253
    TEK BAŞINA push'u bloklayan dosya : 68/250

474 CRITICAL'in **410'u (%86,5)** kendini WARNING ilan eden iki dedektörden geliyor.

KÖK NEDEN — kaldırma deneyiyle ölçüldü, kod okunarak değil:

    base_detector.py:180
        severity = self.config.severity if self.config else self.default_severity

`self.config` DAİMA truthy: Pydantic BaseModel `__bool__`/`__len__` tanımlamaz, ayrıca
`__init__` içinde `config or DetectorConfig()` var — yani `config=None` bile bir model
üretiyor. Canlı probe:

    bool(DetectorConfig())              -> True
    MockAbuseDetector(config=None)      -> DetectorConfig (bool=True)
    MockAbuseDetector beyan=WARNING     -> üretilen=CRITICAL   (dal ölü)
    HardcodedTestDataDetector beyan=WARNING -> üretilen=CRITICAL

Aynı niyet İKİNCİ bir yerde de ölüydü: `config/reward_hacking_config.yaml` bu iki
dedektöre `severity: WARNING` diyordu, ama pre-push `--config` geçmiyor ve
`GlobalConfig().detectors == {}` — YAML hiç okunmuyordu. **#454'te SİLİNDİ**:
elle yüklendiğinde sonuç birebir aynıydı (crit 64 / warn 658 / toplam 722, küme
farkı 0), yani tam no-op. Artık tek doğruluk kaynağı aşağıdaki parametrik testin
denetlediği sınıf beyanları. (`--config <yol>` yeteneği CI sıkılaştırması için
duruyor.)

NEDEN WARNING DOĞRU SEVİYE — ölçüldü: `hardcoded_test_data` dedektörü `_is_test_file`
kapısı yüzünden üretim kodunu HİÇ taramıyor. Üretimde `password = "test1234"` -> 0
bulgu. Yani CRITICAL statüsü tek bir gerçek sır bile yakalamıyor; karşılığında sıradan
test dosyalarını push edilemez yapıyor. Sır taraması `push_secret_guard.py` + ruff S105.

`mock_abuse` için de aynısı: dedektör "collaborator mock'landı" (meşru) ile "test edilen
birim mock'landı" (gerçek hile) arasını AYIRT EDEMEZ — `MagicMock()` deseni ikisinde de
eşleşir. Ayırt edemeyen bir sinyal bloklayıcı olamaz; tavsiye olur.

Sözleşme kardeşi: test_severity_from_confidence.py (confidence -> severity eşiği).
"""

from __future__ import annotations

import pytest

from hooks.reward_hacking.cli import main as cli_main
from hooks.reward_hacking.detectors import (
    HardcodedTestDataDetector,
    MockAbuseDetector,
)
from hooks.reward_hacking.hook_manager import HookManager
from hooks.reward_hacking.models.detection_result import DetectorConfig
from hooks.reward_hacking.models.enums import ExitCode, SeverityLevel

pytestmark = [pytest.mark.unit, pytest.mark.security]


# ---------------------------------------------------------------------------
# 1) SINIF-DÜZEYİ BEYAN FİİLEN UYGULANIR
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "detector_cls", HookManager.DETECTOR_CLASSES, ids=lambda c: c.__name__
)
def test_beyan_edilen_default_severity_uretilene_yansir(detector_cls):
    """Her dedektörün `default_severity` beyanı ürettiği bulguya yansımalı.

    Bu test tek bir dedektöre değil SÖZLEŞMEYE bakar: ileride biri
    `default_severity = WARNING` yazdığında o beyan sessizce ölü kalmasın.
    Ölçüm anında 8 dedektörün 2'sinde (Mock, HardcodedTestData) KIRMIZI.
    """
    detector = detector_cls()
    sonuc = detector._create_result(
        file_path="tests/test_ornek.py",
        line_number=1,
        code_snippet="kod",
        message="mesaj",
        confidence=0.95,
    )
    assert sonuc.severity == detector.default_severity, (
        f"{detector_cls.__name__} beyan={detector.default_severity} "
        f"ama uretilen={sonuc.severity} — beyan olu"
    )


@pytest.mark.parametrize("detector_cls", [MockAbuseDetector, HardcodedTestDataDetector])
def test_mock_ve_hardcoded_bulgusu_push_bloklamaz(detector_cls):
    """İki heuristik dedektör CRITICAL üretemez — yoksa push'u bloklar.

    `should_block` = `critical_count > 0`. Bu iki dedektör tasarım kokusu
    raporluyor, hile kanıtı değil (bkz modül docstring'i).
    """
    sonuc = detector_cls()._create_result(
        file_path="tests/test_ornek.py",
        line_number=1,
        code_snippet="MagicMock()",
        message="mesaj",
        confidence=0.95,
    )
    assert sonuc.severity != SeverityLevel.CRITICAL


def test_acik_config_severity_beyani_ezer():
    """MUTASYON GÜVENCESİ: override yolu ölmemeli.

    Düzeltme `default_severity`yi kablolarken `config.severity`yi devre dışı
    bırakırsa CI/YAML ile sıkılaştırma imkânı kaybolur. `_create_result` sadece
    `self.default_severity` döndürmeye başlarsa bu test kırmızıya döner.
    """
    detector = MockAbuseDetector(config=DetectorConfig(severity=SeverityLevel.CRITICAL))
    sonuc = detector._create_result(
        file_path="tests/test_ornek.py",
        line_number=1,
        code_snippet="MagicMock()",
        message="mesaj",
        confidence=0.95,
    )
    assert sonuc.severity == SeverityLevel.CRITICAL


# ---------------------------------------------------------------------------
# 2) UÇTAN UCA ÇIKIŞ KODU — asıl kullanıcı görünür davranış
# ---------------------------------------------------------------------------

# Yalnızca mock + hardcoded kuralı tetikler. assert_true / placeholder /
# empty_exception / coverage_manipulation / cicd_bypass deseni BİLİNÇLİ olarak
# yok — bu dosya "sıradan test dosyası" temsilcisi.
_SIRADAN_TEST_DOSYASI = """\
from unittest.mock import MagicMock, patch


@patch("modul.a")
@patch("modul.b")
def test_ornek(b, a):
    istemci = MagicMock()
    email = "test@test.com"
    user_id = 1
    assert istemci is not None
    assert email.endswith(".com")
    assert user_id > 0
"""

_GERCEK_IHLAL_ASSERT = "def test_sahte():\n    assert True\n"
_GERCEK_IHLAL_BARE_EXCEPT = (
    "def f():\n    try:\n        g()\n    except:\n        pass\n"
)


def _cli(tmp_path, icerik: str, *ek_arg: str) -> int:
    dosya = tmp_path / "test_ornek.py"
    dosya.write_text(icerik, encoding="utf-8")
    return cli_main([str(dosya), *ek_arg])


def test_siradan_test_dosyasi_push_edilebilir(tmp_path):
    """Mock + hardcoded idiyomu içeren normal bir test dosyası exit 0 vermeli.

    Ölçüm: fix öncesi bu dosya exit 2 veriyordu. 250 dosyalık korpusta 68 dosya
    tek başına aynı sebeple push'u blokluyordu — bekçinin fiili işlevi
    `--no-verify`'ı alışkanlığa çevirmekti.
    """
    assert _cli(tmp_path, _SIRADAN_TEST_DOSYASI) == ExitCode.SUCCESS


def test_siradan_test_dosyasi_bulguyu_yine_de_raporlar(tmp_path):
    """KÖRLEŞME GÜVENCESİ: gevşetme = susturma DEĞİL.

    Bulgular WARNING olarak üretilmeye devam etmeli; `--fail-on-warning` ile
    sıkı modda yine bloklamalı. Dedektör tamamen kapatılırsa bu test kırmızıya
    döner (exit 0 gelir).
    """
    assert (
        _cli(tmp_path, _SIRADAN_TEST_DOSYASI, "--fail-on-warning")
        == ExitCode.BLOCKING_ERROR
    )


@pytest.mark.parametrize(
    "icerik",
    [_GERCEK_IHLAL_ASSERT, _GERCEK_IHLAL_BARE_EXCEPT],
    ids=["assert_true", "bare_except"],
)
def test_gercek_ihlal_bayraksiz_da_bloklar(tmp_path, icerik):
    """MUTASYON GÜVENCESİ: kalibrasyon gerçek reward-hacking'i geçirmemeli.

    `default_severity` kablolaması yanlışlıkla tüm dedektörleri WARNING'e
    indirirse (ya da eşik oynarsa) bu test kırmızıya döner.
    """
    assert _cli(tmp_path, icerik) == ExitCode.BLOCKING_ERROR
