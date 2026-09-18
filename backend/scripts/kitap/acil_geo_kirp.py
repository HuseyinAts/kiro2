#!/usr/bin/env python
"""ACIL 2023-2024 TYT-AYT Geometri: kirpim kutularindan soru gorselleri uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (yuzlerce MB; `veriseti/` zaten .gitignore'da).
Her kutu `acil_2324_geometri_kirpim_kutulari.json` icinde durdugu icin
gorseller her ortamda YENIDEN uretilebilir. fiz345_kirp.py ile ayni desen.

KAYNAK: PDF DEGIL PNG
---------------------
Bu kitabin PDF'i zaten ayni PNG'lerden uretilmis; PNG'den kirpmak
render boyutu uyusmazligi riskini bastan kaldirir. Yine de her sayfanin
boyutu BEKLENEN_BOYUT ile karsilastirilir ve tutmazsa script DURUR.

OKUYUCU SIMGESI BEYAZLATILIR -- NEDEN
-------------------------------------
Sol sutunun metni tam `gx_sag`'da bittigi icin sol kutu `gx_sag + 1`'e
kadar uzuyor (yoksa son sikkin son harfi kesiliyordu). Bunun yan etkisi,
SAG sutun simgesinin diskinin sol kenarindan ~10 px'in kutuya girmesi.
Disk okuyucunun kendi katmani; ogrenciye gosterilecek gorselde isi yok.
Disk OPAK oldugu icin altinda kitap icerigi zaten gorunmuyor -- beyaza
boyamak bilgi kaybettirmez.

Beyazlatma renge gore DEGIL, bilinen simge konumlarina gore yapilir;
konumlar kutu dosyasinin kendi `simge` alanindan gelir (her simgenin bir
kutusu var, yani liste tam). Renge gore boyamak kitabin kendi
mor/lacivert cizimlerini de silebilirdi -- Faz 0'da s435'teki bisikletli
cizimin glif rengine dustugu olculmustu.

KULLANIM
--------
    python backend/scripts/kitap/acil_geo_kirp.py
    python backend/scripts/kitap/acil_geo_kirp.py --ornek 40   # ilk 40 kutu
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw

KLASOR_DESENI = "2023-2024-AC*TYT-AYT Geometri Soru Bank*"
KART = (593, 46)
BEKLENEN_BOYUT = (1920, 1080)
ONEK = "ACILGEO_2324"
# Disk glifin merkezine gore 30x32; golgesi icin her yone 4 px pay.
DISK_SOL, DISK_UST, DISK_SAG, DISK_ALT = 13, 14, 27, 28


def _disk_dikdortgeni(gx: int, gy: int) -> tuple[int, int, int, int]:
    return (gx - DISK_SOL, gy - DISK_UST, gx + DISK_SAG, gy + DISK_ALT)


def ana() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default="veriseti/zkitap/screenshots")
    ap.add_argument(
        "--kutular",
        default="veriseti/zkitap/cikti/acil_2324_geometri_kirpim_kutulari.json",
    )
    ap.add_argument(
        "--crop-dir", default=os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    )
    ap.add_argument("--ornek", type=int, default=0, help="yalniz ilk N kutu")
    a = ap.parse_args()

    kokler = sorted(Path(a.kok).glob(KLASOR_DESENI))
    if not kokler:
        print(f"HATA: klasor bulunamadi: {KLASOR_DESENI}", file=sys.stderr)
        return 2
    kok = kokler[0]

    veri = json.loads(Path(a.kutular).read_text("utf-8"))
    # ORTULU sorular islenmez (sahip karari): sag sutun simgesi sol sutundaki
    # satirin uzerine biniyor ve son sik diskin altinda kaliyor.
    kutular = [b for b in veri["kutular"] if not b.get("ortulu")]
    if a.ornek:
        kutular = kutular[: a.ornek]
    hedef = Path(a.crop_dir) / ONEK
    hedef.mkdir(parents=True, exist_ok=True)

    sayfa_kutu = defaultdict(list)
    sayfa_simge = defaultdict(list)
    for b in veri["kutular"]:  # beyazlatma TUM simgeleri ister
        sayfa_simge[b["sayfa"]].append(b["simge"])
    for b in kutular:
        sayfa_kutu[b["sayfa"]].append(b)

    uretilen = 0
    beyazlatilan = 0
    for n in sorted(sayfa_kutu):
        yol = kok / f"sayfa_{n:04d}.png"
        im = Image.open(yol).convert("RGB")
        if im.size != BEKLENEN_BOYUT:
            print(
                f"HATA: s{n} boyutu {im.size}, beklenen {BEKLENEN_BOYUT}; duruldu",
                file=sys.stderr,
            )
            return 1
        d = ImageDraw.Draw(im)
        # Sayfadaki TUM simgeleri (kart koordinatindan tam goruntuye tasiyarak)
        # beyaza boya; kutu kirpimi bundan sonra yapilir.
        for gx, gy in sayfa_simge[n]:
            x0, y0, x1, y1 = _disk_dikdortgeni(gx + KART[0], gy + KART[1])
            d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
            beyazlatilan += 1
        for b in sayfa_kutu[n]:
            bx0, by0, bx1, by1 = b["kirpim_kutusu"]
            kirp = im.crop((bx0 + KART[0], by0 + KART[1], bx1 + KART[0], by1 + KART[1]))
            ad = f"s{b['sayfa']:04d}_{b['sutun']}_{b['sira']}.png"
            kirp.save(hedef / ad)
            uretilen += 1

    atlanan = sum(1 for b in veri["kutular"] if b.get("ortulu"))
    print(
        f"{uretilen} kirpim -> {hedef}  (beyazlatilan simge: {beyazlatilan}; "
        f"ortulu oldugu icin atlanan soru: {atlanan})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
