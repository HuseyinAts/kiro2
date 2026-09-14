#!/usr/bin/env python
"""345 2025 AYT Biyoloji Soru Bankasi -- soru kirpimlarini uretir.

NEDEN AYRI SCRIPT
-----------------
`question_image_url` TAM SORU KIRPIMIDIR (metin + sekil birlikte) ve
kirpim kutusu `pipeline_metadata.kirpim_kutusu` icinde saklanir. Boylece
gorseller depoya konmaz, her ortamda kaynaktan YENIDEN URETILIR.
mikro_geo_kirp.py / geo345_kirp.py ile ayni sozlesme.

KAYNAK
------
Kitap bir zkitap goruntuleyici EKRAN GORUNTUSU dizisidir; sayfalar
1504x1936 PNG olarak `temiz ...` klasorunde durur (374 sayfa,
sayfa_0003 - sayfa_0376). PDF yok, metin katmani yok.

CALISMA ZAMANI OLCEK DENETIMI
-----------------------------
Kirpim kutulari 1504x1936 uzerinde OLCULDU. Kaynak klasor bir gun baska
bir olcekle yeniden uretilirse kutular sessizce yanlis yere duser --
bu yuzden ilk sayfada boyut DOGRULANIR ve uymazsa script DURUR.
(geo345_kirp.py'de ayni denetim var; oradaki gerekce de ayni.)

KULLANIM
--------
    python backend/scripts/kitap/biyo345_kirp.py [--cikti <dizin>]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

KOK = Path(__file__).resolve().parents[3]
VARSAYILAN_VERI = KOK / "veriseti/zkitap/cikti/biyo345_sorular.json"
SAYFA_DIZINI = (
    KOK
    / "veriseti/zkitap/screenshots"
    / ("345 2025 Ayt Biyoloji Soru Bankas" + chr(0x0131))
    / ("temiz 345 2025 Ayt Biyoloji Soru Bankas" + chr(0x0131))
)
VARSAYILAN_CIKTI = KOK / "d-dataset/output/crops/BIYO345"
BEKLENEN_BOYUT = (1504, 1936)


def uret(veri_yolu: Path, cikti: Path) -> int:
    kayitlar = json.loads(veri_yolu.read_text(encoding="utf-8"))
    if not kayitlar:
        print("DURDU: veri seti bos")
        return 2
    cikti.mkdir(parents=True, exist_ok=True)

    onbellek: dict[str, Image.Image] = {}
    yazilan = atlanan = 0
    for k in kayitlar:
        sayfa = k["sayfa"]
        if sayfa not in onbellek:
            yol = SAYFA_DIZINI / f"sayfa_{sayfa}.png"
            if not yol.exists():
                print(f"DURDU: sayfa bulunamadi: {yol}")
                return 2
            with Image.open(yol) as im:
                sim = im.convert("RGB")
            if sim.size != BEKLENEN_BOYUT:
                print(
                    f"DURDU: sayfa_{sayfa}.png boyutu {sim.size}, beklenen "
                    f"{BEKLENEN_BOYUT}. Kirpim kutulari beklenen olcekte "
                    "olculdu; baska olcekte kirpim SESSIZCE yanlis olur."
                )
                return 3
            onbellek.clear()  # tek sayfa bellekte yeter
            onbellek[sayfa] = sim
        hedef = cikti / f"{k['id']}.png"
        if hedef.exists():
            atlanan += 1
            continue
        x0, y0, x1, y1 = k["kutu"]
        onbellek[sayfa].crop((x0, y0, x1, y1)).save(hedef)
        yazilan += 1

    print(f"kirpim: {yazilan} yazildi, {atlanan} zaten vardi -> {cikti}")
    var = len(list(cikti.glob("*.png")))
    print(f"dizinde toplam {var} png; veri setinde {len(kayitlar)} soru")
    if var < len({k["id"] for k in kayitlar}):
        print("HATA: bazi kirpimlar uretilemedi")
        return 3
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--veri", default=str(VARSAYILAN_VERI))
    p.add_argument("--cikti", default=str(VARSAYILAN_CIKTI))
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    return uret(Path(a.veri), Path(a.cikti))


if __name__ == "__main__":
    raise SystemExit(main())
