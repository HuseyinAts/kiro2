"""String-literal bagisikligi: bekci kendi fixture korpusunu ihlal saymamali.

30 Tem 2026 — bekcinin 4. kusuru. `pre-commit run reward-hacking-check` bu
paketin test dosyalarini push'ta bloklamaya basladi:

    test_detectors.py -> exit 2, 5 critical
      Line 342: Bare except: - use specific exception type
      Line 286: Mock always returns True
      Line 387: Magic ID number: 1
      Line 225: pragma: no cover without documented reason
      Line 1:   Many mocks without verification

Bu bulgularin HICBIRI gercek kod degil — hepsi ucgen-tirnakli fixture
string'lerinin ICINDE. Kontrollu A/B (gercek yolda) olculdu: dosya benim
degisikligimden ONCE de exit 2 veriyordu (4 critical). Yani gizli tuzak:
bu 3 dosyaya dokunan HER commit push'ta bloklanir.

    test_detectors.py            -> exit 2
    test_hook_manager.py         -> exit 2
    test_properties.py           -> exit 2
    test_severity_from_confidence.py -> exit 0

KOK NEDEN: base_detector._regex_detect ham metin uzerinde finditer kosuyor,
string literal ile kodu ayirt etmiyor.

NEDEN `ast` DEGIL `tokenize`: ast dugumlerinde `col_offset` UTF-8 BAYT
cinsindendir. Bu depo Turkce karakterlerle dolu, bayt != karakter oldugu
icin span'ler kayar. Olculdu:

    satir: '    assert True, "guso mesaji"'  (32 karakter / 38 bayt)
    ast:   col=17 end_col=38   -> end_col SATIR UZUNLUGUNU ASIYOR
    tokenize: span=(108,123)   -> KAYNAK[108:123] == '"guso mesaji"'  (dogru)

tokenize karakter tabanlidir; bu yuzden span kaynagi odur.
"""

from __future__ import annotations

import pytest

from backend.hooks.reward_hacking.detectors import (
    AssertTrueDetector,
    EmptyExceptionDetector,
)
from backend.hooks.reward_hacking.models.enums import ExitCode

pytestmark = [pytest.mark.unit, pytest.mark.security]


@pytest.fixture
def assert_dedektor():
    return AssertTrueDetector()


@pytest.fixture
def except_dedektor():
    return EmptyExceptionDetector()


# ---------------------------------------------------------------------------
# 1) Bastirma: literal icindeki desen bulgu URETMEZ
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_string_icindeki_desen_bulunmaz(assert_dedektor):
    """Ucgen-tirnakli fixture icindeki `assert True` TEST VERISIDIR, ihlal degil."""
    content = 'ORNEK = """\ndef test_sahte():\n    assert True\n"""\n'
    results = await assert_dedektor.detect("test_x.py", content)
    assert (
        results == []
    ), f"literal icindeki desen bulgu uretti: {[r.message for r in results]}"


@pytest.mark.asyncio
async def test_tek_tirnakli_string_icinde_de_bulunmaz(assert_dedektor):
    """Tek satirli string de literaldir."""
    content = 'DESEN = "assert True"\n'
    results = await assert_dedektor.detect("test_x.py", content)
    assert (
        results == []
    ), f"tek-tirnakli literal bulgu uretti: {[r.message for r in results]}"


@pytest.mark.asyncio
async def test_bare_except_literal_icinde_bulunmaz(except_dedektor):
    """`_detect_bare_except` de ayni bagisikliga tabi."""
    content = 'ORNEK = """\ntry:\n    x()\nexcept:\n    handle()\n"""\n'
    results = await except_dedektor.detect("test_x.py", content)
    assert (
        results == []
    ), f"literal icindeki bare except bulgu uretti: {[r.message for r in results]}"


# ---------------------------------------------------------------------------
# 2) KORLESME BEKCILERI — bir bekci gevsetiliyor, kanit zorunlu
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gercek_ihlal_hala_bulunur(assert_dedektor):
    """KONTROL: gercek kodda `assert True` HALA yakalanmali."""
    content = "def test_sahte():\n    assert True\n"
    results = await assert_dedektor.detect("test_x.py", content)
    assert len(results) >= 1, "gercek ihlal korlestirildi"


@pytest.mark.asyncio
async def test_ayni_satirda_string_ve_ihlal(assert_dedektor):
    """`assert True, "mesaj"` GERCEK ihlaldir — satiri komple bastirmak YANLIS.

    Satir-granulerliginde filtre yazilirsa bu test kirmiziya doner: satirda
    string VAR ama ihlal string'in DISINDA. Karakter-bazli span sarti.
    """
    content = 'def test_sahte():\n    assert True, "aciklama"\n'
    results = await assert_dedektor.detect("test_x.py", content)
    assert len(results) >= 1, "ayni satirda string olmasi gercek ihlali maskeledi"


@pytest.mark.asyncio
async def test_turkce_karakter_span_kaymasi_yok(assert_dedektor):
    """ast/bayt-offset regresyon bekcisi.

    Ihlalden ONCE Turkce karakterli string var. Span'ler BAYT cinsinden
    hesaplanirsa kayar ve gercek ihlali yutar.
    """
    content = 'MESAJ = "ğüşiöçİI karakterler"\ndef test_sahte():\n    assert True\n'
    results = await assert_dedektor.detect("test_x.py", content)
    assert (
        len(results) >= 1
    ), "Turkce karakterli literal sonrasi ihlal yutuldu (bayt/karakter kaymasi)"


@pytest.mark.asyncio
async def test_parse_edilemeyen_dosyada_filtre_yok(assert_dedektor):
    """Sozdizimi bozuksa FILTRELEME YAPILMAZ — bekci sessizce korlesmemeli."""
    content = "def bozuk(:\n    assert True\n"
    results = await assert_dedektor.detect("test_x.py", content)
    assert len(results) >= 1, "parse hatasi bekciyi korlestirdi (fail-open olmaliydi)"


# ---------------------------------------------------------------------------
# 3) ENTEGRASYON — asil sozlesme: bekcinin kendi korpusu push edilebilir olmali
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bekcinin_kendi_korpusu_bloklanmaz():
    """Bu paketin test dosyalari pre-push kapisini GECMELI.

    Bu testin kirmiziya donmesi iki seyden birini gosterir:
      (a) filtre bozuldu, fixture'lar yine ihlal sayiliyor, veya
      (b) bu dizine GERCEKTEN tembel bir test eklendi.
    Ikisi de incelenmeyi hak eder — bu yuzden dosya listesi sabitlenmedi.
    """
    from pathlib import Path

    from backend.hooks.reward_hacking.hook_manager import HookManager

    dizin = Path(__file__).parent
    dosyalar = [str(p) for p in sorted(dizin.glob("test_*.py"))]
    assert len(dosyalar) >= 4, f"korpus beklenenden kucuk: {dosyalar}"

    sonuc = await HookManager().run_hooks(dosyalar)
    assert sonuc.exit_code == ExitCode.SUCCESS, (
        f"bekci kendi korpusunu blokluyor (exit={sonuc.exit_code}, "
        f"critical={sonuc.critical_count}):\n{sonuc.summary}"
    )
