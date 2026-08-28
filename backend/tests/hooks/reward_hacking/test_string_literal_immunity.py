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


# ---------------------------------------------------------------------------
# 4) YORUM KURALI — iki yonlu
#
# 30 Tem oz-denetiminde bulundu: bu kural (`bulgu_bastirilmali` icindeki
# `if "#" in desen: return False`) c8792f022 ile GONDERILDI ama TEK TESTI YOKTU.
# Kural olcumle secilmisti (desen dagilimi sayildi) ama bekciyi
# korlestirebilecek en riskli dal oldugu icin civilenmesi sart.
#
# Kural: eslesme yorum icindeyse, ancak DESENIN KENDISI '#' iceriyorsa
# mesrudur (`# pragma: no cover`, `# noqa`, `# TODO: implement` gibi
# kurallarin KONUSU yorumdur). Icermiyorsa yorumdaki eslesme
# calistirilamaz metindir ve bastirilir.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_yorumdaki_desen_bastirilir(assert_dedektor):
    """Yorumdaki fake-assertion deseni calistirilamaz -> bulgu URETMEZ.

    Gercek vaka: test_detectors.py'de
    `("assert_true", 3),  # At least 3 patterns for assert True`
    satiri push'u blokluyordu. O desen ('\\bassert\\s+True\\s*$') '#' ICERMEZ.
    """
    content = 'AYAR = {"a": 3}  # ornek olarak: assert True\n'
    results = await assert_dedektor.detect("test_x.py", content)
    assert (
        results == []
    ), f"yorumdaki desen bulgu uretti: {[r.message for r in results]}"


@pytest.mark.asyncio
async def test_yorum_konulu_desen_yorumda_hala_atesler():
    """KORLESME BEKCISI: deseni '#' iceren kural yorumda bastirilmaz.

    Bu test olmadan yorum bastirmasi `# pragma: no cover` / `# noqa` /
    `# type: ignore` kurallarini komple kor edebilirdi — o kurallarin
    tek yasadigi yer yorumdur.
    """
    from backend.hooks.reward_hacking.detectors import CoverageManipulationDetector

    dedektor = CoverageManipulationDetector()
    for content, ad in (
        ("if DEBUG:  # pragma: no cover\n", "pragma: no cover"),
        ("x = hesapla()  # noqa\n", "noqa"),
        ("y = donustur()  # type: ignore\n", "type: ignore"),
    ):
        results = await dedektor.detect("test_x.py", content)
        assert len(results) >= 1, f"yorum-konulu kural korlestirildi: {ad}"


@pytest.mark.asyncio
async def test_todo_yorum_kurali_hala_atesler():
    """Satir-sonu `# TODO: implement` yakalanmali (deseninde '#' var).

    NOT: PlaceholderDetector'in `pass` + yorum fixture'i buraya YAZILAMADI —
    `.claude/hooks/pre-tool-use.py` (Claude Code yazma-ani bekcisi, AYRI bir
    uygulama) o literali gercek kod sanip Edit'i blokluyor. Yani pre-push
    bekcisinde c8792f022 ile duzeltilen kusurun ayni sinifi orada da var.
    Ayri is olarak kaydedildi; kural buradaki 4 vakayla zaten iki yonlu civili.
    """
    from backend.hooks.reward_hacking.detectors import PlaceholderDetector

    results = await PlaceholderDetector().detect(
        "test_x.py", "x = 1  # TODO: implement this\n"
    )
    assert len(results) >= 1, "satir-sonu TODO kurali korlestirildi"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "#451 — ONCEDEN VAR OLAN hole (A/B ile dogrulandi, literal filtresiyle "
        "ILGISIZ): base_detector._is_in_exception yorum-ONLY satirdaki HER "
        "bulguyu atiyor ('assert' gecenler haric). Olculdu: satir-sonu "
        "`if DEBUG:  # pragma: no cover` -> 1 bulgu, tek basina "
        "`# pragma: no cover` -> 0 bulgu. coverage_manipulation desenlerinin "
        "8'inden 6'si '#' ile BASLIYOR, yani fiilen etkisiz. Hole kapatilinca "
        "bu test XPASS olur ve strict=True onu KIRMIZIYA cevirir -> xfail'i "
        "kaldir. Yanlis davranisi 'dogru' diye civilemek yerine DOGRU sozlesme "
        "iddia ediliyor."
    ),
)
@pytest.mark.asyncio
async def test_tek_basina_yorum_satiri_da_yakalanmali():
    """DOGRU sozlesme: tek basina `# pragma: no cover` de bulgu URETMELI."""
    from backend.hooks.reward_hacking.detectors import CoverageManipulationDetector

    results = await CoverageManipulationDetector().detect(
        "test_x.py", "# pragma: no cover\nx = 1\n"
    )
    assert len(results) >= 1, "tek basina yorum satiri kor"


# ---------------------------------------------------------------------------
# 5) BaseException — gather(return_exceptions=True) CancelledError DA dondurur
#
# 30 Tem: c690854c5'te `isinstance(result, Exception)` -> `BaseException`
# yapildi (mypy zorladi) ama TESTI YAZILMADI. Bu salt tip duzeltmesi degil:
# CancelledError Python 3.8+'ta Exception'in alt sinifi DEGILDIR, dolayisiyla
# eski daraltma onu `results.extend(...)` icine sokup TypeError uretiyordu.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancellederror_toplamayi_cokertmez():
    """Iptal edilen dedektor sessizce atlanir, digerleri calismaya devam eder.

    MUTASYON: hook_manager'da `BaseException` -> `Exception` yapilirsa
    `results.extend(CancelledError())` calisir ve TypeError firlatir.
    """
    import asyncio

    from backend.hooks.reward_hacking.hook_manager import HookManager

    yonetici = HookManager()
    assert yonetici.detectors, "hic dedektor kayitli degil"

    async def iptal_firlat(file_path: str, content: str):
        raise asyncio.CancelledError

    yonetici.detectors[0].detect = iptal_firlat  # type: ignore[method-assign]

    sonuclar = await yonetici._run_detectors(
        "test_x.py", "def test_sahte():\n    assert True\n"
    )

    assert isinstance(sonuclar, list)
    assert all(
        not isinstance(r, BaseException) for r in sonuclar
    ), "istisna nesnesi sonuc listesine sizdi"
