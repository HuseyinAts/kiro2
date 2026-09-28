"""kitap_hat/kesif: profilsiz yerlesim olcumu -- saf fonksiyonlar (sentetik kart)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.kitap.kitap_hat import kesif, ortak


def _kart() -> np.ndarray:
    return np.full((979, 742, 3), 255, np.uint8).astype(int)


def test_en_uzun_kosu_bosluk_birlestirir() -> None:
    v = np.zeros(100, bool)
    v[10:30] = True
    v[32:60] = True  # 2 px bosluk: ayni kosu (serit cercevesi hucre siniri)
    v[70:80] = True
    assert kesif.en_uzun_kosu(v) == (10, 59)
    assert kesif.en_uzun_kosu(np.zeros(5, bool)) == (0, -1)


def test_yatay_cizgiler_serit_ve_tam_genislik() -> None:
    a = _kart()
    a[890, 376:676] = 0  # serit cizgisi 300 px
    a[891, 376:676] = 0  # kalinlik: tek cizgi
    a[905, 376:676] = 0
    a[905, 30:120] = 0  # ayni satirda metin: kosuyu uzatmaz
    a[927, 5:737] = 0  # sayfa cizgisi (tam genislik)
    a[500, 100:150] = 0  # kisa cizgi: sayilmaz
    c = kesif.yatay_cizgiler(a)
    assert [(y, g) for y, g, _, _ in c] == [(891, 300), (905, 300), (927, 732)]
    assert c[0][2:] == (376, 675)


def test_metin_seridi_alttaki_dar_sayfa_numarasini_atlar() -> None:
    a = _kart()
    a[913:921, 584:674:2] = 0  # duz metin serit (seyrek, 90 px genis)
    a[922:927, 359:366] = 0  # sayfa numarasi (dar)
    a[927, 5:737] = 0  # sayfa cizgisi
    assert kesif.metin_seridi(a) == [913, 920, 584, 672]
    b = _kart()
    b[922:927, 359:366] = 0
    assert kesif.metin_seridi(b) is None


def test_orta_bosluk_ve_murekkep_araligi() -> None:
    v = np.zeros(742)
    v[20:350] = 50
    v[380:700] = 50
    v[362] = 0.05  # ayrac artigi (esik binde 2 -> 0.1'in altinda)
    assert kesif.orta_bosluk(v) == (350, 379)
    assert kesif.murekkep_araligi(v) == [20, 699]


def test_numara_maskeleri_on_ayarlari() -> None:
    a = _kart()
    a[10, 10] = (200, 40, 40)  # kirmizi
    a[10, 11] = (64, 96, 160)  # mavi
    a[10, 12] = (0, 160, 224)  # camgobegi
    a[10, 13] = (20, 20, 20)  # siyah
    for ad, x in zip(
        ("kirmizi", "mavi", "camgobegi", "siyah"), (10, 11, 12, 13), strict=True
    ):
        m = ortak.NUMARA_MASKELERI[ad](a)
        assert m[10, x], ad
    # camgobegi maviye de girer (alt kume); kirmizi ve siyah girmez
    assert (
        ortak.mavi(a)[10, 12]
        and not ortak.mavi(a)[10, 10]
        and not ortak.mavi(a)[10, 13]
    )


def test_sayfa_ozeti_araliklari() -> None:
    def s(glif: int, serit: bool, koyu: int = 5000) -> dict:
        return {
            "glif": [[100, 30]] * glif,
            "alt_cizgi": [(890, 300, 376, 675)] if serit else [],
            "metin_seridi": None,
            "sari_bant": 0,
            "kirmizi_bant": 0,
            "koyu": koyu,
        }

    sayfalar = {
        1: s(0, False, 100),
        2: s(4, True),
        3: s(4, True),
        4: s(0, False),
        5: s(2, True),
    }
    satir, aralik = kesif.sayfa_ozeti(sayfalar)
    assert aralik == [[2, 3], [5, 5]]
    assert satir[0] == "1:g0-kapak" and satir[1] == "2:g4s"
