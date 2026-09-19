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

import numpy as np
from PIL import Image, ImageDraw

KLASOR_DESENI = "2023-2024-AC*TYT-AYT Geometri Soru Bank*"
KART = (593, 46)
BEKLENEN_BOYUT = (1920, 1080)
ONEK = "ACILGEO_2324"
# Disk glifin merkezine gore 30x32; golgesi icin her yone pay.
# SAG payi OLCUMLE sinirlandi: 41 sayfada her simgenin cevresi tarandi,
# diskin golgesi en fazla gx+22'ye ulasiyor, soru numarasinin KIRMIZI
# glifi ise en erken gx+25'te (antialias) / gx+26'da (dolu piksel)
# basliyor. Eski deger 27 idi ve numaranin ilk 1-2 sutununu beyazliyordu;
# s0009_sag_2'de basili "8" boylece "3" gibi okunuyordu. 23, golgeyi tam
# kapsar ve numaraya 2 px uzak kalir.
DISK_SOL, DISK_UST, DISK_SAG, DISK_ALT = 13, 14, 23, 28


def _disk_dikdortgeni(gx: int, gy: int) -> tuple[int, int, int, int]:
    return (gx - DISK_SOL, gy - DISK_UST, gx + DISK_SAG, gy + DISK_ALT)


def _numara_sol_kenari(dizi: np.ndarray, gx: int, gy: int) -> int | None:
    """Simgenin sagindaki KIRMIZI soru numarasinin en sol sutunu (tam goruntu).

    None => o pencerede kirmizi piksel yok (numara baska yerde ya da yok).

    Pencere DAR: y gy-2 .. gy+20, x gx+22 .. gx+60.

    Neden: oluk boyunca dondurulmus kirmizi-sari "ACIL MATEMATIK" logosu
    uzuyor; o serit diskin ust/alt ucunda ve gx+14 civarinda kirmizi piksel
    birakiyor, genis pencere onu numara saniyordu (28 yanlis alarm).
    41 sayfalik olcumde numaranin en sol sutunu her zaman gx+26 .. gx+34,
    diskin golgesi ise en fazla gx+22; bu yuzden gx+22'den saga bakmak
    numarayi kacirmadan logoyu disarida birakiyor. Olcum penceresi
    beyazlatmadan ONCEKI goruntude calisir, bu yuzden pay gx+22'yi assa
    bile numara hala gorulur ve kapi tetiklenir.
    """
    pencere = dizi[gy - 2 : gy + 20, gx + 22 : gx + 60]
    if pencere.size == 0:
        return None
    kirmizi = (
        (pencere[:, :, 0] > 140) & (pencere[:, :, 1] < 90) & (pencere[:, :, 2] < 90)
    )
    sutunlar = np.nonzero(kirmizi.any(axis=0))[0]
    if not len(sutunlar):
        return None
    return int(gx + 22 + sutunlar.min())


def _kapi6(dizi: np.ndarray, simgeler: list[list[int]], n: int) -> list[str]:
    """KAPI 6 -- beyazlatma soru numarasina DOKUNMASIN.

    Neden var: disk dikdortgeninin sag payi 27 iken numaranin ilk 1-2
    sutununu beyazliyordu ve basili "8" kirpimda "3" gibi okunuyordu
    (s0009_sag_2). Olcum yerine varsayimla secilmis bir paydi; bu kapi
    ayni hatanin sessizce geri gelmesini engeller.
    """
    ihlal = []
    for gx, gy in simgeler:
        sol = _numara_sol_kenari(dizi, gx, gy)
        if sol is None:
            continue
        if gx + DISK_SAG >= sol:
            ihlal.append(
                f"s{n} simge({gx},{gy}): beyazlatma {gx + DISK_SAG}'e kadar, "
                f"numara {sol}'de basliyor"
            )
    return ihlal


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

    # 1. GECIS -- yalniz dogrulama. Tek bir sayfa bile kapiyi gecemezse hic
    # dosya yazilmaz; kismi/bozuk bir kirpim seti birakmak istemiyoruz.
    tum_ihlal: list[str] = []
    for n in sorted(sayfa_kutu):
        im = Image.open(kok / f"sayfa_{n:04d}.png").convert("RGB")
        if im.size != BEKLENEN_BOYUT:
            print(
                f"HATA: s{n} boyutu {im.size}, beklenen {BEKLENEN_BOYUT}; duruldu",
                file=sys.stderr,
            )
            return 1
        tam = [[gx + KART[0], gy + KART[1]] for gx, gy in sayfa_simge[n]]
        tum_ihlal += _kapi6(np.asarray(im, dtype=int), tam, n)
    if tum_ihlal:
        print("HATA: KAPI6 (beyazlatma soru numarasina degiyor):", file=sys.stderr)
        for satir in tum_ihlal[:10]:
            print("  " + satir, file=sys.stderr)
        print(f"  toplam {len(tum_ihlal)} ihlal; hic dosya yazilmadi", file=sys.stderr)
        return 1

    # 2. GECIS -- kirpimlari yaz.
    uretilen = 0
    beyazlatilan = 0
    for n in sorted(sayfa_kutu):
        im = Image.open(kok / f"sayfa_{n:04d}.png").convert("RGB")
        tam = [[gx + KART[0], gy + KART[1]] for gx, gy in sayfa_simge[n]]
        d = ImageDraw.Draw(im)
        # Sayfadaki TUM simgeleri (kart koordinatindan tam goruntuye tasiyarak)
        # beyaza boya; kutu kirpimi bundan sonra yapilir.
        for x0, y0, x1, y1 in (_disk_dikdortgeni(gx, gy) for gx, gy in tam):
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
