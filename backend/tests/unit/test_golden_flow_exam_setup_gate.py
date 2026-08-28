"""Golden Flow sinav-kurulumu sozlesmesi (S255).

NEDEN VAR
---------
27 Agu 2026 olcumu -- `_create_exam_session`'i kullanan DORT test her
kosumda sessizce atlaniyordu:

    pytest ...::test_gf3c... ::test_gf3d... ::test_gf1w... ::test_gf3w...
    -> 4 skipped, 2 warnings   ...   EXIT KODU: 0

Skip ASLA FAIL uretmez. `.claude/rules/golden-flows.md` bu pakete "Merge
block" yetkisi veriyor; yani kapi YESIL rapor verirken save-answer,
complete, BKT ve dogrulama yollarinin hicbiri olculmuyordu. Bu, deponun
"yanlis-SIFIR bir ilerleme sayacinda tek kabul edilemez hata turudur"
kuralinin (`.claude/rules/audit-methodology.md`) birebir vakasi.

IKI AYRI KUSUR VARDI
--------------------
D1 (ALET) -- kurulum reddi `pytest.skip`'e cevriliyordu. Testin OLCMEK
    istedigi sey degil, KURULUMU basarisiz oldu; bu "ortam yok" degil
    "kurulum yanlis" demektir ve FAIL uretmelidir.

D2 (SEKIL) -- helper ciplak ``{"exam_type": "TYT"}`` gonderiyordu.
    `core/osym_exam_engine.py:415-420` yalnizca ``custom_config["subject"]``
    varsa dagitimi tek derse indiriyor; o anahtar yoksa ``total_questions``
    **120** kaliyor. TYT dagitimi dokuz ders istiyor (`:191-205`), kapili
    havuzda yalnizca MATEMATIK 26 + KIMYA 7 = 33 var:

        POST /api/v1/osym-exam/create {"exam_type":"TYT"}
        -> 400 {"detail":"Yeterli soru bulunamadi. Gerekli: 120, Mevcut: 33"}

    Yani 400 DOGRU cevapti. Ustelik bu sekli hicbir canli kullanici yolu
    uretmiyor (olculdu: `components/Exam/ExamStart.tsx` 0 importer,
    `services/examService.ts::createExamSession` 0 cagiran; routed olan
    `ModernExamStart` -> `ModernExamStartPage.tsx:154-165` daima
    `custom_config` gonderiyor).

D1'i tek basina duzeltmek paketi KALICI KIRMIZI yapardi; D2'yi tek basina
duzeltmek bir sonraki sekil kaymasini yine sessize alirdi. Ikisi birlikte
gerekli.

Bu dosya SAHTE istemciyle sinar; canli backend GEREKTIRMEZ.
Kardes sozlesme: `test_golden_flow_login_gate.py` (ayni sinif, `_login`).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

# pytest.fail/skip `BaseException` turetir -- `pytest.raises(Exception)` onlari
# YAKALAMAZ (kardes dosyanin ilk surumunde tam bu hata vardi: test kendisi
# "skipped" olup hicbir sey olcmedi). Gercek siniflari dogrudan import ediyoruz.
from _pytest.outcomes import Failed, Skipped

from tests.e2e import test_golden_flows as gf

pytestmark = [pytest.mark.unit]

JETON = "sahte-jeton"  # pragma: allowlist secret

# Havuz gercegi (20-27 Agu olcumleri): kapida MATEMATIK dilimi ~353 soru.
# Kurulumun istedigi sayi bunun ALTINDA kalmali; tavan, birinin sayiyi
# yeniden 120'ye cikarmasina karsi circir gorevi goruyor.
KURULUM_SORU_TAVANI = 10


class _SahteYanit:
    def __init__(self, kod: int, govde: dict[str, Any] | None = None) -> None:
        self.status_code = kod
        self._govde = {} if govde is None else govde
        self.text = str(self._govde)

    def json(self) -> dict[str, Any]:
        return self._govde


class _SahteIstemci:
    """Yolu ayirt eden, GONDERILEN GOVDEYI kaydeden httpx.Client taklidi."""

    def __init__(
        self,
        create_yanit: _SahteYanit | None = None,
        start_yanit: _SahteYanit | None = None,
    ) -> None:
        self._create = create_yanit or _SahteYanit(200, {"session_id": "oturum-1"})
        self._start = start_yanit or _SahteYanit(200, {"status": "in_progress"})
        self.gonderilenler: list[tuple[str, dict[str, Any]]] = []

    def post(
        self,
        yol: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> _SahteYanit:
        self.gonderilenler.append((yol, json or {}))
        return self._create if yol.endswith("/create") else self._start

    def _create_govdesi(self) -> dict[str, Any]:
        for yol, govde in self.gonderilenler:
            if yol.endswith("/create"):
                return govde
        raise AssertionError(
            "hic /create cagrisi kaydedilmedi -> bekci BOS kume uzerinde "
            "gecerdi (alet dogrulamasi)"
        )


def test_mutlu_yol_oturum_kimligi_donuyor() -> None:
    """KONTROL KOLU: mutlu yol bozuksa asagidaki testler anlamsiz."""
    istemci = _SahteIstemci()
    assert gf._create_exam_session(istemci, JETON) == "oturum-1"


def test_create_reddi_fail_uretir_skip_degil() -> None:
    """Kurulum reddi SKIP degil FAIL.

    MUTASYON: `_create_exam_session`'daki `raise AssertionError`/`assert`
    tekrar `pytest.skip`'e cevrilirse bu test Skipped alir ve DUSER.
    """
    istemci = _SahteIstemci(
        create_yanit=_SahteYanit(400, {"detail": "Yeterli soru bulunamadi"})
    )
    with pytest.raises(BaseException) as kutu:
        gf._create_exam_session(istemci, JETON)
    assert not isinstance(kutu.value, Skipped), (
        "create reddi SKIP'e cevrildi -- GF3c/GF3d/GF1w/GF3w yeniden sessizce "
        "atlanir ve kapi hicbir sey olcmeden yesil doner (27 Agu vakasi)."
    )
    assert isinstance(
        kutu.value, Failed | AssertionError
    ), f"beklenen Failed/AssertionError, gelen {type(kutu.value).__name__}"


def test_start_reddi_fail_uretir_skip_degil() -> None:
    """Ikinci skip dali: create 200 ama start reddediyor."""
    istemci = _SahteIstemci(start_yanit=_SahteYanit(500, {"detail": "patladi"}))
    with pytest.raises(BaseException) as kutu:
        gf._create_exam_session(istemci, JETON)
    assert not isinstance(
        kutu.value, Skipped
    ), "start reddi SKIP'e cevrildi -- ayni yanlis-sifir sinifi"


def test_session_id_yoksa_fail_uretir() -> None:
    """Ucuncu skip dali: 200 ama govdede session_id yok."""
    istemci = _SahteIstemci(create_yanit=_SahteYanit(200, {"detail": "bos"}))
    with pytest.raises(BaseException) as kutu:
        gf._create_exam_session(istemci, JETON)
    assert not isinstance(
        kutu.value, Skipped
    ), "govdesiz 200 SKIP'e cevrildi -- ayni yanlis-sifir sinifi"


def test_kurulum_tam_sinav_dagitimini_istemez() -> None:
    """ASIL DUZELTME (D2): istenen sekil havuzun servis EDEBILECEGI sekil.

    `osym_exam_engine.py:415-420` dagitimi yalnizca `custom_config["subject"]`
    varsa tek derse indiriyor. O anahtar dusurulurse backend yeniden 120
    soruluk tam TYT kurmaya calisir ve 400 doner.

    MUTASYON: gonderilen govdeden `custom_config` (veya `subject`) silinirse
    bu test DUSER.
    """
    istemci = _SahteIstemci()
    gf._create_exam_session(istemci, JETON)
    govde = istemci._create_govdesi()

    assert govde.get("exam_type") == "TYT", f"exam_type kaymasi: {govde!r}"
    ozel = govde.get("custom_config")
    assert isinstance(ozel, dict), (
        "kurulum `custom_config` GONDERMIYOR -> backend tam TYT dagitimini "
        f"(120 soru) kurmaya calisir ve 400 doner. Govde: {govde!r}"
    )
    assert ozel.get("subject"), (
        "`custom_config.subject` yok -> engine tek-ders dalina hic girmez "
        f"(osym_exam_engine.py:415-420). custom_config: {ozel!r}"
    )
    sayi = ozel.get("question_count")
    assert isinstance(sayi, int) and 0 < sayi <= KURULUM_SORU_TAVANI, (
        f"`question_count` {sayi!r} -- kurulum havuzun servis edebilecegi "
        f"kadar kucuk olmali (tavan {KURULUM_SORU_TAVANI})."
    )


def test_kucuk_oturum_yardimcisi_ayni_sekli_kullanir() -> None:
    """GF3x + GF90'in kullandigi ikiz yardimci AYRISMAMALI.

    Iki kopya sekil tutmak, birinin sessizce bayatlamasi demektir; bu dosyanin
    varlik sebebi tam olarak bayat bir kurulum sekliydi.
    """
    istemci = _SahteIstemci()
    assert gf._create_small_exam_session(istemci, JETON) == "oturum-1"
    ozel = istemci._create_govdesi().get("custom_config")
    assert isinstance(ozel, dict) and ozel.get("subject"), (
        "`_create_small_exam_session` artik farkli bir sekil gonderiyor -- "
        f"iki kurulum yolu ayristi: {ozel!r}"
    )


def test_yardimcida_pytest_skip_kalmadi() -> None:
    """SINIF BEKCISI (D1) -- yeni bir dal eklendiginde de gecerli.

    Yukaridaki davranis testleri BILINEN uc dali kapatiyor. Bu test, ileride
    EKLENECEK bir dalin da skip'e kacamayacagini yapisal olarak civiliyor.

    AST kullaniliyor: "bir deseni ANLATAN yorum onu ICERIR" tuzagi (bu depoda
    bir oturumda uc kez isirdi) boylece yapisal olarak imkansiz -- yorumlar ve
    docstring'ler AST'de cagri dugumu olarak gorunmez.
    """
    kaynak = Path(gf.__file__).read_text(encoding="utf-8")
    agac = ast.parse(kaynak)

    hedefler = {"_create_exam_session", "_create_small_exam_session"}
    bulunan: set[str] = set()
    suclular: list[str] = []

    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.FunctionDef) or dugum.name not in hedefler:
            continue
        bulunan.add(dugum.name)
        for ic in ast.walk(dugum):
            if (
                isinstance(ic, ast.Call)
                and isinstance(ic.func, ast.Attribute)
                and ic.func.attr == "skip"
                and isinstance(ic.func.value, ast.Name)
                and ic.func.value.id == "pytest"
            ):
                suclular.append(f"{dugum.name} (satir {ic.lineno})")

    # ALET DOGRULAMASI: yardimci yeniden adlandirilirsa bekci BOS kume
    # uzerinde sessizce gecerdi ("0 satir tarandi, sorun yok" sahte yesili).
    assert bulunan == hedefler, (
        f"taranacak yardimci bulunamadi: {sorted(hedefler - bulunan)} -> bekci "
        "hicbir sey olcmuyor. Ad degistiyse bu test guncellenmeli."
    )
    assert not suclular, (
        "Sinav kurulumu yardimcisi kurulum hatasini yeniden `pytest.skip`'e "
        f"ceviriyor: {suclular}. Skip FAIL uretmez -> GF3c/GF3d/GF1w/GF3w "
        "sessizce atlanir ve kapi bos yesil doner."
    )
