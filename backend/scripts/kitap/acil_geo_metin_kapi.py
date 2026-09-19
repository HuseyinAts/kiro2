#!/usr/bin/env python
"""ACIL 2023-2024 Geometri: transkripsiyon veri setinin yapisal kapilari.

NEDEN AYRI KAPI
---------------
Transkripsiyonu 37 ayri ajan uretti; her biri yalniz kendi 47 gorselini
gordu. Hicbiri butunu gormedigi icin "sira kaydi", "eksik soru", "yanlis
teste yazildi" turu hatalar ajan icinde yakalanamaz. Bu script veri setini
kitabin KENDI cevap anahtarina ve kirpim kutularina karsi dogrular.

KAPILAR
-------
1. Sayim: `sorular` uzunlugu == kutu sayisi - ortulu sayisi.
2. Ortume: hicbir ortulu kutu veri sette olmamali.
3. Eslesme: her kaydin gorsel adi, kutu listesinden tam olarak bir kutuya
   denk gelmeli (ve tersi).
4. Test basina: her testin kutu sayisi, cevap anahtarindaki cevap sayisina
   esit olmali.
5. Numara: basili soru numarasi, test icindeki siraya esit olmali.
   ISTISNA: `kaynak_kusuru` dolu olan kayitlar (kitabin kendi basim
   hatasi belgelenmis demektir) rapor edilir ama kapiyi dusurmez.
6. Cevap: her kaydin cevabi, anahtarda ayni test+sira icin yazan cevap
   olmali.
7. Doluluk: govde bos olmamali, tam 5 sik bulunmali.

KULLANIM
--------
    python backend/scripts/kitap/acil_geo_metin_kapi.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

KOK = "veriseti/zkitap/cikti"


def _sirala(kutular: list[dict]) -> list[dict]:
    """Okuma sirasi: sayfa, sonra sol sutun, sonra sutun ici sira."""
    return sorted(
        kutular, key=lambda b: (b["sayfa"], 0 if b["sutun"] == "sol" else 1, b["sira"])
    )


def _sayfa_test(anahtar: list[dict]) -> dict[int, int]:
    esle: dict[int, int] = {}
    for c in anahtar:
        for s in range(c["bas_sayfa"], c["son_sayfa"] + 1):
            esle[s] = c["test"]
    return esle


def _ad(b: dict) -> str:
    return f"s{b['sayfa']:04d}_{b['sutun']}_{b['sira']}.png"


def _kapi123(kayitlar: list[dict], kutular: list[dict]) -> list[str]:
    """Sayim, ortume, ad eslesmesi."""
    hata: list[str] = []
    islenecek = [b for b in kutular if not b.get("ortulu")]
    if len(kayitlar) != len(islenecek):
        hata.append(f"KAPI1 sayim: kayit {len(kayitlar)}, beklenen {len(islenecek)}")

    ortulu_ad = {_ad(b) for b in kutular if b.get("ortulu")}
    kayit_ad = {k["gorsel"] for k in kayitlar}
    if kayit_ad & ortulu_ad:
        hata.append(f"KAPI2 ortume: veri sette {len(kayit_ad & ortulu_ad)} ortulu kutu")

    beklenen_ad = {_ad(b) for b in islenecek}
    if kayit_ad != beklenen_ad:
        hata.append(
            f"KAPI3 eslesme: eksik {len(beklenen_ad - kayit_ad)}, "
            f"fazla {len(kayit_ad - beklenen_ad)}"
        )
    return hata


def _kapi56(
    k: dict, b: dict, t: int, i: int, bekl_cevap: str, kusurlu: list[str]
) -> list[str]:
    """Tek kayit icin test/sira, basili numara ve cevap kontrolu."""
    hata: list[str] = []
    if k.get("test") != t or k.get("test_ici_sira") != i:
        hata.append(
            f"KAPI5 {_ad(b)}: test/sira {k.get('test')}/"
            f"{k.get('test_ici_sira')}, beklenen {t}/{i}"
        )
    if k.get("soru_no_basili") != i:
        satir = f"{_ad(b)}: basili {k.get('soru_no_basili')}, sira {i}"
        # kaynak_kusuru dolu => kitabin kendi basim hatasi belgelenmis.
        if k.get("kaynak_kusuru"):
            kusurlu.append(satir)
        else:
            hata.append("KAPI5 numara " + satir)
    if k.get("cevap") != bekl_cevap:
        hata.append(f"KAPI6 {_ad(b)}: cevap {k.get('cevap')}, anahtar {bekl_cevap}")
    return hata


def _kapi7(kayitlar: list[dict]) -> list[str]:
    hata: list[str] = []
    for k in kayitlar:
        if not k.get("govde"):
            hata.append(f"KAPI7 {k['gorsel']}: govde bos")
        if len(k.get("sikler") or {}) != 5:
            hata.append(f"KAPI7 {k['gorsel']}: sik sayisi 5 degil")
    return hata


def dogrula(veri: dict, anahtar: list[dict], kutular: list[dict]) -> list[str]:
    kayitlar = veri["sorular"]
    hata = _kapi123(kayitlar, kutular)

    testler: dict[int, list[dict]] = defaultdict(list)
    for c in anahtar:
        testler[c["test"]].append(c)
    for t in testler:
        testler[t].sort(key=lambda c: c["soru_no"])

    st = _sayfa_test(anahtar)
    per: dict[int, list[dict]] = defaultdict(list)
    for b in _sirala(kutular):
        per[st[b["sayfa"]]].append(b)

    for t, cs in testler.items():
        if len(per[t]) != len(cs):
            hata.append(f"KAPI4 test {t}: kutu {len(per[t])}, cevap {len(cs)}")

    kayit = {k["gorsel"]: k for k in kayitlar}
    numara_kusurlu: list[str] = []
    for t, bl in per.items():
        for i, b in enumerate(bl, 1):
            k = None if b.get("ortulu") else kayit.get(_ad(b))
            if k is None:
                continue
            hata += _kapi56(k, b, t, i, testler[t][i - 1]["cevap"], numara_kusurlu)

    hata += _kapi7(kayitlar)

    if numara_kusurlu:
        print(f"NOT: kitabin kendi numara hatasi ({len(numara_kusurlu)} kayit):")
        for satir in numara_kusurlu:
            print("  " + satir)
    return hata


def ana() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", default=KOK)
    a = ap.parse_args()
    kok = Path(a.kok)
    veri = json.loads((kok / "acil_2324_geometri_metin.json").read_text("utf-8"))
    anahtar = json.loads(
        (kok / "acil_2324_geometri_cevap_anahtari.json").read_text("utf-8")
    )["anahtar"]
    kutular = json.loads(
        (kok / "acil_2324_geometri_kirpim_kutulari.json").read_text("utf-8")
    )["kutular"]

    hata = dogrula(veri, anahtar, kutular)
    if hata:
        print(f"HATA: {len(hata)} ihlal", file=sys.stderr)
        for s in hata[:20]:
            print("  " + s, file=sys.stderr)
        return 1
    print(
        f"YEDI KAPI DA GECTI: {len(veri['sorular'])} soru, "
        f"{veri['test']} test, {veri['ortulu_disarida']} ortulu disarida"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())
