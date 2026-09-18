#!/usr/bin/env python
"""345 2025 AYT Fizik veri setindeki kutulardan soru gorsellerini uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (yuzlerce MB; veriseti/ zaten .gitignore'da). Veri
setindeki her kayit kendi kirpim kutusunu (`kirpim_kutusu`) tasidigi icin
gorseller PDF'ten her ortamda YENIDEN uretilebilir. fiz345_kirp.py ile
ayni desen.

KOORDINAT SISTEMI -- DIKKAT
---------------------------
`kirpim_kutusu` SAYFA KARTI koordinatlarindadir (kart = tam goruntunun
icindeki (584, 42)-(1332, 1022) dikdortgeni). PDF sayfasi ise 1920x1080
render edilir. Bu yuzden her kutuya KART_OFSET eklenir. Render boyutu
BEKLENEN_BOYUT ile karsilastirilir ve tutmazsa script DURUR; sessizce
kaymis kirpim uretmektense hic uretmemek yeglenir.

Uretilen dosya adi question_content.question_image_url ile birebir ayni:

    <CROP_IMAGE_DIR>/FIZ345_AYT/<kayit_id>.png

KULLANIM
--------
    python backend/scripts/kitap/fiz345_kirp.py [--olcek 1.0]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

VARSAYILAN_VERI = "veriseti/zkitap/cikti/345_ayt_fizik_sorular.json"
PDF_DESENI = "veriseti/zkitap/screenshots/345 2025 Ayt Fizik*/*.pdf"
ONEK = "FIZ345_AYT"
KART_OFSET = (584, 42)
BEKLENEN_BOYUT = (1920, 1080)


def _kirp(sayfa_im: Image.Image, kutu: list[int]) -> Image.Image:
    sol, ust, sag, alt = (int(v) for v in kutu)
    dx, dy = KART_OFSET
    return sayfa_im.crop(
        (
            max(0, sol + dx),
            max(0, ust + dy),
            min(sayfa_im.width, sag + dx),
            min(sayfa_im.height, alt + dy),
        )
    )


def uret(veri_yolu: Path, pdf_yolu: Path, hedef: Path, olcek: float) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    hedef.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_yolu))

    onbellek_no: int | None = None
    onbellek_im: Image.Image | None = None
    adet = 0
    atlanan = 0

    for i, r in enumerate(veri, 1):
        kutu = r.get("kirpim_kutusu")
        if not kutu:
            atlanan += 1
            continue
        sayfa = r["sayfa"]
        if sayfa != onbellek_no:
            onbellek_im = pdf[sayfa - 1].render(scale=1.0).to_pil().convert("RGB")
            if onbellek_im.size != BEKLENEN_BOYUT:
                print(
                    f"DURDU: s{sayfa} render {onbellek_im.size} != {BEKLENEN_BOYUT}; "
                    "kutu koordinatlari bu olcege gore olculdu"
                )
                return 2
            onbellek_no = sayfa
        assert onbellek_im is not None
        soru = _kirp(onbellek_im, kutu)
        if olcek != 1.0:
            soru = soru.resize(
                (int(soru.width * olcek), int(soru.height * olcek)),
                Image.Resampling.LANCZOS,
            )
        soru.save(hedef / f"{r['id']}.png")
        adet += 1
        if i % 250 == 0:
            print(f"  {i}/{len(veri)}", flush=True)

    print(f"uretildi: {adet} soru gorseli -> {hedef}")
    print(f"kutusu olmayan (gorsel_yok_sekilli): {atlanan}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument(
        "--pdf", default=None, help=f"varsayilan: {PDF_DESENI} deseniyle bulunur"
    )
    p.add_argument(
        "--crop-dir", default=os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    )
    p.add_argument("--olcek", type=float, default=1.0)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    if args.pdf:
        pdf_yolu = Path(args.pdf)
    else:
        adaylar = sorted(Path().glob(PDF_DESENI))
        if not adaylar:
            print(f"DURDU: {PDF_DESENI} deseniyle PDF bulunamadi")
            return 2
        if len(adaylar) > 1:
            print(f"DURDU: birden fazla PDF bulundu, --pdf ile sec: {adaylar}")
            return 2
        pdf_yolu = adaylar[0]
        print(f"PDF: {pdf_yolu}")
    if not pdf_yolu.is_file():
        print(f"DURDU: PDF yok: {pdf_yolu}")
        return 2
    return uret(Path(args.veri), pdf_yolu, Path(args.crop_dir) / ONEK, args.olcek)


if __name__ == "__main__":
    raise SystemExit(main())
