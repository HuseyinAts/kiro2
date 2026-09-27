#!/usr/bin/env python
"""2019-2020 ACIL TYT Matematik: soru kirpim kutularini uretir (acil25_geo_kutu deseni).

CAPA
----
`acil_1920_tyt_matematik_capa_taramasi.json`: test basina kirmizi basili
numara capalari (sayisi == cevap seridi hucre sayisi, 95/95 test).

YATAY (olculdu, a_sutun_olc: test sayfalarinda x murekkep profili)
------------------------------------------------------------------
Tek dosya: sol metin <= 348, dikey 'ACIL MATEMATIK' logosu x 363-366, sag
numara 377, sag metin 399-676. Cift dosya: sol <= 363, logo 378-381, sag
numara 394, sag metin 417-693. Sinirlar logonun DISINDA:

    tek : sol [45, 356]  sag [370, 700]   (kirmizi logo motifi tek x 358-366,
    cift: sol [62, 370]  sag [386, 716]    cift x 372-381; kenar kapisi olctu)

DIKEY
-----
- ust : numaradan yukari, okuyucu diski beyazlatilmis sayfada en az BOSLUK
        satirlik bos bandin alt ucu - UST_PAY; tavan onceki numaranin
        alti ya da UST_BANT (test bandi alti).
- alt : ayni sutundaki sonraki kutunun ustu - 1; sutunun sonuncusunda
        SAYFA_ALTI (metin y 902'ye kadar iniyor) ya da cevap
        seridi o sutunla yatayda ortusuyorsa seridin ustu - SERIT_PAY.

KAPILAR
-------
kutu sayisi == 1203 == anahtar; kart ici; >= EN_KISA; ayni sutunda
cakisma yok; numara kutunun icinde; kutu seride girmiyor; SUTUN ICI
ARTIK MUREKKEP: sutun sinirlari icinde UST_BANT..alt sinir arasinda hicbir
kutunun kapsamadigi koyu murekkep satiri (> ARTIK_ESIK piksel) yok.

KULLANIM
--------
    python backend/scripts/kitap/acil1920tyt_kutu.py [--yaz]
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acil1920tyt_kirp import beyaz_sayfa, kaynak_dizin

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_1920_tyt_matematik_"
TARAMA = CIKTI / f"{ONEK}capa_taramasi.json"
ANAHTAR = CIKTI / f"{ONEK}cevap_anahtari.json"
HEDEF = CIKTI / f"{ONEK}kirpim_kutulari.json"
KART_G, KART_Y = 742, 979
SUTUNLAR = {1: {"L": (45, 356), "R": (370, 700)}, 0: {"L": (62, 370), "R": (386, 716)}}
UST_BANT = 76  # konunun ilk test sayfasinda bandin altinda y 72-74 koyu cizgi (s117)
UST_PAY = 3
BOSLUK = 10
SAYFA_ALTI = 904  # olculen en alt metin satiri y 902 (s15 sag); rozet sutun disinda
SERIT_PAY = 12  # sari seridi saran mavi cerceve seridin ~8 px ustunde (s186 olculdu)
EN_KISA = 40
MUREKKEP = 200
ARTIK_ESIK = 6
BEKLENEN_KUTU = 1203


def _satirlar(a: np.ndarray, x0: int, x1: int) -> np.ndarray:
    m: np.ndarray = (a[:, x0:x1].min(axis=2) < MUREKKEP).any(axis=1)
    return m


def _ust(y: int, tavan: int, murekkep: np.ndarray) -> int:
    bos = 0
    r = y - 1
    while r >= tavan:
        if murekkep[r]:
            bos = 0
        else:
            bos += 1
            if bos >= BOSLUK:
                return max(tavan, r + BOSLUK - UST_PAY)
        r -= 1
    return tavan


def _alt_sinir(sayfa: dict, x0: int, x1: int) -> int:
    s = sayfa.get("serit")
    if s and min(x1, s[3]) - max(x0, s[2]) > 20:
        return int(s[0]) - SERIT_PAY
    return SAYFA_ALTI


def kutulari_uret() -> tuple[dict[str, Any], list[str]]:
    tarama = json.loads(TARAMA.read_text("ascii"))
    anahtar = json.loads(ANAHTAR.read_text("ascii"))
    cevap = {(c["dosya"], c["sutun"], c["sutun_sira"]): c for c in anahtar["cevaplar"]}
    kaynak = kaynak_dizin()
    sutun: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for t in tarama["testler"]:
        for c in t["capalar"]:
            sutun[(c["dosya"], c["sutun"])].append(c)
    kutular, artik = [], []
    sayfa_cache: dict[int, np.ndarray] = {}
    for (d, s), sutun_capa in sorted(sutun.items()):
        if d not in sayfa_cache:
            sayfa_cache.clear()
            sayfa_cache[d] = beyaz_sayfa(kaynak, d, tarama["sayfalar"][str(d)]["glif"])[
                0
            ]
        a = sayfa_cache[d]
        x0, x1 = SUTUNLAR[d % 2][s]
        mur = _satirlar(a, x0, x1)
        capa = sorted(sutun_capa, key=lambda c: c["y"])
        alt_sinir = _alt_sinir(tarama["sayfalar"][str(d)], x0, x1)
        ustler = []
        for i, c in enumerate(capa):
            tavan = capa[i - 1]["y"] + 12 if i else UST_BANT
            ustler.append(min(_ust(c["y"], tavan, mur), c["y"] - UST_PAY))
        for i, c in enumerate(capa):
            alt = ustler[i + 1] - 1 if i + 1 < len(capa) else alt_sinir
            cv = cevap[(d, s, i)]
            kutular.append(
                {
                    "birim": cv["birim"],
                    "soru": cv["soru"],
                    "dosya": d,
                    "sutun": s,
                    "sutun_sira": i,
                    "kutu": [x0, ustler[i], x1, alt],
                    "capa": [c["y"], c["x"]],
                }
            )
        # sutun ici artik murekkep: UST_BANT..alt_sinir arasinda kutusuz koyu satir
        kapsanan = np.zeros(KART_Y, bool)
        for k in kutular[-len(capa) :]:
            kapsanan[k["kutu"][1] : k["kutu"][3]] = True
        koyu = (a[:, x0:x1].min(axis=2) < 160).sum(axis=1)
        for y in range(UST_BANT, alt_sinir):
            if not kapsanan[y] and koyu[y] > ARTIK_ESIK:
                artik.append(f"artik murekkep s{d}{s} y{y} ({int(koyu[y])} px)")
                break
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    veri = {
        "kaynak": "2019-2020 ACIL TYT Matematik Soru Bankasi",
        "arac": "scripts/kitap/acil1920tyt_kutu.py",
        "capa": "kirmizi basili soru numarasi (capa_taramasi.json)",
        "sutun_sinirlari": {"tek": SUTUNLAR[1], "cift": SUTUNLAR[0]},
        "kutu_sayisi": len(kutular),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]},
        "kutular": kutular,
    }
    return veri, artik


def kapilar(veri: dict[str, Any], tarama: dict[str, Any]) -> list[str]:
    hata = []
    if veri["kutu_sayisi"] != BEKLENEN_KUTU:
        hata.append(f"kutu sayisi {veri['kutu_sayisi']} != {BEKLENEN_KUTU}")
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {k['birim']}_{k['soru']}")
        if y1 - y0 < EN_KISA:
            hata.append(f"cok kisa: {k['birim']}_{k['soru']} {y1 - y0}px")
        if not y0 <= k["capa"][0] < y1:
            hata.append(f"numara kutu disinda: {k['birim']}_{k['soru']}")
        s = tarama["sayfalar"][str(k["dosya"])].get("serit")
        if s and min(x1, s[3]) - max(x0, s[2]) > 20 and y1 > s[0]:
            hata.append(f"seride giriyor: {k['birim']}_{k['soru']}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] > c["kutu"][1]:
                hata.append(f"cakisma: {anahtar}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    veri, artik = kutulari_uret()
    hata = kapilar(veri, json.loads(TARAMA.read_text("ascii"))) + artik
    print(
        f"kutu {veri['kutu_sayisi']}, yukseklik {veri['yukseklik']}, kapi ihlali {len(hata)}"
    )
    for h in hata[:40]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        HEDEF.write_text(json.dumps(veri, indent=0) + "\n", "ascii")
        print("yazildi", HEDEF)


if __name__ == "__main__":
    main()
