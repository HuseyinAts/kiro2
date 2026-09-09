#!/usr/bin/env python
"""OSYM temel soru kitapcigi (PDF) -> yapisal JSON (soru, sik, anahtar, bayraklar).

NEDEN (9 Eyl 2026, docs/veritabani-denetimi-20260909.md madde 10 / karar 2)
---------------------------------------------------------------------------
Havuzdaki 5.796 sorunun tamami ticari kitaplardan; OSYM'nin kendi sorusu 1.
Eski deneme (`scripts/osym_question_extractor.py`, 17 Agu) iki sutunlu sayfayi
tek akista okuyup satirlari ic ice gecirmisti: 73 soru, 0 anahtar. Bu hat
sayfayi sutun sutun kirpar, soru numarasini yalnizca BEKLENEN sirayla kabul
eder, anahtari son sayfadaki tablodan x-konumuyla eslestirir ve gorsel /
alt cizgi / roma-rakami isaretlerini bayraklar.

Olcum kurali: cikti, blueprint ile (TYT 40/20/40/20 = 120) ve anahtar
sayisiyla karsilastirilir; sapma varsa ithal DURUR (yanlis-sifir yok).

KULLANIM
--------
    python backend/scripts/osym/kitapcik_cikar.py data/osym/tyt_2025.pdf --cikti data/osym/tyt_2025.json

Ithal: scripts/osym/kitapcik_ithal.py (is_active=false ile).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pdfplumber

# --- Kitapcik sozlesmesi (2025 TYT; AYT icin ayni bicim, farkli test kodlari) ---
TEST_KODU_DERS = {
    "TÜR": "TURKCE",
    "SOS": "SOSYAL",
    "MAT": "MATEMATIK",
    "TEM": "MATEMATIK",  # 2025 TYT baslik kodu: 2025-TYT/TEM
    "FEN": "FEN",
    "EDB": "EDEBIYAT",  # AYT Turk Dili ve Edebiyati - Sosyal Bilimler-1
    "SOS2": "SOSYAL",
    "FİZ": "FIZIK",
    "KİM": "KIMYA",
    "BİY": "BIYOLOJI",
}
# TYT icinde alt ders: (test, soru araligi) -> subject_area
TYT_ALT_DERS = {
    # 21-25: Din Kulturu'nden muaf adaylar icin ek Felsefe sorulari (kitapcikta 25 soru).
    "SOS": [
        (1, 5, "TARIH"),
        (6, 10, "COGRAFYA"),
        (11, 15, "FELSEFE"),
        (16, 20, "DIN"),
        (21, 25, "FELSEFE"),
    ],
    "FEN": [(1, 7, "FIZIK"), (8, 14, "KIMYA"), (15, 20, "BIYOLOJI")],
}
TYT_BEKLENEN = {"TÜR": 40, "SOS": 25, "MAT": 40, "FEN": 20}
# AYT 2025: TDE-SB1 (Edebiyat 1-24, Tarih-1 25-34, Cografya-1 35-40), SB2 (Tarih-2 1-11,
# Cografya-2 12-22, Felsefe grubu 23-34, Din 35-40, Din muafi ek Felsefe 41-46), MAT 40, FEN 40.
AYT_ALT_DERS = {
    "TDE-SB1": [(1, 24, "EDEBIYAT"), (25, 34, "TARIH"), (35, 40, "COGRAFYA")],
    "SB2": [
        (1, 11, "TARIH"),
        (12, 22, "COGRAFYA"),
        (23, 34, "FELSEFE"),
        (35, 40, "DIN"),
        (41, 46, "FELSEFE"),
    ],
    "FEN": [(1, 14, "FIZIK"), (15, 27, "KIMYA"), (28, 40, "BIYOLOJI")],
}
AYT_BEKLENEN = {"TDE-SB1": 40, "SB2": 46, "MAT": 40, "FEN": 40}
BEKLENEN = {"TYT": TYT_BEKLENEN, "AYT": AYT_BEKLENEN}
ALT_DERS = {"TYT": TYT_ALT_DERS, "AYT": AYT_ALT_DERS}
# Cevap anahtari sayfasinda baslik sutununu tanitan ILK kelime -> test kodu.
ANAHTAR_BASLIK = {
    "TYT": {"TÜRKÇE": "TÜR", "SOSYAL": "SOS", "TEMEL": "MAT", "FEN": "FEN"},
    "AYT": {"TÜRK": "TDE-SB1", "SOSYAL": "SB2", "MATEMATİK": "MAT", "FEN": "FEN"},
}
# Baslik kodu takma adlari: 2025 TYT matematik basligi "2025-TYT/TEM" (anahtar tablosu "MATEMATİK").
TEST_TAKMA_AD = {"TEM": "MAT"}

_BASLIK = re.compile(r"^\d{4}-(TYT|AYT|YDT)/([A-ZÇĞİÖŞÜ0-9-]+)\b")
_SORU_NO = re.compile(
    r"^(\d{1,2})\.(?:\s+(.*))?$"
)  # "2." tek basina da soru baslangici
_SIK = re.compile(r"(?:(?<=\s)|^)([A-E])\)\s*")
_ATLA = re.compile(
    r"^(\d+\s*)?(Diğer sayfaya geçiniz\.?|TEST BİTTİ\.?|.*işaretleyiniz\.?|"
    r"\d\.\s*Bu testte \d+ soru vardır\.?|\d\.\s*Cevaplarınızı, cevap kâğıdının.*|"
    r"[A-ZÇĞİÖŞÜ ]+TESTİ|E TESTİ|\d{1,2})$"
)
_ROMA = {"I", "II", "III", "IV", "V", "VI"}


@dataclass
class Kelime:
    metin: str
    x0: float
    x1: float
    top: float
    bottom: float
    alt_cizgi: bool = False
    etiket: str | None = None  # roma rakami
    boyut: float = 0.0  # font boyutu (alt/ust simge tespiti)


@dataclass
class Soru:
    test: str
    no: int
    sayfa: int
    sutun: str
    govde: list[str] = field(default_factory=list)
    siklar: dict[str, str] = field(default_factory=dict)
    son_sik: str | None = None
    top: float = 0.0
    bottom: float = 0.0
    bayraklar: set[str] = field(default_factory=set)
    anahtar: str | None = None
    parcalar: list[list[Any]] = field(
        default_factory=list
    )  # [sayfa, sutun, top, bottom]
    kucuk_yazi: int = 0

    def metin(self) -> str:
        return " ".join(p for p in self.govde if p).strip()


def _satirlar(kelimeler: list[Kelime], tol: float = 3.0) -> list[list[Kelime]]:
    """Kelimeleri `top` yakinligiyla satirlara boler (sutun icinde)."""
    satirlar: list[list[Kelime]] = []
    for k in sorted(kelimeler, key=lambda w: (round(w.top / tol), w.x0)):
        if satirlar and abs(satirlar[-1][0].top - k.top) <= tol:
            satirlar[-1].append(k)
        else:
            satirlar.append([k])
    for s in satirlar:
        s.sort(key=lambda w: w.x0)
    return satirlar


def _sutun_kelimeleri(sayfa: Any, x0: float, x1: float) -> list[Kelime]:
    ham = sayfa.crop((x0, 0, x1, sayfa.height)).extract_words(
        x_tolerance=1.5, y_tolerance=3, keep_blank_chars=False, extra_attrs=["size"]
    )
    return [
        Kelime(
            w["text"],
            w["x0"],
            w["x1"],
            w["top"],
            w["bottom"],
            boyut=float(w.get("size", 0)),
        )
        for w in ham
    ]


def _alt_cizgileri_isaretle(
    sayfa: Any, kelimeler: list[Kelime], x0: float, x1: float
) -> None:
    """Ince yatay cizgi/dikdortgenlerin hemen ustundeki kelimeler alti cizili."""
    cizgiler = []
    for c in sayfa.lines + sayfa.rects:
        if not (x0 <= c["x0"] and c["x1"] <= x1 + 1):
            continue
        if abs(c["top"] - c["bottom"]) <= 1.5 and (c["x1"] - c["x0"]) >= 6:
            cizgiler.append((c["x0"], c["x1"], c["top"]))
    for k in kelimeler:
        for cx0, cx1, ctop in cizgiler:
            if -1.0 <= ctop - k.bottom <= 4.0:
                ortusme = min(k.x1, cx1) - max(k.x0, cx0)
                if ortusme >= 0.5 * (k.x1 - k.x0):
                    k.alt_cizgi = True
                    break


def _roma_etiketle(satirlar: list[list[Kelime]]) -> None:
    """Tek basina 'I'..'VI' olan satir, ustundeki ortusen kelimeye etiket olur."""
    for i, s in enumerate(satirlar):
        if len(s) != 1 or s[0].metin not in _ROMA or i == 0:
            continue
        r = s[0]
        ust = satirlar[i - 1]
        hedef = None
        for k in ust:
            if min(k.x1, r.x1) - max(k.x0, r.x0) > -2:
                hedef = k
                break
        if hedef is None:
            hedef = min(ust, key=lambda k: abs(k.x0 - r.x0))
        hedef.etiket = r.metin
        s.clear()  # satir tuketildi


def _satir_metni(s: list[Kelime]) -> str:
    parcalar: list[str] = []
    for k in s:
        m = k.metin
        if k.alt_cizgi or k.etiket:
            m = "$\\underline{\\text{" + m + "}}"
            if k.etiket:
                m += "^{\\text{" + k.etiket + "}}"
            m += "$"
        parcalar.append(m)
    return " ".join(parcalar)


def _gorsel_var(sayfa: Any, x0: float, x1: float, top: float, bottom: float) -> bool:
    for nesne in sayfa.images + sayfa.curves:
        if nesne["x1"] < x0 or nesne["x0"] > x1:
            continue
        if nesne["bottom"] < top or nesne["top"] > bottom:
            continue
        return True
    # tablo/cerceve: boyu 5pt'den buyuk dikdortgen
    for r in sayfa.rects:
        if r["x1"] < x0 or r["x0"] > x1 or r["bottom"] < top or r["top"] > bottom:
            continue
        if abs(r["bottom"] - r["top"]) > 5 and (r["x1"] - r["x0"]) > 20:
            return True
    return False


def _anahtar_tablosu(sayfa: Any, sinav: str) -> dict[tuple[str, int], str]:
    """Cevap anahtari sayfasi: baslik satirindaki test adlari x-konumuyla sutun olur.

    'n. X' ciftleri en yakin baslik sutununa atanir (satirlar kisalinca konum
    kaymasin diye pozisyon degil x kullanilir).
    """
    kelimeler = [
        Kelime(w["text"], w["x0"], w["x1"], w["top"], w["bottom"])
        for w in sayfa.extract_words(x_tolerance=1.5, y_tolerance=3)
    ]
    satirlar = _satirlar(kelimeler)
    baslik_adi = ANAHTAR_BASLIK.get(sinav, ANAHTAR_BASLIK["TYT"])
    sutunlar: list[tuple[float, str]] = []
    for s in satirlar:
        adlar = [k for k in s if k.metin in baslik_adi]
        if len(adlar) >= 2 and any(k.metin == "TESTİ" for k in s):
            sutunlar = [(k.x0, baslik_adi[k.metin]) for k in adlar]
            break
    if not sutunlar:
        return {}
    anahtar: dict[tuple[str, int], str] = {}
    for s in satirlar:
        i = 0
        while i + 1 < len(s):
            m = re.fullmatch(r"(\d{1,2})\.", s[i].metin)
            if m and re.fullmatch(r"[A-E]", s[i + 1].metin):
                x = s[i].x0
                test = min(sutunlar, key=lambda c: abs(c[0] - x))[1]
                anahtar[(test, int(m.group(1)))] = s[i + 1].metin
                i += 2
            else:
                i += 1
    return anahtar


def _sik_parcala(metin: str) -> list[tuple[str, str]]:
    """'A) I B) II C) III' -> [('A','I'),('B','II'),('C','III')]; sik yoksa []."""
    bul = list(_SIK.finditer(metin))
    if not bul:
        return []
    parcalar = []
    for j, m in enumerate(bul):
        son = bul[j + 1].start() if j + 1 < len(bul) else len(metin)
        parcalar.append((m.group(1), metin[m.end() : son].strip()))
    return parcalar


def _sik_baslangici(son_sik: str | None, ilk_harf: str) -> bool:
    """Satir yeni sik(lar) mi baslatiyor? Siklar A'dan baslar ve artan gider;
    govdedeki '( 1H, 6C)' gibi bir 'C)' ilk sik olamaz (AYT 2025 FEN-25 vakasi)."""
    if son_sik is None:
        return ilk_harf == "A"
    return ilk_harf > son_sik


def cikar(pdf_yolu: Path) -> dict[str, Any]:  # noqa: PLR0912 -- tek gecisli durum makinesi; bolmek okunurlugu dusurur
    sorular: list[Soru] = []
    anahtar: dict[tuple[str, int], str] = {}
    meta: dict[str, Any] = {"dosya": pdf_yolu.name}
    with pdfplumber.open(str(pdf_yolu)) as pdf:
        ilk = pdf.pages[0].extract_text() or ""
        m = re.search(r"\((\d{4})-(TYT|AYT|YDT)\)", ilk)
        if m:
            meta["yil"], meta["sinav"] = int(m.group(1)), m.group(2)
        t = re.search(r"(\d{1,2} [A-ZÇĞİÖŞÜ]+ \d{4})", ilk)
        meta["tarih"] = t.group(1) if t else None
        meta["telif_notu"] = "her hakkı saklıdır" in ilk.lower()

        test: str | None = None
        beklenen = 1
        aktif: Soru | None = None
        talimat = False  # bolum basligi ile '2. Cevaplarinizi...' arasi atlanir
        talimat_alt = -1.0  # talimat blogu sayfa genisliginde: sag sutunun ayni yukseklikteki satirlari da atlanir
        for sayfa_no, sayfa in enumerate(pdf.pages, start=1):
            duz = sayfa.extract_text() or ""
            if "CEVAP ANAHTARI" in duz.upper() or (
                "TESTİ" in duz and re.search(r"\b1\. [A-E] +1\. [A-E]", duz)
            ):
                anahtar.update(_anahtar_tablosu(sayfa, meta.get("sinav", "TYT")))
                continue
            orta = sayfa.width / 2
            talimat_alt = -1.0
            for sutun, (x0, x1) in (("sol", (0.0, orta)), ("sag", (orta, sayfa.width))):
                kelimeler = _sutun_kelimeleri(sayfa, x0, x1)
                if not kelimeler:
                    continue
                _alt_cizgileri_isaretle(sayfa, kelimeler, x0, x1)
                satirlar = _satirlar(kelimeler)
                _roma_etiketle(satirlar)
                for s in satirlar:
                    if not s:
                        continue
                    ham = " ".join(k.metin for k in s)
                    b = _BASLIK.match(ham)
                    if b:
                        kod = TEST_TAKMA_AD.get(b.group(2), b.group(2))
                        if (
                            kod != test
                        ):  # yalnizca bolum degisince; baslik her sayfada tekrar eder
                            test, beklenen, aktif = kod, 1, None
                            talimat = True
                        continue
                    if talimat:
                        if ham.startswith("2. Cevaplarınızı"):
                            talimat = False
                            talimat_alt = s[-1].bottom
                        continue
                    if sutun == "sag" and s[0].top <= talimat_alt + 2:
                        continue  # talimat blogunun sag sutuna tasan kuyrugu
                    if _ATLA.match(ham):
                        continue
                    if test is None:
                        continue
                    sn = _SORU_NO.match(ham)
                    if sn and int(sn.group(1)) == beklenen:
                        aktif = Soru(test, beklenen, sayfa_no, sutun, top=s[0].top)
                        aktif.parcalar.append([sayfa_no, sutun, s[0].top, s[-1].bottom])
                        sorular.append(aktif)
                        beklenen += 1
                        if re.fullmatch(r"\d{1,2}\.", s[0].metin):
                            kalan = s[1:]
                        else:  # '1.Metin' bitisik yazilmis
                            ilk_k = s[0]
                            kalan = [
                                Kelime(
                                    re.sub(r"^\d{1,2}\.", "", ilk_k.metin),
                                    ilk_k.x0,
                                    ilk_k.x1,
                                    ilk_k.top,
                                    ilk_k.bottom,
                                    ilk_k.alt_cizgi,
                                    ilk_k.etiket,
                                )
                            ] + s[1:]
                        satir_metni = _satir_metni(kalan)
                    else:
                        if aktif is None:
                            continue
                        satir_metni = _satir_metni(s)
                    if (
                        aktif.parcalar[-1][0] != sayfa_no
                        or aktif.parcalar[-1][1] != sutun
                    ):
                        aktif.bayraklar.add("cok_parcali")  # soru sutun/sayfa asiyor
                        aktif.parcalar.append([sayfa_no, sutun, s[0].top, s[-1].bottom])
                    else:
                        aktif.parcalar[-1][3] = max(aktif.parcalar[-1][3], s[-1].bottom)
                        if aktif.sayfa == sayfa_no and aktif.sutun == sutun:
                            aktif.bottom = aktif.parcalar[-1][3]
                    if any(k.boyut and k.boyut < 8.5 for k in s):
                        aktif.kucuk_yazi += 1
                    parcalar = _sik_parcala(satir_metni)
                    # Siklar A'dan baslar; govdedeki "( 1H, 6C)" gibi bir "C)" sik degildir.
                    if parcalar and _sik_baslangici(aktif.son_sik, parcalar[0][0]):
                        on = satir_metni[: _SIK.search(satir_metni).start()].strip()
                        if on:
                            if aktif.son_sik:
                                aktif.siklar[aktif.son_sik] += " " + on
                            else:
                                aktif.govde.append(on)
                        for harf, icerik in parcalar:
                            aktif.siklar[harf] = icerik
                            aktif.son_sik = harf
                    elif aktif.son_sik:
                        aktif.siklar[aktif.son_sik] = (
                            aktif.siklar[aktif.son_sik] + " " + satir_metni
                        ).strip()
                    else:
                        aktif.govde.append(satir_metni)
                # gorsel bayragi (sutun icinde soru araligi)
                for q in sorular:
                    if (
                        q.sayfa == sayfa_no
                        and q.sutun == sutun
                        and _gorsel_var(sayfa, x0, x1, q.top, q.bottom or sayfa.height)
                    ):
                        q.bayraklar.add("gorsel")
    for q in sorular:
        q.anahtar = anahtar.get((q.test, q.no))
        if "\\underline" in q.metin() or any(
            "\\underline" in v for v in q.siklar.values()
        ):
            q.bayraklar.add("alt_cizgi")
        if "^{\\text{" in q.metin():
            q.bayraklar.add("roma")
        if len(q.siklar) != 5:
            q.bayraklar.add(f"sik_{len(q.siklar)}")
        if any(not v.strip() for v in q.siklar.values()):
            q.bayraklar.add("sik_bos")  # sik icerigi grafik (formul) -- metin yok
        if not q.metin().strip():
            q.bayraklar.add("govde_bos")
        if q.kucuk_yazi:
            q.bayraklar.add(
                "alt_ust_simge"
            )  # 8pt alt/ust simge (kimya formulu vb.), metinde duz akiyor
        if not q.anahtar:
            q.bayraklar.add("anahtar_yok")
    return {"meta": meta, "sorular": sorular, "anahtar_sayisi": len(anahtar)}


KIRP_GEREKTIREN = {
    "gorsel",
    "sik_bos",
    "govde_bos",
    "alt_cizgi",
    "roma",
    "cok_parcali",
    "alt_ust_simge",
}


def kirp(
    pdf_yolu: Path, sorular: list[Soru], hedef: Path, onek: str, cozunurluk: int = 150
) -> dict[tuple[str, int], str]:
    """Bayrakli sorularin sutun icindeki bolgesini PNG olarak kaydeder.

    Ogrenciye ozgun dizgi (formul, sekil, alti cizili soz) gosterilsin diye;
    metin arama/embedding icin ayrica saklanir. Dosya adi mevcut crops
    sozlesmesiyle ayni: <onek>/<onek>_p####_q##.png (bkz. /static/crops).
    """
    hedef.mkdir(parents=True, exist_ok=True)
    yollar: dict[tuple[str, int], str] = {}
    with pdfplumber.open(str(pdf_yolu)) as pdf:
        for q in sorular:
            if not (q.bayraklar & KIRP_GEREKTIREN):
                continue
            goruntuler = []
            for sayfa_no, sutun, top, bottom in q.parcalar:
                sayfa = pdf.pages[sayfa_no - 1]
                orta = sayfa.width / 2
                x0, x1 = (0.0, orta) if sutun == "sol" else (orta, sayfa.width)
                ust = max(0.0, top - 4)
                alt = min(sayfa.height, bottom + 4)
                goruntuler.append(
                    sayfa.crop((x0 + 6, ust, x1 - 6, alt))
                    .to_image(resolution=cozunurluk)
                    .original
                )
            ad = f"{onek}_p{q.sayfa:04d}_{q.test}_q{q.no:02d}.png"
            if len(goruntuler) == 1:
                goruntuler[0].save(str(hedef / ad))
            else:
                from PIL import Image

                genislik = max(g.width for g in goruntuler)
                yukseklik = sum(g.height for g in goruntuler)
                tuval = Image.new("RGB", (genislik, yukseklik), "white")
                y = 0
                for g in goruntuler:
                    tuval.paste(g, (0, y))
                    y += g.height
                tuval.save(str(hedef / ad))
            yollar[(q.test, q.no)] = ad
    return yollar


def ders_alani(sinav: str, test: str, no: int) -> str:
    if test in ALT_DERS.get(sinav, {}):
        for a, b, ders in ALT_DERS[sinav][test]:
            if a <= no <= b:
                return ders
    return TEST_KODU_DERS.get(test, test)


def ozet(sonuc: dict[str, Any]) -> dict[str, Any]:
    sorular: list[Soru] = sonuc["sorular"]
    test_sayim = Counter(q.test for q in sorular)
    bayrak_sayim: Counter[str] = Counter()
    for q in sorular:
        bayrak_sayim.update(q.bayraklar)
    sik_dagilimi = Counter(q.anahtar for q in sorular if q.anahtar)
    return {
        "toplam_soru": len(sorular),
        "test_basina": dict(test_sayim),
        "anahtar_tablosu": sonuc["anahtar_sayisi"],
        "anahtari_olan": sum(1 for q in sorular if q.anahtar),
        "bes_sikli": sum(1 for q in sorular if len(q.siklar) == 5),
        "bayraklar": dict(bayrak_sayim),
        "anahtar_dagilimi": dict(sorted(sik_dagilimi.items())),
    }


def json_kayitlari(
    sonuc: dict[str, Any], gorseller: dict[tuple[str, int], str] | None = None
) -> list[dict[str, Any]]:
    sinav = sonuc["meta"].get("sinav", "")
    gorseller = gorseller or {}
    kayitlar = []
    for q in sonuc["sorular"]:
        kayitlar.append(
            {
                "test": q.test,
                "no": q.no,
                "sayfa": q.sayfa,
                "sutun": q.sutun,
                "subject_area": ders_alani(sinav, q.test, q.no),
                "question_text": q.metin(),
                "options": {h: q.siklar.get(h, "") for h in "ABCDE"},
                "correct_answer": q.anahtar,
                "bayraklar": sorted(q.bayraklar),
                "gorsel_dosya": gorseller.get((q.test, q.no)),
            }
        )
    return kayitlar


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("pdf")
    p.add_argument(
        "--cikti", help="JSON cikti yolu (varsayilan: pdf ile ayni ad .json)"
    )
    p.add_argument(
        "--beklenen", help="test:adet,... (varsayilan TYT: TÜR:40,SOS:25,MAT:40,FEN:20)"
    )
    p.add_argument(
        "--kirp",
        help="bayrakli sorularin PNG kirpilarinin yazilacagi dizin (orn. ../d-dataset/output/crops/OSYM_2025_TYT)",
    )
    args = p.parse_args()
    pdf_yolu = Path(args.pdf)
    sonuc = cikar(pdf_yolu)
    oz = ozet(sonuc)
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    print(json.dumps({"meta": sonuc["meta"], "ozet": oz}, ensure_ascii=False, indent=2))

    beklenen = dict(BEKLENEN.get(sonuc["meta"].get("sinav", ""), {}))
    if args.beklenen:
        beklenen = {
            k: int(v) for k, v in (c.split(":") for c in args.beklenen.split(","))
        }
    sapma = {
        t: (oz["test_basina"].get(t, 0), n)
        for t, n in beklenen.items()
        if oz["test_basina"].get(t, 0) != n
    }
    gorseller: dict[tuple[str, int], str] = {}
    if args.kirp:
        hedef = Path(args.kirp)
        gorseller = kirp(pdf_yolu, sonuc["sorular"], hedef, hedef.name)
        print(f"kirpildi: {len(gorseller)} PNG -> {hedef}")
    cikti = Path(args.cikti) if args.cikti else pdf_yolu.with_suffix(".json")
    cikti.write_text(
        json.dumps(
            {
                "meta": sonuc["meta"],
                "ozet": oz,
                "sorular": json_kayitlari(sonuc, gorseller),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"yazildi: {cikti}")
    if sapma:
        print(f"SAPMA (bulunan, beklenen): {sapma}")
        return 1
    if oz["anahtari_olan"] != oz["toplam_soru"]:
        print("SAPMA: anahtarsiz soru var")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
