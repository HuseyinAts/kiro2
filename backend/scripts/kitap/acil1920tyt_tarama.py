#!/usr/bin/env python
"""2019-2020 ACIL TYT Matematik: sayfa taramasi -> test sinirlari + soru capalari.

KAYNAK
------
FERNUS okuyucusunun 1920x1080 ekran goruntuleri, 432 PNG; sayfa karti
(589, 43) - (1331, 1022). Basili sayfa numarasi = dosya numarasi.

SAYFA TURU
----------
* TEST sayfasi: ust bandi camgobegi-gri ('Test - N' + konu adi). Testin son
  sayfasinin sag altinda sari cerceveli cevap seridi var ("1. C 2. E ...").
* On Calisma sayfasi: acik bant; sorular ACIK UCLU (sik yok, seritte sayi
  cevap). Coktan secmeli degil -> KAPSAM DISI (345 Start Matematik emsali).

Test = ardisik test sayfalari, son sayfasi seritli. Olculen: 95 test.

CAPA: OKUYUCU SIMGESI + KIRMIZI BASILI NUMARA
---------------------------------------------
Her sorunun yaninda okuyucu simgesi (mor glif 69,39,160) ve kirmizi basili
numara var. Simge 1:1 degil: bazi sekillerin yaninda da simge var (s141)
ya da fotograf icinde glif rengi (s367). Bu yuzden capa = simgenin
sag-alt penceresinde (x +18..+52, y -6..+62; simge bazen numaranin 25-40
px USTUNDE) bulunan ilk kirmizi numara blobu. Simge sutun konumlarinin
(tek sayfa 27 / 357, cift 43 / 371) disindaki glif ve numarasiz glif capa
degildir. Numara x'i tek sayfada 50 / 377, cift sayfada 67 / 394.

KAPI: test basina capa sayisi == cevap seridindeki hucre sayisi (ham
okumalardan). Olculen: 95/95 test, 1203 capa == 1203 hucre.

KULLANIM
--------
    python backend/scripts/kitap/acil1920tyt_tarama.py          # olc + kapi
    python backend/scripts/kitap/acil1920tyt_tarama.py --yaz    # JSON yaz
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from scipy import ndimage

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_1920_tyt_matematik_"
HEDEF = CIKTI / f"{ONEK}capa_taramasi.json"
HAM = CIKTI / f"{ONEK}ham_okumalar.json"
KLASOR = "2019-2020-AC\u0130L-TYT-Soru Bankas\u0131"
KART = (589, 43, 1331, 1022)
BEKLENEN_SAYFA = 432
BEKLENEN_TEST = 95
GLIF = (69, 39, 160)
SIMGE_X = {1: {"L": 27, "R": 357}, 0: {"L": 43, "R": 371}}  # dosya no % 2
NUMARA_X = {1: {"L": 50, "R": 377}, 0: {"L": 67, "R": 394}}
SIMGE_TOLERANS = 4
NUMARA_TOLERANS = 3
PENCERE = (-6, 62, 18, 52)  # y0, y1, x0, x1 (simgeye gore)
SERIT_ALT = 780


def kaynak_dizin() -> Path:
    d = KOK / "veriseti" / "zkitap" / "screenshots" / KLASOR
    n = len(list(d.glob("sayfa_*.png")))
    if n != BEKLENEN_SAYFA:
        raise SystemExit(f"kaynak sayfa sayisi {n} != {BEKLENEN_SAYFA}")
    return d


def kart(d: Path, n: int) -> np.ndarray:
    return np.asarray(
        Image.open(d / f"sayfa_{n:04d}.png").convert("RGB").crop(KART)
    ).astype(int)


def glifler(a: np.ndarray) -> list[list[int]]:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = (abs(r - GLIF[0]) < 35) & (abs(g - GLIF[1]) < 35) & (abs(b - GLIF[2]) < 40)
    lab, _ = ndimage.label(m)
    out = []
    for s in ndimage.find_objects(lab):
        h, w = s[0].stop - s[0].start, s[1].stop - s[1].start
        if 8 <= h <= 14 and 5 <= w <= 10:
            out.append([s[0].start, s[1].start])
    return sorted(out)


def sayfa_olc(a: np.ndarray) -> dict[str, Any]:
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sari = (r > 230) & (g > 220) & (b < 150)
    alt = sari[SERIT_ALT:]
    ys = np.where(alt.sum(axis=1) > 20)[0]
    xs = np.where(alt.sum(axis=0) > 3)[0]
    serit = (
        [
            int(ys.min()) + SERIT_ALT,
            int(ys.max()) + SERIT_ALT,
            int(xs.min()),
            int(xs.max()),
        ]
        if len(ys)
        else None
    )
    ust = a[5:60, 100:600].reshape(-1, 3).mean(axis=0)
    bant = "test" if (ust[1] - ust[0] > 15 and ust[0] < 215) else "acik"
    return {"glif": glifler(a), "bant": bant, "serit": serit}


def testleri_bul(sayfalar: dict[int, dict]) -> list[list[int]]:
    testler: list[list[int]] = []
    cur: list[int] = []
    for n in sorted(sayfalar):
        v = sayfalar[n]
        if v["bant"] != "test":
            if cur:
                raise SystemExit(f"seritsiz test sayfalari: {cur}")
            continue
        cur.append(n)
        if v["serit"]:
            testler.append(cur)
            cur = []
    if cur:
        raise SystemExit(f"sonda seritsiz test: {cur}")
    return testler


def capalar(
    a: np.ndarray, n: int, glif: list[list[int]]
) -> tuple[list[dict], list[list[int]]]:
    """Sayfanin soru capalari (sutun, y, x) ve capa olmayan glifler."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    kir = (r > 170) & (g < 100) & (b < 110)
    out: list[dict] = []
    disari = []
    for gy, gx in glif:
        sut = next(
            (s for s, v in SIMGE_X[n % 2].items() if abs(gx - v) <= SIMGE_TOLERANS),
            None,
        )
        if sut is None:
            disari.append([gy, gx])
            continue
        y0, x0 = max(0, gy + PENCERE[0]), gx + PENCERE[2]
        w = kir[y0 : gy + PENCERE[1], x0 : gx + PENCERE[3]]
        lab, _ = ndimage.label(ndimage.binary_dilation(w, np.ones((3, 3), bool)))
        bl = [
            s
            for s in ndimage.find_objects(lab)
            if s[0].stop - s[0].start >= 6
            and (s[0].stop - s[0].start) * (s[1].stop - s[1].start) >= 12
        ]
        if not bl:
            disari.append([gy, gx])
            continue
        ny = min(s[0].start for s in bl) + y0
        nx = min(s[1].start for s in bl if s[0].start + y0 - ny <= 4) + x0
        if abs(nx - NUMARA_X[n % 2][sut]) > NUMARA_TOLERANS:
            disari.append([gy, gx])
            continue
        if any(c["sutun"] == sut and abs(c["y"] - ny) < 20 for c in out):
            continue
        out.append({"sutun": sut, "y": int(ny), "x": int(nx), "simge": [gy, gx]})
    out.sort(key=lambda c: (c["sutun"], c["y"]))
    return out, disari


