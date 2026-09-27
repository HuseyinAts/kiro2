#!/usr/bin/env python
"""345 2025 TYT Turkce: test -> konu / unite haritasi (Faz 2).

KAYNAK
------
1. Icindekiler (dosya 3-4, gozle): 7 unite + 'Karma Dil Bilgisi' (s420) ve
   konularin basili baslangic sayfalari (UNITELER, KONU_SAYFASI).
2. Her soru sayfasinin ust bandi (iki bagimsiz okuma, ham dosyada): rozet
   (KO 'k. TEST Kazanim Odakli', OT 'OSYM Tadinda k', OR 'Orijinal k',
   KA 'Karma k') ve KONU adi (bazi sayfalarda yok).
3. Cevap anahtari tablosunun konu basliklari ve test satirlari.

KAPILAR
-------
* A ve B bant okumalari (normalize) birebir ayni.
* Her testin sayfalarinda bant (tur, no) == anahtar satiri (tur, no).
* KO / OT / OR testlerinde bant konusu (varsa) == anahtar konusu.
* Her konunun ilk test sayfasi == icindekiler sayfasi; her test tek unitenin
  sayfa araliginda; unite kapak sayfalari (simgesiz) araliklarin arasinda.

DUZEY
-----
KO / OT / OR testi KONU dugumune (TUR-345T25-Unn-Kmm), KA ('Karma Sorular k')
testi UNITE dugumune (TUR-345T25-Unn) baglanir: karma testler unitenin
birden cok konusunu kapsar (bant konusu 'SOZCUK VE CUMLE ANLAMI',
'PARAGRAF', 'FIILLER' ... kayitta `karma_konu`). 'Karma Dil Bilgisi'
(s420-431) U08.

CIKTI
-----
veriseti/zkitap/cikti/345_2025_tyt_turkce_konu_haritasi.json
"""

from __future__ import annotations

import itertools
import json
import re
import unicodedata
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
ON = "345_2025_tyt_turkce_"
HAM = CIKTI / f"{ON}ham_okumalar.json"
ANAHTAR = CIKTI / f"{ON}cevap_anahtari.json"
TARAMA = CIKTI / f"{ON}capa_taramasi.json"
HEDEF = CIKTI / f"{ON}konu_haritasi.json"
KOD_ONEKI = "TUR-345T25"
BEKLENEN_TEST = 207
# (unite no, ad, ilk sayfa, son sayfa) -- icindekiler + unite kapaklari
UNITELER: tuple[tuple[int, str, int, int], ...] = (
    (1, "ANLAM B\u0130LG\u0130S\u0130", 6, 148),
    (2, "SES - YAZIM - NOKTALAMA", 150, 196),
    (3, "S\u00d6ZC\u00dcK YAPISI", 198, 214),
    (4, "\u0130S\u0130M SOYLU S\u00d6ZC\u00dcKLER", 216, 286),
    (5, "F\u0130\u0130LLER (EYLEMLER)", 288, 340),
    (6, "C\u00dcMLE B\u0130LG\u0130S\u0130", 342, 386),
    (7, "ANLATIM BOZUKLU\u011eU", 388, 419),
    (8, "KARMA D\u0130L B\u0130LG\u0130S\u0130", 420, 431),
)
# icindekilerdeki basili baslangic sayfalari (anahtar konu adiyla)
KONU_SAYFASI: dict[str, int] = {
    "S\u00d6ZC\u00dcKTE ANLAM": 6,
    "DEY\u0130M VE ATAS\u00d6Z\u00dc": 28,
    "C\u00dcMLEDE KAVRAMLAR": 32,
    "C\u00dcMLE YORUMU": 42,
    "ANLATIM TEKN\u0130KLER\u0130": 68,
    "PARAGRAF YORUMU": 84,
    "PARAGRAFTA YARDIMCI D\u00dc\u015e\u00dcNCE": 100,
    "PARAGRAF YAPISI": 116,
    "SES B\u0130LG\u0130S\u0130": 150,
    "YAZIM KURALLARI": 162,
    "NOKTALAMA \u0130\u015eARETLER\u0130": 174,
    "S\u00d6ZC\u00dcK YAPISI": 198,
    "\u0130S\u0130M (AD)": 216,
    "SIFAT (\u00d6N AD)": 228,
    "ZAM\u0130R (ADIL)": 240,
    "ZARF (BEL\u0130RTE\u00c7)": 252,
    "EDAT (\u0130LGE\u00c7) - BA\u011eLA\u00c7 - \u00dcNLEM": 264,
    "F\u0130\u0130L - F\u0130\u0130L \u00c7EK\u0130M\u0130": 288,
    "F\u0130\u0130L - EK F\u0130\u0130L": 296,
    "F\u0130\u0130L - F\u0130\u0130LDE YAPI": 304,
    "F\u0130\u0130L - F\u0130\u0130L\u0130MS\u0130LER": 312,
    "F\u0130\u0130L - F\u0130\u0130LDE \u00c7ATI": 320,
    "S\u00d6Z \u00d6BEKLER\u0130": 342,
    "C\u00dcMLEN\u0130N \u00d6GELER\u0130": 350,
    "C\u00dcMLE \u00c7E\u015e\u0130TLER\u0130": 362,
    "ANLAMA DAYALI ANLATIM BOZUKLUKLARI": 388,
    "D\u0130L B\u0130LG\u0130S\u0130NE DAYALI ANLATIM BOZUKLUKLARI": 398,
}


