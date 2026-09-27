"""metin_iki_okuma.norm: bicim farklarini esitler, anlami korur.

Ornekler ACL21T hakem kararlarindan (VeraFilm a2_hakem, 27 Eyl 2026): 'esasli
hata yok' denilen bicim farklari ESIT olmali; hakemin esasli buldugu farklar
(carpi/x, parantez/oncelik, us, isaret) FARKLI kalmali.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_YOL = Path(__file__).resolve().parents[2] / "scripts" / "kitap" / "metin_iki_okuma.py"
_spec = importlib.util.spec_from_file_location("metin_iki_okuma", _YOL)
assert _spec is not None and _spec.loader is not None
m = importlib.util.module_from_spec(_spec)
sys.modules["metin_iki_okuma"] = m
_spec.loader.exec_module(m)


def _esit(a: str, b: str) -> bool:
    return m.sikistir(m.norm(a)) == m.sikistir(m.norm(b))


@pytest.mark.parametrize(
    ("bir", "iki"),
    [
        ("(f \u2218 g)(x)", "(f o g)(x)"),  # bileske halkasi (T132_15, T131_08)
        ("A br^2", "A br\u00b2"),  # ust simge (T066_07)
        ("\u221b\u03c0", "\u221b(\u03c0)"),  # kokte tek atom (T061_06)
        ("3\u221b(3)", "3\u221b3"),  # T065_13
        ("(2xy)/(x^2 + y^2)", "2xy/(x^2 + y^2)"),  # T071_01
        ("(-f(1))/3", "-f(1)/3"),  # T127_03
        ("n!)/((n + 2)!) = 5/6", "n!)/(n + 2)! = 5/6"),  # T022_02
        ("x\u0305\u221a^y", "x\u221a^y"),  # ust cizgi (T010_01)
        ("\u221a\u203e , Y", "\u221a, Y"),  # kok cizgisi (T104_07)
        ("- | 1 | - | \u2192 abc", "- | 1 | - \u2192 abc"),  # tablo ayraci (T012_13)
        ("x^(2)", "x^2"),
        ("C(5, 2)", "(5 2)"),
        ("a \u2212 b", "a - b"),
        ("(g\u00f6rsel)", "(\u015fekil)"),
    ],
)
def test_bicim_farki_esit(bir: str, iki: str) -> None:
    assert _esit(bir, iki)


@pytest.mark.parametrize(
    ("bir", "iki"),
    [
        (
            "5 \u00d7 K",
            "5 x K",
        ),  # carpi / harf x: hakem esasli buldu (T011_06, T015_07)
        ("(a + b)/c", "a + b/c"),  # oncelik
        ("(x^2)/3", "x^2/3"),  # us tasiyan pay parantezi esitlenmez
        ("f(1)/3", "f1/3"),  # fonksiyon uygulamasi
        ("f(2)/3", "f(1)/3"),
        ("\u221a(x + 1)", "\u221ax + 1"),
        ("x^2", "x^3"),
        ("12", "-12"),
        ("(f o g)(2)", "(g o f)(2)"),
        ("(2, 1)", "(2.1)"),  # T132_08: nokta / virgul ayraci
    ],
)
def test_anlam_farki_korunur(bir: str, iki: str) -> None:
    assert not _esit(bir, iki)


def test_none_bos() -> None:
    assert m.norm(None) == ""


def test_soru_farklari_alanlari() -> None:
    a = {
        "govde": "(f \u2218 g)(x) = 3",
        "sikler": dict.fromkeys("ABCDE", "1"),
        "basili_no": 3,
        "sekil_var": False,
        "sikler_gorsel": False,
        "etiket": None,
    }
    b = dict(a, govde="(f o g)(x) = 3", sikler=dict(a["sikler"], C="2"), sekil_var=True)
    alanlar = [f["alan"] for f in m.soru_farklari(a, b)]
    assert alanlar == ["sik_C", "sekil_var"]  # govde bicim farki elendi
    assert m.soru_farklari(a, dict(a)) == []


def test_vurgu_ayri_alan() -> None:
    a = {"govde": "hangisi <u>yanlistir</u>?", "sikler": dict.fromkeys("ABCDE", "1")}
    b = {"govde": "hangisi yanlistir?", "sikler": dict.fromkeys("ABCDE", "1")}
    assert [f["alan"] for f in m.soru_farklari(a, b)] == ["vurgu"]
