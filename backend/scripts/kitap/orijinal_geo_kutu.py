#!/usr/bin/env python
"""Orijinal 2024 TYT-AYT Geometri: soru kirpim kutularini uretir.

DIKEY KURAL (degismedi)
-----------------------
- Kutu ustu   : simge glif merkezi - 12 (disk ustu) - 6 px pay.
- Kutu altu   : ayni sutundaki BIR SONRAKI simgenin disk ustu - 8 px;
                yoksa sayfanin alt siniri.
- Alt sinir   : o sayfada cevap seridi varsa seridin ust kenari - 4 px,
                yoksa 944 (kart ici metin alaninin altu).
- Kitabin simge basmadigi iki soruda (s151 sag 8, s323 sol 3) kutu ustu
  soru numarasinin ust kenarindan ELLE olculdu.

YATAY KURAL (bu surumde DUZELTILDI)
-----------------------------------
Onceki surum TUM sayfalarda sabit sutun sinirlari kullaniyordu
(SOL 30-349 / SAG 352-700). Olculdu ki bu YANLIS: kitabin metin blogu
TEK ve CIFT sayfalarda ~16 px kayiyor (ic/dis kenar payi), ustelik
bolumlere gore sutun genisligi de degisiyor. Sabit sinir yuzunden CIFT
sayfalarda sol sutunun sag kenari kesiliyordu -- ornegin s432 sol #2'de
son sik (E) ve satir sonlari, s145 sol #2'de seklin sag kenari.

Sinirlar artik SAYFANIN KENDI olcumunden turetiliyor: her sayfada o
sayfanin simge x konumlari sutunlarin sol kenarini isaretler.

    sol_x0 = (o sayfadaki en kucuk SOL simge x) - 7
    sag_x0 = (o sayfadaki en kucuk SAG simge x) - 7
    sol_x1 = sag_x0 - 2
    sag_x1 = sag_x0 + (sag_x0 - sol_x0) - 2      # sol sutunla ayni genislik

FILIGRAN BANTLARI
-----------------
Yayinevi filigrani (dikey "ORIJINAL YAYINLARI" yazisi) DIS kenarda
basili, yani TEK sayfalarda sagda, CIFT sayfalarda solda. 425 soru
sayfasinin piksel sikligi olculerek bant yerleri bulundu (bir pikselin
sayfalarin >= %70'inde koyu olmasi):

    TEK sayfa : x 678-699   (asil yazi 687-691)
    CIFT sayfa: x  33-46    (asil yazi  43-46)

Sinirlar bu bantlarin disinda tutulur; boylece filigran kirpimlara
girmez. Bant kirpmasi sutun GENISLIGINI degistirmez: genislik ham
(filigran kirpilmamis) sol kenardan olculur, yoksa sag sutunun sag
kenari kisalir ve oradaki metin kesilirdi -- s10 sag #2'de olculdu.

KULLANIM
--------
    python backend/scripts/kitap/orijinal_geo_kutu.py
    python backend/scripts/kitap/orijinal_geo_kutu.py --yaz
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
SIMGE_YOLU = CIKTI / "orijinal_2024_geometri_simge_taramasi.json"
SERIT_YOLU = CIKTI / "orijinal_2024_geometri_serit_taramasi.json"
BIRIM_YOLU = CIKTI / "orijinal_2024_geometri_birim_haritasi.json"
HEDEF = CIKTI / "orijinal_2024_geometri_kirpim_kutulari.json"

KART = [593, 46, 734, 968]
KART_G, KART_Y = 734, 968
DISK_YARICAP_Y = 12  # glif merkezinden disk ustune
UST_PAY, ALT_PAY, SERIT_PAY = 6, 8, 4
SAYFA_ALTI = 944
SIMGE_PAY = 7  # simgenin solunda birakilan bosluk
SUTUN_ARA = 2  # iki sutun arasi guvenlik payi
SUTUN_AYIRAN_X = 200  # simge x bunun altindaysa SOL sutun
FILIGRAN = {1: (678, 699), 0: (33, 46)}  # tek / cift sayfa dis kenar bandi

SIMGESIZ_KUTU: list[dict[str, Any]] = [
    {"sayfa": 151, "sutun": "sag", "ust": 806, "soru": 8},
    {"sayfa": 323, "sutun": "sol", "ust": 790, "soru": 3},
]


def _yukle() -> tuple[dict, dict, dict]:
    simge = {
        int(k): v
        for k, v in json.loads(SIMGE_YOLU.read_text("ascii"))["sayfalar"].items()
    }
    serit = {
        int(k): v
        for k, v in json.loads(SERIT_YOLU.read_text("ascii"))["sayfalar"].items()
    }
    birim = json.loads(BIRIM_YOLU.read_text("ascii"))
    return simge, serit, birim


def _alt_sinir(s: int, serit: dict) -> int:
    bloklar = serit.get(s)
    if not bloklar:
        return SAYFA_ALTI
    return int(min(b["y"][0] for b in bloklar)) - SERIT_PAY


def sutun_sinirlari(simge: dict) -> dict[int, dict[str, list[int]]]:
    """Her sayfanin sutun x sinirlari -- o sayfanin kendi simgelerinden."""
    sinir: dict[int, dict[str, list[int]]] = {}
    for s, konumlar in simge.items():
        sol = [x for _, x in konumlar if x < SUTUN_AYIRAN_X]
        sag = [x for _, x in konumlar if x >= SUTUN_AYIRAN_X]
        if not sol or not sag:
            continue
        ham_sol0, sag0 = min(sol) - SIMGE_PAY, min(sag) - SIMGE_PAY
        # Sutun genisligi HAM sol kenardan olculur; filigran kirpmasi
        # genisligi kucultmemeli -- kucultseydi sag sutun kesilirdi.
        genislik = sag0 - ham_sol0
        bant = FILIGRAN[s % 2]
        sol0 = max(ham_sol0, bant[1] + 1) if s % 2 == 0 else ham_sol0
        sag1 = sag0 + genislik - SUTUN_ARA
        if s % 2 == 1:  # tek: filigran SAGDA
            sag1 = min(sag1, bant[0] - 1)
        sinir[s] = {"sol": [sol0, sag0 - SUTUN_ARA], "sag": [sag0, sag1]}
    return sinir


def kutulari_uret() -> dict:
    simge, serit, birim = _yukle()
    sinir = sutun_sinirlari(simge)
    kutular = []
    for b in birim["birimler"]:
        for s in range(b["bas_sayfa"], b["son_sayfa"] + 1):
            taban = _alt_sinir(s, serit)
            for ad in ("sol", "sag"):
                sut = sorted(
                    p
                    for p in simge.get(s, [])
                    if (p[1] < SUTUN_AYIRAN_X) == (ad == "sol")
                )
                x0, x1 = sinir[s][ad]
                for i, (cy, cx) in enumerate(sut):
                    ust = cy - DISK_YARICAP_Y - UST_PAY
                    alt = (
                        sut[i + 1][0] - DISK_YARICAP_Y - ALT_PAY
                        if i + 1 < len(sut)
                        else taban
                    )
                    kutular.append(
                        {
                            "birim": b["kod"],
                            "sayfa": s,
                            "sutun": ad,
                            "sira": i + 1,
                            "kutu": [x0, max(0, ust), x1, alt],
                            "simge": [cy, cx],
                        }
                    )

    def birim_of(s: int) -> str:
        for b in birim["birimler"]:
            if b["bas_sayfa"] <= s <= b["son_sayfa"]:
                return str(b["kod"])
        raise KeyError(s)

    for ek in SIMGESIZ_KUTU:
        s, ad, ust = int(ek["sayfa"]), str(ek["sutun"]), int(ek["ust"])
        x0, x1 = sinir[s][ad]
        ayni = sorted(
            (k for k in kutular if k["sayfa"] == s and k["sutun"] == ad),
            key=lambda k: k["kutu"][1],
        )
        onceki = [k for k in ayni if k["kutu"][1] < ust][-1]
        onceki["kutu"][3] = ust - ALT_PAY
        kutular.append(
            {
                "birim": birim_of(s),
                "sayfa": s,
                "sutun": ad,
                "sira": onceki["sira"] + 1,
                "kutu": [x0, ust, x1, _alt_sinir(s, serit)],
                "simge": None,
                "elle": True,
            }
        )
    kutular.sort(key=lambda k: (k["sayfa"], k["sutun"], k["sira"]))
    yuk = sorted(k["kutu"][3] - k["kutu"][1] for k in kutular)
    return {
        "kaynak": "Orijinal 2024 TYT-AYT Geometri Soru Bankasi",
        "kart": KART,
        "sutun_kurali": (
            "Sutun sinirlari SAYFA BASINA olculur: o sayfadaki en kucuk SOL/SAG "
            "simge x degeri sutunun sol kenarini verir (7 px pay). Sabit sinir "
            "kullanilamaz; metin blogu tek/cift sayfada ~16 px kayiyor."
        ),
        "filigran_bantlari": {"tek": list(FILIGRAN[1]), "cift": list(FILIGRAN[0])},
        "sayfa_sutunlari": {str(s): v for s, v in sorted(sinir.items())},
        "kural": (
            "Kutu ustu simge disk ustu - 6; altu ayni sutundaki sonraki simgenin "
            "disk ustu - 8, yoksa sayfa alt siniri (serit ustu - 4 ya da 944)."
        ),
        "elle_girilen": SIMGESIZ_KUTU,
        "kutu_sayisi": len(kutular),
        "yukseklik": {"min": yuk[0], "medyan": yuk[len(yuk) // 2], "max": yuk[-1]},
        "kutular": kutular,
    }


def kapilar(veri: dict, serit: dict) -> list[str]:
    hata = []
    sinir = veri["sayfa_sutunlari"]
    for k in veri["kutular"]:
        x0, y0, x1, y1 = k["kutu"]
        if not (0 <= x0 < x1 <= KART_G and 0 <= y0 < y1 <= KART_Y):
            hata.append(f"kart disi/ters: {k['sayfa']} {k['sutun']} {k['kutu']}")
        if y1 - y0 < 40:
            hata.append(f"cok kisa: {k['sayfa']} {k['sutun']} {y1 - y0}px")
        if [x0, x1] != sinir[str(k["sayfa"])][k["sutun"]]:
            hata.append(f"sutun sinirina oturmuyor: {k['sayfa']} {k['sutun']}")
        t = _alt_sinir(k["sayfa"], serit)
        if y1 > t:
            hata.append(f"serit sizintisi: {k['sayfa']} {y1} > {t}")
    grup = defaultdict(list)
    for k in veri["kutular"]:
        grup[(k["sayfa"], k["sutun"])].append(k)
    for anahtar, g in grup.items():
        g.sort(key=lambda k: k["kutu"][1])
        for a, c in itertools.pairwise(g):
            if a["kutu"][3] > c["kutu"][1]:
                hata.append(f"cakisma: {anahtar} {a['kutu']} {c['kutu']}")
    for s, v in sinir.items():
        if not v["sol"][0] < v["sol"][1] < v["sag"][0] < v["sag"][1]:
            hata.append(f"sutunlar ortusuyor: s{s} {v}")
    return hata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true", help="JSON dosyasini guncelle")
    args = ap.parse_args()

    _, serit, _ = _yukle()
    veri = kutulari_uret()
    hata = kapilar(veri, serit)
    print(f"kutu sayisi: {veri['kutu_sayisi']}")
    print(f"sayfa sayisi: {len(veri['sayfa_sutunlari'])}")
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
