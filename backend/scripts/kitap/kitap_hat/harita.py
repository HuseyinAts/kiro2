"""Test -> konu haritasi (profil gudumlu; acil2021tyt_harita deseni).

IKI KANAL
---------
A. Icindekiler (profilde BOLUMLER / ICINDEKILER; basili baslangic sayfasi).
B. Her testin ilk sayfasinin ust bandindaki ad (ham okumalar: A ve B).

KAPILAR
-------
* her testin TUM sayfalari tek bir icindekiler araliginda;
* bant adi (A == B) o konuyla ayni (normalize) ya da profilin BANT_ESLER
  acik listesindeki esleme;
* her konu en az bir test tasir.

KULLANIM (backend dizininden)
-----------------------------
    python -m scripts.kitap.kitap_hat.harita --profil K [--yaz]
"""

from __future__ import annotations

import argparse
import unicodedata
from types import ModuleType
from typing import Any

from scripts.kitap.kitap_hat import ortak


def norm(s: str) -> str:
    s = s.replace("\u0131", "i").replace("\u0130", "I")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return " ".join(s.replace(" - ", "-").replace(" -", "-").replace("- ", "-").split())


def konular(p: ModuleType) -> list[dict[str, Any]]:
    out = []
    say: dict[int, int] = {}
    ic = p.ICINDEKILER
    for i, (b, ad, bas) in enumerate(ic):
        son = ic[i + 1][2] - 1 if i + 1 < len(ic) else p.SON_SAYFA
        say[b] = say.get(b, 0) + 1
        out.append(
            {
                "kod": f"{p.KOD_ONEKI}-B{b:02d}-K{say[b]:02d}",
                "bolum": f"{p.KOD_ONEKI}-B{b:02d}",
                "ad": getattr(p, "KONU_AD_DUZELTME", {}).get(ad, ad),
                "icindekiler_adi": ad,
                "sayfalar": [bas, son],
            }
        )
    return out


def harita_uret(
    p: ModuleType, ham: dict[str, Any], tarama: dict[str, Any], anahtar: dict[str, Any]
) -> dict:
    ks = konular(p)
    a = {t["test"]: t["konu"] for t in ham["okuma_a"]["testler"]}
    b = {t["test"]: t["konu"] for t in ham["okuma_b"]["testler"]}
    soru: dict[str, int] = {}
    for c in anahtar["cevaplar"]:
        soru[c["birim"]] = soru.get(c["birim"], 0) + 1
    testler, hata = [], []
    for t in tarama["testler"]:
        n = t["test"]
        aday = [
            k
            for k in ks
            if all(k["sayfalar"][0] <= s <= k["sayfalar"][1] for s in t["sayfalar"])
        ]
        if len(aday) != 1:
            hata.append(f"test {n}: sayfalar {t['sayfalar']} tek konu araliginda degil")
            continue
        k = aday[0]
        if a[n] != b[n]:
            hata.append(f"test {n}: bant A != B")
        bant = norm(a[n])
        hedef = norm(k["icindekiler_adi"])
        if bant != hedef and p.BANT_ESLER.get(bant) != hedef:
            hata.append(f"test {n}: bant {bant!r} != konu {hedef!r}")
        birim = ortak.birim_kodu(p, n)
        testler.append(
            {
                "birim": birim,
                "test": n,
                "sayfalar": t["sayfalar"],
                "bant": a[n],
                "konu": k["kod"],
                "bolum": k["bolum"],
                "soru_sayisi": soru[birim],
            }
        )
    bos = [k["kod"] for k in ks if not any(t["konu"] == k["kod"] for t in testler)]
    if bos:
        hata.append(f"testsiz konu: {bos}")
    if hata:
        raise ValueError("; ".join(hata[:10]))
    return {
        "kaynak": p.KAYNAK_ADI,
        "arac": "scripts/kitap/kitap_hat/harita.py",
        "nereden": p.HARITA_NEREDEN,
        "bolumler": [
            {"kod": f"{p.KOD_ONEKI}-B{no:02d}", "no": no, "ad": ad}
            for no, ad in p.BOLUMLER
        ],
        "konular": ks,
        "test_sayisi": len(testler),
        "testler": testler,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profil", required=True)
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    p = ortak.profil(args.profil)
    h = harita_uret(
        p,
        ortak.oku(p, "ham_okumalar"),
        ortak.oku(p, "capa_taramasi"),
        ortak.oku(p, "cevap_anahtari"),
    )
    print(
        f"{len(h['bolumler'])} bolum, {len(h['konular'])} konu, {h['test_sayisi']} test -- kapilar TEMIZ"
    )
    if args.yaz:
        ortak.yaz(p, "konu_haritasi", h)
        print("yazildi")


if __name__ == "__main__":
    main()
