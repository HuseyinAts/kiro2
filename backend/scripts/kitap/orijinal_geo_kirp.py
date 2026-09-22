#!/usr/bin/env python
"""Orijinal 2024 TYT-AYT Geometri: kirpim kutularindan soru gorselleri uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (`veriseti/` .gitignore'da). Her kutu
`orijinal_2024_geometri_kirpim_kutulari.json` icinde durdugu icin gorseller
her ortamda YENIDEN uretilebilir. c1cell_geo_kirp.py ile ayni desen.

KAYNAK: PNG
-----------
Kaynak FERNUS okuyucusunun 1920x1080 ekran goruntuleridir. Sayfa karti
goruntunun icinde (593, 46)-(1327, 1014) = 734x968 piksel yer kaplar --
BU KITAP ICIN olculdu (C1CELL'de 738x968 idi, kart konumu kitaba gore
degisiyor). Her sayfa BEKLENEN_BOYUT ile karsilastirilir; tutmazsa DURUR.

OKUYUCU DISKI BEYAZLATILIR -- KAPI 6
------------------------------------
Her sorunun solunda FERNUS okuyucu diski var (lila disk 240,238,247 /
glif 69,39,160). Disk okuyucunun kendi katmani; ogrenciye gosterilecek
gorselde isi yok. Beyazlatma RENGE gore DEGIL, bilinen simge KONUMLARINA
gore yapilir; konum-bazli beyazlatma kitabin mor/lila cizimlerini silmez.

Ortme olcumu (GEO_ORIJINAL_2024_FAZ1.md bolum 14) bu kitapta soru
sayfalarinda disk altinda soru icerigi KALMADIGINI olctu: 2070 simgenin
halka medyani 0, %99'u 18, en yuksek 20 ornek sutun arasi filigrana
biniyor. Yani beyazlatma soru kaybettirmiyor.

SIMGE ALANI
-----------
Kutu JSON'unda `simge` alani [y, x] sirasindadir (kart ici koordinat).
Iki kutunun simgesi yoktur (`elle: true`): s151 sag #4 ve s323 sol #3 --
o iki soruda okuyucu simgesi basilmamis, kutu ustu elle olculmustu.

KULLANIM
--------
    python backend/scripts/kitap/orijinal_geo_kirp.py
    python backend/scripts/kitap/orijinal_geo_kirp.py --ornek 40
    python backend/scripts/kitap/orijinal_geo_kirp.py --cikti <dizin>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
KUTULAR = CIKTI / "orijinal_2024_geometri_kirpim_kutulari.json"

KART = (593, 46, 593 + 734, 46 + 968)
BEKLENEN_BOYUT = (1920, 1080)
BEKLENEN_SAYFA = 432
BEKLENEN_KUTU = 2072
# Disk merkezi simge kaydinin TAM uzerinde degil: olculen kayma (+3, +1)
# (simge alani glif bilesenin merkezi, disk ondan biraz asagida/sagda).
DISK_KAYMA_Y = 3
DISK_KAYMA_X = 1
# Penceredeki her pikseli degil, YALNIZ okuyucu katmaninin renklerini
# beyazlatiriz. Duz daire (yaricap 20) soru numarasini yiyordu: disk s8'de
# x 40-67 arasinda, numara x 69'da basliyor -- daire numaraya giriyor.
DISK_PENCERE = 22
GLIF_RENK = (69, 39, 160)  # okuyucu buyutec glifi
DISK_RENK = (240, 238, 247)  # lila disk
GLIF_ESIK = 120
DISK_ESIK = 40
GOLGE_EN_AZ = 225  # diskin acik gri golgesi (max kanal)
GOLGE_FARK = 12  # golge grisi: max-min bundan kucuk


def _kaynak_dizin() -> Path:
    """Kaynak dizini SECMEZ, DOGRULAR.

    screenshots/ altinda benzer adli baska kitaplar var (ornegin
    "Orijinal-2024-Geometri" 160 sayfalik AYRI bir kitap). Gevsek bir glob
    sessizce yanlis kitabi kirpar; bu yuzden desen dar tutulur, tek eslesme
    zorunludur ve sayfa sayisi olculen degerle karsilastirilir.
    """
    adaylar = sorted(
        (KOK / "veriseti" / "zkitap" / "screenshots").glob(
            "Orijinal-2024-Geometri Soru Bank*"
        )
    )
    if len(adaylar) != 1:
        raise SystemExit(f"Kaynak dizin tek degil: {[a.name for a in adaylar]}")
    kaynak = adaylar[0]
    sayfa = len(list(kaynak.glob("sayfa_*.png")))
    if sayfa != BEKLENEN_SAYFA:
        raise SystemExit(f"Kaynak sayfa sayisi {sayfa} != {BEKLENEN_SAYFA}")
    return kaynak


def _diskleri_beyazlat(img: Image.Image, simgeler: list[list[int]]) -> Image.Image:
    """Okuyucu diskini KONUM+RENK ile siler.

    Konum: yalnizca bilinen simge kutucuklarinin icinde calisir, yani
    kitabin kendi mor/lila cizimlerine dokunmaz. Renk: pencerede de her
    pikseli degil, sadece okuyucu katmaninin renklerini (glif moru, lila
    disk, diskin acik gri golgesi) beyaza cevirir -- soru numarasinin
    pembesi ve metnin siyahi kalir.
    """
    if not simgeler:
        return img
    a = np.asarray(img).astype(np.int16)
    maske = np.zeros(a.shape[:2], bool)
    for gy, gx in simgeler:
        cy = KART[1] + gy + DISK_KAYMA_Y
        cx = KART[0] + gx + DISK_KAYMA_X
        y0, y1 = max(0, cy - DISK_PENCERE), min(a.shape[0], cy + DISK_PENCERE)
        x0, x1 = max(0, cx - DISK_PENCERE), min(a.shape[1], cx + DISK_PENCERE)
        maske[y0:y1, x0:x1] = True
    fark_glif = np.abs(a - np.array(GLIF_RENK)).sum(axis=2)
    fark_disk = np.abs(a - np.array(DISK_RENK)).sum(axis=2)
    enb, enk = a.max(axis=2), a.min(axis=2)
    golge = (enb - enk < GOLGE_FARK) & (enb >= GOLGE_EN_AZ)
    okuyucu = (fark_glif < GLIF_ESIK) | (fark_disk < DISK_ESIK) | golge
    a[maske & okuyucu] = 255
    return Image.fromarray(a.astype(np.uint8))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ornek", type=int, default=0, help="ilk N kutu (0=hepsi)")
    ap.add_argument(
        "--cikti", default=str(KOK / "backend" / "_geo1_gecici" / "orj24_kirpim")
    )
    args = ap.parse_args()

    veri = json.loads(KUTULAR.read_text("utf-8"))
    kutular = veri["kutular"]
    if len(kutular) != BEKLENEN_KUTU:
        raise SystemExit(f"Kutu sayisi {len(kutular)} != {BEKLENEN_KUTU}")
    if args.ornek:
        kutular = kutular[: args.ornek]
    kaynak = _kaynak_dizin()
    outdir = Path(args.cikti)
    outdir.mkdir(parents=True, exist_ok=True)

    # sayfa basina simge konumlari (beyazlatma icin) -- TUM kutulardan,
    # yalnizca uretilen altkumeden degil: komsu sorunun diski kutu kosesine
    # tasabilir.
    simge_sayfa: dict[int, list[list[int]]] = {}
    for k in veri["kutular"]:
        if k.get("simge"):
            simge_sayfa.setdefault(k["sayfa"], []).append(k["simge"])

    sayfada: dict[int, list[dict]] = {}
    for k in kutular:
        sayfada.setdefault(k["sayfa"], []).append(k)

    n = 0
    for p in sorted(sayfada):
        img = Image.open(kaynak / f"sayfa_{p:04d}.png").convert("RGB")
        if img.size != BEKLENEN_BOYUT:
            raise SystemExit(f"BOYUT UYUSMAZLIGI s{p}: {img.size} != {BEKLENEN_BOYUT}")
        img = _diskleri_beyazlat(img, simge_sayfa.get(p, []))
        for k in sayfada[p]:
            x0, y0, x1, y1 = k["kutu"]
            c = img.crop((KART[0] + x0, KART[1] + y0, KART[0] + x1, KART[1] + y1))
            c.save(outdir / f"s{p:04d}_{k['sutun']}_{k['sira']}.png")
            n += 1

    print(f"uretildi {n} soru gorseli -> {outdir}")


if __name__ == "__main__":
    main()
