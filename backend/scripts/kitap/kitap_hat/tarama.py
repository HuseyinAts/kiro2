"""Sayfa taramasi -> sayfa turu, test sinirlari, soru capalari (profil gudumlu).

CAPA: OKUYUCU SIMGESI + KIRMIZI BASILI NUMARA (acil2021tyt_tarama deseni)
-----------------------------------------------------------------------
Okuyucu (FERNUS) her sorunun basina mor bir simge koyar; simgenin sutun
konumu profilde olculmustur (SIMGE_X, sayfa paritesine gore). Capa =
simgenin sagindaki PENCERE icinde ilk kirmizi numara blobu; blobun simgeye
gore yatay ofseti NUMARA_DX araliginda olmali (tek / iki basamakli numara).

SAYFA TURU VE TEST SINIRI
-------------------------
`p.sayfa_turu(a, n)` 'test' ya da baska bir tur dondurur; `p.anahtar_bolgesi(a, n)`
cevap anahtari bolgesinin kutusunu [y0, y1, x0, x1] ya da None. ANAHTAR_KAPSAMI
'test' ise test = ardisik test sayfalari, son sayfasi anahtarli.

KAPILAR
-------
test sayfalari kumesi == profilin TEST_SAYFALARI araliklari (kontak sayfasindan
gozle); test sayisi == BEKLENEN_TEST; test basina capa == anahtar hucresi
(ham okumalar varsa); numara ofseti aralikta.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.tarama --profil acl23ag [--yaz]
"""

from __future__ import annotations

import argparse
from types import ModuleType
from typing import Any

import numpy as np
from scipy import ndimage

from scripts.kitap.kitap_hat import ortak


def sayfa_olc(p: ModuleType, a: np.ndarray, n: int) -> dict[str, Any]:
    return {
        "glif": ortak.glifler(p, a),
        "tur": p.sayfa_turu(a, n),
        "anahtar": p.anahtar_bolgesi(a, n),
    }


def beklenen_test_sayfalari(p: ModuleType) -> set[int]:
    return {n for a, b in p.TEST_SAYFALARI for n in range(a, b + 1)}


def testleri_bul(sayfalar: dict[int, dict]) -> list[list[int]]:
    testler: list[list[int]] = []
    cur: list[int] = []
    for n in sorted(sayfalar):
        v = sayfalar[n]
        if v["tur"] != "test":
            if cur:
                raise SystemExit(f"anahtarsiz biten test sayfalari: {cur}")
            continue
        cur.append(n)
        if v["anahtar"]:
            testler.append(cur)
            cur = []
    if cur:
        raise SystemExit(f"sonda anahtarsiz test: {cur}")
    return testler


def capalar(
    p: ModuleType,
    a: np.ndarray,
    n: int,
    glif: list[list[int]],
    anahtar: list[int] | None = None,
) -> tuple[list[dict], list[list[int]]]:
    """Sayfanin soru capalari (sutun, y, x) ve capa olmayan glifler."""
    kir = ortak.kirmizi(a)
    out: list[dict] = []
    disari = []
    py0, py1, px0, px1 = p.PENCERE
    dx0, dx1 = p.NUMARA_DX
    numarasiz = set(getattr(p, "NUMARASIZ_CAPA", ()))
    for gy, gx in glif:
        if anahtar and gy >= anahtar[0] - p.SERIT_SIMGE_PAY:
            disari.append([gy, gx])
            continue
        sut = next(
            (s for s, v in p.SIMGE_X[n % 2].items() if abs(gx - v) <= p.SIMGE_TOLERANS),
            None,
        )
        if sut is None:
            disari.append([gy, gx])
            continue
        if (n, gy, gx) in numarasiz:
            # Kitapta numara BASILMAMIS soru (gozle dogrulandi, profilde listeli):
            # capa simgeden; numara yok.
            out.append(
                {
                    "sutun": sut,
                    "y": int(gy),
                    "x": None,
                    "simge": [gy, gx],
                    "numarasiz": True,
                }
            )
            continue
        y0, x0 = max(0, gy + py0), gx + px0
        w = kir[y0 : gy + py1, x0 : gx + px1]
        lab, _ = ndimage.label(ndimage.binary_dilation(w, np.ones((3, 3), bool)))
        bl = [
            s
            for s in ndimage.find_objects(lab)
            if p.NUMARA_H[0] <= s[0].stop - s[0].start <= p.NUMARA_H[1]
            and s[1].stop - s[1].start <= p.NUMARA_W_EN_COK
        ]
        if not bl:
            disari.append([gy, gx])
            continue
        ny = min(s[0].start for s in bl) + y0
        nx = min(s[1].start for s in bl if s[0].start + y0 - ny <= 4) + x0
        if not dx0 <= nx - gx <= dx1:
            disari.append([gy, gx])
            continue
        if any(c["sutun"] == sut and abs(c["y"] - ny) < 20 for c in out):
            continue
        out.append({"sutun": sut, "y": int(ny), "x": int(nx), "simge": [gy, gx]})
    out.sort(key=lambda c: (c["sutun"], c["y"]))
    return out, disari