def norm(x: str | None) -> str | None:
    if x is None:
        return None
    x = unicodedata.normalize("NFC", x)
    return re.sub(r"\s+", " ", re.sub(r"\s*-\s*", " - ", x)).strip()


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
        if norm(x["konu"]) != norm(y["konu"]):
            raise SystemExit(f"s{s} konu: A/B farkli")
        for k in ("tur", "no"):
            if x[k] != y[k]:
                raise SystemExit(f"s{s} {k}: A/B farkli")
    return {s: {**x, "konu": norm(x["konu"])} for s, x in a.items()}


def unite_bul(sayfa: int) -> int:
    for no, _ad, ilk, son in UNITELER:
        if ilk <= sayfa <= son:
            return no
    raise SystemExit(f"s{sayfa}: hicbir unite araliginda degil")


def harita_uret(  # noqa: PLR0912
    bant: dict[int, dict], cevaplar: list[dict], okuma_a: list[dict]
) -> tuple[list[dict], list[dict], list[dict]]:
    testler: dict[str, dict] = {}
    for c in cevaplar:
        t = testler.setdefault(
            c["birim"],
            {
                "birim": c["birim"],
                "tur": c["tur"],
                "no": c["no"],
                "sayfalar": set(),
                "soru_sayisi": 0,
            },
        )
        t["sayfalar"].add(c["dosya"])
        t["soru_sayisi"] += 1
    if len(testler) != len(okuma_a):
        raise SystemExit("anahtar test sayisi okuma ile ayni degil")
    konu_ilk: dict[str, int] = {}
    konu_unite: dict[str, int] = {}
    out = []
    for sira, kod in enumerate(sorted(testler), 1):
        t = testler[kod]
        satir = okuma_a[sira - 1]
        if (satir["tur"], satir["no"]) != (t["tur"], t["no"]):
            raise SystemExit(f"{kod}: anahtar sirasi bozuk")
        anahtar_konu = norm(satir["konu"])
        sayfalar = sorted(t["sayfalar"])
        bant_konu = set()
        for s in sayfalar:
            b = bant[s]
            if (b["tur"], b["no"]) != (t["tur"], t["no"]):
                raise SystemExit(
                    f"{kod} s{s}: bant ({b['tur']}, {b['no']}) != anahtar ({t['tur']}, {t['no']})"
                )
            if b["konu"]:
                bant_konu.add(b["konu"])
        if len(bant_konu) > 1:
            raise SystemExit(f"{kod}: bant konusu tek degil {bant_konu}")
        unite = {unite_bul(s) for s in sayfalar}
        if len(unite) != 1:
            raise SystemExit(f"{kod}: sayfalar iki uniteye tasiyor")
        u = unite.pop()
        kayit = {
            "birim": kod,
            "tur": t["tur"],
            "no": t["no"],
            "anahtar_konu": anahtar_konu,
            "sayfalar": sayfalar,
            "soru_sayisi": t["soru_sayisi"],
        }
        if t["tur"] == "KA":
            kayit["karma_konu"] = next(iter(bant_konu)) if bant_konu else None
            kayit["dugum"] = f"{KOD_ONEKI}-U{u:02d}"
            kayit["duzey"] = "unite"
        else:
            if bant_konu and bant_konu != {anahtar_konu}:
                raise SystemExit(
                    f"{kod}: bant konusu {bant_konu} != anahtar {anahtar_konu!r}"
                )
            if anahtar_konu not in KONU_SAYFASI:
                raise SystemExit(f"{kod}: konu {anahtar_konu!r} icindekilerde yok")
            konu_ilk.setdefault(anahtar_konu, sayfalar[0])
            if konu_unite.setdefault(anahtar_konu, u) != u:
                raise SystemExit(f"{kod}: konu iki uniteye dagiliyor")
            kayit["duzey"] = "konu"
        kayit["unite"] = f"{KOD_ONEKI}-U{u:02d}"
        out.append(kayit)
    if konu_ilk != KONU_SAYFASI:
        fark = {
            k: (konu_ilk.get(k), v)
            for k, v in KONU_SAYFASI.items()
            if konu_ilk.get(k) != v
        }
        raise SystemExit(f"konu ilk sayfasi icindekilerle ayni degil: {fark}")
    konular = []
    sayac: dict[int, int] = {}
    kod_konu: dict[str, str] = {}
    for ad in sorted(konu_ilk, key=lambda k: konu_ilk[k]):
        u = konu_unite[ad]
        sayac[u] = sayac.get(u, 0) + 1
        kod_konu[ad] = f"{KOD_ONEKI}-U{u:02d}-K{sayac[u]:02d}"
        konular.append(
            {
                "kod": kod_konu[ad],
                "unite": f"{KOD_ONEKI}-U{u:02d}",
                "ad": ad,
                "ad_ascii": ascii_buyuk(ad),
                "ilk_sayfa": konu_ilk[ad],
            }
        )
    for k in out:
        if k["duzey"] == "konu":
            k["dugum"] = kod_konu[k["anahtar_konu"]]
    uniteler = [
        {
            "kod": f"{KOD_ONEKI}-U{no:02d}",
            "ad": ad,
            "ad_ascii": ascii_buyuk(ad),
            "sayfalar": [ilk, son],
        }
        for no, ad, ilk, son in UNITELER
    ]
    return out, uniteler, konular


