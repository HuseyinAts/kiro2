#!/usr/bin/env python
"""Neofizik veri setindeki kutu koordinatlarindan soru ve varlik gorsellerini uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (yuzlerce MB; d-dataset/ zaten .gitignore'da). Veri
setindeki her kayit kendi kirpim kutusunu (`kirpim_kutusu`) ve varlik
kutularini (`gorsel_varliklar[].kutu`) tasidigi icin gorseller PDF'ten her
ortamda YENIDEN uretilebilir -- tasinmasi gereken tek sey koordinatlar.

Uretilen dosya adlari question_content.question_image_url ve
pipeline_metadata->gorsel_varliklar[].url ile birebir ayni:

    <CROP_IMAGE_DIR>/NEOFIZIK_2025/<kayit_id>.png
    <CROP_IMAGE_DIR>/NEOFIZIK_2025/<kayit_id>-<tur>-<n>.png

CROP_IMAGE_DIR varsayilani core/application.py ile ayni: d-dataset/output/crops

KULLANIM
--------
    python backend/scripts/kitap/neofizik_kirp.py [--olcek 1.0]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

VARSAYILAN_VERI = "veriseti/zkitap/cikti/neofizik_2025_sorular_v2.json"
# Kitabin klasor/dosya adi Turkce karakter tasiyor; kabuk kodlamasina
# takilmamak icin yol elle yazilmaz, desenle bulunur.
PDF_DESENI = "veriseti/zkitap/screenshots/Neofizik*Ayt*Fizik*2025/*.pdf"
ONEK = "NEOFIZIK_2025"
PAY = 3  # varlik kirpimlarinda kenar payi (piksel)


def _kirp(sayfa_im: Image.Image, kutu: list[float], pay: int = 0) -> Image.Image:
    sol, ust, sag, alt = (int(v) for v in kutu)
    return sayfa_im.crop(
        (
            max(0, sol - pay),
            max(0, ust - pay),
            min(sayfa_im.width, sag + pay),
            min(sayfa_im.height, alt + pay),
        )
    )


def uret(veri_yolu: Path, pdf_yolu: Path, hedef: Path, olcek: float) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    hedef.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(pdf_yolu))

    onbellek_no: int | None = None
    onbellek_im: Image.Image | None = None
    soru_adet = varlik_adet = 0

    for i, r in enumerate(veri, 1):
        kutu = r.get("kirpim_kutusu")
        if not kutu:
            continue
        sayfa = r["sayfa"]
        if sayfa != onbellek_no:
            onbellek_im = pdf[sayfa - 1].render(scale=1.0).to_pil().convert("RGB")
            onbellek_no = sayfa
        assert onbellek_im is not None
        soru = _kirp(onbellek_im, kutu)
        if olcek != 1.0:
            soru = soru.resize(
                (int(soru.width * olcek), int(soru.height * olcek)),
                Image.Resampling.LANCZOS,
            )
        soru.save(hedef / f"{r['id']}.png")
        soru_adet += 1

        for n, v in enumerate(r.get("gorsel_varliklar", []), 1):
            # varlik kutulari SORU kirpimina goredir, sayfaya degil
            vs, vu, vsag, valt = v["kutu"]
            mutlak = [kutu[0] + vs, kutu[1] + vu, kutu[0] + vsag, kutu[1] + valt]
            _kirp(onbellek_im, mutlak, PAY).save(
                hedef / f"{r['id']}-{v['tur']}-{n}.png"
            )
            varlik_adet += 1

        if i % 250 == 0:
            print(f"  {i}/{len(veri)}", flush=True)

    print(f"uretildi: {soru_adet} soru gorseli + {varlik_adet} varlik -> {hedef}")
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
