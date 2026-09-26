#!/usr/bin/env python
"""345 2025 TYT Kimya: unite agaci haritasi (migration 0062'nin kaynagi).

KAYNAK -- ADLAR UYDURULMADI
---------------------------
* Unite adlari, konu adlari ve basili baslangic sayfalari: icindekiler
  (dosya 3-4, gozle; `ham_okumalar.icindekiler`). Basili sayfa = dosya.
* Bagimsiz dogrulama: her unitenin ilk soru sayfasinin ust bandi (gozle;
  `ham_okumalar.bant_okumasi`): '1. TEST' rozeti ve orta bantta unitenin
  ILK KONUSUNUN adi. Bant adi konu adinin ASCII-buyuk katlamasidir
  (s110 bandi 'MADDENIN FIZIKSEL HALLERI', icindekiler 'Maddenin Fiziksel
  Halleri'; sapka/noktalama yok sayilir). Unite ayraci sayfalari (5, 35,
  71, 109, 139, 155, 195, 231, 263) seritsiz; her unite bir onceki ayractan
  sonra baslar.
* Her test tek unitenin sayfa araliginda (`kim345tyt_anahtar.py` kapisi).

DUZEY
-----
Unite KIM kokunun altinda (kok+1), kod `KIM-345T25-Unn`. Kitap uniteyi
konulara boler (icindekiler), ama her unitenin sonundaki 'OSYM TADINDA'
testleri butun uniteyi kapsar ve son konunun sayfa araligina duser; test
turu pikselden ayrilmadigi icin sorular UNITE dugumune baglanir
(`konu_eslesme_duzeyi` = 'unite'). Konu listesi haritada kayitlidir
(ileride konu duzeyine inmek icin), agaca yazilmaz.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK_DOSYA = CIKTI / "345_2025_tyt_kimya"
HAM = Path(f"{ONEK_DOSYA}_ham_okumalar.json")
ANAHTAR = Path(f"{ONEK_DOSYA}_cevap_anahtari.json")
HEDEF = Path(f"{ONEK_DOSYA}_konu_haritasi.json")
KOD_ONEKI = "KIM-345T25"
_TR = str.maketrans({"\u0131": "i", "\u0130": "I"})


def ascii_buyuk(ad: str) -> str:
    """Turkce ad -> bant bicimi (ASCII, buyuk harf, yalniz harf/rakam/bosluk)."""
    duz = unicodedata.normalize("NFKD", ad.translate(_TR))
    duz = "".join(c for c in duz if ord(c) < 128).upper()
    return " ".join(re.sub(r"[^A-Z0-9 ]", " ", duz).split())


def harita(ham: dict, anahtar: dict) -> dict:
    icindekiler = ham["icindekiler"]["uniteler"]
    konular = ham["icindekiler"]["konular"]
    bant = ham["bant_okumasi"]["baslangic"]
    uniteler = []
    for no, ad, sayfa in icindekiler:
        ilk = [k for k in konular if k[0] == no]
        if not ilk:
            raise SystemExit(f"U{no}: icindekilerde konu yok")
        if ilk[0][2] != sayfa:
            raise SystemExit(f"U{no}: ilk konu s{ilk[0][2]} != unite s{sayfa}")
        b = bant.get(str(sayfa))
        if b is None:
            raise SystemExit(f"U{no}: s{sayfa} bant okumasi yok")
        if b["rozet"] != "1. TEST":
            raise SystemExit(f"U{no}: s{sayfa} rozet {b['rozet']!r}")
        if b["konu_adi"] != ascii_buyuk(ilk[0][1]):
            raise SystemExit(
                f"U{no}: bant '{b['konu_adi']}' != '{ascii_buyuk(ilk[0][1])}'"
            )
        uniteler.append(
            {
                "kod": f"{KOD_ONEKI}-U{no:02d}",
                "no": no,
                "ad": ad,
                "ad_ascii": ascii_buyuk(ad),
                "basili_baslangic": sayfa,
                "bant_ilk_konu": b["konu_adi"],
                "konular": [[k[1], k[2]] for k in ilk],
            }
        )
    if [u["no"] for u in uniteler] != list(range(1, len(uniteler) + 1)):
        raise SystemExit("unite numaralari 1..n sirali degil")
    bas = [u["basili_baslangic"] for u in uniteler]
    if bas != sorted(bas):
        raise SystemExit("unite baslangiclari artan degil")
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
        "kaynak": "345 2025 TYT Kimya Soru Bankasi",
        "arac": "scripts/kitap/kim345tyt_harita.py",
        "nereden": (
            "Unite ve konu adlari, baslangic sayfalari: icindekiler (dosya 3-4, gozle). "
            "Dogrulama: unitenin ilk soru sayfasinin ust bandi ('1. TEST' + ilk konu adi, gozle)."
        ),
        "dogrulama": (
            f"{len(uniteler)}/{len(uniteler)} baslangic sayfasi '1. TEST' + bant adi == "
            "ilk konu adi"
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
