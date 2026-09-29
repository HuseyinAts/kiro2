#!/usr/bin/env python
"""Iki bagimsiz okuma + hakem: kitaptan BAGIMSIZ ortak arac.

ACL21T'ye kadar her kitapta dort gecici script (a_talimat2, a_metin_karsilastir,
a_hakem_hazirla, a_duzeltme_yaz) yeniden yazildi. Bu modul ayni isi kitap
parametreleriyle yapar.

OLCUM (ACL21T, 27 Eyl 2026, dosya zaman damgalari)
--------------------------------------------------
Metin fazi 98 dk = is suresinin %62'si (toplam is 158 dk + CI 49 dk).
  okuma 1  : 20:32 -> 21:08 (36 dk; 45 grup, 15'lik 3 dalga, dalga bariyeri)
  okuma 2  : 21:09 -> 21:49 (40 dk; okuma 1 BITTIKTEN sonra baslatildi)
  hakem    : 21:50 -> 22:11 (21 dk; 8 hakem, 249 fark)
Hakemin 249 kararindan 89'u (%36) 'esasli hata yok' = yalniz bicim farki
(bileske halkasi U+2218 / o, ust simge ^2 / U+00B2,
tek atomu saran parantez, ust cizgi, kok cizgisi). Carpi U+00D7 / x
BILEREK esitlenmez: ACL21T T011_06 ve T015_07'de hakem bunu esasli buldu
(harf x ile carpi isareti ayni kirpimda ayirt edildi). Gercek veri dogrulamasi:
ACL21T'de 249 fark -> 208 (41 bicim farki elendi, tek tarafli esasli hata gizlenmedi;
hakemin yalniz halka farkindan yola cikip BULDUGU 2 ortak hata (T132_08,
T134_15) artik tesadufen yakalanmaz -- bu 'iki okumanin ayni atladigi' sinifidir).

PROTOKOL (dar bogaz cozumu)
---------------------------
1. `hazirla` iki okuma dizinini ve iki talimati AYNI ANDA kurar. Okuma 1 ve
   okuma 2 okuyuculari TEK toplu dagitimda, dalga bariyeri olmadan baslar.
   Bagimsizlik zamansal sira DEGIL dizin ayrimidir: okuyucu 2 yalniz
   `<onek>_metin_parca2` altindaki liste/ortme dosyalarini gorur.
2. `karsilastir` bicim farklarini normalize eder; yalniz kalan farklar
   hakeme gider. Normalizasyon YALNIZ karsilastirma anahtarindadir;
   saklanan metin okuma 1 bicimidir. Anlam tasiyan parantez
   ((a+b)/c vs a+b/c) ASLA esitlenmez; yalniz tek atomu saran parantez
   ve ciftlenmis parantez esitlenir.
3. `hakem-hazirla --hakem N` farklari N hakeme boler; hepsi tek dagitimda.
   Grup hatti (is akisi, bariyersiz): bir grubun iki okumasi biter bitmez
   `grup-fark --grup NN` o grubun farklarini `hakem_gNN.json`a yazar ve o
   grubun hakemi hemen baslar; kitabin geri kalani okunmaya devam eder.
   Sonda `karsilastir` tum kitabi yeniden karsilastirir (fark.json) ve
   `duzeltme-yaz --hakem 0` hakem_gNN kararlarini bu kapsamla denetler.
4. `duzeltme-yaz` kararlari `duzeltme.json`a ve
   `<cikti>_ikinci_okuma.json` 'sonuc'una yazar.

KULLANIM
--------
    python backend/scripts/kitap/metin_iki_okuma.py --onek ACL21T \
        --cikti acil_2021_tyt_matematik --veraf a2 --beklenen 2113 \
        --kitap "2020-2021 ACIL TYT Matematik Soru Bankasi" hazirla \
        --ornek acil_1920_tyt_matematik --tarih 2026-09-27
    ... karsilastir
    ... hakem-hazirla --hakem 8
    ... duzeltme-yaz
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

KOK = Path(__file__).resolve().parents[3]
CIKTI = KOK / "veriseti" / "zkitap" / "cikti"
VERAFILM = Path(r"C:\Users\husey\VeraFilm")

ALANLAR = (
    "basili_no",
    "govde",
    "sikler",
    "sekil_var",
    "sikler_gorsel",
    "etiket",
    "kaynak_kusuru",
)
KARAR_ALANLARI = ("basili_no", "govde", "sekil_var", "sikler_gorsel", "etiket")

# --- normalizasyon tablolari (yalniz karsilastirma anahtari) -----------------
_KESME = "\u2019\u2018\u02bc\u00b4`\u2032"
_TIRNAK = "\u201c\u201d"
_EKSI = "\u2212\u2013\u2014"
_BIRLESIK = "\u0305\u0304\u0332"  # ust cizgi / makron / alt cizgi (birlesik)
_UST = {
    "\u2070": "^0",
    "\u00b9": "^1",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u2074": "^4",
    "\u2075": "^5",
    "\u2076": "^6",
    "\u2077": "^7",
    "\u2078": "^8",
    "\u2079": "^9",
}
_GLIF = {
    "\u2218": "o",  # bileske halkasi -> o
    "\u22c5": "\u00b7",  # nokta operatoru -> orta nokta
    "\u2026": "...",
    "\u221a\u203e": "\u221a",  # kok + ust cizgi -> kok
    "\u230b": "\u2518",  # sag alt kose glif varyanti
}
_ATOM = r"-?[A-Za-z0-9\u03b1-\u03c9]+(?:\([^()]*\))?"


def norm(x: Any) -> str:
    """Karsilastirma anahtari: bicim farklarini yok sayar, anlami korur."""
    if x is None:
        return ""
    x = unicodedata.normalize("NFC", str(x))
    for a in _KESME:
        x = x.replace(a, "'")
    for a in _TIRNAK:
        x = x.replace(a, '"')
    for a in _EKSI:
        x = x.replace(a, "-")
    for a in _BIRLESIK:
        x = x.replace(a, "")
    for a, b in _UST.items():
        x = x.replace(a, b)
    for a, b in _GLIF.items():
        x = x.replace(a, b)
    x = re.sub(r"([_^])\((\w)\)", r"\1\2", x)  # x^(2) -> x^2
    x = re.sub(r"([_^])\{(\w)\}", r"\1\2", x)
    x = x.replace("(g\u00f6rsel)", "(\u015fekil)")
    x = re.sub(r"C\((\w+), (\w+)\)", r"(\1 \2)", x)  # C(n, r) -> (n r)
    x = re.sub(
        r"([\u221a\u221b\u221c])\(([A-Za-z0-9\u03c0]{1,3})\)", r"\1\2", x
    )  # kokte tek atom
    # (2xy)/ -> 2xy/ ; f(1)/ gibi fonksiyon uygulamasina DOKUNMAZ (onunde harf/rakam/parantez yok)
    x = re.sub(r"(?<![A-Za-z0-9\u03b1-\u03c9)])\((" + _ATOM + r")\)(?=/)", r"\1", x)
    x = re.sub(r"\(\(([^()]*)\)(!?)\)", r"(\1)\2", x)  # ((n+2)!) -> (n+2)!
    x = re.sub(r"\|\s*(?=\u2192)", "", x)  # tablo hucre ayraci + ok
    return _SEKIL_SATIRI.sub(_sekil_sirala, x)


# 'Sekil: a; b; c' satiri (metin.SEKIL_SATIRI_KURALI): etiket SIRASI okuyucudan
# okuyucuya degisir (soldan saga / yukaridan asagiya), icerigi degil -> anahtar
# sirasiz kume. APO19FZ: 455 farkin 327'si sekil etiketi, 221'i 'esasli yok'.
_SEKIL_SATIRI = re.compile(r"^\u015eekil:[ \t]*(.*)$", re.M)


def _sekil_sirala(m: re.Match[str]) -> str:
    parca = sorted(re.sub(r"\s+", "", t) for t in m.group(1).split(";") if t.strip())
    return "\u015eekil: " + "; ".join(parca)


def sikistir(x: str) -> str:
    """Bosluk/satir sonu farklarini yok sayan bicim."""
    return re.sub(r"\s+", "", x)


def _vurgusuz(x: str) -> str:
    return re.sub(r"</?u>", "", x)


def ayir(a: str, b: str) -> list[dict[str, str]]:
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        out.append(
            {"bir": a[max(0, i1 - 15) : i2 + 15], "iki": b[max(0, j1 - 15) : j2 + 15]}
        )
    return out


def soru_farklari(a: dict[str, Any], b: dict[str, Any]) -> list[dict[str, Any]]:
    """Iki okumanin ayni sorusu icin alan alan fark listesi (bos = ayni)."""
    f: list[dict[str, Any]] = []
    x, y = norm(a.get("govde")), norm(b.get("govde"))
    xs, ys = sikistir(x), sikistir(y)
    if _vurgusuz(xs) != _vurgusuz(ys):
        f.append({"alan": "govde", "parca": ayir(_vurgusuz(x), _vurgusuz(y))})
    elif xs != ys:
        f.append({"alan": "vurgu", "bir": x, "iki": y})
    for h in "ABCDE":
        x = norm((a.get("sikler") or {}).get(h))
        y = norm((b.get("sikler") or {}).get(h))
        if sikistir(x) != sikistir(y):
            f.append({"alan": "sik_" + h, "bir": x, "iki": y})
    for alan in ("basili_no", "sekil_var", "sikler_gorsel", "etiket"):
        if a.get(alan) != b.get(alan):
            f.append({"alan": alan, "bir": a.get(alan), "iki": b.get(alan)})
    return f


# --- dosya duzeni ------------------------------------------------------------
@dataclass(frozen=True)
class Kitap:
    onek: str  # ACL21T
    cikti: str  # acil_2021_tyt_matematik
    veraf: str  # a2
    beklenen: int
    kitap: str

    @property
    def parca1(self) -> Path:
        return VERAFILM / f"{self.veraf}_metin_parca"

    @property
    def parca2(self) -> Path:
        return VERAFILM / f"{self.veraf}_metin_parca2"

    @property
    def hakem(self) -> Path:
        return VERAFILM / f"{self.veraf}_hakem"

    @property
    def kirpim(self) -> Path:
        return VERAFILM / f"{self.veraf}_okuma_kirpim"

    @property
    def talimat1(self) -> Path:
        return VERAFILM / f"{self.veraf}_metin_talimat.md"

    @property
    def talimat2(self) -> Path:
        return VERAFILM / f"{self.veraf}_metin_talimat2.md"

    @property
    def ak(self) -> Path:
        return KOK / "backend" / f"_{self.veraf}_ak"

    @property
    def io(self) -> Path:
        return CIKTI / f"{self.cikti}_ikinci_okuma.json"


def oku(d: Path) -> dict[str, dict[str, Any]]:
    r: dict[str, dict[str, Any]] = {}
    for f in sorted(d.glob("grup_*.json")):
        for s in json.loads(f.read_text("utf-8"))["sorular"]:
            r[s["dosya"]] = s
    return r


def hazirla(k: Kitap, ornek: str, tarih: str) -> None:
    """Ikinci okuma dizini + talimati + on kayit. Okuma 1 hazirla'dan SONRA, okuyuculardan ONCE."""
    s = k.talimat1.read_text("utf-8")
    bas = s.splitlines()[0]
    yeni_bas = (
        "# Transkripsiyon talimat\u0131 (BA\u011eIMSIZ \u0130K\u0130NC\u0130 OKUMA) -- "
        + k.kitap
    )
    s = s.replace(bas, yeni_bas, 1)
    n = s.count(f"{k.veraf}_metin_parca\\")
    if n == 0:
        raise SystemExit(f"talimatta {k.veraf}_metin_parca\\ gecmiyor")
    s = s.replace(f"{k.veraf}_metin_parca\\", f"{k.veraf}_metin_parca2\\")
    s = s.replace(f"{k.veraf}_tmp\\NN", f"{k.veraf}_tmp2\\NN")
    s += (
        "\n## Ba\u011f\u0131ms\u0131zl\u0131k\n"
        f"Bu ikinci okumad\u0131r. `{VERAFILM}\\{k.veraf}_metin_parca\\` dizinindeki (sonunda 2 OLMAYAN)\n"
        f"hi\u00e7bir dosyay\u0131 A\u00c7MA; yaln\u0131z `{k.veraf}_metin_parca2` alt\u0131ndaki liste / ortme "
        "dosyalar\u0131n\u0131 kullan.\n"
    )
    k.talimat2.write_text(s, "utf-8")
    k.parca2.mkdir(exist_ok=True)
    for f in k.parca1.glob("*.txt"):
        (k.parca2 / f.name).write_text(f.read_text("ascii"), "ascii")
    eski = json.loads((CIKTI / f"{ornek}_ikinci_okuma.json").read_text("ascii"))
    grup = len(list(k.parca1.glob("liste_*.txt")))
    yeni = {
        "kitap": k.kitap,
        "on_kayit_tarihi": tarih,
        "kural": (
            "Onceki kitaplarin olcusu: esasli ilk okuma hatasi CP95 ust siniri <= %3 saglanmadi "
            "(KMT345 %4.7, SOS345 %5.9, TRT345 %4.0, ACL20T %4.9, ACL21T %3.7). Dogrudan TAM ikinci okuma."
        ),
        "tasarim": (
            f"Ilk okumayi gormeyen {grup} ayri okuyucu; ayni talimat (yalniz teslim dizini "
            f"{k.veraf}_metin_parca2), ayni gruplar ve kirpimlar. Okuma 1 ve okuma 2 okuyuculari "
            "TEK toplu dagitimda birlikte kosulur (bagimsizlik dizin ayrimiyla saglanir). "
            "Karsilastirma bu dosya yazildiktan SONRA yapilir."
        ),
        "karsilastirma": eski["karsilastirma"],
        "esasli_hata_tanimi": eski["esasli_hata_tanimi"],
    }
    k.io.write_text(json.dumps(yeni, ensure_ascii=True, indent=1) + "\n", "ascii")
    print(
        "talimat2 yazildi; parca2 liste",
        len(list(k.parca2.glob("*.txt"))),
        "; on kayit",
        k.io.name,
    )


