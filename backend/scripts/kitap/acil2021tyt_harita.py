#!/usr/bin/env python
"""2020-2021 ACIL TYT Matematik: test -> konu haritasi.

IKI KANAL
---------
A. Icindekiler (dosya 3): 13 bolum, 30 konu ve her konunun basili
   baslangic sayfasi (asagidaki ICINDEKILER sabiti; basili sayfa = dosya).
B. Her testin ilk sayfasinin ust bandindaki kirmizi konu adi (ham
   okumalar: okuma A ve B, iki bagimsiz okuyucu).

KAPILAR
-------
* her testin TUM sayfalari tek bir icindekiler araliginda;
* bant adi (A == B) o araligin konusuyla ayni (normalize) ya da BANT_ESLER
  listesindeki basili alt baslik (acik liste; uydurma esleme yok). Bu
  kitapta bantlar konudan ince: 'BOLME' / 'BOLUNEBILME', 'EBOB' / 'EKOK',
  problem turleri ('YAS PROBLEMLERI' ...), fonksiyon alt basliklari;
* her konu en az bir test tasir (30 / 30) -- degilse agac bos dugum acar.

Bant adi testin `bant` alaninda saklanir (alt konu bilgisi).

KULLANIM
--------
    python backend/scripts/kitap/acil2021tyt_harita.py [--yaz]
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ONEK = "acil_2021_tyt_matematik_"
HAM = CIKTI / f"{ONEK}ham_okumalar.json"
TARAMA = CIKTI / f"{ONEK}capa_taramasi.json"
ANAHTAR = CIKTI / f"{ONEK}cevap_anahtari.json"
HEDEF = CIKTI / f"{ONEK}konu_haritasi.json"
KOD = "MAT-ACL21T"
SON_SAYFA = 447

# (bolum no, bolum adi) -- icindekiler, basildigi gibi (Turkce harf \u kacisli)
BOLUMLER: tuple[tuple[int, str], ...] = (
    (1, "SAYILAR"),
    (2, "RASYONEL VE ONDALIKLI SAYILAR"),
    (3, "BAS\u0130T E\u015e\u0130TS\u0130ZL\u0130K-MUTLAK DE\u011eER"),
    (4, "\u00dcSL\u00dc-K\u00d6KL\u00dc SAYILAR"),
    (5, "\u00c7ARPANLARA AYIRMA"),
    (6, "ORAN-ORANTI"),
    (7, "B\u0130R\u0130NC\u0130 DERECEDEN DENKLEMLER"),
    (8, "PROBLEMLER"),
    (9, "SEMBOL\u0130K MANTIK"),
    (10, "K\u00dcMELER-KARTEZYEN \u00c7ARPIM"),
    (11, "FONKS\u0130YONLAR"),
    (12, "SAYMA-OLASILIK"),
    (13, "\u0130STAT\u0130ST\u0130K"),
)
# (bolum no, konu adi, baslangic sayfasi)
ICINDEKILER: tuple[tuple[int, str, int], ...] = (
    (1, "Pozitif ve Negatif Tam Say\u0131lar", 6),
    (1, "Tek ve \u00c7ift Say\u0131lar", 12),
    (1, "En K\u00fc\u00e7\u00fck ve En B\u00fcy\u00fck De\u011fer Bulma", 20),
    (1, "Ard\u0131\u015f\u0131k Say\u0131lar ve \u00d6r\u00fcnt\u00fc", 26),
    (1, "\u0130\u015flem Yetene\u011fi", 32),
    (1, "Basamak Kavram\u0131", 38),
    (1, "B\u00f6lme-B\u00f6l\u00fcnebilme", 50),
    (1, "Fakt\u00f6riyel", 66),
    (1, "Asal Say\u0131lar-Asal \u00c7arpanlara Ay\u0131rma", 70),
    (1, "EBOB-EKOK", 80),
    (1, "Periyodik Problemler", 94),
    (2, "Rasyonel ve Ondal\u0131kl\u0131 Say\u0131lar", 101),
    (3, "Basit E\u015fitsizlik", 122),
    (3, "Mutlak De\u011fer", 139),
    (4, "\u00dcsl\u00fc Say\u0131lar", 153),
    (4, "K\u00f6kl\u00fc Say\u0131lar", 172),
    (4, "Reel Say\u0131lar", 189),
    (5, "\u00c7arpanlara Ay\u0131rma", 195),
    (6, "Oran-Orant\u0131", 217),
    (6, "Bilin\u00e7li T\u00fcketim Aritmeti\u011fi", 235),
    (7, "Birinci Dereceden Denklemler", 238),
    (8, "Problemler", 249),
    (9, "Sembolik Mant\u0131k", 321),
    (10, "K\u00fcmeler-Kartezyen \u00c7arp\u0131m", 336),
    (11, "Fonksiyonlar", 360),
    (12, "Perm\u00fctasyon", 395),
    (12, "Kombinasyon", 409),
    (12, "Binom A\u00e7\u0131l\u0131m\u0131", 421),
    (12, "Olas\u0131l\u0131k", 424),
    (13, "\u0130statistik", 441),
)
EBOK_DUZELTME: dict[str, str] = {}
# Bant adi icindekiler adindan farkliysa KABUL edilen basili alt basliklar
# (normalize edilmis bant -> normalize edilmis konu).
BANT_ESLER: dict[str, str] = {
    "BOLME": "BOLME-BOLUNEBILME",
    "BOLUNEBILME": "BOLME-BOLUNEBILME",
    "EBOB": "EBOB-EKOK",
    "EKOK": "EBOB-EKOK",
    "EBOB-EKOK PROBLEMLERI": "EBOB-EKOK",
    "SAYI PROBLEMLERI": "PROBLEMLER",
    "KESIR PROBLEMLERI": "PROBLEMLER",
    "SAYI VE KESIR PROBLEMLERI": "PROBLEMLER",
    "YAS PROBLEMLERI": "PROBLEMLER",
    "ISCI PROBLEMLERI": "PROBLEMLER",
    "HIZ PROBLEMLERI": "PROBLEMLER",
    "YUZDE KAR-ZARAR PROBLEMLERI": "PROBLEMLER",
    "KARISIM PROBLEMLERI": "PROBLEMLER",
    "GRAFIK PROBLEMLERI": "PROBLEMLER",
    "SAYISAL MANTIK PROBLEMLERI": "PROBLEMLER",
    "KUMELER": "KUMELER-KARTEZYEN CARPIM",
    "KARTEZYEN CARPIM": "KUMELER-KARTEZYEN CARPIM",
    "FONKSIYON VE OZELLIKLERI": "FONKSIYONLAR",
    "TERS VE BILESKE FONKSIYON": "FONKSIYONLAR",
    "FONKSIYONLARIN GRAFIKLERI": "FONKSIYONLAR",
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
        birim = f"ACL21T-T{n:03d}"
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
        "kaynak": "2020-2021 ACIL TYT Matematik Soru Bankasi",
        "arac": "scripts/kitap/acil2021tyt_harita.py",
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