def tara(p: ModuleType) -> dict[str, Any]:
    d = ortak.kaynak_dizin(p)
    sayfalar: dict[int, dict] = {}
    for f in sorted(d.glob("sayfa_*.png")):
        n = int(f.stem[-4:])
        sayfalar[n] = sayfa_olc(p, ortak.kart(p, d, n), n)
    testler = testleri_bul(sayfalar)
    cikti: list[dict[str, Any]] = []
    disari_top = []
    for i, g in enumerate(testler, 1):
        capa = []
        for n in g:
            c, dis = capalar(
                p, ortak.kart(p, d, n), n, sayfalar[n]["glif"], sayfalar[n]["anahtar"]
            )
            capa += [{"dosya": n, **x} for x in c]
            disari_top += [{"test": i, "dosya": n, "glif": x} for x in dis]
        cikti.append({"test": i, "sayfalar": g, "capalar": capa})
    turler: dict[str, int] = {}
    for v in sayfalar.values():
        turler[v["tur"]] = turler.get(v["tur"], 0) + 1
    return {
        "kaynak": p.KAYNAK_ADI,
        "arac": "scripts/kitap/kitap_hat/tarama.py",
        "profil": p.KOD,
        "kart": list(p.KART),
        "sayfa_turu": dict(sorted(turler.items())),
        "test_sayisi": len(cikti),
        "capa_toplam": sum(len(t["capalar"]) for t in cikti),
        "capa_olmayan_glif": disari_top,
        "sayfalar": {str(n): v for n, v in sayfalar.items()},
        "testler": cikti,
    }


def kapilar(
    p: ModuleType, veri: dict[str, Any], ham: dict[str, Any] | None
) -> list[str]:
    hata = []
    if veri["test_sayisi"] != p.BEKLENEN_TEST:
        hata.append(f"test sayisi {veri['test_sayisi']} != {p.BEKLENEN_TEST}")
    test_s = {int(n) for n, v in veri["sayfalar"].items() if v["tur"] == "test"}
    bek = beklenen_test_sayfalari(p)
    if test_s != bek:
        hata.append(
            f"test sayfalari farkli: fazla {sorted(test_s - bek)[:10]} eksik {sorted(bek - test_s)[:10]}"
        )
    if ham is not None:
        hucre = {t["test"]: len(t["hucreler"]) for t in ham["okuma_a"]["testler"]}
        for t in veri["testler"]:
            if len(t["capalar"]) != hucre.get(t["test"]):
                hata.append(
                    f"test {t['test']}: capa {len(t['capalar'])} != anahtar {hucre.get(t['test'])}"
                )
    dx0, dx1 = p.NUMARA_DX
    for t in veri["testler"]:
        if not t["capalar"]:
            hata.append(f"test {t['test']}: capa yok")
        for c in t["capalar"]:
            if c.get("numarasiz"):
                if (c["dosya"], *c["simge"]) not in set(
                    getattr(p, "NUMARASIZ_CAPA", ())
                ):
                    hata.append(f"profilde olmayan numarasiz capa: {c}")
                continue
            if not dx0 <= c["x"] - c["simge"][1] <= dx1:
                hata.append(f"numara x kaymis: test {t['test']} {c}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    veri = tara(p)
    ham_y = ortak.yol(p, "ham_okumalar")
    ham = ortak.oku(p, "ham_okumalar") if ham_y.exists() else None
    hata = kapilar(p, veri, ham)
    print(
        f"sayfa turu {veri['sayfa_turu']}, test {veri['test_sayisi']}, "
        f"capa {veri['capa_toplam']}, capa olmayan glif {len(veri['capa_olmayan_glif'])}"
    )
    print("test basina capa:", [len(t["capalar"]) for t in veri["testler"]])
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        ortak.yaz(p, "capa_taramasi", veri, girinti=None)
        print("yazildi")


if __name__ == "__main__":
    main()