def karsilastir(k: Kitap) -> dict[str, list[dict[str, Any]]]:
    A, B = oku(k.parca1), oku(k.parca2)
    if set(A) != set(B) or len(A) != k.beklenen:
        raise SystemExit(f"okuma kapsami: {len(A)} / {len(B)} / beklenen {k.beklenen}")
    fark = {ad: f for ad in sorted(A) if (f := soru_farklari(A[ad], B[ad]))}
    k.ak.mkdir(exist_ok=True)
    (k.ak / "fark.json").write_text(
        json.dumps(fark, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    say: dict[str, int] = {}
    for v in fark.values():
        for x in v:
            say[x["alan"]] = say.get(x["alan"], 0) + 1
    print("farkli soru", len(fark), "ayni", k.beklenen - len(fark), sorted(say.items()))
    return fark


def hakem_hazirla(k: Kitap, n: int) -> None:
    A, B = oku(k.parca1), oku(k.parca2)
    fark = json.loads((k.ak / "fark.json").read_text("utf-8"))
    adlar = sorted(fark)
    k.hakem.mkdir(exist_ok=True)
    for i in range(n):
        parca = adlar[i::n]
        out = [
            {
                "dosya": a,
                "farklar": fark[a],
                "okuma_1": {x: A[a].get(x) for x in ALANLAR},
                "okuma_2": {x: B[a].get(x) for x in ALANLAR},
            }
            for a in parca
        ]
        (k.hakem / f"hakem_{i + 1}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print("hakem", i + 1, len(parca))
    print("kirpim", len(list(k.kirpim.glob("*.png"))))


def grup_fark(k: Kitap, nn: str) -> int:
    """Tek grubun iki okumasini karsilastirir, hakem girdisini hakem_gNN.json'a yazar.

    Is akisi hatti (okuma bitti -> hemen hakem) icin: grup okumalari biter bitmez
    o grubun hakemi baslar, tum kitabin okunmasi beklenmez. Sonda `karsilastir`
    tum kitapta ayni farklari yeniden uretir; duzeltme-yaz kapsami ona gore
    denetler."""
    ad = f"grup_{nn}.json"
    A = {
        s["dosya"]: s for s in json.loads((k.parca1 / ad).read_text("utf-8"))["sorular"]
    }
    B = {
        s["dosya"]: s for s in json.loads((k.parca2 / ad).read_text("utf-8"))["sorular"]
    }
    liste = (k.parca1 / f"liste_{nn}.txt").read_text("ascii").split()
    beklenen = {Path(x).stem for x in liste}
    if set(A) != set(B) or set(A) != beklenen:
        raise SystemExit(
            f"grup {nn} kapsami: {len(A)} / {len(B)} / liste {len(beklenen)}"
        )
    out = [
        {
            "dosya": a,
            "farklar": f,
            "okuma_1": {x: A[a].get(x) for x in ALANLAR},
            "okuma_2": {x: B[a].get(x) for x in ALANLAR},
        }
        for a in sorted(A)
        if (f := soru_farklari(A[a], B[a]))
    ]
    k.hakem.mkdir(exist_ok=True)
    (k.hakem / f"hakem_g{nn}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print("grup", nn, "soru", len(A), "farkli", len(out))
    return len(out)


def _uygula(s: dict[str, Any], ad: str, ek: dict[str, Any]) -> None:
    for eski, yeni in ek.get("govde_degistir", {}).get(ad, []):
        if eski not in s["govde"]:
            raise SystemExit(f"{ad}: govde parcasi yok: {eski!r}")
        s["govde"] = s["govde"].replace(eski, yeni)
    for h, eski, yeni in ek.get("sik_degistir", {}).get(ad, []):
        if eski not in s["sikler"][h]:
            raise SystemExit(f"{ad}: sik {h} parcasi yok: {eski!r}")
        s["sikler"][h] = s["sikler"][h].replace(eski, yeni)
    if ad in ek.get("kusur", {}):
        s["kaynak_kusuru"] = ek["kusur"][ad]


def _karar_dogrula(x: dict[str, Any], farklar: list[dict[str, Any]]) -> None:
    """Hakem karari, karsilastirmanin buldugu HER alani kapsamali."""
    nihai = x["nihai"]
    for a in {f["alan"] for f in farklar}:
        if a.startswith("sik_") and a[-1] not in (nihai.get("sikler") or {}):
            raise SystemExit(f"{x['dosya']}: {a} karari yok")
        if a in ("govde", "vurgu") and "govde" not in nihai:
            raise SystemExit(f"{x['dosya']}: govde karari yok")
        if (
            a in ("basili_no", "sekil_var", "sikler_gorsel", "etiket")
            and a not in nihai
        ):
            raise SystemExit(f"{x['dosya']}: {a} karari yok")
    if x["esasli_hata"] not in ("okuma_1", "okuma_2", "ikisi", "yok"):
        raise SystemExit(f"{x['dosya']}: esasli_hata {x['esasli_hata']!r}")


def duzeltme_yaz(k: Kitap, n: int) -> None:
    A = oku(k.parca1)
    karar: list[dict[str, Any]] = []
    # n > 0: hakem-hazirla bolumu (hakem_1..n); n == 0: grup hatti (hakem_gNN).
    yollar = (
        [k.hakem / f"hakem_{i}_karar.json" for i in range(1, n + 1)]
        if n
        else sorted(k.hakem.glob("hakem_g*_karar.json"))
    )
    for y in yollar:
        karar += json.loads(y.read_text("utf-8"))
    fark = json.loads((k.ak / "fark.json").read_text("utf-8"))
    if sorted(x["dosya"] for x in karar) != sorted(fark):
        raise SystemExit("hakem kapsami != fark")
    ek_yol = k.ak / "ek_duzeltme.json"
    ek = json.loads(ek_yol.read_text("utf-8")) if ek_yol.exists() else {}
    duz: list[dict[str, Any]] = []
    hukum: list[dict[str, str]] = []
    for x in sorted(karar, key=lambda x: x["dosya"]):
        s = json.loads(json.dumps(A[x["dosya"]]))
        nihai = x["nihai"]
        for alan in KARAR_ALANLARI:
            if alan in nihai:
                s[alan] = nihai[alan]
        for h, v in (nihai.get("sikler") or {}).items():
            s["sikler"][h] = v
        _karar_dogrula(x, fark[x["dosya"]])
        _uygula(s, x["dosya"], ek)
        s["hukum"] = x["gerekce"]
        duz.append(s)
        hukum.append(
            {
                "dosya": x["dosya"],
                "esasli_hata": x["esasli_hata"],
                "gerekce": x["gerekce"],
            }
        )
    ek_adlar = (
        set(ek.get("kusur", {}))
        | set(ek.get("govde_degistir", {}))
        | set(ek.get("sik_degistir", {}))
    )
    for ad in sorted(ek_adlar - set(fark)):
        s = json.loads(json.dumps(A[ad]))
        _uygula(s, ad, ek)
        s["hukum"] = "yalniz goz (yakinlastirma) duzeltmesi"
        duz.append(s)
    (k.parca1 / "duzeltme.json").write_text(
        json.dumps({"sorular": duz}, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    say: dict[str, int] = {}
    for h in hukum:
        say[h["esasli_hata"]] = say.get(h["esasli_hata"], 0) + 1
    bir = say.get("okuma_1", 0) + say.get("ikisi", 0)
    iki = say.get("okuma_2", 0) + say.get("ikisi", 0)
    io = json.loads(k.io.read_text("ascii"))
    io["sonuc"] = {
        "soru": k.beklenen,
        "ayni_soru_normalize": k.beklenen - len(fark),
        "farkli_soru": len(fark),
        "hukum_dagilimi": say,
        "ilk_okuma_esasli_hata": bir,
        "ikinci_okuma_esasli_hata": iki,
        "not": (
            "Normalizasyon (metin_iki_okuma.norm): NFC, kesme/tirnak tipi, eksi/tire tipi, birlesik ust/alt "
            "cizgi, Unicode ust simge -> ^n, bileske halkasi U+2218 -> o, nokta operatoru, "
            "uc nokta, kok+ust cizgi -> kok, tek karakterli us/indis parantezi, kokte tek atom parantezi, "
            "'/' oncesi tek atom parantezi, ciftlenmis parantez, tablo ayraci+ok, (gorsel)/(sekil), "
            "C(n, r) = (n r) ve TUM bosluk. Anlam tasiyan parantez esitlenmez. Her kalan fark hakem "
            "tarafindan kirpimdan gozle karara baglandi; karar ilk okumanin yerine duzeltme.json ile gecer. "
            "Iki okumanin AYNI bicimde atladigi sekil verisi karsilastirmada gorunmez."
        ),
    }
    io["hukumler"] = hukum
    io["duzeltmeler"] = [
        {
            x: s[x]
            for x in (
                "dosya",
                "basili_no",
                "govde",
                "sikler",
                "sekil_var",
                "sikler_gorsel",
                "etiket",
            )
        }
        for s in duz
    ]
    soluk = k.ak / "soluk_ozet.json"
    if soluk.exists():
        io["soluk_isaret_taramasi"] = json.loads(soluk.read_text("utf-8"))
    k.io.write_text(
        json.dumps(io, ensure_ascii=True, indent=1) + "\n", encoding="ascii"
    )
    print(len(duz), say, "ilk", bir, "ikinci", iki)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--onek", required=True)
    p.add_argument("--cikti", required=True)
    p.add_argument("--veraf", required=True)
    p.add_argument("--beklenen", type=int, required=True)
    p.add_argument("--kitap", required=True)
    alt = p.add_subparsers(dest="komut", required=True)
    h = alt.add_parser("hazirla")
    h.add_argument(
        "--ornek",
        required=True,
        help="karsilastirma/esasli_hata metni alinacak onceki kitap cikti oneki",
    )
    h.add_argument("--tarih", required=True)
    alt.add_parser("karsilastir")
    hh = alt.add_parser("hakem-hazirla")
    hh.add_argument("--hakem", type=int, default=8)
    g = alt.add_parser("grup-fark")
    g.add_argument("--grup", required=True, help="iki haneli grup no (01, 02 ...)")
    d = alt.add_parser("duzeltme-yaz")
    d.add_argument(
        "--hakem", type=int, default=8, help="0: grup hatti (hakem_gNN_karar.json)"
    )
    a = p.parse_args()
    k = Kitap(a.onek, a.cikti, a.veraf, a.beklenen, a.kitap)
    if a.komut == "hazirla":
        hazirla(k, a.ornek, a.tarih)
    elif a.komut == "karsilastir":
        karsilastir(k)
    elif a.komut == "hakem-hazirla":
        hakem_hazirla(k, a.hakem)
    elif a.komut == "grup-fark":
        grup_fark(k, a.grup)
    else:
        duzeltme_yaz(k, a.hakem)


if __name__ == "__main__":
    main()
