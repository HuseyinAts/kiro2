#!/usr/bin/env python
"""C1CELL 2024 TYT-AYT Geometri: kirpim kutularindan soru gorselleri uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (`veriseti/` .gitignore'da). Her kutu
`c1cell_2024_geometri_kirpim_kutulari.json` icinde durdugu icin gorseller
her ortamda YENIDEN uretilebilir. acil_geo_kirp.py ile ayni desen.

KAYNAK: PNG
-----------
Kaynak FERNUS okuyucusunun 1920x1080 ekran goruntuleridir. Sayfa karti
goruntunun icinde (591, 46)-(1329, 1014) = 738x968 piksel yer kaplar --
BU KITAP ICIN olculdu. Her sayfa BEKLENEN_BOYUT ile karsilastirilir;
tutmazsa script DURUR.

OKUYUCU DISKI BEYAZLATILIR -- KAPI 6
------------------------------------
Her sorunun solunda FERNUS okuyucu diski var (lila disk 240,238,247 /
glif 69,39,160). Disk okuyucunun kendi katmani; ogrenciye gosterilecek
gorselde isi yok. Kutunun sol kenari zaten simgenin SAGINDAN baslar, ama
komsu sutunun diski kutu kosesine tasabilir. Beyazlatma RENGE gore DEGIL,
bilinen simge KONUMLARINA gore yapilir (her simgenin bir kutusu var, liste
tam); konum-bazli beyazlatma kitabin mor/lila cizimlerini silmez.

C1CELL'DE ORTULU SORU YOK
-------------------------
ACIL 2023-2024'te sag sutun diski sol sutun sikkini ortuyordu (151 soru
disarida). C1CELL'de kutular kapidan (birim simge-sayisi == cevap-sayisi,
163/163) gecti ve ortme yok; 1770 sorunun tamami kirpilir.

KULLANIM
--------
    python backend/scripts/kitap/c1cell_geo_kirp.py
    python backend/scripts/kitap/c1cell_geo_kirp.py --ornek 40
    python backend/scripts/kitap/c1cell_geo_kirp.py --cikti <dizin>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "c1cell_2024_geometri_kirpim_kutulari.json"

KART = (591, 46, 1329, 1014)
BEKLENEN_BOYUT = (1920, 1080)
DISK_YARICAP = 16


def _kaynak_dizin():
    adaylar = sorted(
        (KOK / "veriseti" / "zkitap" / "screenshots").glob(
            "C1CELL-2024-TYT-AYT-Geometri Soru Bank*"
        )
    )
    if not adaylar:
        raise SystemExit("Kaynak ekran goruntuleri bulunamadi (C1CELL screenshots).")
    return adaylar[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0, help="ilk N kutu (0=hepsi)")
    ap.add_argument(
        "--cikti", default=str(KOK / "backend" / "_geo1_gecici" / "c1_kirpim")
    )
    args = ap.parse_args()

    veri = json.loads(KUTULAR.read_text("utf-8"))
    kutular = veri["kutular"]
    if args.ornek:
        kutular = kutular[: args.ornek]
    kaynak = _kaynak_dizin()
    outdir = Path(args.cikti)
    outdir.mkdir(parents=True, exist_ok=True)

    # sayfa basina simge konumlari (beyazlatma icin) -- tum kutulardan
    simge_sayfa: dict[int, list[list[int]]] = {}
    for k in veri["kutular"]:
        simge_sayfa.setdefault(k["sayfa"], []).append(k["simge"])

    by_page: dict[int, list[dict]] = {}
    for k in kutular:
        by_page.setdefault(k["sayfa"], []).append(k)

    n = 0
    for p in sorted(by_page):
        yol = kaynak / f"sayfa_{p:04d}.png"
        img = Image.open(yol).convert("RGB")
        if img.size != BEKLENEN_BOYUT:
            raise SystemExit(f"BOYUT UYUSMAZLIGI s{p}: {img.size} != {BEKLENEN_BOYUT}")
        d = ImageDraw.Draw(img)
        for gx, gy in simge_sayfa.get(p, []):
            cx, cy = KART[0] + gx, KART[1] + gy
            d.ellipse(
                [
                    cx - DISK_YARICAP,
                    cy - DISK_YARICAP,
                    cx + DISK_YARICAP,
                    cy + DISK_YARICAP,
                ],
                fill=(255, 255, 255),
            )
        for k in by_page[p]:
            x0, y0, x1, y1 = k["kirpim_kutusu"]
            c = img.crop((KART[0] + x0, KART[1] + y0, KART[0] + x1, KART[1] + y1))
            ad = f"s{p:04d}_{k['sutun']}_{k['sira']}.png"
            c.save(outdir / ad)
            n += 1

    print(f"uretildi {n} soru gorseli -> {outdir}")


if __name__ == "__main__":
    main()
