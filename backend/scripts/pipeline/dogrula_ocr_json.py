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

Kullanim:
    python dogrula_ocr_json.py --kitap "345 2025 Tyt Biyoloji Soru Bankası"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

KOK = Path(r"C:\Users\husey\kiro2\veriseti\zkitap\screenshots")
GECERLI_CEVAP = {"A", "B", "C", "D", "E", None}


def _sayim_kontrol(
    ad: str, d: dict, sorular: list, m: dict, kusurlar: list[str]
) -> None:
    """K1/K2/K3 -- sayfa duzeyindeki sayim ve beyan kontrolleri."""
    bekl = int(m["beklenen_soru"])
    bekl_sol, bekl_sag = int(m["sol_sutun"]), int(m["sag_sutun"])
    # K1
    if len(sorular) != bekl:
        kusurlar.append(f"{ad}: K1 soru sayisi {len(sorular)} != manifest {bekl}")
    # K2
    sol = sum(1 for q in sorular if q.get("column") == "sol")
    sag = sum(1 for q in sorular if q.get("column") == "sag")
    if (sol, sag) != (bekl_sol, bekl_sag):
        kusurlar.append(
            f"{ad}: K2 sutun dagilimi ({sol},{sag}) != manifest ({bekl_sol},{bekl_sag})"
        )
    # K3 - ureticinin kendi beyani durust mu
    gercek = len(sorular) == bekl
    if "count_matches" in d and bool(d["count_matches"]) != gercek:
        kusurlar.append(
            f"{ad}: K3 count_matches={d['count_matches']} ama gercek={gercek} (YANLIS BEYAN)"
        )
    if d.get("extracted_question_count") not in (None, len(sorular)):
        kusurlar.append(
            f"{ad}: K3 extracted_question_count={d.get('extracted_question_count')} "
            f"ama dizi uzunlugu {len(sorular)}"
        )


def _soru_kontrol(etiket: str, q: dict, kusurlar: list[str]) -> str:
    """K4-K7 -- soru duzeyi kontrolleri; tekillik anahtarini dondurur.

    K9/K10 anahtari metin + SIKLAR (pilot_500p.soru_hash ile ayni sozlesme).
    Yalniz soru koku kullanmak yanlis-pozitif uretir: "Asagidakilerden
    hangisi tum canlilarin ortak ozelligi degildir?" koku kitapta iki FARKLI
    soruda geciyor (2018 MSU ve 2025), siklari ayri.
    """
    # K4
    ca = q.get("correct_answer")
    if ca not in GECERLI_CEVAP:
        kusurlar.append(f"{etiket}: K4 gecersiz correct_answer={ca!r}")
    # K5
    ops = q.get("options") or {}
    for harf in ("A", "B", "C", "D"):
        if not (ops.get(harf) or "").strip():
            kusurlar.append(f"{etiket}: K5 secenek {harf} bos/eksik")
    if ca and ca in ops and not (ops.get(ca) or "").strip():
        kusurlar.append(f"{etiket}: K5 dogru cevap {ca} secenegi bos")
    # K6 + K7
    metin = q.get("question_text") or ""
    parcalar = [metin, *[str(v) for v in ops.values() if v]]
    for p in parcalar:
        if p.rstrip().endswith(("...", "…")):
            kusurlar.append(f"{etiket}: K6 kisaltma izi -> {p[-40:]!r}")
            break
    for p in parcalar:
        if unicodedata.normalize("NFC", p) != p:
            kusurlar.append(f"{etiket}: K7 NFC degil")
            break
    if len(metin.strip()) < 15:
        kusurlar.append(f"{etiket}: K6 soru metni cok kisa ({len(metin)} krk)")
    return " ".join(
        [
            " ".join(metin.split()),
            *[f"{h}:{(ops.get(h) or '').strip()}" for h in "ABCDE"],
        ]
    ).lower()


def _sayfa_dogrula(
    ad: str,
    d: dict,
    m: dict,
    metin_sahibi: dict[str, str],
    kusurlar: list[str],
) -> tuple[int, int, int]:
    """Bir sayfayi dogrular; (soru sayisi, bos cevap, supheli) dondurur."""
    sorular = d.get("questions") or []
    _sayim_kontrol(ad, d, sorular, m, kusurlar)

    bos_cevap = 0
    numaralar: list[int] = []
    sayfa_metinleri: set[str] = set()
    for i, q in enumerate(sorular):
        etiket = f"{ad}#{i + 1}"
        anahtar = _soru_kontrol(etiket, q, kusurlar)
        if q.get("correct_answer") is None:
            bos_cevap += 1
        # K8
        no = q.get("question_number_on_page")
        if isinstance(no, int):
            numaralar.append(no)
        # K9 / K10 -- anahtar her zaman doludur (sik etiketleri hep var), bu
        # yuzden orijinaldeki `if anahtar:` korumasi kaldirildi: davranis ayni.
        if anahtar in sayfa_metinleri:
            kusurlar.append(f"{etiket}: K9 ayni sayfada TEKRAR eden soru metni")
        sayfa_metinleri.add(anahtar)
        if anahtar in metin_sahibi and metin_sahibi[anahtar] != ad:
            kusurlar.append(f"{etiket}: K10 metin {metin_sahibi[anahtar]} ile AYNI")
        metin_sahibi.setdefault(anahtar, ad)

    if numaralar != sorted(numaralar):
        kusurlar.append(f"{ad}: K8 soru numaralari artan degil -> {numaralar}")
    supheli = 1 if (d.get("page_notes") or "").strip() else 0
    return len(sorular), bos_cevap, supheli


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
        beklenen_toplam += int(m["beklenen_soru"])
        adet, bos, supheli = _sayfa_dogrula(ad, d, m, metin_sahibi, kusurlar)
        toplam_soru += adet
        bos_cevap += bos
        supheli_sayfa += supheli

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
