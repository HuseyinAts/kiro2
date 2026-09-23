#!/usr/bin/env python
"""ACIL 2025 KURS TYT-AYT Geometri: soru kirpim kutularini uretir.

CAPA: BASILI SORU NUMARASI (simge DEGIL)
----------------------------------------
Bu kitapta FERNUS buyutec simgeleri soruyla 1:1 degil (Faz 0): sari alt
baslik kutularinin ve bazi sekillerin yaninda da simge var, bazi sorularda
yok. Kutular bu yuzden sayfadaki basili soru numarasi blob'larindan
(`acil_2025_geometri_numara_taramasi.json`) turetilir. Sutun basina capa
sayisi, kitabin kendi cevap seridindeki girdi sayisina esittir (784/784).

DIKEY KURAL
-----------
- Kutu ustu : numaranin USTUNE yapisik icerik de soruya aittir (ornek:
              seklin tepe etiketi "A" numara satirinin 3-12 px ustunde
              basili; ilk surumde 8 kirpimda kesildi, okuyucular bildirdi).
              Numaradan yukari dogru, okuyucu katmani beyazlatilmis sayfada
              en az BOSLUK satirlik bos bir bant aranir; kutu ustu o bandin
              alt ucu - UST_PAY. Tavan: ayni sutundaki onceki numaranin alti
              ya da aradaki sari kutunun alti ya da UST_BANT.
- Kutu altu : ayni sutundaki sonraki kutunun ustu - 1; arada sari alt baslik
              kutusu varsa onun ustu - SARI_PAY; sutunun son sorusunda
              SAYFA_ALTI (serit bandi y 910'da basliyor).

YATAY KURAL (tek / cift sayfa olculdu)
--------------------------------------
Numara x'i tek sayfada sol 45 / sag 372, cift sayfada sol 61 / sag 388
(392 sayfada en fazla 1 px sapma). Sutunlar arasindaki dikey ACIL
MATEMATIK logosu tek sayfada x 353-363, cift sayfada x 370-380 (cift
sayfada ayrica x 375'te ara cizgi). Sinirlar logo ve cizginin DISINDA:

    tek : sol [41, 351]  sag [368, 684]
    cift: sol [57, 368]  sag [384, 700]

KAPILAR
-------
kart ici, ters/kisa kutu, ayni sutunda cakisma, serit sizintisi
(alt <= 906), kutu sayisi == birim haritasindaki soru sayisi (1948),
her kutunun ustu kendi numarasinin ustunde, altu sonraki numaranin ustunde.

KULLANIM
--------
    python backend/scripts/kitap/acil25_geo_kutu.py
    python backend/scripts/kitap/acil25_geo_kutu.py --yaz
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
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acil25_geo_kirp import (
    KART as KART_PX,
)
from acil25_geo_kirp import (
    _kaynak_dizin,
    okuyucu_maskesi,
)

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
NUMARA_YOLU = CIKTI / "acil_2025_geometri_numara_taramasi.json"
SARI_YOLU = CIKTI / "acil_2025_geometri_sari_kutular.json"
SIMGE_YOLU = CIKTI / "acil_2025_geometri_simge_taramasi.json"
BIRIM_YOLU = CIKTI / "acil_2025_geometri_birim_haritasi.json"
HEDEF = CIKTI / "acil_2025_geometri_kirpim_kutulari.json"

KART = [593, 46, 734, 968]
KART_G, KART_Y = 734, 968
UST_PAY, SARI_PAY = 3, 4
BOSLUK = 10
UST_BANT = 68
MUREKKEP = 200
SAYFA_ALTI = 906
EN_KISA = 30
BEKLENEN_KUTU = 1948
SUTUNLAR = {
    1: {"L": (41, 351), "R": (368, 684)},  # tek dosya no
    0: {"L": (57, 368), "R": (384, 700)},  # cift dosya no
}


def _yukle() -> tuple[dict, dict, dict, dict]:
    num = json.loads(NUMARA_YOLU.read_text("ascii"))["sutunlar"]
    sari: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for k in json.loads(SARI_YOLU.read_text("ascii"))["kutular"]:
        for t in k["sutun"]:  # "L", "R" ya da "LR" (tam genislik)
            sari[(k["dosya"], t)].append(k)
    simge = json.loads(SIMGE_YOLU.read_text("ascii"))["sayfalar"]
    birim = json.loads(BIRIM_YOLU.read_text("utf-8"))
    return num, sari, simge, birim


def _satir_murekkebi(d: int, t: str, simge: dict, kaynak: Path) -> np.ndarray:
    """Beyazlatilmis sayfada sutun genisligince satir basina murekkep var mi."""
    a = np.array(Image.open(kaynak / f"sayfa_{d:04d}.png").convert("RGB").crop(KART_PX))
    a[okuyucu_maskesi(a, simge.get(str(d), []))] = 255
    x0, x1 = SUTUNLAR[d % 2][t]
    satir: np.ndarray = (a[:, x0:x1].min(axis=2) < MUREKKEP).any(axis=1)
    return satir


def _ust(y: int, tavan: int, murekkep: np.ndarray) -> int:
    """Numaradan yukari: ilk >= BOSLUK satirlik bos bandin alt ucu."""
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


def kutulari_uret() -> dict[str, Any]:
    num, sari, simge, birim = _yukle()
    kaynak = _kaynak_dizin()
    sutunlar: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for b in birim["birimler"]:
        for i, q in enumerate(b["sorular"]):
            sutunlar[(q["dosya"], q["sutun"])].append(
                {"birim": b["kod"], "soru": i + 1, "serit_sira": q["serit_sira"]}
            )
    kutular = []
    ek_ust = 0
    for (d, t), qs in sorted(sutunlar.items()):
        capalar = sorted(num[f"{d}{t}"])
        murekkep = _satir_murekkebi(d, t, simge, kaynak)
        sariler = sari.get((d, t), [])
        ustler = []
        for q in qs:
            s = q["serit_sira"]
            y, x, h, w = capalar[s]
            tavan = capalar[s - 1][0] + capalar[s - 1][2] + 1 if s > 0 else UST_BANT
            for k in sariler:
                if tavan <= k["y1"] <= y:
                    tavan = max(tavan, k["y1"] + 1)
            u = _ust(y, tavan, murekkep)
            if u < y - UST_PAY:
                ek_ust += 1
            ustler.append(min(u, y - UST_PAY))
        x0, x1 = SUTUNLAR[d % 2][t]
        for j, q in enumerate(qs):
            s = q["serit_sira"]
            y, x, h, w = capalar[s]
            alt = ustler[j + 1] - 1 if j + 1 < len(qs) else SAYFA_ALTI
            for k in sariler:
                if y < k["y0"] <= alt + SARI_PAY:
                    alt = min(alt, k["y0"] - SARI_PAY)
            kutular.append(
                {
                    "birim": q["birim"],
                    "soru": q["soru"],
                    "dosya": d,
                    "sutun": t,
                    "serit_sira": s,
                    "kutu": [x0, ustler[j], x1, alt],
                    "capa": [y, x, h, w],
                }
            )
    kutular.sort(key=lambda k: (k["birim"], k["soru"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "ACIL 2025 KURS TYT-AYT Geometri Soru Bankasi",
        "kart": KART,
        "capa": "basili soru numarasi (acil_2025_geometri_numara_taramasi.json)",
        "sutun_sinirlari": {"tek": SUTUNLAR[1], "cift": SUTUNLAR[0]},
        "kural": (
            f"Kutu ustu: numaradan yukari ilk {BOSLUK} satirlik bos bandin alt ucu - {UST_PAY} "
            f"(tavan onceki numara / sari kutu / y {UST_BANT}); altu sonraki kutunun ustu - 1, "
            f"arada sari alt baslik varsa onun ustu - {SARI_PAY}, sutun sonunda {SAYFA_ALTI}."
        ),
        "numara_ustune_uzayan_kutu": ek_ust,
        "kutu_sayisi": len(kutular),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]},
        "kutular": kutular,
    }


def kapilar(veri: dict[str, Any], birim: dict) -> list[str]:
    hata = []
    if veri["kutu_sayisi"] != BEKLENEN_KUTU:
        hata.append(f"kutu sayisi {veri['kutu_sayisi']} != {BEKLENEN_KUTU}")
    beklenen = sum(b["soru_sayisi"] for b in birim["birimler"])
    if veri["kutu_sayisi"] != beklenen:
        hata.append(f"kutu sayisi {veri['kutu_sayisi']} != birim haritasi {beklenen}")
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {k['dosya']}{k['sutun']} {k['kutu']}")
        if y1 - y0 < EN_KISA:
            hata.append(
                f"cok kisa: {k['dosya']}{k['sutun']} #{k['serit_sira']} {y1 - y0}px"
            )
        if y1 > SAYFA_ALTI:
            hata.append(
                f"serit sizintisi: {k['dosya']}{k['sutun']} {y1} > {SAYFA_ALTI}"
            )
        if not y0 <= k["capa"][0] < y1:
            hata.append(
                f"numara kutu disinda: {k['dosya']}{k['sutun']} #{k['serit_sira']}"
            )
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["dosya"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] > c["kutu"][1]:
                hata.append(f"cakisma: {anahtar} {a['kutu']} {c['kutu']}")
            if a["kutu"][3] > c["capa"][0]:
                hata.append(f"sonraki numara ustteki kutuda: {anahtar}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="JSON dosyasini guncelle")
    args = ap.parse_args()
    birim = _yukle()[3]
    veri = kutulari_uret()
    hata = kapilar(veri, birim)
    print(f"kutu sayisi: {veri['kutu_sayisi']}")
    print(f"numara ustune uzayan kutu: {veri['numara_ustune_uzayan_kutu']}")
    print(f"yukseklik: {veri['yukseklik']}")
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    if args.yaz:
        HEDEF.write_text(
            json.dumps(veri, indent=1) + "\n", encoding="ascii", newline="\n"
        )
        print("yazildi:", HEDEF)


if __name__ == "__main__":
    main()
