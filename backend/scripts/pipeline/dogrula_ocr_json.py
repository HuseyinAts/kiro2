"""OCR JSON ciktilarini manifest'e ve yapisal kurallara karsi DOGRULA.

Ureticiye (ajan/model) GUVENMEZ: JSON'un kendi 'count_matches' alanini da
bagimsiz olarak yeniden hesaplar ve yalan soyluyorsa isaretler.

Kontroller:
  K1  soru sayisi == manifest.beklenen_soru
  K2  sol/sag dagilimi == manifest sol_sutun/sag_sutun
  K3  count_matches alani DURUST mu (gercek durumla ayni mi)
  K4  correct_answer in {A,B,C,D,E,null}; null orani raporlanir
  K5  options: A-D dolu (E opsiyonel), bos string yok
  K6  kisaltma izi yok ('...', '…' ile biten metin)
  K7  metin NFC normalize
  K8  soru numaralari sayfa icinde artan
  K9  ayni sayfada tekrar eden soru metni yok (sol/sag bindirme artefakti)
  K10 sayfalar arasi tekrar eden soru metni yok
  K11 soru numaralari sayfalar arasi surekli (atlanan soru / kopyalanan sayfa)

Kullanim:
    python dogrula_ocr_json.py --kitap "345 2025 Tyt Biyoloji Soru Bankası"
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import unicodedata
from pathlib import Path

if isinstance(sys.stdout, io.TextIOWrapper):  # cp1254 konsolda Turkce cokmesin
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
GECERLI_CEVAP = {"A", "B", "C", "D", "E", None}


def _sayfa_kontrolleri(
    ad: str, d: dict, m: dict, sorular: list, kusurlar: list[str]
) -> int:
    """K1-K3: sayi, sutun dagilimi ve ureticinin KENDI beyaninin durustlugu.

    Donus: manifest'in bekledigi soru sayisi.
    """
    bekl = int(m["beklenen_soru"])
    bekl_sol, bekl_sag = int(m["sol_sutun"]), int(m["sag_sutun"])

    if len(sorular) != bekl:
        kusurlar.append(f"{ad}: K1 soru sayisi {len(sorular)} != manifest {bekl}")

    sol = sum(1 for q in sorular if q.get("column") == "sol")
    sag = sum(1 for q in sorular if q.get("column") == "sag")
    if (sol, sag) != (bekl_sol, bekl_sag):
        kusurlar.append(
            f"{ad}: K2 sutun dagilimi ({sol},{sag}) != manifest ({bekl_sol},{bekl_sag})"
        )

    gercek = len(sorular) == bekl
    # count_matches=null -> uretici "olcemedim" diyor (orn. manifest okunamadi).
    # Bu DURUST bir beyan yoklugudur; yalan beyan degil, K3 bunu cezalandirmaz.
    if d.get("count_matches") is not None and bool(d["count_matches"]) != gercek:
        kusurlar.append(
            f"{ad}: K3 count_matches={d['count_matches']} ama gercek={gercek} (YANLIS BEYAN)"
        )
    if d.get("extracted_question_count") not in (None, len(sorular)):
        kusurlar.append(
            f"{ad}: K3 extracted_question_count={d.get('extracted_question_count')} "
            f"ama dizi uzunlugu {len(sorular)}"
        )
    return bekl


def _soru_kontrolleri(etiket: str, q: dict, kusurlar: list[str]) -> tuple[bool, str]:
    """K4-K7: cevap, secenekler, kisaltma izi, NFC.

    Donus: (cevap_null_mi, tekillik_anahtari).
    """
    ca = q.get("correct_answer")
    if ca not in GECERLI_CEVAP:
        kusurlar.append(f"{etiket}: K4 gecersiz correct_answer={ca!r}")

    ops = q.get("options") or {}
    for harf in ("A", "B", "C", "D"):
        if not (ops.get(harf) or "").strip():
            kusurlar.append(f"{etiket}: K5 secenek {harf} bos/eksik")
    if ca and ca in ops and not (ops.get(ca) or "").strip():
        kusurlar.append(f"{etiket}: K5 dogru cevap {ca} secenegi bos")

    metin = q.get("question_text") or ""
    parcalar = [metin, *[str(v) for v in ops.values() if v]]
    kisa = next((p for p in parcalar if p.rstrip().endswith(("...", "…"))), None)
    if kisa is not None:
        kusurlar.append(f"{etiket}: K6 kisaltma izi -> {kisa[-40:]!r}")
    if any(unicodedata.normalize("NFC", p) != p for p in parcalar):
        kusurlar.append(f"{etiket}: K7 NFC degil")
    if len(metin.strip()) < 15:
        kusurlar.append(f"{etiket}: K6 soru metni cok kisa ({len(metin)} krk)")

    # Tekillik anahtari metin + SIKLAR (pilot_500p.soru_hash ile ayni sozlesme).
    # Yalniz soru koku kullanmak yanlis-pozitif uretir: "Asagidakilerden hangisi
    # tum canlilarin ortak ozelligi degildir?" koku kitapta iki FARKLI soruda
    # geciyor (2018 MSU ve 2025), siklari ayri.
    anahtar = " ".join(
        [
            " ".join(metin.split()),
            *[f"{h}:{(ops.get(h) or '').strip()}" for h in "ABCDE"],
        ]
    ).lower()
    return ca is None, anahtar


def _sureklilik_kontrol(
    sayfalar: dict[int, tuple[int, int]], kusurlar: list[str]
) -> None:
    """K11: soru numaralari SAYFALAR ARASI surekli mi.

    Kitapta numaralandirma test boyunca artar ve yeni testin ilk sayfasinda 1'e
    doner. Bir sayfada soru ATLANMISSA zincir kirilir -- bu, sayfa-ici hicbir
    kontrolun goremeyecegi bir kusur sinifidir (sayi manifestle tutsa bile).
    Ayni sekilde bir sayfanin icerigi baska sayfaya KOPYALANMISSA numaralar
    tekrar eder ve yine burada gorunur.
    """
    for no in sorted(sayfalar):
        ilk, _son = sayfalar[no]
        onceki = sayfalar.get(no - 1)
        if onceki is None or ilk == 1:
            continue  # kitabin ilk sayfasi, kapak atlamasi veya yeni test
        if ilk != onceki[1] + 1:
            kusurlar.append(
                f"sayfa_{no:04d}: K11 numara zinciri kirik -- onceki sayfa {onceki[1]} "
                f"ile bitti, bu sayfa {ilk} ile basliyor"
            )


def _tekrar_kontrol(
    etiket: str,
    ad: str,
    anahtar: str,
    *,
    sayfa_metinleri: set[str],
    metin_sahibi: dict[str, str],
    kusurlar: list[str],
) -> None:
    """K9/K10: ayni sayfada ve sayfalar arasi kopya soru."""
    if not anahtar.strip(" ABCDE:"):
        return
    if anahtar in sayfa_metinleri:
        kusurlar.append(f"{etiket}: K9 ayni sayfada TEKRAR eden soru metni")
    sayfa_metinleri.add(anahtar)
    if anahtar in metin_sahibi and metin_sahibi[anahtar] != ad:
        kusurlar.append(f"{etiket}: K10 metin {metin_sahibi[anahtar]} ile AYNI")
    metin_sahibi.setdefault(anahtar, ad)


def dogrula(hedef: Path) -> int:
    manifest = {
        r["dosya"][:-4]: r
        for r in csv.DictReader((hedef / "manifest.csv").open(encoding="utf-8"))
    }
    json_dizin = hedef / "ocr_json"
    dosyalar = sorted(json_dizin.glob("sayfa_*.json"))
    if not dosyalar:
        print(f"HATA: {json_dizin} icinde JSON yok")
        return 2

    kusurlar: list[str] = []
    toplam_soru = bos_cevap = 0
    supheli_sayfa = 0
    metin_sahibi: dict[str, str] = {}
    sayfa_numaralari: dict[int, tuple[int, int]] = {}
    beklenen_toplam = 0

    for f in dosyalar:
        ad = f.stem
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            kusurlar.append(f"{ad}: JSON PARSE HATASI -> {e}")
            continue

        m = manifest.get(ad)
        if m is None:
            kusurlar.append(f"{ad}: manifest'te yok")
            continue
        sorular = d.get("questions") or []
        toplam_soru += len(sorular)
        beklenen_toplam += _sayfa_kontrolleri(ad, d, m, sorular, kusurlar)

        numaralar = []
        sayfa_metinleri: set[str] = set()
        for i, q in enumerate(sorular):
            etiket = f"{ad}#{i + 1}"
            bos, anahtar = _soru_kontrolleri(etiket, q, kusurlar)
            bos_cevap += int(bos)
            # K8
            no = q.get("question_number_on_page")
            if isinstance(no, int):
                numaralar.append(no)
            _tekrar_kontrol(
                etiket,
                ad,
                anahtar,
                sayfa_metinleri=sayfa_metinleri,
                metin_sahibi=metin_sahibi,
                kusurlar=kusurlar,
            )

        if numaralar:
            sayfa_numaralari[int(ad.split("_")[1])] = (numaralar[0], numaralar[-1])
        if numaralar != sorted(numaralar):
            kusurlar.append(f"{ad}: K8 soru numaralari artan degil -> {numaralar}")

        if (d.get("page_notes") or "").strip():
            supheli_sayfa += 1

    _sureklilik_kontrol(sayfa_numaralari, kusurlar)

    print(f"islenen sayfa: {len(dosyalar)} / manifest soru sayfasi: {len(manifest)}")
    print(
        f"cikarilan soru: {toplam_soru} | bu sayfalar icin beklenen: {beklenen_toplam}"
    )
    print(f"cevabi null olan soru: {bos_cevap}")
    print(f"page_notes dolu sayfa (supheli/uyari tasiyan): {supheli_sayfa}")
    print(f"KUSUR: {len(kusurlar)}")
    for k in kusurlar[:40]:
        print(f"  {k}")
    if len(kusurlar) > 40:
        print(f"  ... +{len(kusurlar) - 40} kusur daha")
    return 1 if kusurlar else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kitap", required=True)
    args = ap.parse_args()
    hedef = KOK / args.kitap / f"temiz {args.kitap}"
    if not hedef.is_dir():
        print(f"HATA: {hedef} yok")
        return 2
    return dogrula(hedef)


if __name__ == "__main__":
    raise SystemExit(main())