def tara() -> dict[str, Any]:
    d = kaynak_dizin()
    sayfalar: dict[int, dict] = {}
    for f in sorted(d.glob("sayfa_*.png")):
        n = int(f.stem[-4:])
        sayfalar[n] = sayfa_olc(kart(d, n))
    testler = testleri_bul(sayfalar)
    cikti: list[dict[str, Any]] = []
    disari_top = []
    for i, g in enumerate(testler, 1):
        capa = []
        for n in g:
            c, dis = capalar(kart(d, n), n, sayfalar[n]["glif"])
            capa += [{"dosya": n, **x} for x in c]
            disari_top += [{"test": i, "dosya": n, "glif": x} for x in dis]
        cikti.append({"test": i, "sayfalar": g, "capalar": capa})
    return {
        "kaynak": "2019-2020 ACIL TYT Matematik Soru Bankasi",
        "arac": "scripts/kitap/acil1920tyt_tarama.py",
        "kart": list(KART),
        "sayfa_turu": {
            "test": sum(1 for v in sayfalar.values() if v["bant"] == "test"),
            "acik": sum(1 for v in sayfalar.values() if v["bant"] == "acik"),
        },
        "test_sayisi": len(cikti),
        "capa_toplam": sum(len(t["capalar"]) for t in cikti),
        "capa_olmayan_glif": disari_top,
        "sayfalar": {str(n): v for n, v in sayfalar.items()},
        "testler": cikti,
    }


def kapilar(veri: dict[str, Any], ham: dict[str, Any] | None) -> list[str]:
    hata = []
    if veri["test_sayisi"] != BEKLENEN_TEST:
        hata.append(f"test sayisi {veri['test_sayisi']} != {BEKLENEN_TEST}")
    if ham is not None:
        hucre = {t["test"]: len(t["hucreler"]) for t in ham["okuma_a"]["testler"]}
        for t in veri["testler"]:
            if len(t["capalar"]) != hucre.get(t["test"]):
                hata.append(
                    f"test {t['test']}: capa {len(t['capalar'])} != serit {hucre.get(t['test'])}"
                )
    for t in veri["testler"]:
        for c in t["capalar"]:
            if abs(c["x"] - NUMARA_X[c["dosya"] % 2][c["sutun"]]) > NUMARA_TOLERANS:
                hata.append(f"numara x kaymis: test {t['test']} {c}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    veri = tara()
    ham = json.loads(HAM.read_text("ascii")) if HAM.exists() else None
    hata = kapilar(veri, ham)
    print(
        f"sayfa turu {veri['sayfa_turu']}, test {veri['test_sayisi']}, "
        f"capa {veri['capa_toplam']}, capa olmayan glif {len(veri['capa_olmayan_glif'])}"
    )
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        HEDEF.write_text(json.dumps(veri, separators=(",", ":")) + "\n", "ascii")
        print("yazildi", HEDEF)


if __name__ == "__main__":
    main()
