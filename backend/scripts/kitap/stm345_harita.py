#!/usr/bin/env python
"""345 2025 Start Matematik: unite agaci haritasi (0057 migration'inin kaynagi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
* Unite adlari: unite ayraci sayfalarinda basili '<no>. <ad>' basligi
  (Turkce, gozle; `ham_okumalar.ayrac_okumasi`).
* Bagimsiz dogrulama 1: ayrac adinin ASCII-buyuk katlamasi == icindekiler
  (dosya 3) satiri; ayrac dosyasi == icindekiler basili sayfasi + 1.
* Bagimsiz dogrulama 2: 45 testin her sayfasinin bandindaki unite adi ==
  sayfanin dustugu icindekiler araligindaki unite (`stm345_anahtar.py`
  kapisi; burada tekrar denetlenir).

DUZEY
-----
Unite MAT kokunun altinda (kok+1), kod `MAT-345S25-Unn`. Kitap uniteyi
alt konuya bolmuyor: test bandi yalniz unite adini basar ('0'dan Basla'
alt basliklari konu sayfalarinda, kapsam disi). Sorular unite dugumune
baglanir (`konu_eslesme_duzeyi` = 'unite').

KULLANIM
--------
    python backend/scripts/kitap/stm345_harita.py
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_start_matematik"
HAM = Path(f"{ONEK_DOSYA}_ham_okumalar.json")
ANAHTAR = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
HEDEF = Path(f"{ONEK_DOSYA}_konu_haritasi.json")
KOD_ONEKI = "MAT-345S25"
_TR = str.maketrans({"\u0131": "i", "\u0130": "I"})


def ascii_buyuk(ad: str) -> str:
    """Turkce ad -> icindekiler bicimi (ASCII, buyuk harf)."""
    duz = unicodedata.normalize("NFKD", ad.translate(_TR))
    return "".join(c for c in duz if ord(c) < 128).upper()


def harita(ham: dict, anahtar: dict) -> dict:
    icindekiler = {u[0]: (u[1], u[2]) for u in ham["icindekiler"]["uniteler"]}
    ayrac = ham["ayrac_okumasi"]["sayfalar"]
    if len(ayrac) != len(icindekiler):
        raise SystemExit(f"ayrac {len(ayrac)} != icindekiler {len(icindekiler)}")
    uniteler = []
    for dosya, (no, ad) in sorted(ayrac.items(), key=lambda kv: int(kv[0])):
        i_ad, i_sayfa = icindekiler[no]
        if ascii_buyuk(ad) != i_ad:
            raise SystemExit(
                f"U{no}: ayrac '{ascii_buyuk(ad)}' != icindekiler '{i_ad}'"
            )
        if int(dosya) != i_sayfa + 1:
            raise SystemExit(f"U{no}: ayrac dosya {dosya} != icindekiler {i_sayfa} + 1")
        uniteler.append(
            {
                "kod": f"{KOD_ONEKI}-U{no:02d}",
                "no": no,
                "ad": ad,
                "ad_ascii": i_ad,
                "ayrac_sayfasi": int(dosya),
                "basili_baslangic": i_sayfa,
            }
        )
    if [u["no"] for u in uniteler] != list(range(1, len(uniteler) + 1)):
        raise SystemExit("unite numaralari 1..n sirali degil")
    kod = {u["no"]: u["kod"] for u in uniteler}
    ad_ascii = {u["no"]: u["ad_ascii"] for u in uniteler}
    bant = ham["bant_okumasi"]["sayfalar"]
    testler = []
    for t in anahtar["testler"]:
        for s in t["sayfalar"]:
            if bant[str(s)][1] != ad_ascii[t["unite"]]:
                raise SystemExit(
                    f"s{s}: bant '{bant[str(s)][1]}' != unite {t['unite']}"
                )
        testler.append(
            {
                "birim": t["birim"],
                "unite": kod[t["unite"]],
                "test_adi": f"SINAVA GECIS {t['unite_ici_test']}",
                "sayfalar": t["sayfalar"],
                "soru_sayisi": t["soru_sayisi"],
            }
        )
    return {
        "kaynak": "345 2025 Start Matematik",
        "arac": "scripts/kitap/stm345_harita.py",
        "nereden": (
            "Unite adlari: unite ayraci sayfalari (gozle). Dogrulama: icindekiler "
            "(dosya 3) ASCII adi ve basili sayfasi; test bandindaki unite adi."
        ),
        "dogrulama": (
            "16/16 ayrac adi == icindekiler; 16/16 ayrac dosyasi == basili + 1; "
            "90/90 test sayfasi bandi == unite."
        ),
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