def kapak_dogrula(tarama: dict) -> None:
    """Unite kapaklari (simgesiz sayfa) iki unite araligi arasinda olmali."""
    simgesiz = set(tarama["seritli_simgesiz_sayfa"])
    for (_a, _b, _c, son), (_d, _e, ilk, _f) in itertools.pairwise(UNITELER):
        ara = set(range(son + 1, ilk))
        if ara and not ara <= simgesiz:
            raise SystemExit(f"unite arasi {sorted(ara)} soru sayfasi iceriyor")


def main() -> None:
    ham = json.loads(HAM.read_text("ascii"))
    cev = json.loads(ANAHTAR.read_text("ascii"))["cevaplar"]
    kapak_dogrula(json.loads(TARAMA.read_text("ascii")))
    testler, uniteler, konular = harita_uret(
        bantlar(ham), cev, ham["anahtar_okumalari"]["A"]
    )
    if len(testler) != BEKLENEN_TEST:
        raise SystemExit(f"test {len(testler)} != {BEKLENEN_TEST}")
    veri = {
        "kaynak": "345 2025 TYT Turkce Soru Bankasi",
        "arac": "scripts/kitap/tur345tyt_harita.py",
        "nereden": "icindekiler (unite + konu baslangic sayfasi) + sayfa ust bandi (tur, no, konu) iki okuma",
        "dogrulama": {
            "bant_a_esittir_b": True,
            "bant_esittir_anahtar_tur_no": True,
            "bant_konu_esittir_anahtar_konu": True,
            "konu_ilk_sayfa_esittir_icindekiler": True,
        },
        "unite_sayisi": len(uniteler),
        "uniteler": uniteler,
        "konu_sayisi": len(konular),
        "konular": konular,
        "test_sayisi": len(testler),
        "testler": testler,
    }
    HEDEF.write_text(
        json.dumps(veri, ensure_ascii=True, indent=1) + "\n",
        encoding="ascii",
        newline="\n",
    )
    print(
        f"{len(testler)} test, {len(uniteler)} unite, {len(konular)} konu; KA {sum(1 for t in testler if t['tur'] == 'KA')}"
    )


if __name__ == "__main__":
    main()
