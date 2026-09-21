#!/usr/bin/env python
"""C1CELL 2024 TYT-AYT Geometri: kirpim kutularini SIMGEDEN turetir + 4 kapi.

GEOMETRI (Faz 0/3'te olculdu)
-----------------------------
Kart (591,46) 738x968. 'yer' kart-ici koordinat. Kolon: x<180 sol, >=180 sag.
Simge x paritede kayar: tek ~30/348, cift ~47/365 (sayfa-ici min, yoksa varsayilan).
Kutu: ust = gy-6; alt = ayni sutunda sonraki gy-9, yoksa region_bottom.
region_bottom: cevap seridi olan sayfada serit_ust-6 (serit FERNUS'ta sabit ~896);
  seritsiz sayfada 906 (footer ustu). Sol sutun x:[gx_sol+22, gx_sag+18];
  sag sutun x:[gx_sag+22, 690]. Sol x1 = gx_sag+18: sag sutun diskinin (beyazlatilan)
  ust boslugu; sol sutunun tasan son sikkini yakalar, sag numaraya (gx_sag+22) degmez.

GARANTI: birim simge-sayisi == cevap-sayisi (KAPI 163/163). Yalnizca KAPIDAN GECEN
birimlerin sayfalari kirpilir. Kutular LLM tahmini DEGIL; her simge piksel duzeyinde
Faz 0'da bulundu, konum-duzeltme overlay'i (yanlis-pozitif konu-kutusu isaretleri)
uygulandi.

DORT KAPI: (1) kutu==1770 ve birim==N, (2) serit sizintisi (alt<serit), (3) ayni
sutunda ortusme/kisa kutu, (4) her kutuda murekkep.

GIRDI (faz0/serit _geo1_gecici scratch'te; git'e girmez):
  backend/_geo1_gecici/faz0_c1.json, c1_serit.json
  veriseti/zkitap/cikti/c1cell_2024_geometri_simge_duzeltme.json
  veriseti/zkitap/cikti/c1cell_2024_geometri_kapi_raporu.json
  veriseti/zkitap/cikti/c1cell_2024_geometri_cevap_anahtari.json
CIKTI: veriseti/zkitap/cikti/c1cell_2024_geometri_kirpim_kutulari.json

KULLANIM: python backend/scripts/kitap/c1cell_geo_kutu.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from itertools import pairwise
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
GECICI = KOK / "backend" / "_geo1_gecici"
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KART = (591, 46, 1329, 1014)
SAG_KENAR = 690
KUTUSUZ_ALT = 906
SERIT_SABIT = 896
KUTU1 = np.array([211, 228, 245])
KUTU2 = np.array([113, 185, 227])


def _kaynak_dizin():
    adaylar = sorted(
        (KOK / "veriseti" / "zkitap" / "screenshots").glob(
            "C1CELL-2024-TYT-AYT-Geometri Soru Bank*"
        )
    )
    if not adaylar:
        raise SystemExit("Kaynak ekran goruntuleri bulunamadi.")
    return adaylar[0]


def _yakin(a, b, tol=3):
    return abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _yer_haritasi():
    faz = json.loads((GECICI / "faz0_c1.json").read_text("utf-8"))
    duz = json.loads(
        (CIKTI / "c1cell_2024_geometri_simge_duzeltme.json").read_text("utf-8")
    )
    yer = {}
    for d in faz:
        p = d["sayfa"]
        ys = [list(pt) for pt in d.get("yer", [])]
        giris = duz.get(str(p))
        kal = giris.get("kaldir", []) if isinstance(giris, dict) else []
        yer[p] = [pt for pt in ys if not any(_yakin(pt, k) for k in kal)]
    return yer


def _serit_ust(a):
    m = (np.abs(a - KUTU1).max(axis=2) < 18) | (np.abs(a - KUTU2).max(axis=2) < 30)
    cnt = m[820:].sum(axis=1)
    idx = np.nonzero(cnt > 80)[0]
    if len(idx):
        v = 820 + int(idx.min())
        if 885 <= v <= 905:
            return v
    return SERIT_SABIT


def _ham_kutular(rap, yer, region_bottom):
    """Her birimin sayfalarinda simgeden ham kutulari turetir."""
    ham = []
    for b in rap["birimler"]:
        for p in b["sayfalar"]:
            pts = yer.get(p, [])
            if not pts:
                continue
            alt_sinir = region_bottom(p)
            sol = sorted([q for q in pts if q[0] < 180], key=lambda q: q[1])
            sag = sorted([q for q in pts if q[0] >= 180], key=lambda q: q[1])
            gx_sol = min((q[0] for q in sol), default=(30 if p % 2 else 47))
            gx_sag = min((q[0] for q in sag), default=(348 if p % 2 else 365))
            for etiket, grup, x0, x1 in (
                ("sol", sol, gx_sol + 22, gx_sag + 18),
                ("sag", sag, gx_sag + 22, SAG_KENAR),
            ):
                for i, (gx, gy) in enumerate(grup):
                    ust = gy - 6
                    alt = (grup[i + 1][1] - 9) if i + 1 < len(grup) else alt_sinir
                    ham.append(
                        {
                            "birim": b["birim"],
                            "sayfa": p,
                            "sutun": etiket,
                            "kol_sira": i + 1,
                            "x0": x0,
                            "x1": x1,
                            "y0": ust,
                            "y1": alt,
                            "simge": [gx, gy],
                        }
                    )
    return ham


def _kapilar(ham, by_unit, nmap, kaynak):
    """Dort kapi: sayi/birim==N, ortusme, kisa kutu, bos kutu."""
    assert len(ham) == 1770, f"KAPI1 sayi: {len(ham)}"
    assert all(len(ks) == nmap[u] for u, ks in by_unit.items()), "KAPI1 birim==N"
    g = defaultdict(list)
    for k in ham:
        g[(k["sayfa"], k["sutun"])].append(k)
    for v in g.values():
        v.sort(key=lambda k: k["y0"])
        assert all(a["y1"] <= b["y0"] for a, b in pairwise(v)), "KAPI3 ortusme"
    assert all(k["y1"] - k["y0"] >= 35 for k in ham), "KAPI3 kisa kutu"
    sp = defaultdict(list)
    for k in ham:
        sp[k["sayfa"]].append(k)
    for p in sorted(sp):
        a = np.asarray(Image.open(kaynak / f"sayfa_{p:04d}.png").convert("RGB")).astype(
            int
        )[KART[1] : KART[3], KART[0] : KART[2]]
        mx = a.max(axis=2)
        mn = a.min(axis=2)
        mur = (mx < 170) & ((mx - mn) < 60)
        for k in sp[p]:
            assert (
                mur[max(0, k["y0"]) : k["y1"], max(0, k["x0"]) : k["x1"]].sum() >= 100
            ), f"KAPI4 bos kutu s{p} {k['sutun']} {k['kol_sira']}"


def main():
    B = _kaynak_dizin()
    yer = _yer_haritasi()
    rap = json.loads(
        (CIKTI / "c1cell_2024_geometri_kapi_raporu.json").read_text("utf-8")
    )
    serit = json.loads((GECICI / "c1_serit.json").read_text("utf-8"))
    strip_pages = {
        int(n) for n, v in serit.items() if v["yayilim"] > 300 and v["mavi_px"] > 200
    }
    cev = json.loads(
        (CIKTI / "c1cell_2024_geometri_cevap_anahtari.json").read_text("utf-8")
    )
    Nmap: defaultdict[int, int] = defaultdict(int)
    for a in cev["anahtar"]:
        Nmap[a["birim"]] = max(Nmap[a["birim"]], a["soru_no"])

    alt_cache: dict[int, int] = {}

    def region_bottom(p):
        if p not in strip_pages:
            return KUTUSUZ_ALT
        if p not in alt_cache:
            a = np.asarray(Image.open(B / f"sayfa_{p:04d}.png").convert("RGB")).astype(
                int
            )[KART[1] : KART[3], KART[0] : KART[2]]
            alt_cache[p] = _serit_ust(a) - 6
        return alt_cache[p]

    ham = _ham_kutular(rap, yer, region_bottom)

    by_unit = defaultdict(list)
    for k in ham:
        by_unit[k["birim"]].append(k)
    for ks in by_unit.values():
        ks.sort(key=lambda k: (k["sayfa"], 0 if k["sutun"] == "sol" else 1, k["y0"]))
        for j, k in enumerate(ks, 1):
            k["soru_no"] = j

    _kapilar(ham, by_unit, Nmap, B)

    kutular = []
    for k in sorted(
        ham, key=lambda k: (k["sayfa"], 0 if k["sutun"] == "sol" else 1, k["y0"])
    ):
        kutular.append(
            {
                "sayfa": k["sayfa"],
                "sutun": k["sutun"],
                "sira": k["kol_sira"],
                "birim": k["birim"],
                "soru_no": k["soru_no"],
                "kirpim_kutusu": [k["x0"], k["y0"], k["x1"], k["y1"]],
                "tavan": [k["x1"], k["y1"]],
                "simge": k["simge"],
                "tam_genislik": False,
                "ortulu": False,
            }
        )
    urun = {
        "kaynak": "C1CELL 2024 TYT-AYT Geometri Soru Bankasi",
        "kirpim_koordinat_sistemi": "kart-ici (591,46 orijin)",
        "kart": "738x968",
        "kutu": len(kutular),
        "ortulu": 0,
        "islenecek": len(kutular),
        "not": (
            "C1CELL'de ortulu (disk-ortmesi) soru YOK; 163 birim kapidan gecti, "
            "1770 kutu islenir. Kutular simgeden turetildi, KAPI 1-4'ten gecti."
        ),
        "kutular": kutular,
    }
    yol = CIKTI / "c1cell_2024_geometri_kirpim_kutulari.json"
    yol.write_text(
        json.dumps(urun, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"4 kapi GECTI. {len(kutular)} kutu -> {yol.relative_to(KOK)}")


if __name__ == "__main__":
    main()
