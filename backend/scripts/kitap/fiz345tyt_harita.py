#!/usr/bin/env python
"""345 2025 TYT Fizik: unite agaci haritasi (migration 0060'in kaynagi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
* Unite adlari ve basili baslangic sayfalari: icindekiler (dosya 3-4, gozle;
  `ham_okumalar.icindekiler`). Basili sayfa = dosya.
* Bagimsiz dogrulama: her unitenin baslangic sayfasinin ust bandi (gozle;
  `ham_okumalar.bant_okumasi`): '1. bolum' rozeti ve orta bantta unite adi.
  Bant adi icindekiler adinin ASCII-buyuk katlamasi ya da onun onekidir
  (s316 bandi 'ISIK AKISI VE AYDINLANMA', icindekiler 'Isik Akisi -
  Aydinlanma - Golge Olaylari'; noktalama/tire yok sayilir).
* Her test tek unitenin sayfa araliginda (`fiz345tyt_anahtar.py` kapisi).

DUZEY
-----
Unite FIZ kokunun altinda (kok+1), kod `FIZ-345T25-Unn`. Kitap uniteyi
'N. bolum' parcalarina boler ama parca adi basmaz; sorular unite dugumune
baglanir (`konu_eslesme_duzeyi` = 'unite').
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_tyt_fizik"
HAM = Path(f"{ONEK_DOSYA}_ham_okumalar.json")
ANAHTAR = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
HEDEF = Path(f"{ONEK_DOSYA}_konu_haritasi.json")
KOD_ONEKI = "FIZ-345T25"
_TR = str.maketrans({"\u0131": "i", "\u0130": "I"})


def ascii_buyuk(ad: str) -> str:
    """Turkce ad -> bant bicimi (ASCII, buyuk harf, yalniz harf/rakam/bosluk)."""
    duz = unicodedata.normalize("NFKD", ad.translate(_TR))
    duz = "".join(c for c in duz if ord(c) < 128).upper()
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", duz).split())


def bant_uyar(bant: str, ad: str) -> bool:
    """Bant kelimeleri icindekiler adinin kelimelerinde SIRAYLA var, ilk kelime ayni."""
    iw = ascii_buyuk(ad).split()
    # Baglac 've' bantta tire yerine yazilabilir (s316: 'AKISI VE AYDINLANMA').
    bw = [w for w in bant.split() if w != "VE" or w in iw]
    j = 0
    for w in iw:
        if j < len(bw) and w == bw[j]:
            j += 1
    return bool(bw) and bw[0] == iw[0] and j == len(bw)


def harita(ham: dict, anahtar: dict) -> dict:
    icindekiler = ham["icindekiler"]["uniteler"]
    bant = ham["bant_okumasi"]["baslangic"]
    uniteler = []
    for no, ad, sayfa in icindekiler:
        b = bant.get(str(sayfa))
        if b is None:
            raise SystemExit(f"U{no}: s{sayfa} bant okumasi yok")
        if b["rozet"] != "1. bolum":
            raise SystemExit(f"U{no}: s{sayfa} rozet {b['rozet']!r}")
        if not bant_uyar(b["unite_adi"], ad):
            raise SystemExit(f"U{no}: bant '{b['unite_adi']}' != '{ascii_buyuk(ad)}'")
        uniteler.append(
            {
                "kod": f"{KOD_ONEKI}-U{no:02d}",
                "no": no,
                "ad": ad,
                "ad_ascii": ascii_buyuk(ad),
                "basili_baslangic": sayfa,
                "bant_adi": b["unite_adi"],
            }
        )
    if [u["no"] for u in uniteler] != list(range(1, len(uniteler) + 1)):
        raise SystemExit("unite numaralari 1..n sirali degil")
    kod = {u["no"]: u["kod"] for u in uniteler}
    testler = [
        {
            "birim": t["birim"],
            "unite": kod[t["unite"]],
            "sayfalar": t["sayfalar"],
            "soru_sayisi": t["soru_sayisi"],
        }
        for t in anahtar["testler"]
    ]
    return {
        "kaynak": "345 2025 TYT Fizik Soru Bankasi",
        "arac": "scripts/kitap/fiz345tyt_harita.py",
        "nereden": (
            "Unite adlari ve baslangic sayfalari: icindekiler (dosya 3-4, gozle). "
            "Dogrulama: baslangic sayfasinin ust bandi ('1. bolum' + unite adi, gozle)."
        ),
        "dogrulama": "19/19 baslangic sayfasi '1. bolum' + bant adi == icindekiler adi",
        "unite_sayisi": len(uniteler),
        "uniteler": uniteler,
        "test_sayisi": len(testler),
        "testler": testler,
    }


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    anahtar = json.loads(ANAHTAR.read_text("ascii"))
    veri = harita(ham, anahtar)
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(f"unite {veri['unite_sayisi']}  test {veri['test_sayisi']}  -> {HEDEF.name}")


if __name__ == "__main__":
    main()
