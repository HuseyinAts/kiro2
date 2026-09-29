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
import re
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


def testleri_bul(
    sayfalar: dict[int, dict], bas: set[int] | None = None, serit_sart: bool = True
) -> list[list[int]]:
    """Test = ardisik test sayfalari.

    bas None (varsayilan, ANAHTAR_KAPSAMI 'test'): test anahtarli sayfada biter.
    bas verilirse (TEST_SINIRI 'bas_listesi': her sayfanin kendi cevap seridi
    var, numaralar sayfalar boyunca surer): test, bas kumesindeki sayfada ya da
    test disi sayfadan sonra baslar; HER sayfasi anahtarli olmali -- anahtar
    kitap sonundaysa (ANAHTAR_HARICI, serit_sart=False) sayfada serit aranmaz.
    """
    testler: list[list[int]] = []
    cur: list[int] = []
    for n in sorted(sayfalar):
        v = sayfalar[n]
        if v["tur"] != "test":
            if cur:
                if bas is not None:
                    testler.append(cur)
                    cur = []
                else:
                    raise SystemExit(f"anahtarsiz biten test sayfalari: {cur}")
            continue
        if bas is not None:
            if serit_sart and not v["anahtar"]:
                raise SystemExit(f"seritsiz test sayfasi: {n}")
            if cur and n in bas:
                testler.append(cur)
                cur = []
            cur.append(n)
            continue
        cur.append(n)
        if v["anahtar"]:
            testler.append(cur)
            cur = []
    if cur:
        if bas is not None:
            testler.append(cur)
        else:
            raise SystemExit(f"sonda anahtarsiz test: {cur}")
    return testler


def capalar(
    p: ModuleType,
    a: np.ndarray,
    n: int,
    glif: list[list[int]],
    anahtar: list[int] | None = None,
) -> tuple[list[dict], list[tuple[list[int], str]]]:
    """Sayfanin soru capalari (sutun, y, x) ve capa olmayan glifler
    ([y, x], neden). Neden, elenme noktasini ve olculen degeri tasir
    (serit_ustu / sutun_disi / blob_yok / dx_disi / gecerli_red) -- profil
    kalibrasyonunda hangi sabitin oynayacagini soyler."""
    # Basili numara rengi profile gore (varsayilan kirmizi; MOZ duzeni mavi).
    kir = getattr(p, "numara_maskesi", ortak.kirmizi)(a)
    out: list[dict] = []
    disari: list[tuple[list[int], str]] = []
    py0, py1, px0, px1 = p.PENCERE
    dx0, dx1 = p.NUMARA_DX
    numarasiz = set(getattr(p, "NUMARASIZ_CAPA", ()))
    for gy, gx in glif:
        if anahtar and gy >= anahtar[0] - p.SERIT_SIMGE_PAY:
            disari.append(([gy, gx], "serit_ustu"))
            continue
        simge_x = p.SIMGE_X[ortak.parite(p, n)]
        sut = next(
            (s for s, v in simge_x.items() if abs(gx - v) <= p.SIMGE_TOLERANS),
            None,
        )
        if sut is None:
            en_yakin = min(simge_x.values(), key=lambda v: abs(gx - v))
            disari.append(([gy, gx], f"sutun_disi gx={gx} en_yakin_simge_x={en_yakin}"))
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
            # Pencerede numara boyunda blob yok: maske rengi mi, pencere mi,
            # NUMARA_H mi? Tum bloblarin boyu (h, w) ve maske piksel sayisi verilir.
            tum = [
                (s[0].stop - s[0].start, s[1].stop - s[1].start)
                for s in ndimage.find_objects(lab)
            ]
            disari.append(
                ([gy, gx], f"blob_yok maske_px={int(w.sum())} bloblar_hw={tum[:6]}")
            )
            continue
        ny = min(s[0].start for s in bl) + y0
        ilk = min(
            (s for s in bl if s[0].start + y0 - ny <= 4), key=lambda s: s[1].start
        )
        nx = ilk[1].start + x0
        if not dx0 <= nx - gx <= dx1:
            disari.append(
                ([gy, gx], f"dx_disi dx={nx - gx} dy={ny - gy} aralik={dx0}-{dx1}")
            )
            continue
        gecerli = getattr(p, "capa_gecerli", None)
        if gecerli is not None and not gecerli(a, int(ny), int(nx)):
            disari.append(([gy, gx], f"gecerli_red ny={ny} nx={nx}"))
            continue
        if any(c["sutun"] == sut and abs(c["y"] - ny) < 20 for c in out):
            continue
        out.append(
            {
                "sutun": sut,
                "y": int(ny),
                "x": int(nx),
                "simge": [gy, gx],
                "numara_w": int(ilk[1].stop - ilk[1].start),
            }
        )
    for dn, sut_e, ey, ex in getattr(p, "EK_CAPA", ()):
        # Okuyucu simgesi KONMAMIS soru (gozle dogrulandi, profilde listeli):
        # capa basili numaradan.
        if dn == n:
            out.append(
                {
                    "sutun": sut_e,
                    "y": int(ey),
                    "x": int(ex),
                    "simge": None,
                    "simgesiz": True,
                    "numara_w": 0,
                }
            )
    out.sort(key=lambda c: (c["sutun"], c["y"]))
    return out, disari


