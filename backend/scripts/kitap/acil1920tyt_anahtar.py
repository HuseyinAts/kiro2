#!/usr/bin/env python
"""2019-2020 ACIL TYT Matematik: cevap anahtari (test sonu seritlerinden).

KAYNAK VE KANALLAR
------------------
Her testin son sayfasinda sari cerceveli cevap seridi ("1. C", "2. E" ...).
Ham okumalar `acil_1920_tyt_matematik_ham_okumalar.json`:

* okuma A / okuma B: iki bagimsiz gorsel okuma (A ileri, B geri; hucre
  sayisi okuyucuya soylenmedi). A == B hucre ve harf duzeyinde olmali.
* glif: seritteki harf glifleri en-yakin-komsu birini-disarida-birak; her
  segmentlenen hucrede glif komsusunun harfi okumayla ayni olmali.
* goz_c: glif segmentasyonu kapsami disindaki testler 5x gozle.

Her hucre ya glif ya goz_c kanalinca kapsanir; kapsanmayan hucre DURDURUR.
Hicbir soru cozulmedi; tek kaynak kitabin basili seridi.

CIKTI
-----
`acil_1920_tyt_matematik_cevap_anahtari.json`: soru basina birim (test),
soru (test ici sira), cevap, dosya, sutun, sutun_sira (capa taramasindan).

KULLANIM
--------
    python backend/scripts/kitap/acil1920tyt_anahtar.py [--yaz]
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_1920_tyt_matematik_"
HAM = CIKTI / f"{ONEK}ham_okumalar.json"
TARAMA = CIKTI / f"{ONEK}capa_taramasi.json"
HEDEF = CIKTI / f"{ONEK}cevap_anahtari.json"
BIRIM_ONEK = "ACL20T"
HARFLER = set("ABCDE")


def birim_kodu(test: int) -> str:
    return f"{BIRIM_ONEK}-T{test:03d}"


def dogrula(ham: dict[str, Any]) -> list[str]:
    hata = []
    a = {t["test"]: t["hucreler"] for t in ham["okuma_a"]["testler"]}
    b = {t["test"]: t["hucreler"] for t in ham["okuma_b"]["testler"]}
    if set(a) != set(b):
        hata.append("A ve B test kumeleri farkli")
    for t in sorted(a):
        if a[t] != b.get(t):
            hata.append(f"test {t}: A != B")
        if [n for n, _ in a[t]] != list(range(1, len(a[t]) + 1)):
            hata.append(f"test {t}: numaralar 1..N degil")
        if any(h not in HARFLER for _, h in a[t]):
            hata.append(f"test {t}: A-E disi harf")
    glif_disi = set(ham["glif"]["kapsam_disi_test"])
    if ham["glif"]["uyumsuz"]:
        hata.append(f"glif uyumsuz {len(ham['glif']['uyumsuz'])}")
    kapsam = sum(len(a[t]) for t in a if t not in glif_disi)
    if kapsam != ham["glif"]["hucre"] or ham["glif"]["uyum"] != ham["glif"]["hucre"]:
        hata.append(f"glif kapsami {ham['glif']['hucre']} != {kapsam}")
    goz = {int(k): v for k, v in ham["goz_c"]["testler"].items()}
    if set(goz) != glif_disi:
        hata.append(f"goz_c testleri {sorted(goz)} != glif disi {sorted(glif_disi)}")
    for t, s in goz.items():
        if s != "".join(h for _, h in a[t]):
            hata.append(f"test {t}: goz_c != okuma")
    return hata


def cevaplar_uret(ham: dict[str, Any], tarama: dict[str, Any]) -> list[dict[str, Any]]:
    a = {t["test"]: t["hucreler"] for t in ham["okuma_a"]["testler"]}
    out = []
    for t in tarama["testler"]:
        capa = t["capalar"]
        if len(capa) != len(a[t["test"]]):
            raise ValueError(
                f"test {t['test']}: capa {len(capa)} != serit {len(a[t['test']])}"
            )
        sira: Counter[tuple[int, str]] = Counter()
        for (no, harf), c in zip(a[t["test"]], capa, strict=True):
            k = (c["dosya"], c["sutun"])
            out.append(
                {
                    "birim": birim_kodu(t["test"]),
                    "soru": no,
                    "cevap": harf,
                    "dosya": c["dosya"],
                    "sutun": c["sutun"],
                    "sutun_sira": sira[k],
                }
            )
            sira[k] += 1
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    ham = json.loads(HAM.read_text("ascii"))
    tarama = json.loads(TARAMA.read_text("ascii"))
    hata = dogrula(ham)
    print(f"kapi ihlali: {len(hata)}")
    for h in hata[:20]:
        print("   ", h)
    if hata:
        raise SystemExit(1)
    cev = cevaplar_uret(ham, tarama)
    dag = Counter(c["cevap"] for c in cev)
    print(
        f"{len(cev)} cevap, {len(tarama['testler'])} test, dagilim {dict(sorted(dag.items()))}"
    )
    if args.yaz:
        veri = {
            "kaynak": "2019-2020 ACIL TYT Matematik Soru Bankasi",
            "arac": "scripts/kitap/acil1920tyt_anahtar.py",
            "nereden": "test sonu cevap seridi",
            "dogrulama": {
                "a_esittir_b_hucre": sum(
                    len(t["hucreler"]) for t in ham["okuma_a"]["testler"]
                ),
                "glif_loo_uyum": ham["glif"]["uyum"],
                "goz_c_hucre": sum(len(v) for v in ham["goz_c"]["testler"].values()),
                "hucre_sayisi_esittir_capa": True,
            },
            "toplam_cevap": len(cev),
            "test_sayisi": len(tarama["testler"]),
            "harf_dagilimi": dict(sorted(dag.items())),
            "cevaplar": cev,
        }
        HEDEF.write_text(json.dumps(veri, indent=0) + "\n", "ascii")
        print("yazildi", HEDEF)


if __name__ == "__main__":
    main()
