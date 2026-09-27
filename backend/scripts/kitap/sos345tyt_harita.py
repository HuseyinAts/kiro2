#!/usr/bin/env python
"""345 2025 TYT Sosyal Bilgiler: test -> ders / konu / unite haritasi (Faz 2).

KAYNAK
------
Her soru sayfasinin ust bandi (iki bagimsiz okuma, ham dosyada): ortada
DERS, altinda KONU, 'OSYM TADINDA SORULAR k' rozetinde TEST, tek sayfalarda
mavi kitap simgesinde GUN. Her test iki sayfa (cift + sonraki tek).

KAPILAR
-------
* A ve B bant okumalari (normalize) birebir ayni.
* Anahtardan turetilen her testin sayfalarinda bant (gun, test) == anahtar
  satiri (gun, test); cift sayfanin gunu sonraki tek sayfadan.
* Bir testin sayfalarinda ders ve konu tek (bos konu satiri diger sayfadan).

UNITE
-----
Unite = (ders, konu tabani); taban = konu sonundaki ' - I/II/...' eki
atilmis hali. Kodlar: TAR-345T25-Unn, COG-345T25-Unn (mevcut kokler),
Felsefe ve Din Kulturu SOS kokunun altinda SOS-345T25-FEL-Unn /
SOS-345T25-DIN-Unn.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_tyt_sosyal_konu_haritasi.json
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_sosyal_"
HAM = CIKTI / f"{ON}ham_okumalar.json"
ANAHTAR = CIKTI / f"{ON}cevap_anahtari.json"
HEDEF = CIKTI / f"{ON}konu_haritasi.json"
DERS = {
    "TAR\u0130H": ("TARIH", "TAR-345T25-U"),
    "CO\u011eRAFYA": ("COGRAFYA", "COG-345T25-U"),
    "FELSEFE": ("FELSEFE", "SOS-345T25-FEL-U"),
    "D\u0130N K\u00dcLT\u00dcR\u00dc VE AHLAK B\u0130LG\u0130S\u0130": (
        "DIN",
        "SOS-345T25-DIN-U",
    ),
}
BEKLENEN_TEST = 150
_EK = re.compile(r"\s*-\s*(?:[IVX]+)?\s*$")


def norm(x: str | None) -> str | None:
    if x is None:
        return None
    x = unicodedata.normalize("NFC", x).replace("\u2019", "'")
    return re.sub(r"\s+", " ", re.sub(r"\s*/\s*", " / ", x)).strip()


def taban(konu: str) -> str:
    """'IKLIM BILGISI - III' -> 'IKLIM BILGISI'; ic tireler korunur."""
    return _EK.sub("", konu).strip()


def ascii_buyuk(x: str) -> str:
    tablo = str.maketrans(
        "\u0130\u0131\u015e\u015f\u011e\u011f\u00dc\u00fc\u00d6\u00f6\u00c7\u00e7\u00ce\u00ee\u00c2\u00e2\u00db\u00fb",
        "IISSGGUUOOCCIIAAUU",
    )
    return x.translate(tablo).upper()


def bantlar(ham: dict) -> dict[int, dict]:
    a = {b["sayfa"]: b for b in ham["baslik_okumalari"]["A"]}
    b = {x["sayfa"]: x for x in ham["baslik_okumalari"]["B"]}
    if set(a) != set(b):
        raise SystemExit("A/B bant sayfa kumesi farkli")
    for s, x in a.items():
        y = b[s]
        for k in ("ders", "konu"):
            if norm(x[k]) != norm(y[k]):
                raise SystemExit(f"s{s} {k}: A/B farkli")
        for k in ("test", "gun"):
            if x[k] != y[k]:
                raise SystemExit(f"s{s} {k}: A/B farkli")
    return {
        s: {**x, "ders": norm(x["ders"]), "konu": norm(x["konu"])} for s, x in a.items()
    }


def harita_uret(bant: dict[int, dict], cevaplar: list[dict]) -> tuple[list, list]:
    testler: dict[str, dict] = {}
    for c in cevaplar:
        t = testler.setdefault(
            c["birim"],
            {
                "birim": c["birim"],
                "gun": c["gun"],
                "test": c["test"],
                "sayfalar": set(),
                "soru_sayisi": 0,
            },
        )
        t["sayfalar"].add(c["dosya"])
        t["soru_sayisi"] += 1
    uniteler: dict[tuple[str, str], dict] = {}
    sayac: dict[str, int] = {}
    out = []
    for kod in sorted(testler):
        t = testler[kod]
        sayfalar = sorted(t["sayfalar"])
        dersler, konular = set(), set()
        for s in sayfalar:
            b = bant[s]
            gun = b["gun"] if s % 2 == 1 else bant[s + 1]["gun"]
            if (gun, b["test"]) != (t["gun"], t["test"]):
                raise SystemExit(
                    f"{kod} s{s}: bant ({gun}, {b['test']}) != anahtar ({t['gun']}, {t['test']})"
                )
            dersler.add(b["ders"])
            if b["konu"]:
                konular.add(b["konu"])
        if len(dersler) != 1 or len(konular) != 1:
            raise SystemExit(f"{kod}: ders/konu tek degil {dersler} {konular}")
        ders, konu = dersler.pop(), konular.pop()
        if ders not in DERS:
            raise SystemExit(f"{kod}: taninmayan ders {ders!r}")
        alan, onek = DERS[ders]
        anahtar = (ders, taban(konu))
        if anahtar not in uniteler:
            sayac[onek] = sayac.get(onek, 0) + 1
            uniteler[anahtar] = {
                "kod": f"{onek}{sayac[onek]:02d}",
                "ders": alan,
                "ad": taban(konu),
                "ad_ascii": ascii_buyuk(taban(konu)),
            }
        out.append(
            {
                "birim": kod,
                "gun": t["gun"],
                "test": t["test"],
                "ders": alan,
                "konu": konu,
                "unite": uniteler[anahtar]["kod"],
                "sayfalar": sayfalar,
                "soru_sayisi": t["soru_sayisi"],
            }
        )
    return out, list(uniteler.values())


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    cev = json.loads(ANAHTAR.read_text("ascii"))["cevaplar"]
    testler, uniteler = harita_uret(bantlar(ham), cev)
    if len(testler) != BEKLENEN_TEST:
        raise SystemExit(f"test {len(testler)} != {BEKLENEN_TEST}")
    veri = {
        "kaynak": "345 2025 TYT Sosyal Bilgiler Soru Bankasi",
        "arac": "scripts/kitap/sos345tyt_harita.py",
        "nereden": "sayfa ust bandi (ders, konu, test, gun) iki bagimsiz okuma",
        "dogrulama": {
            "bant_a_esittir_b": True,
            "bant_esittir_anahtar_gun_test": True,
            "test_basina_sayfa": 2,
        },
        "unite_sayisi": len(uniteler),
        "uniteler": uniteler,
        "test_sayisi": len(testler),
        "testler": testler,
    }
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(
        f"{len(testler)} test, {len(uniteler)} unite:",
        {
            d: sum(1 for u in uniteler if u["ders"] == d)
            for d in ("TARIH", "COGRAFYA", "FELSEFE", "DIN")
        },
    )


if __name__ == "__main__":
    main()