def tara(p: ModuleType) -> dict[str, Any]:
    d = ortak.kaynak_dizin(p)
    sayfalar: dict[int, dict] = {}
    for f in sorted(d.glob("sayfa_*.png")):
        n = int(f.stem[-4:])
        sayfalar[n] = sayfa_olc(p, ortak.kart(p, d, n), n)
    sayfa_capa: dict[int, tuple[list[dict], list[tuple[list[int], str]]]] = {}
    for n, v in sayfalar.items():
        if v["tur"] == "test":
            sayfa_capa[n] = capalar(p, ortak.kart(p, d, n), n, v["glif"], v["anahtar"])
    bas = None
    if getattr(p, "TEST_SINIRI", "anahtar") == "bas_listesi":
        # Her sayfanin kendi seridi var, numara sayfalar boyunca surer: test
        # baslangic sayfalari profilde (sayfa basina serit okumasindan: seridi
        # '1.' ile baslayan sayfalar; iki okuma ayni). Dogrulama: anahtar
        # numaralari her testte 1..N.
        bas = set(p.BAS_SAYFALARI)
    testler = testleri_bul(sayfalar, bas, not hasattr(p, "ANAHTAR_HARICI"))
    cikti: list[dict[str, Any]] = []
    disari_top = []
    for i, g in enumerate(testler, 1):
        capa = []
        for n in g:
            c, dis = sayfa_capa[n]
            capa += [{"dosya": n, **x} for x in c]
            disari_top += [
                {"test": i, "dosya": n, "glif": x, "neden": r} for x, r in dis
            ]
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
        hucre = {
            t["test"]: len(ortak.yakalanan(p, t["test"], t["hucreler"]))
            for t in ham["okuma_a"]["testler"]
        }
        for t in veri["testler"]:
            if len(t["capalar"]) != hucre.get(t["test"]):
                hata.append(
                    f"test {t['test']}: capa {len(t['capalar'])} != anahtar {hucre.get(t['test'])}"
                )
    for t in veri["testler"]:
        if not t["capalar"]:
            hata.append(f"test {t['test']}: capa yok")
        for c in t["capalar"]:
            h = _capa_hatasi(p, c)
            if h:
                hata.append(f"test {t['test']}: {h}")
    return hata


def _capa_hatasi(p: ModuleType, c: dict[str, Any]) -> str | None:
    if c.get("simgesiz"):
        if (c["dosya"], c["sutun"], c["y"], c["x"]) not in set(
            getattr(p, "EK_CAPA", ())
        ):
            return f"profilde olmayan simgesiz capa: {c}"
        return None
    if c.get("numarasiz"):
        if (c["dosya"], *c["simge"]) not in set(getattr(p, "NUMARASIZ_CAPA", ())):
            return f"profilde olmayan numarasiz capa: {c}"
        return None
    dx0, dx1 = p.NUMARA_DX
    if not dx0 <= c["x"] - c["simge"][1] <= dx1:
        return f"numara x kaymis: {c}"
    return None


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
    nedenler: dict[str, int] = {}
    for x in veri["capa_olmayan_glif"]:
        ad = x["neden"].split(" ")[0]
        nedenler[ad] = nedenler.get(ad, 0) + 1
    if nedenler:
        print("capa olmayan glif nedenleri:", dict(sorted(nedenler.items())))
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        # Capa != hucre olan testlerin elenen glifleri, nedeniyle: hangi sabit
        # (SIMGE_X / PENCERE / NUMARA_H / NUMARA_DX / maske) oynayacak, buradan.
        kotu = {int(m.group(1)) for h in hata if (m := re.match(r"test (\d+):", h))}
        for x in [x for x in veri["capa_olmayan_glif"] if x["test"] in kotu][:30]:
            print(f"    T{x['test']:03d} s{x['dosya']} glif {x['glif']}: {x['neden']}")
        raise SystemExit(1)
    if args.yaz:
        ortak.yaz(p, "capa_taramasi", veri, girinti=None)
        print("yazildi")


if __name__ == "__main__":
    main()
