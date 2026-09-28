"""kitap_hat/bas_listesi: iki gecisli test siniri -- saf fonksiyonlar (sentetik veri)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kitap_hat import bas_listesi as bl


def _t(i: int, h: list[list]) -> dict:
    return {"test": i, "konu": "K", "test_no": str(i), "hucreler": h}


def _tarama_testi(i: int, sayfa: int, capa: int) -> dict:
    return {"test": i, "sayfalar": [sayfa], "capalar": [{}] * capa}


def test_gecis1_bas_ve_ardisiklik_temiz() -> None:
    # s7: 1-6, s8: 7-12 (devam), s10: 1-4 (yeni test)
    A = [
        _t(1, [[1, "A"], [2, "B"], [3, "C"], [4, "D"], [5, "E"], [6, "A"]]),
        _t(2, [[7, "B"], [8, "C"], [9, "D"], [10, "E"], [11, "A"], [12, "B"]]),
        _t(3, [[1, "C"], [2, "D"], [3, "E"], [4, "A"]]),
    ]
    T = [_tarama_testi(1, 7, 6), _tarama_testi(2, 8, 6), _tarama_testi(3, 10, 4)]
    v = bl.gecis1_olc(A, A, T)
    assert v["bas"] == [7, 10]
    assert v["hucre_farki"] == [] and v["capa_farki"] == [] and v["kopuk"] == []


def test_gecis1_farklar_yakalanir() -> None:
    A = [_t(1, [[1, "A"], [2, "B"]]), _t(2, [[3, "C"], [4, "D"]]), _t(3, [[6, "E"]])]
    B = [_t(1, [[1, "A"], [2, "E"]]), _t(2, [[3, "C"], [4, "D"]]), _t(3, [[6, "E"]])]
    T = [_tarama_testi(1, 7, 2), _tarama_testi(2, 8, 3), _tarama_testi(3, 9, 1)]
    v = bl.gecis1_olc(A, B, T)
    assert v["hucre_farki"] == [1]  # A != B
    assert v["capa_farki"] == [(8, 3, 2, 3)]  # capa 3, hucre 2
    assert v["kopuk"] == [(9, [6])]  # 4'ten sonra 6


def test_grupla_sayfa_okumalarini_teste_birlestirir() -> None:
    sayfa = [_t(1, [[1, "A"], [2, "B"]]), _t(2, [[3, "C"]]), _t(3, [[1, "D"]])]
    tarama = {
        "sayfalar": {
            "7": {"tur": "test"},
            "8": {"tur": "test"},
            "9": {"tur": "konu"},
            "10": {"tur": "test"},
        },
        "testler": [{"test": 1, "sayfalar": [7, 8]}, {"test": 2, "sayfalar": [10]}],
    }
    out = bl.grupla(sayfa, tarama)
    assert [x["hucreler"] for x in out] == [[[1, "A"], [2, "B"], [3, "C"]], [[1, "D"]]]
    assert out[0]["test_no"] == "1" and out[1]["test_no"] == "3"
    with pytest.raises(SystemExit):
        bl.grupla(sayfa[:2], tarama)


def test_profil_yaz(tmp_path: Path) -> None:
    f = tmp_path / "p.py"
    f.write_text(
        "KOD = 'X'\nBEKLENEN_TEST = 3\nBAS_SAYFALARI: tuple[int, ...] = (1, 2, 3)\n",
        "ascii",
    )
    bl.profil_yaz(f, [7, 10, 13, 15])
    s = f.read_text("ascii")
    assert "BEKLENEN_TEST = 4\n" in s
    assert "BAS_SAYFALARI: tuple[int, ...] = (7, 10, 13, 15)\n" in s
    (tmp_path / "bos.py").write_text("KOD = 1\n", "ascii")
    with pytest.raises(SystemExit):
        bl.profil_yaz(tmp_path / "bos.py", [1])
