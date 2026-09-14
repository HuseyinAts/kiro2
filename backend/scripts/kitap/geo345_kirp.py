#!/usr/bin/env python
"""345 TYT-AYT Geometri veri setindeki kutu koordinatlarindan soru gorselleri uretir.

NEDEN AYRI SCRIPT
-----------------
Gorseller git'e girmez (yuzlerce MB; veriseti/ zaten .gitignore'da). Veri
setindeki her kayit kendi kirpim kutusunu (`kutu`) tasidigi icin gorseller
PDF'ten her ortamda YENIDEN uretilebilir. mikro_geo_kirp.py ile ayni desen.

IKI CILT
--------
Bu kitap iki cilt: c1 (440 sayfa) ve c2 (336 sayfa). Her kayit hangi cilde
ait oldugunu `cilt` ve `pdf_dosya` alanlarinda tasir; script iki PDF'i de
acar ve kayit basina dogru olani kullanir.

OLCEK 1:1 -- VE BU DOGRULANIR
-----------------------------
Kutu koordinatlari sayfa PNG'leri uzerinde olculdu. PDF sayfa boyutu
olculdu: 1920x1080 pt, PNG de 1920x1080 -- yani scale=1.0'da birebir,
donusum gerekmiyor. Bu VARSAYIM DEGIL: script her sayfada render boyutunu
BEKLENEN_BOYUT ile karsilastirir ve tutmazsa DURUR. Sessizce kaymis
kirpim uretmektense hic uretmemek yeglenir.

Uretilen dosya adi question_content.question_image_url ile birebir ayni:

    <CROP_IMAGE_DIR>/GEO345/<kayit_id>.png

CROP_IMAGE_DIR varsayilani core/application.py ile ayni: d-dataset/output/crops

KULLANIM
--------
    python backend/scripts/kitap/geo345_kirp.py [--olcek 1.0]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

VARSAYILAN_VERI = "veriseti/zkitap/cikti/geo345_sorular.json"
# Kitabin klasor adi Turkce karakter tasiyor; kabuk kodlamasina takilmamak
# icin yol elle yazilmaz, desenle bulunur. Desen DAR: ayni klasorde
# "345 2025 Tyt Ayt Geometri Soru Bankasi 1" adli UCUNCU bir klasor daha var
# (c1'in ilk 336 sayfasinin ayri kopyasi) ve o KULLANILMAZ.
PDF_KOK = "veriseti/zkitap/screenshots"
ONEK = "GEO345"
BEKLENEN_BOYUT = (1920, 1080)


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


def _pdf_bul(kok: Path, dosya_adi: str) -> Path | None:
    for p in kok.glob("*/*.pdf"):
        if p.name == dosya_adi:
            return p
    return None


def uret(veri_yolu: Path, pdf_kok: Path, hedef: Path, olcek: float) -> int:
    veri = json.loads(veri_yolu.read_text(encoding="utf-8"))
    hedef.mkdir(parents=True, exist_ok=True)

    belgeler: dict[str, pdfium.PdfDocument] = {}
    for ad in sorted({r["pdf_dosya"] for r in veri}):
        yol = _pdf_bul(pdf_kok, ad)
        if yol is None:
            print(f"DURDU: PDF bulunamadi: {ad} (kok: {pdf_kok})")
            return 2
        belgeler[ad] = pdfium.PdfDocument(str(yol))
        print(f"PDF: {yol}  ({len(belgeler[ad])} sayfa)")

    onbellek: tuple[str, int] | None = None
    onbellek_im: Image.Image | None = None
    adet = 0

    for i, r in enumerate(veri, 1):
        kutu = r.get("kutu")
        if not kutu:
            continue
        anahtar = (r["pdf_dosya"], r["sayfa"])
        if anahtar != onbellek:
            onbellek_im = (
                belgeler[r["pdf_dosya"]][r["sayfa"] - 1]
                .render(scale=1.0)
                .to_pil()
                .convert("RGB")
            )
            if onbellek_im.size != BEKLENEN_BOYUT:
                print(
                    f"DURDU: {r['pdf_dosya']} s{r['sayfa']} render boyutu "
                    f"{onbellek_im.size}, beklenen {BEKLENEN_BOYUT}. Kutu "
                    f"koordinatlari bu boyutta olculdu; kaymis kirpim "
                    f"uretmektense duruyorum."
                )
                return 3
            onbellek = anahtar
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
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=VARSAYILAN_VERI)
    p.add_argument("--pdf-kok", default=PDF_KOK)
    p.add_argument(
        "--crop-dir", default=os.environ.get("CROP_IMAGE_DIR", "d-dataset/output/crops")
    )
    p.add_argument("--olcek", type=float, default=1.0)
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    veri = Path(args.veri)
    if not veri.is_file():
        print(f"DURDU: veri dosyasi yok: {veri}")
        return 2
    return uret(veri, Path(args.pdf_kok), Path(args.crop_dir) / ONEK, args.olcek)


if __name__ == "__main__":
    raise SystemExit(main())
