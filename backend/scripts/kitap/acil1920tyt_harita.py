#!/usr/bin/env python
"""2019-2020 ACIL TYT Matematik: test -> konu haritasi.

IKI KANAL
---------
A. Icindekiler (dosya 3): 17 bolum, 32 konu ve her konunun basili
   baslangic sayfasi (asagidaki ICINDEKILER sabiti; basili sayfa = dosya).
B. Her testin ilk sayfasinin ust bandindaki kirmizi konu adi (ham
   okumalar: okuma A ve B, iki bagimsiz okuyucu).

KAPILAR
-------
* her testin TUM sayfalari tek bir icindekiler araliginda;
* bant adi (A == B) o araligin konusuyla ayni (normalize) ya da BANT_ESLER
  listesindeki basili esdegeri (acik liste; uydurma esleme yok);
* her konu en az bir test tasir (32 / 32) -- degilse agac bos dugum acar.

Konu adlari ICINDEKILER'den; tek istisna kitabin icindekiler dizgi hatasi
'EBOK-EKOK' -- test bantlarinin 2'si de 'EBOB - EKOK' basiyor, dugum adi
bant yazimi 'EBOB-EKOK' (EBOK_DUZELTME, belgelendi).

KULLANIM
--------
    python backend/scripts/kitap/acil1920tyt_harita.py [--yaz]
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_1920_tyt_matematik_"
HAM = CIKTI / f"{ONEK}ham_okumalar.json"
TARAMA = CIKTI / f"{ONEK}capa_taramasi.json"
ANAHTAR = CIKTI / f"{ONEK}cevap_anahtari.json"
HEDEF = CIKTI / f"{ONEK}konu_haritasi.json"
KOD = "MAT-ACL20T"
SON_SAYFA = 431

# (bolum no, bolum adi) -- icindekiler, basildigi gibi (Turkce harf \u kacisli)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "YEN\u0130 NES\u0130L \u0130\u015eLEM YETENE\u011e\u0130"),
    (2, "SAYILAR"),
    (3, "RASYONEL VE ONDALIKLI SAYILAR"),
    (4, "BAS\u0130T E\u015e\u0130TS\u0130ZL\u0130K-MUTLAK DE\u011eER"),
    (5, "\u00dcSL\u00dc-K\u00d6KL\u00dc SAYILAR"),
    (6, "SAYISAL MANTIK"),
    (7, "\u00c7ARPANLARA AYIRMA"),
    (8, "ORAN-ORANTI"),
    (9, "B\u0130R\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    (10, "PROBLEMLER"),
    (11, "SEMBOL\u0130K MANTIK"),
    (12, "K\u00dcMELER-KARTEZYEN \u00c7ARPIM"),
    (13, "FONKS\u0130YONLAR"),
    (14, "POL\u0130NOMLAR"),
    (15, "\u0130K\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    (16, "SAYMA-OLASILIK"),
    (17, "\u0130STAT\u0130ST\u0130K-GRAF\u0130K"),
)
# (bolum no, konu adi, baslangic sayfasi)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Yeni Nesil \u0130\u015flem Yetene\u011fi", 5),
    (2, "Temel Kavramlar", 18),
    (2, "Basamak Kavram\u0131", 36),
    (2, "B\u00f6lme", 44),
    (2, "B\u00f6l\u00fcnebilme", 49),
    (2, "Fakt\u00f6riyel", 59),
    (2, "Asal Say\u0131lar-Asal \u00c7arpanlara Ay\u0131rma", 63),
    (2, "Sihirli Say\u0131lar", 72),
    (2, "EBOK-EKOK", 74),
    (2, "Periyodik Problemler", 85),
    (3, "Rasyonel ve Ondal\u0131kl\u0131 Say\u0131lar", 91),
    (4, "Basit E\u015fitsizlik", 110),
    (4, "Mutlak De\u011fer", 128),
    (5, "\u00dcsl\u00fc Say\u0131lar", 144),
    (5, "K\u00f6kl\u00fc Say\u0131lar", 162),
    (5, "Reel Say\u0131lar", 180),
    (6, "Say\u0131sal Mant\u0131k", 184),
    (7, "\u00c7arpanlara Ay\u0131rma", 190),
    (8, "Oran-Orant\u0131", 209),
    (8, "Bilin\u00e7li T\u00fcketim Aritmeti\u011fi", 228),
    (9, "Birinci Dereceden Denklemler", 230),
    (10, "Problemler", 245),
    (11, "Sembolik Mant\u0131k", 293),
    (12, "K\u00fcmeler-Kartezyen \u00c7arp\u0131m", 307),
    (13, "Fonksiyonlar", 332),
    (14, "Polinomlar", 362),
    (15, "\u0130kinci Dereceden Denklemler", 375),
    (16, "Perm\u00fctasyon", 379),
    (16, "Kombinasyon", 392),
    (16, "Olas\u0131l\u0131k", 405),
    (17, "\u0130statistik", 417),
    (17, "Grafik", 425),
)
EBOK_DUZELTME = {"EBOK-EKOK": "EBOB-EKOK"}
# Bant adi icindekiler adindan farkliysa KABUL edilen basili esdegerler
# (normalize edilmis bant -> normalize edilmis konu).
BANT_ESLER: dict[str, str] = {
    "KARMA": "TEMEL KAVRAMLAR",
    "EBOB-EKOK": "EBOK-EKOK",
    "KUMELER": "KUMELER-KARTEZYEN CARPIM",
    "KARTEZYEN CARPIM": "KUMELER-KARTEZYEN CARPIM",
    "GRAFIKLER": "GRAFIK",
}


def norm(s: str) -> str:
    s = s.replace("\u0131", "i").replace("\u0130", "I")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return " ".join(s.replace(" - ", "-").replace(" -", "-").replace("- ", "-").split())


def konular() -> list[dict[str, Any]]:
    out = []
    say: dict[int, int] = {}
    for i, (b, ad, bas) in enumerate(ICINDEKILER):
        son = ICINDEKILER[i + 1][2] - 1 if i + 1 < len(ICINDEKILER) else SON_SAYFA
        say[b] = say.get(b, 0) + 1
        out.append(
            {
                "kod": f"{KOD}-B{b:02d}-K{say[b]:02d}",
                "bolum": f"{KOD}-B{b:02d}",
                "ad": EBOK_DUZELTME.get(ad, ad),
                "icindekiler_adi": ad,
                "sayfalar": [bas, son],
            }
        )
    return out


def harita_uret(
    ham: dict[str, Any], tarama: dict[str, Any], anahtar: dict[str, Any]
) -> dict:
    ks = konular()
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
            if all(k["sayfalar"][0] <= p <= k["sayfalar"][1] for p in t["sayfalar"])
        ]
        if len(aday) != 1:
            hata.append(f"test {n}: sayfalar {t['sayfalar']} tek konu araliginda degil")
            continue
        k = aday[0]
        if a[n] != b[n]:
            hata.append(f"test {n}: bant A != B")
        bant = norm(a[n])
        hedef = norm(k["icindekiler_adi"])
        if bant != hedef and BANT_ESLER.get(bant) != hedef:
            hata.append(f"test {n}: bant {bant!r} != konu {hedef!r}")
        birim = f"ACL20T-T{n:03d}"
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
        "kaynak": "2019-2020 ACIL TYT Matematik Soru Bankasi",
        "arac": "scripts/kitap/acil1920tyt_harita.py",
        "nereden": "icindekiler (dosya 3) + test ilk sayfasi ust bandi (iki okuma)",
        "bolumler": [
            {"kod": f"{KOD}-B{no:02d}", "no": no, "ad": ad} for no, ad in BOLUMLER
        ],
        "konular": ks,
        "test_sayisi": len(testler),
        "testler": testler,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yaz", action="store_true")
    args = ap.parse_args()
    ham = json.loads(HAM.read_text("ascii"))
    tarama = json.loads(TARAMA.read_text("ascii"))
    anahtar = json.loads(ANAHTAR.read_text("ascii"))
    h = harita_uret(ham, tarama, anahtar)
    print(
        f"{len(h['bolumler'])} bolum, {len(h['konular'])} konu, {h['test_sayisi']} test -- kapilar TEMIZ"
    )
    if args.yaz:
        HEDEF.write_text(json.dumps(h, ensure_ascii=True, indent=0) + "\n", "ascii")
        print("yazildi", HEDEF)


if __name__ == "__main__":
    main()
