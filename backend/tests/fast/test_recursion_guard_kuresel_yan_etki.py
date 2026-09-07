"""RecursionDepthGuard kuresel ozyineleme limitini DUSURMEMELI.

NEDEN VAR (olcum: CI run 34058968872, 7 Eyl 2026)
-------------------------------------------------
`app/guardrails/guards/recursion_depth_guard.py` kurucu metodunda kosulsuz
`sys.setrecursionlimit(recursion_limit + 100)` cagiriyordu. Bu cagri SURECIN
TAMAMINI etkiler. Muhafizin kendi testi onu `{"recursion_limit": 10}` ile
kuruyor (`tests/guardrails/test_guards.py:217`), yani surecin limiti 110'a
DUSUYOR ve oyle kaliyordu.

xdist worker'inda o dosyadan sonra kosan her test, biraz derin bir yigin
isteyen her yerde `RecursionError` ile dusuyordu -- FastAPI istegi,
SQLAlchemy motoru, pydantic sema uretimi. Hepsi ALAKASIZ testlerdi ve
yiginlar hep baska yerleri gosterdigi icin bulgu aylarca "flaky" okundu.

OLCULEN ETKI: CI'da 160 basarisizligin 92'si (57 dogrudan + 35 setup hatasi)
tek bu satirdan geliyordu. Yerel tekrar (6 saniye):

    pytest tests/guardrails/test_guards.py tests/unit/test_admin_api.py -n 0
    -> once: 20 passed, 46 errors (hepsi RecursionError)
    -> sonra: 66 passed

Bu bekci o davranisi civiliyor: kucuk limitle kurmak limiti DUSURMEZ, buyuk
limitle kurmak YUKSELTIR (muhafizin asil amaci: derin ozyinelemeye baslik
acmak).
"""

from __future__ import annotations

import sys

from app.guardrails.guards import RecursionDepthGuard


def test_kucuk_limit_kuresel_limiti_dusurmez():
    onceki = sys.getrecursionlimit()
    try:
        RecursionDepthGuard({"recursion_limit": 10, "warning_threshold": 0.7})
        assert sys.getrecursionlimit() == onceki, (
            "Muhafiz kurucu metodu kuresel ozyineleme limitini DUSURDU "
            f"({onceki} -> {sys.getrecursionlimit()}). Bu, surecteki TUM "
            "sonraki kodu (ve xdist worker'indaki sonraki tum testleri) "
            "RecursionError'a acik hale getirir."
        )
    finally:
        sys.setrecursionlimit(onceki)


def test_buyuk_limit_kuresel_limiti_yukseltir():
    onceki = sys.getrecursionlimit()
    try:
        hedef = onceki + 500
        RecursionDepthGuard({"recursion_limit": hedef})
        assert sys.getrecursionlimit() >= hedef, (
            "Muhafizin ASIL isi derin ozyinelemeye baslik acmak; buyuk limit "
            "istendiginde kuresel limit yukselmeliydi "
            f"(istenen>={hedef}, gorulen={sys.getrecursionlimit()})."
        )
    finally:
        sys.setrecursionlimit(onceki)


def test_muhafiz_hala_kendi_limitini_biliyor():
    """Limit dusurulmese de muhafizin KENDI esigi yapilandirildigi gibi kalmali.

    Aksi halde 'duzeltme' muhafizi islevsizlestirirdi -- yani kuresel yan
    etkiyi kaldirirken olcumu de kaldirmis olurduk (vakum duzeltme).
    """
    onceki = sys.getrecursionlimit()
    try:
        g = RecursionDepthGuard({"recursion_limit": 10})
        assert g.recursion_limit == 10
    finally:
        sys.setrecursionlimit(onceki)
